# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""

import ctypes
import traceback
import sys
import time
import _thread
from threading import Thread
import threading
import json
import datetime
import pickle
import functools
import os
from os import path, listdir
import gc
import subprocess as sp

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from mcvqoe import write_log
from mcvqoe.simulation.QoEsim import QoEsim
from mcvqoe import hardware



import tkinter.messagebox as msb
import tkinter.filedialog as fdl
import tkinter.font as font
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk

import shared
from shared import Abort_by_User, InvalidParameter
import loadandsave
import accesstime_gui
from accesstime_gui import AccssDFrame
import m2e_gui
from m2e_gui import M2eFrame
import psud_gui
from psud_gui import PSuDFrame


# basic config
TITLE_ = 'MCV QoE'

WIN_SIZE = (900, 750)


control_list = {
    'EmptyFrame': [],
    
    'TestInfoGuiFrame': [
            'Test Type',
            'Tx Device',
            'Rx Device',
            'System',
            'Test Loc'
            ],
    
    'PostTestGuiFrame': [],
    
    'TestProgressFrame': [],
    
    'PostProcessingFrame': [],
    
    'M2eFrame': [
        'audio_files',
        'bgnoise_file',
        'bgnoise_volume',
        'outdir',
        'ptt_wait',
        'test',
        'trials'
    ],

    'AccssDFrame': [
        'audio_files',
        'audio_path',
        'auto_stop',
        'bgnoise_file',
        'bgnoise_volume',
        'data_file',
        'outdir',
        'ptt_gap',
        'ptt_rep',
        'ptt_step',
        's_thresh',
        's_tries',
        'stop_rep',
        'trials',
        'dev_dly',
    ],
    
    'PSuDFrame' : [
        'audio_files',
        'audio_path',
        'trials',
        'outdir',
        'ptt_wait',
        'ptt_gap',
        'm2e_min_corr',
        'intell_est',
    ],
        
    'SimSettings': [
        'overplay',
        'channel_tech',
        'channel_rate',
        'm2e_latency',
        'access_delay',
        'rec_snr',
        'PTT_sig_freq',
        'PTT_sig_aplitude',
    ],
    
    'HdwSettings' : [
        
        'overplay',
        'radioport',
        'dev_dly',
        'blocksize',
        'buffersize',
        ]
}

initial_measure_objects = {
    'M2eFrame': m2e_gui.m2e.measure(),
    'AccssDFrame': accesstime_gui.adly.Access(),
    'PSuDFrame' : psud_gui.psud.measure(),
    'SimSettings': QoEsim(),
    'HdwSettings': shared._HdwPrototype()
    }


# load default values from objects
DEFAULTS = {}
for name_, key_group in control_list.items():
    
    DEFAULTS[name_] = {}
    
    if name_ in initial_measure_objects:
        obj = initial_measure_objects[name_]
        
        for key in key_group:
            if hasattr(obj, key):
                DEFAULTS[name_][key] = getattr(obj, key)

#values that require more than one control
DEFAULTS['AccssDFrame']['_ptt_delay_min'] = initial_measure_objects[
    'AccssDFrame'].ptt_delay[0]
try:
    DEFAULTS['AccssDFrame']['_ptt_delay_max'] = str(initial_measure_objects[
        'AccssDFrame'].ptt_delay[1])
except IndexError:
    DEFAULTS['AccssDFrame']['_ptt_delay_max'] = '<default>'
    
for k in ('AccssDFrame','PSuDFrame'):
    DEFAULTS[k]['_time_expand_i'] = initial_measure_objects[k].time_expand[0]
    try:
        DEFAULTS[k]['_time_expand_f'] = str(initial_measure_objects[
            k].time_expand[1])
    except IndexError:
        DEFAULTS[k]['_time_expand_f'] = '<default>'

#the following should be a string, not any other type
DEFAULTS['AccssDFrame']['trials'] = str(int(DEFAULTS['AccssDFrame']['trials']))

DEFAULTS['SimSettings']['channel_rate'] = str(DEFAULTS['SimSettings']['channel_rate'])


# the following should be a float
DEFAULTS['SimSettings']['access_delay'] = float(DEFAULTS['SimSettings']['access_delay'])

#free initial objects
del initial_measure_objects
del obj


    
    
def in_thread(thread, wait=True):
    """A function decorator to ensure that a function runs in the given thread.
    
    thread: can be {'GuiThread', 'MainThread'}
        the thread to run the function in
    wait:
        whether to wait for the function to return in the other thread
        if this is false, it may or may not return None.
    
    Example:
        
        @in_thread('MainThread')
        def my_mainthread_func(*args, **kwargs):
            print('Hello from the main thread!')
        
    """
    if thread not in ('MainThread', 'GuiThread'):
        raise ValueError(f'Thread {thread} does not exist')
        
    def decorator(func):
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            
            
                
            
            if thread == threading.current_thread().getName():
                # we are already in that thread!!
                return func(*args, **kwargs)
            
            switch_obj = _dec_return(func, args, kwargs)
            
            if thread == 'MainThread':
                main.callback(switch_obj.callbacker)
            elif thread == 'GuiThread':
                main.gui_thread.callback(switch_obj.callbacker)
            
            
            # wait until function is finished if applicable
            while wait and not switch_obj.finished:
                if thread == 'MainThread':
                    # keep the gui responsive
                    main.win.update_idletasks()
                    
                time.sleep(0.1)
                
            if wait:
                return switch_obj.return_val
                
            
        return wrapper
    return decorator

class _dec_return:
    def __init__(self, func, args, kwargs):
        
        self.func = func
        self.finished = False
        self.args = args
        self.kwargs = kwargs

    def callbacker(self):
        self.return_val = self.func(*self.args, **self.kwargs)
        self.finished = True
        










class MCVQoEGui(tk.Tk):
    """The main window


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        
        
        # when the user closes the window
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # dpi scaling
        dpi_scaling(self)

        # indicates that the user does not need to save the configuration
        self.set_saved_state(True)

        # dimensions
        self.minsize(width=600, height=370)
        self.geometry(f'{WIN_SIZE[0]}x{WIN_SIZE[1]}')

        # tcl variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')

        # change test frame when user selects a test
        self.selected_test.trace_add(
            'write', lambda a, b, c: self._select_test())
        
        # initiate left frame with logo and test selections
        self.LeftFrame = LeftFrame(self, main_=self)
        self.LeftFrame.pack(side=tk.LEFT, fill=tk.Y)
        
        # initiate row of buttons on bottom of window
        BottomButtons(master=self).pack(side=tk.BOTTOM, fill=tk.X,
                                        padx=10, pady=10)
        
        # the frame containing the meat of the software
        self.RightFrame = shared.ScrollableFrame(self)
        

        # handling changing of window size
        self.bind('<Configure>', self.LeftFrame.on_change_size)
        
        # binding keyboard shortcuts
        self.bind('<Control-s>', self.save)
        self.bind('<Control-S>', self.save)
        self.bind('<Control-o>', self.open_)
        self.bind('<Control-O>', self.open_)
        self.bind('<Control-Shift-s>', self.save_as)
        self.bind('<Control-Shift-S>', self.save_as)
        self.bind('<Control-w>', self.restore_defaults)
        self.bind('<Control-W>', self.restore_defaults)
        self.bind('<MouseWheel>', self.RightFrame.scroll)
        self.bind('<Button-5>', self.RightFrame.scroll)
        self.bind('<Button-4>', self.RightFrame.scroll)
        
        # create test-specific frames
        
        self._init_frames()
        
        # sets the current frame to be blank
        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        
        # instance vars
        self.controls = {}
        self._red_controls = []
        self.cnf_filepath = None
        self.is_destroyed = False
        self.set_step(0)



    def _init_frames(self):
        """consructs the test-specific frames"""
        frame_types = [
            EmptyFrame,
            TestInfoGuiFrame,
            PostTestGuiFrame,
            TestProgressFrame,
            PostProcessingFrame,
            
            M2eFrame,
            AccssDFrame,
            PSuDFrame,
            
        ]
                
        self.frames = {}
        for F in frame_types:
            
            btnvars = loadandsave.TkVarDict(**DEFAULTS[F.__name__])
            
            if F in (AccssDFrame, PostProcessingFrame):
                parent=self.RightFrame
            else:
                parent=self
            
            # initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=parent, btnvars=btnvars)

            # when user changes a control
            btnvars.on_change = self.on_change
        
        self.simulation_settings = loadandsave.TkVarDict(
            **DEFAULTS['SimSettings'])
        
        self.hardware_settings = loadandsave.TkVarDict(
            **DEFAULTS['HdwSettings'])
        
        
        

    def _select_test(self):
        if self.step in (0, 1):
            self.configure_test()
    
    
    @in_thread('GuiThread', wait=False)
    def configure_test(self):
        """Called when the user changes the selected test.
        Changes the frame to show the proper test configuration"""
        
        self.set_step(1)

    def show_frame(self, framename):
        # first hide the showing widget
        self.currentframe.pack_forget()
        try:
            self.currentframe = self.frames[framename]
        finally:
            self.currentframe.pack(side=tk.RIGHT,
                                   fill=tk.BOTH, padx=10, pady=10, expand=True)
            
        if self.currentframe.master is self.RightFrame:
            self.RightFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        else:
            self.RightFrame.pack_forget()

    def is_empty(self):
        return self.currentframe == self.frames['EmptyFrame']

    def on_change(self, *args, **kwargs):
        self.set_saved_state(False)

    def on_close(self):
        if self.ask_save():
            # canceled by user
            return
        if main.is_running and self.abort():
            # abort was canceled by user
            return
        
        # destroy plots to prevent errors
        self.frames['PostProcessingFrame'].reset()
        
        main.stop()
        #waits for test to close gracefully, then destroys window
        self.after(50, self._wait_to_destroy)
        
        
    def _wait_to_destroy(self):
        if main.is_running:
            self.after(50, self._wait_to_destroy)
        else:
            #destroy any open plots (they otherwise raise errors)
            self.frames['PostProcessingFrame'].reset()
            gc.collect(2)
            
            self.destroy()
            
    def destroy(self, *args, **kwargs):
        super().destroy(*args, **kwargs)
        self.is_destroyed = True
            
    def restore_defaults(self, *args, **kwargs):
        if self.ask_save():
            # cancelled
            return
        
        for fname, f in self.frames.items():
            f.btnvars.set(DEFAULTS[fname])
            
        
        self.is_simulation.set(False)
        
        # user shouldn't be prompted to save the default config
        self.set_saved_state(True)

    def open_(self, *args, **kwargs):
        """Loads config from .json file
        """
        if self.ask_save():
            # cancelled
            return

        fpath = fdl.askopenfilename(
            filetypes=[('json files', '*.json')]
        )

        if not fpath:
            # canceled by user
            return

        with open(fpath, 'r') as fp:

            dct = json.load(fp)
            for frame_name, frame in self.frames.items():
                if frame_name in dct:
                    frame.btnvars.set(dct[frame_name])

            self.is_simulation.set(dct['is_simulation'])
            self.selected_test.set(dct['selected_test'])
            self.set_step(1)

            # the user has not modified the new config, so it is saved
            self.set_saved_state(True)

            # 'save' will now save to this file
            self.cnf_filepath = fpath

    def save_as(self, *args, **kwargs) -> bool:
        """



        Returns
        -------
        cancelled : bool
            True if the save was cancelled.

        """
        fp = fdl.asksaveasfilename(filetypes=[('json files', '*.json')],
                                   defaultextension='.json')
        if fp:
            self.cnf_filepath = fp
            return self.save()
        else:
            return True

    def save(self, *args, **kwargs) -> bool:
        """Saves config to .json file

        Returns True if the save was cancelled
        """
        # if user hasnt saved or loaded
        if not self.cnf_filepath:
            return self.save_as()

        with open(self.cnf_filepath, mode='w') as fp:

            obj = self.get_cnf()

            json.dump(obj, fp)
            self.set_saved_state(True)
        return False

    def ask_save(self) -> bool:
        """Prompts the user to save the config


        Returns
        -------
        cancel : bool
            True if the user pressed 'cancel', indicating that the action
            should be cancelled.

        """
        if self.is_saved:
            # no need to ask!
            return False

        out = msb.askyesnocancel(title='Warning',
                                 message='Would you like to save unsaved changes?')
        if out:
            return self.save()
        else:
            # true if user cancelled
            return out is None

    def set_saved_state(self, is_saved: bool = True):
        """changes whether or not the program considers the config unmodified


        Parameters
        ----------
        is_saved : bool, optional
            Is the config yet unmodified by the user?. The default is True.

        """
        self.is_saved = is_saved

        # puts a star in the window title for unsaved file
        if self.is_saved:
            self.title(f'{TITLE_}')
        else:
            self.title(f'{TITLE_}*')

    def get_cnf(self):
        obj = {
            'is_simulation': self.is_simulation.get(),
            'selected_test': self.selected_test.get(),
            'SimSettings'  : self.simulation_settings.get(),
            'HdwSettings'  : self.hardware_settings.get(),
        }

        for framename, frame in self.frames.items():
            obj[framename] = frame.btnvars.get()
        
        txt_box = self.frames['TestInfoGuiFrame'].pre_notes
        
        # gets 'Pre Test Notes' from text widget
        obj['TestInfoGuiFrame']['Pre Test Notes'] = txt_box.get(1.0, tk.END)
        
        
        
        return obj
    

    def verify_config(self, root_cfg):
        try:
            #translate cfg items as necessary
            param_modify(root_cfg)
            
        except InvalidParameter as e:
            # highlight the offending control in red
            
            if e.param_loc == 'SimSettings':
                shared.SimSettings(self, self.simulation_settings)
                loc = self
            elif e.param_loc == 'HdwSettings':
                shared.HdwSettings(self, self.hardware_settings)
                loc = self
            else:
                loc = self.frames[root_cfg['selected_test']]
                
            try:
                ctrl = loc.controls[e.parameter].m_ctrl
            except AttributeError:
                ctrl = None
            
            if ctrl is not None:
                # make the control red
                ctrl.configure(style='Error.' + ctrl.winfo_class())
                
                # create a tooltip
                tw = shared.ToolTip(
                    ctrl,
                    e.message,
                    style='Error.McvToolTip.TLabel')
                # get location of control
                x, y, cx, cy = ctrl.bbox("insert")
                rootx = self.winfo_rootx()
        
                # calculate location of tooltip
                x = x + ctrl.winfo_rootx() - tw.winfo_width()
                y = y + cy + ctrl.winfo_rooty() + 27
        
                #ensure tooltip does not fall off left edge of window
                if x < rootx + 20: x = rootx + 20
                
                # set position of tooltip
                tw.wm_geometry("+%d+%d" % (x, y))
                ctrl.bind('<FocusOut>', lambda _e: tw.destroy())
                
                #show tooltip
                tw.show()
                
                #focus the offending control
                ctrl.focus_force()
            
                self._red_controls.append(ctrl)
            
            # back to config
            self.set_step(1)
            return False
        else:
            # clear all controls of redness
            for ctrl in self._red_controls:
                # unbind lost focus function
                ctrl.unbind_all('<FocusOut>')
                
                # reset style
                ctrl.configure(style=ctrl.winfo_class())
            self._red_controls = []
            
            
        return True
    
    
    def pretest(self):
        
        if self.verify_config(self.get_cnf()):
            self.set_step(2)
            
            
            
            
            
            
            

    def run(self):
        progress('pre', 0, 0)
        
        #set step to 'running'
        self.set_step(3)
        
        #retrieve configuration from controls
        root_cfg = self.get_cnf()
        
        if self.verify_config(root_cfg):
        
            #runs the test
            run(root_cfg)

    def abort(self):
        """Aborts the test by raising KeyboardInterrupt
        
        returns:
            
        cancel : bool
            whether the user opted to cancel the abort
        """
        if tk.messagebox.askyesno('Abort Test',
            'Are you sure you want to abort?'):
            _thread.interrupt_main()
            return False
        else:
            # indicates cancelled by user
            return True
    
    @in_thread('GuiThread', wait=False)
    def post_test(self, error):
        self.set_step(5)
        
        err_class, err_msg, trace = error
        if err_class and err_class not in (KeyboardInterrupt,):
            tk.messagebox.showerror(
               err_class.__name__, err_msg)
        
    def submit_post_test(self):
        
        txt_box = self.frames['PostTestGuiFrame'].post_test
        
        # retrieve post_notes
        self.post_test_info = {'Post Test Notes': txt_box.get(1.0, tk.END)}
        
               
    
    @in_thread('GuiThread')
    def set_step(self, step):
        self.step = step
        
        back_btn_txt = 'Back'
        
        if step == 0:
            # blank window
            self.selected_test.set('EmptyFrame')
            self.show_frame('EmptyFrame')
            next_btn_txt = 'Next'
            next_btn = None #disabled
            back_btn = None
        
        elif step == 1:
            # test configuration
            self.show_frame(self.selected_test.get())
            next_btn_txt = 'Next'
            next_btn = self.pretest
            back_btn = lambda : self.set_step(0)
        
        elif step == 2:
            # test info gui
            self.show_frame('TestInfoGuiFrame')
            next_btn_txt = 'Run Test'
            next_btn = self.run
            back_btn = self.configure_test
        
        elif step == 3:
            # progress bar
            self.show_frame('TestProgressFrame')
            next_btn_txt = 'Abort Test'
            next_btn = lambda : self.set_step(4)
            back_btn = None
            
        elif step == 4:
            # in process of aborting
            self.show_frame('TestProgressFrame')
            self.frames['TestProgressFrame'].primary_text.set('Aborting...')
            
            next_btn_txt = 'Cancel Abort'
            next_btn = lambda : self.set_step(3)
            back_btn = None
            
        elif step == 5:
            #post_test
            self.show_frame('PostTestGuiFrame')
            next_btn_txt = 'Submit'
            next_btn = self.submit_post_test
            back_btn = None
            
        
        elif step == 6:
            self.show_frame('PostProcessingFrame')
            next_btn_txt = 'Finish'
            next_btn = lambda : self.set_step(0)
            back_btn = lambda : self.set_step(2)
            back_btn_txt = 'Run Again'
            
        
        #changes function and text of the next button
        self.set_next_btn(next_btn_txt, next_btn)
        
        #changes back button
        self.set_back_btn(back_btn_txt, back_btn)
    
    @in_thread('GuiThread', wait=False)
    def clear_notes(self):
        # clears pre_test and post_test notes
        self.frames['TestInfoGuiFrame'].pre_notes.delete(1.0, tk.END)
        self.frames['PostTestGuiFrame'].post_test.delete(1.0, tk.END)





#-----------------------------Sub-frames of main gui--------------------------

class BottomButtons(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.master = master
        self.do_run = True
        self.run_textvar = tk.StringVar()
        self.back_textvar = tk.StringVar()
        
        self.master.set_next_btn = self.set_next_btn
        self.master.set_back_btn = self.set_back_btn
        
        # a text-changeable 'next', 'run' or 'abort' button
        self._nxt_btn_wgt = ttk.Button(
                   master=self, textvariable=self.run_textvar,
                   command=self._next_btn)
        self._nxt_btn_wgt.pack(side=tk.RIGHT)
        
        
        # Back Button
        self._bck_btn_wgt = ttk.Button(self, textvariable=self.back_textvar,
                    command=self._back_btn)
        self._bck_btn_wgt.pack(side=tk.RIGHT)
        
        
        ttk.Button(master=self, text='Restore Defaults',
                   command=master.restore_defaults).pack(
            side=tk.RIGHT)
        
        ttk.Button(master=self, text='Load Config',
                   command=master.open_).pack(
            side=tk.RIGHT)

        ttk.Button(master=self, text='Save Config',
                   command=master.save).pack(
            side=tk.RIGHT)
    
    def set_back_btn(self, text, callback):
        self.back_textvar.set(text)
        self._back_callback = callback
        
        if callback:
            self._bck_btn_wgt.state(['!disabled'])
        else:
            self._bck_btn_wgt.state(['disabled'])
    
    def set_next_btn(self, text, callback):
        self.run_textvar.set(text)
        self._next_callback = callback
        
        if callback:
            self._nxt_btn_wgt.state(['!disabled'])
        else:
            self._nxt_btn_wgt.state(['disabled'])
        
    def _next_btn(self):
        if self._next_callback:
            self._next_callback()
            
    def _back_btn(self):
        if self._back_callback:
            self._back_callback()

class LeftFrame(tk.Frame):
    """Can show and hide the MenuFrame using the MenuButton

    Only applies when the main window is small enough
    """

    def __init__(self, master, main_, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # stores the main Tk window
        self.main_ = main_

        # The window's minimum width at which the menu is shown
        self.MenuShowWidth = WIN_SIZE[0]

        self.DoMenu = False
        self.MenuVisible = True

        self.MenuButton = MenuButton(self, command=self.on_button)

        # pass main_ down the chain to the TestTypeFrame
        self.MenuFrame = MenuFrame(self, main_)
        self.MenuFrame.pack(side=tk.LEFT, fill=tk.Y)

    def on_change_size(self, event):
        w_ = self.main_.winfo_width()
        w = self.MenuShowWidth
        if event.width < 600 or event.height < 370:
            # unknown source of incorrect events
            return
        if w_ < w and not self.DoMenu:
            self.DoMenu = True
            self.MenuVisible = False
            self.MenuButton.pack(side=tk.LEFT, fill=tk.Y)
            self.MenuFrame.pack_forget()
            if self.main_.is_empty():
                self.MenuFrame.pack(side=tk.LEFT, fill=tk.Y)
                self.MenuVisible = True
        elif w_ >= w and self.DoMenu:
            self.MenuButton.pack_forget()
            self.MenuVisible = True
            self.DoMenu = False
            self.MenuFrame.pack(side=tk.LEFT, fill=tk.Y)

    def on_button(self):
        if self.MenuVisible:
            self.MenuVisible = False
            self.MenuFrame.pack_forget()
        else:
            self.MenuVisible = True
            self.MenuFrame.pack(side=tk.LEFT, fill=tk.Y)


class MenuFrame(tk.Frame):
    """Contains the Logo frame and the Choose Test Type frame

    """

    def __init__(self, master, main_, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        LogoFrame(master=self).pack(side=tk.LEFT, fill=tk.Y)

        # pass main_ down the chain to the TestTypeFrame

        TestTypeFrame(master=self, main_=main_, padx=10, pady=10).pack(
            side=tk.LEFT, fill=tk.Y)


class MenuButton(tk.Frame):
    def __init__(self, master, *args, command=None, **kwargs):
        super().__init__(master, *args, **kwargs,)

        #img = ImageTk.PhotoImage(Image.open('pscr_logo.png'))

        tk.Button(master=self, text='...', command=command).pack()


class TestTypeFrame(tk.Frame):
    """Allows the user to choose hardware/sim and which test to perform

    """

    def __init__(self, master, main_, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.main_ = main_

        # StringVars to determine what test to run and show config for
        is_sim = main_.is_simulation
        sel_txt = main_.selected_test

        # Test Type
        ttk.Label(self, text='Test Method:').pack(fill=tk.X)

        # hardware test
        ttk.Radiobutton(self, text='Hardware Test',
                        variable=is_sim, value=False).pack(fill=tk.X)

        # simulation test
        ttk.Radiobutton(self, text='Simulation Test',
                        variable=is_sim, value=True).pack(fill=tk.X)
        
        
        # hardware and simulation settings button
        self.set_btn_txtvar = tk.StringVar(value='Hardware Settings')
               
        ttk.Button(self, textvariable=self.set_btn_txtvar,
                   command=self.settings_btn).pack(fill=tk.X)
        
        
        self._test_btn = ttk.Button(self, text='Test Audio',
                                   command=self.test_audio_btn)
        self._test_btn.pack(fill=tk.X)
        
        #auto-update button text based on is_simulation
        is_sim.trace_add('write', self.update_settings_btn)
        
        
        ttk.Separator(self).pack(fill=tk.X, pady=20)

        # Choose Test
        ttk.Label(self, text='Choose Test:').pack(fill=tk.X)

        ttk.Radiobutton(self, text='M2E Latency',
                        variable=sel_txt, value='M2eFrame').pack(fill=tk.X)

        ttk.Radiobutton(self, text='Access Delay',
                        variable=sel_txt, value='AccssDFrame').pack(fill=tk.X)

        ttk.Radiobutton(self, text='PSuD',
                        variable=sel_txt, value='PSuDFrame').pack(fill=tk.X)

        ttk.Radiobutton(self, text='Intelligibility',
                        variable=sel_txt, value='IntgblFrame').pack(fill=tk.X)
        
    def update_settings_btn(self, *args, **kwargs):
        if self.main_.is_simulation.get():
            val = 'Simulation Settings'
        else:
            val = 'Hardware Settings'
            
        self.set_btn_txtvar.set(val)
        
    def settings_btn(self):
        if self.main_.is_simulation.get():
            shared.SimSettings(
                self.main_, self.main_.simulation_settings)
        else:
            shared.HdwSettings(
                self.main_, self.main_.hardware_settings)
            
    def test_audio_btn(self):
        self._test_btn.state(['disabled'])
        test_audio(self.main_.get_cnf(),
            on_finish=self._test_audio_on_finish)
    
    @in_thread('GuiThread', wait=False)
    def _test_audio_on_finish(self):
        self._test_btn.state(['!disabled'])
        
        
        

class LogoFrame(tk.Canvas):

    crestinf = {'img': 'pscr_logo.png'}

    def __init__(self, master, width=150, height=170, *args, **kwargs):
        super().__init__(*args,
                         width=width,
                         height=height,
                         master=master,
                         bg='white',
                         **kwargs)

        crest = self.crestinf['img']
        if crest is not None:

            img = Image.open(crest)
            img = img.resize(
                (width, height),
                Image.ANTIALIAS
            )
            self.crestimg = ImageTk.PhotoImage(img)
            self.create_image(
                width // 2, height // 2 + 10,
                image=self.crestimg
            )








#------------------------Top-Right Frames-------------------------------------

class EmptyFrame(tk.Frame):
    """An empty frame: shown when no test is selected yet

    """

    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btnvars = btnvars
        
    def run(self, *args, **kwargs):
        raise ValueError('Please select a test.')


class TestInfoGuiFrame(ttk.Labelframe):
    """Replacement for the TestInfoGui, to be compatible with this program
    
    Fits into the main window instead of its own window
    
    """
    
    
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, text='Test Information', **kwargs)
        
        labels = {
            'Test Type': 'Test Type',
            'Tx Device': 'Transmit Device',
            'Rx Device': 'Receive Device',
            'System': 'System',
            'Test Loc': 'Test Location'
            }
        
        
        self.btnvars = btnvars
        
        
        
        padx = shared.PADX
        pady = shared.PADY
        
        ct = 0
        for k, label in labels.items():
            
            self.btnvars.add_entry(k, value='')
            
            
            ttk.Label(self, text=label).grid(column=0, row=ct,
                       sticky='E', padx=padx, pady=pady)
            
            ttk.Entry(self, textvariable=self.btnvars[k]).grid(
                column=1, row=ct, sticky='W', padx=padx, pady=pady)
            
            ct += 1
        
        ttk.Label(self, text='Please enter notes on pre-test conditions').grid(
            columnspan=2, row=ct)
        
        ct += 1
        
        self.pre_notes = tk.Text(self)
        self.pre_notes.grid(
            sticky='NSEW', columnspan=2, row=ct, padx=padx, pady=pady)
        
        #text widget expand to fit frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(ct, weight=1)
        
        
        
class PostTestGuiFrame(ttk.Labelframe):
    """Replacement for PostTestGui
    
    """
    
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, text='Test Information', **kwargs)
        self.btnvars = btnvars
        
        ttk.Label(self, text='Please enter post-test notes').grid(row=0,
            padx=shared.PADX, pady=shared.PADY, sticky='E')
        
        self.post_test = tk.Text(self)
        self.post_test.grid(padx=shared.PADX, pady=shared.PADY,
            sticky='NSEW', row=2)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        
       



class TestProgressFrame(tk.LabelFrame):
    
    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.pack_configure(expand=True, fill=tk.BOTH)
    
    def __init__(self, master, btnvars, *args, **kwargs):
        self.start_time = time.time()
        self.btnvars = btnvars
        
        super().__init__(master, *args, text='', **kwargs)
        
        # text above bar
        self.primary_text = txt = tk.StringVar()
        
        
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        # the progress bar
        self.bar = ttk.Progressbar(self, mode='indeterminate')
        self.bar.pack(fill=tk.X, padx=10, pady=10)
        
        
        #the text below the bar
        
        self.secondary_text = txt = tk.StringVar()
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        self.tertiary_text = txt = tk.StringVar()
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        
    @in_thread('GuiThread', wait=True)
    def progress(self, prog_type, num_trials, current_trial, err_msg='') -> bool:
        
        
        if main.win.step == 4:
            # indicate that the test should not continue
            return False
        
        
        messages = {
            'pre' : ('Loading...', ''),
            
            'proc' : ('Processing test data...',
                      f'Processing trial {current_trial+1} of {num_trials}'),
            
            'test' : ('Performing tests...',
                      f'Trial {current_trial} of {num_trials}'),
            
            'check-fail' : ('Test encountered an error.',
                f'Trial {current_trial+1} of {num_trials}')
            
            }
        
        
        
        
        self.primary_text.set(messages[prog_type][0])
        
        self.secondary_text.set(messages[prog_type][1])
                
        
        if not num_trials:
            #indeterminate progress bar
            self.bar.configure(mode='indeterminate', maximum = 100)
            self.bar.start()
            self.tertiary_text.set('')
            
            
        else:
            # show current progress
            self.bar.stop()
            self.bar.configure(value=current_trial, maximum = num_trials,
                               mode='determinate')
            

            # estimate time remaining
            
            if current_trial == 0:
                self.start_time = time.time()
                self.tertiary_text.set('')
            else:
                time_elapsed = time.time() - self.start_time
                
                time_total = time_elapsed * num_trials / current_trial
                
                time_left = time_total - time_elapsed
                
                time_left = time_left / 60
                
                if time_left < 60:
                    time_left = round(time_left)
                    time_unit = 'minutes'
                elif time_left < 60 * 24:
                    time_left = round(time_left // 60)
                    time_unit = 'hours'
                else:
                    time_left = round(time_left // 60 // 24)
                    time_unit = 'days'
                
                self.tertiary_text.set(f'{time_left} {time_unit} remaining...')
        
            
        
        return True

class PostProcessingFrame(ttk.Frame):
    
    def __init__(self, master, btnvars, **kwargs):
        self.btnvars = btnvars
        self.folder = ''
        super().__init__(master, **kwargs)
        
        ttk.Label(self, text='Test Complete').pack(padx=10, pady=10, fill=tk.X)
        
        ttk.Button(self,
                   text='Open Output Folder',
                   command = self.open_folder
                   ).pack(padx=10, pady=10, fill=tk.X)
        
        self.elements = []
        self.canvasses = []
    
    @in_thread('GuiThread', wait=False)
    def add_element(self, element):
        """Adds an element to the post-processing frame
        
        Parameters
        ----------
        element : UNION[str, Figure]
            A string or matplotlib figure to be added into the window

        """
        
        if isinstance(element, Figure):
            canvas = FigureCanvasTkAgg(element, master=self)
            widget = canvas.get_tk_widget()
            canvas.draw()
            self.canvasses.append(widget)
            
        elif isinstance(element, str):
            widget = ttk.Label(self, text=element)

        widget.pack(fill=tk.X, expand=True, padx=10, pady=10)
        
        self.elements.append(widget)
    
    @in_thread('GuiThread', wait=True)
    def reset(self):
        
        for canvas in self.canvasses:
            canvas.delete('all')
        
        for elt in self.elements:
            elt.destroy()
        
        self.canvasses = []
        self.elements = []
    
    def open_folder(self, e=None):
        """open the outdir folder in os file explorer"""
        dir_ = path.normpath(path.join(os.getcwd(), self.outdir))
        
        try:
            sp.Popen(['explorer', dir_])
        except (FileNotFoundError, OSError):
            try:
                sp.Popen(['open', dir_])
            except (FileNotFoundError, OSError): pass
        






#------------------------------  Appearance ----------------------------------

def set_font(**cfg):
    """Globally changes the font on all tkinter windows.

    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)


def set_styles():
    
    f = ttk.Style().configure
    g = ttk.Style().layout
        
    # set global font
    f('.', font=('TkDefaultFont', shared.FONT_SIZE))
    
    
    # help button and tooltip styles
    f('McvHelpBtn.TLabel', font=('TkDefaultFont',
                round(shared.FONT_SIZE * 0.75)), relief='groove')
    f('McvToolTip.TLabel', 
                background='white')
    f('McvToolTip.TFrame',
                background='white', relief='groove')
    
    
    
    
    
#red highlight for missing or invalid controls
    
    #for Entry
    g("Error.TEntry",
                   [('Entry.plain.field', {'children': [(
                       'Entry.background', {'children': [(
                           'Entry.padding', {'children': [(
                               'Entry.textarea', {'sticky': 'nswe'})],
                      'sticky': 'nswe'})], 'sticky': 'nswe'})],
                      'border':'2', 'sticky': 'nswe'})])
    
    f("Error.TEntry",
      fieldbackground="pink"
      )
    
    # for Spinbox
    g("Error.TSpinbox",
                   [('Entry.plain.field', {'children': [(
                       'Entry.background', {'children': [(
                           'Entry.padding', {'children': [(
                               'Entry.textarea', {'sticky': 'nswe'})],
                      'sticky': 'nswe'})], 'sticky': 'nswe'})],
                      'border':'2', 'sticky': 'nswe'}),
                       ('Spinbox.uparrow', {'side': 'top', 'sticky': 'nse'}),
                       ('Spinbox.downarrow', {'side': 'bottom', 'sticky': 'nse'})])
    
    f("Error.TSpinbox",
      fieldbackground="pink"
      )
    
    f('Error.McvToolTip.TLabel',
      foreground='maroon',
      )
    
    
def dpi_scaling(root):
    global dpi_scale
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        if screen_height < screen_width:
            dpi_scale = screen_height / 800
        else:
            dpi_scale = screen_width / 800
        
        dpi_scale = dpi_scale ** 0.5
        
        if dpi_scale < 1 or dpi_scale > 2.5:
            raise Exception()
    except:  # in case of invalid dpi scale
        dpi_scale = 1
    global WIN_SIZE
    WIN_SIZE = (round(WIN_SIZE[0] * dpi_scale),
                round(WIN_SIZE[1] * dpi_scale))

    # font
    shared.FONT_SIZE = round(shared.FONT_SIZE * dpi_scale)
    shared.FNT = font.Font()
    shared.FNT.configure(size=shared.FONT_SIZE)
    set_styles()







#-------------------------------- Main ---------------------------------------

class TestQueue(list):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self.current_test = None
        self._break = False
    

class GuiThread(Thread):
   
    def callback(self, function):
        """Calls a function in the GUIThread
        

        Parameters
        ----------
        function : callable
        
        """
        self._callbacks.insert(0, function)
    
     
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setName('GuiThread')
        self.setDaemon(True)
        self._callbacks = []
        
    
    
    def run(self):
        
        main.win = MCVQoEGui()
        main.win.after(500, self._main_loop_ext)
        main.win.mainloop()

    def _main_loop_ext(self):
        
        try:
            #grab a function
            f = self._callbacks.pop()
        except IndexError:pass
        else:
            try:
                f()
            except:
                #don't crash in case of error
                traceback.print_exc()
                
                
        #run this function again
        main.win.after(200, self._main_loop_ext)


class Main():
    def __init__(self):
        global main
        main = self
        self._break = False
        self._callbacks = []
        self.is_running = False

        # constructs gui in new thread
        self.gui_thread = GuiThread()
        self.gui_thread.start()
        
        self.main_loop()
        self.gui_thread.join()
        


    
    def callback(self, function):
        """Calls a function in the main thread.
        

        Parameters
        ----------
        function : callable
            

        Returns
        -------
        None.

        """
        self._callbacks.insert(0, function)
        
        
        
    def main_loop(self):
        while True:
            if self._break:
                self.is_running = False
                return
            try:
                try:
                    f = self._callbacks.pop()
                except IndexError:
                    #if no callbacks to be called
                    self.is_running = False
                    time.sleep(0.2)
                else:
                    self.is_running = True
                    f()
                
                
                
                
                
            except Abort_by_User:pass
                
            except SystemExit:
                if self._break:
                    return
                
            except KeyboardInterrupt:pass
                
                    
            except:
                
                # prints exception without exiting main thread
                traceback.print_exc()
        
        
        
        #thread is ending
        self.is_running = False
            

    def stop(self):
        self._break = True
        
        
        
        
        
        
        
        
        
        
        
        
        
#----------------------- Running the tests -----------------------------------
    



@in_thread('MainThread', wait=False)
def test_audio(root_cfg, on_finish=None):
    
    try:
        
    
        sel_tst = root_cfg['selected_test']
    
        cfg = root_cfg[sel_tst]
        
        if 'channel_rate' in root_cfg['SimSettings'] and root_cfg[
            'SimSettings']['channel_rate'] == 'None':
            root_cfg['SimSettings']['channel_rate'] = None
        
        
        
        radio_interface, ap = _get_interfaces(root_cfg)
        
        
        # get selected audio file
        if 'audio_files' in cfg:
            fp = cfg['audio_files'][0]
            
            
            if path.isdir(fp):
                files = [f for f in listdir(fp) if path.isfile(path.join(fp, f))]
                
                for f in files:
                    void, ext = path.splitext(f)
                    if ext.lower() == '.wav':
                        fp = path.join(fp, f)
                        break
                    
            if not path.isfile(fp):
                raise ValueError('Audio File not found')
            
        else:
            fp = None
    
    
        with radio_interface as ri:
        
            if 'ptt_wait' in cfg:
                hardware.PTT_play.single_play(ri, ap, fp,
                    playback=root_cfg['is_simulation'],
                    ptt_wait=cfg['ptt_wait'])
            else:
                hardware.PTT_play.single_play(ri, ap, fp,
                    playback=root_cfg['is_simulation'])
                
                
    except Exception as error:
        tk.messagebox.showerror(error.__class__.__name__, str(error))
    
    if on_finish:
        on_finish()


@in_thread('MainThread', wait=False)
def run(root_cfg):
    
    # TODO implement other tests here
    constructors = {
        'M2eFrame': m2e_gui.M2E_fromGui,
        'AccssDFrame': accesstime_gui.Access_fromGui,
        'PSuDFrame' : psud_gui.PSuD_fromGui
            }
    
    
    # extract test configuration and notes from root_cfg
    sel_tst = root_cfg['selected_test']
    is_sim = root_cfg['is_simulation']
    cfg = root_cfg[sel_tst]
    pre_notes = root_cfg['TestInfoGuiFrame']
    
    
    
    
    #initialize test object
    my_obj = constructors[sel_tst]()
    
    try:
        
        
        
        # set progress update callback
        my_obj.progress_update = progress
        
        
        ppf = main.win.frames['PostProcessingFrame']
        # set postprocessing info callback
        my_obj.gui_show_element = ppf.add_element
        # remove post-processing info from frame
        ppf.reset()
        
        # put outdir folder into frame
        ppf.outdir = cfg['outdir']
        
        
        
        
        
        # if recovery
        if 'data_file' in cfg and cfg['data_file'] != "":
            my_obj.data_file = cfg['data_file']
            with open(my_obj.data_file, "rb") as pkl:
                my_obj.rec_file = pickle.load(pkl)
            
            
            skippy = ['rec_file']
            # load config from recovery file into object
            for k, v in my_obj.rec_file.items():
                if hasattr(my_obj, k) and (k not in skippy):
                    setattr(my_obj, k, v)
        
        else:
                        
            # put config into object
            _set_values_from_cfg(my_obj, cfg)
             
            # Check for value errors with instance variables
            my_obj.param_check()
        
        
        # PSuD handles this by itself
        if sel_tst in ('M2eFrame', 'AccssDFrame'):
            # Get start time and date
            time_n_date = datetime.datetime.now().replace(microsecond=0)
            my_obj.info['Tstart'] = time_n_date
        
            # Add test to info dictionary.
            my_obj.info['test'] = my_obj.test
    
            # Fill 'Arguments' within info dictionary
            my_obj.info.update(write_log.fill_log(my_obj))
    
            # Gather pretest notes and parameters
            my_obj.info.update(pre_notes)
    
    
            # Write pretest notes and info to tests.log
            write_log.pre(info=my_obj.info, outdir=my_obj.outdir)
            
        else:
            my_obj.info = pre_notes
    
        # clear notes from window
        main.win.clear_notes()
        
        # set post_notes callback
        my_obj.get_post_notes=get_post_notes
        
        
        
        
        ri, ap = _get_interfaces(root_cfg)
        
    
        my_obj.audio_interface = ap
       
        # Enter RadioInterface object
        with ri as my_obj.ri:
        
            #run test
            my_obj.run()
            

        if sel_tst in ('M2eFrame',):
            my_obj.plot()
    
            
    #gathers posttest notes without showing error
    except Abort_by_User:pass
    
    #gathers posttest notes without showing error
    except KeyboardInterrupt:pass
    
    #indicates end of test
    except SystemExit:return
        
    except Exception:
        # Gather posttest notes and write to log
        traceback.print_exc()
        post_dict = get_post_notes()
        write_log.post(info=post_dict, outdir=my_obj.outdir)
        
        #show postprocessing frame
        main.win.set_step(6)
        return

    
    #PSuD, m2e handle this internally
    if sel_tst in ('AccssDFrame'):
        # Gather posttest notes and write to log
        post_dict = get_post_notes()
        write_log.post(info=post_dict, outdir=my_obj.outdir)
        
        
        
    #show post-processing frame
    main.win.set_step(6)
    
    
    # leave gap in console for next test
    print('\n\n\n')
    
    
def progress(prog_type, num_trials, current_trial, err_msg='') -> bool:
    return main.win.frames['TestProgressFrame'].progress(
        prog_type, num_trials, current_trial, err_msg)
    


def param_modify(root_cfg):
    
    sel_tst = root_cfg['selected_test']
    is_sim = root_cfg['is_simulation']
    cfg = root_cfg[sel_tst]
    
    
    
    
    # check: audio_files should not be empty
    if not ('audio_files' in cfg
            and cfg['audio_files']
            and cfg['audio_files'][0]):
        
        raise InvalidParameter('audio_files', message='Audio File is required.')
        
    
    # check: audio files should all exist
    ct = 0
    cfg['full_audio_dir'] = False
    for af in cfg['audio_files']:
        if path.isdir(af) and ct == 0:
            
            # set audio_path and full_audio_dir
            cfg['audio_path'] = p = af
            cfg['full_audio_dir'] = True
            cfg['audio_files'] = []
            
            # check folder for audio files
            success = False
            for f in listdir(p):
                fp = path.join(p, f)
                if path.isfile(fp) and path.splitext(fp)[1].lower() == '.wav':
                    success = True
                    break
            if not success:
                raise InvalidParameter('audio_files',
                    message='Folder must contain .wav files') 
            
            break
        
        
        # else, make sure all file names are valid
        if not path.isfile(af):
            raise InvalidParameter('audio_files',
                message=f'"{af}" does not exist')
        if not path.splitext(af)[1].lower() == '.wav':
            raise InvalidParameter('audio_files',
                message='All audio files must be .wav files')
        ct += 1
    
    
    
    
    # make trials an integer if it's not already (mainly for access time)
    bad_param = False
    try:
        cfg['trials'] = int(cfg['trials'])
    except ValueError:
        if cfg['trials'].lower() == 'inf':
            cfg['trials'] = np.inf
        else:
            bad_param = True
    if bad_param:
        raise InvalidParameter('trials',
                    message='Number of trials must be a whole number')
    
    
    
    # if channel_rate should be None, make it so
    if 'channel_rate' in root_cfg['SimSettings'] and root_cfg[
            'SimSettings']['channel_rate'] == 'None':
        
        # turn str(None) into None
        root_cfg['SimSettings']['channel_rate'] = None
    
    
    
    
    
    # combine the 2 ptt_delays into a vector
    if '_ptt_delay_min' in cfg:
        cfg['ptt_delay'] = [cfg['_ptt_delay_min']]
        try:
            cfg['ptt_delay'].append(float(cfg['_ptt_delay_max']))
        except ValueError:pass
        
        
    if '_time_expand_i' in cfg:
        cfg['time_expand'] = [cfg['_time_expand_i']]
        try:
            cfg['time_expand'].append(float(cfg['_time_expand_f']))
        except ValueError:pass
        
        
        
        
        
        
        
    # check auto_stop with ptt_rep
    if ('auto_stop' in cfg) and ('ptt_rep' in cfg) and cfg['auto_stop'] and (
            cfg['ptt_rep'] < 16):
        raise InvalidParameter('ptt_rep',
                    message='Must be greater than 15 if auto-stop is enabled')
        
        
def get_post_notes(error_only=False):
    
    #get current error status, will be None if we are not handling an error
    root_error=sys.exc_info()
    error = root_error[0]
    
    #check if there is no error and we should only show on error
    if((not error) and error_only):
        #nothing to do, bye!
        return {}
    
    
    main.win.post_test_info = None
    main.win.post_test(root_error)
    
    # wait for completion or program close
    
    while main.win.post_test_info is None and not main.win.is_destroyed:
        time.sleep(0.1)
    
    
    nts = main.win.post_test_info
    if nts is None:
        nts = {}
    return nts
    

    


def _get_interfaces(root_cfg):
    # in case of simulation test
        if root_cfg['is_simulation']:
            
            sim = QoEsim()
            
            _set_values_from_cfg(sim, root_cfg['SimSettings'])
                
            
            ri = sim
            ap = sim
        
        else:
            hdw_cfg = root_cfg['HdwSettings']
            
            
            if 'radioport' in hdw_cfg and hdw_cfg['radioport']:
                radioport = hdw_cfg['radioport']
            else:
                radioport = None
                
            ri = hardware.RadioInterface(radioport)
            
            ap = hardware.AudioPlayer()
            
            _set_values_from_cfg(ap, hdw_cfg)
            
            
            ap.blocksize = hdw_cfg['blocksize']
            ap.buffersize = hdw_cfg['buffersize']
            ap.sample_rate = 48000
            
            ap.playback_chans = {'tx_voice':0, 'start_signal':1}
            ap.rec_chans = {'rx_voice':0, 'PTT_signal':1}
            
        return (ri, ap)

def _set_values_from_cfg(my_obj, cfg):
    for k, v in cfg.items():
        if hasattr(my_obj, k):
            setattr(my_obj, k, v)










        

if __name__ == '__main__':
    
    # on Windows, remove dpi scaling (otherwise text is blurry)
    if hasattr(ctypes, 'windll'):
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

       
    
    Main()
