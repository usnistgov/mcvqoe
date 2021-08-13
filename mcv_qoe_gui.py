# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov

"""
# -----------------------------basic config------------------------------------
TITLE_ = 'MCV QoE'
icon = 'MCV-sm.ico'
appid = 'nist.mcvqoe.gui.1_0_0'


import ctypes
# on Windows:
if hasattr(ctypes, 'windll'):
    # remove dpi scaling (otherwise text is blurry)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
    
    # allows icon setting on taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    

#--------------------------imports---------------------------------------------
import pdb
import tkinter.messagebox as msb
import tkinter.filedialog as fdl
import tkinter.font as font
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk

from tk_threading import in_thread
from tk_threading import Main



import traceback
import sys
import time
import _thread
import json
import pickle
import os
from os import path, listdir
import gc
import subprocess as sp
import matplotlib


from mcvqoe.simulation.QoEsim import QoEsim
from mcvqoe import hardware, simulation



import shared
from shared import Abort_by_User, InvalidParameter
import loadandsave
import accesstime_gui
from accesstime_gui import AccssDFrame
import m2e_gui
from m2e_gui import M2eFrame, DevDlyCharFrame
import psud_gui
from psud_gui import PSuDFrame
import intelligibility_gui
from intelligibility_gui import IgtibyFrame


#alternate rendering for pyplot to avoid conflicts with tkinter
use_alternate_plot_rendering = True
try:
    import PyQt5
except: use_alternate_plot_rendering = False
else:
    matplotlib.use('Qt5Agg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np



class MCVQoEGui(tk.Tk):
    """The main window


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # prevents random window flashing
        self.withdraw()
        
        #set the title- and taskbar icon
        self.iconbitmap(path.abspath(icon))
        
        
        # when the user closes the window
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # dpi scaling
        dpi_scaling(self)

        # indicates that the user does not need to save the configuration
        self.set_saved_state(True)


        # tcl variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')

        # change test frame when user selects a test
        self.selected_test.trace_add(
            'write', lambda a, b, c: self._select_test())
        
        # disable/enable some controls when simulation is set/unset
        self.is_simulation.trace_add(
            'write', lambda a, b, c: self._rm_waits_in_sim())
        
        # initiate left frame with logo and test selections
        self.LeftFrame = LeftFrame(self, main_=self)
        self.LeftFrame.pack(side=tk.LEFT, fill=tk.Y)
        
        # initiate row of buttons on bottom of window
        self.BottomButtons = BottomButtons(master=self)
        self.BottomButtons.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # a scrollable frame (currently not used)
        self.RightFrame = shared.ScrollableFrame(self)
        
        # create test-specific frames
        self._init_frames()
        
        # set window size
        self._set_dimensions()
        

        # handling changing of window size
        self.bind('<Configure>', self.LeftFrame.on_change_size)
        
        
        # --------binding keyboard shortcuts-----------
        
        #save (as), open, close
        self.bind('<Control-s>', self.save)
        self.bind('<Control-S>', self.save)
        self.bind('<Control-o>', self.open_)
        self.bind('<Control-O>', self.open_)
        self.bind('<Control-Shift-s>', self.save_as)
        self.bind('<Control-Shift-S>', self.save_as)
        self.bind('<Control-w>', self.restore_defaults)
        self.bind('<Control-W>', self.restore_defaults)
        
        #back, next
        nxt = lambda *a, **k: self.BottomButtons._nxt_btn_wgt.invoke()
        self.bind('<Control-Return>', nxt)
        self.bind('<Alt-n>', nxt)
        self.bind('<Alt-N>', nxt)
        
        bck = lambda *a, **k: self.BottomButtons._bck_btn_wgt.invoke()
        self.bind('<Alt-b>', bck)
        self.bind('<Alt-B>', bck)
        
        #scrolling the scrollbar
        self.bind('<MouseWheel>', self.RightFrame.scroll)
        self.bind('<Button-5>', self.RightFrame.scroll)
        self.bind('<Button-4>', self.RightFrame.scroll)
        
        
        
        
        
        # sets the current frame to be blank
        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        
        # instance vars
        self.controls = {}
        self._red_controls = []
        self.cnf_filepath = None
        self.is_destroyed = False
        self._is_closing = False
        self._pre_notes = None
        self.set_step(0)
        
        
        
        # show the window
        self.deiconify()
        

    def _rm_waits_in_sim(self):
        """ disables ptt_wait and ptt_gap, etc controls in case of a simulation
        
        """
        # !disabled means not disabled
        state = ('!disabled', 'disabled')[self.is_simulation.get()]
        
        in_frames = (
            'M2eFrame',
            'AccssDFrame',
            'PSuDFrame',
            'IgtibyFrame',
            )
        
        for key in ('test', 'ptt_gap', 'ptt_wait', 'pause_trials', '_limited_trials'):
            
            # loop over every frame looking for 'ptt_wait' and 'ptt_gap' configs
            
            for framename, frame in self.frames.items():
                if not framename in in_frames:
                    continue
                
                if not hasattr(frame, 'controls') or key not in frame.controls:
                    continue
                
                # set control's state
                frame.controls[key].m_ctrl.configure(state=state)
        
        
        
        
        # disables m2e location in simulation
        
        if state == 'disabled':
            
            # make it a 1-loc test
            self.frames['M2eFrame'].btnvars['test'].set('m2e_1loc')

    def _init_frames(self):
        """consructs the test-specific frames"""
        
        
        frame_types = [
            EmptyFrame,
            TestInfoGuiFrame,
            PostTestGuiFrame,
            TestProgressFrame,
            PostProcessingFrame,
            
            DevDlyCharFrame,
            
            M2eFrame,
            AccssDFrame,
            PSuDFrame,
            IgtibyFrame,
        ]
        
   
        
        
        self.frames = {}
        for F in frame_types:
            
            btnvars = loadandsave.TkVarDict(**DEFAULTS[F.__name__])
            
            
            
            # initializes the frame, with its key being its own classname
            f = F(master=self, btnvars=btnvars)
            
            self.frames[F.__name__] = f

            # when user changes a control
            btnvars.on_change = self.on_change
            
            
        
        self.simulation_settings = loadandsave.TkVarDict(
            **DEFAULTS['SimSettings'])
        
        self.hardware_settings = loadandsave.TkVarDict(
            **DEFAULTS['HdwSettings'])
        
        
        _get_dev_dly()
        
        
        
    
    def _set_dimensions(self):
        """Algorithm to place and size the window on the screen
        
        """
        
        # which frames should set the minimum size
        important_frame_types = (
            DevDlyCharFrame,
            M2eFrame,
            PSuDFrame,
            IgtibyFrame,
        )
        
        
        
        # get screen dimensions
        screenh = self.winfo_screenheight()
        screenw = self.winfo_screenwidth()
        
        max_ = False
        
        # get cached dimensions
        try:
            
            
            cache = loadandsave.dim_cache
            assert cache.keys() == {'x':0,'y':0,'w':0,'h':0}.keys()
            
            # assumes window was maximized if >=3 borders touch edge of screen
            max_ = ((abs(cache['x']) < 50) +
                    (abs(cache['y']) < 50) +
                    (abs(cache['w'] + cache['x'] - screenw) < 50) +
                    (abs(cache['h'] + cache['y'] - screenh) < 50)
                    ) >= 3
            
            # cached window should be mostly on the screen
            assert cache['x'] >= -25
            assert cache['y'] >= -25
            assert cache['x'] + cache['w'] <= screenw + 50
            assert cache['y'] + cache['h'] <= screenh + 50
            
        except (FileNotFoundError, AssertionError):
            cache = None
        
        
        h = w = 0
        
        for f_name, f in self.frames.items():
             
            if f.__class__ in important_frame_types:
                
                # updates the sizing of the window
                f.pack(side=tk.RIGHT, padx=10, pady=10)
                self.update_idletasks()
                # get the dimensions of the window
                h_f = self.winfo_reqheight()
                w_f = self.winfo_reqwidth()
                
                
                # get largest possible h_f and store in h, etc
                h = (h, h_f)[h < h_f]
                w = (w, w_f)[w < w_f]
                
                
                # hide the frame: it won't be needed until later
                f.pack_forget()
        
        #set the LeftFrame's auto-disappear threshold
        self.LeftFrame.MenuShowWidth = w
        
        # breathing room
        w += 50
        
        # add bottom buttons into equation (not sure why they are not already?)
        h += 50 + self.BottomButtons.winfo_reqheight()
        
         
        
        
        #leave the left-most frame's width out of the width equation
            # because it automatically hides.
            
        minw = w - self.LeftFrame.winfo_reqwidth()
        
        minh = h
        
        
        # dimensions to ensure all frames fit in the window
        self.minsize(width=minw, height=minh)
        
        
        if cache is not None and not max_:
            x, y, w, h = cache['x'], cache['y'], cache['w'], cache['h']
        else:
            # initial size should fit in the screen
            h = (h, screenh)[h > screenh]
            w = (w, screenw)[w > screenw]
            
            # center window on screen
            x = (screenw - w) // 2
            y = (screenh - h) // 2
        
        
        #set the initial size
        self.geometry(f'{w}x{h}')
        
        #set inintial position
        self.geometry(f'+{x}+{y}')
        
        
        # maximize the window if the cache indicates it should be maximized
        if max_:
            try:
                # may not work on some systems
                self.wm_attributes('-zoomed', 1)
                
            except:
                try:
                    self.state("zoomed")
                except: pass
                    
        
        
    def _cache_dimensions(self):
            loadandsave.dim_cache.update(
                           x = self.winfo_x(),
                           y = self.winfo_y(),
                           w = self.winfo_width(),
                           h = self.winfo_height()
            )

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
        
        # if the user already pressed close
        if not self._is_closing:    
            if self.ask_save():
                # canceled by user
                return
            if main.is_running and self.abort():
                # abort was canceled by user
                return
        else:
            # quit the main thread
            _thread.interrupt_main()
            
            
        self._is_closing = True
        # destroy plots to prevent errors
        self.frames['PostProcessingFrame'].reset()
        
        # indicate that main thread should no longer perform operations
        main.stop()
        
        #waits for main thread to close gracefully
        ct = 0
        while main.is_running:
            ct += 1
            
            # if get_post_notes() gets called, wait for user to enter notes
            if self.step == 5:
                self._wait_to_destroy()
                return
            
            
            time.sleep(0.1)
            
            # if main thread is frozen for 100 iterations, freeze the window too.
            # this prevents a frozen program from being uncloseable
            if ct < 100:
                self.update_idletasks()
        
        # cache window dimensions
        self._cache_dimensions()
        
            
        # close the gui
        self.destroy()
        
        
        
        
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
            
        _get_dev_dly()
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
            filetypes=[('json files', '*.json')],
            initialdir = loadandsave.fdl_cache['main']
            
        )

        if not fpath:
            # canceled by user
            return
        
        # cache the folder for next time
        loadandsave.fdl_cache.put('main', fpath)

        with open(fpath, 'r') as fp:

            dct = json.load(fp)
            for frame_name, frame in self.frames.items():
                if frame_name in dct:
                    frame.btnvars.set(dct[frame_name])

            self.is_simulation.set(dct['is_simulation'])
            self.selected_test.set(dct['selected_test'])
            self.set_step(1)
            _get_dev_dly()

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
                                   defaultextension='.json',
                                   initialdir = loadandsave.fdl_cache['main'])
        if fp:
            
            # set the current open filepath
            self.cnf_filepath = fp
            
            # cache the folder for later use in the dialog
            loadandsave.fdl_cache.put('main', fp)
            
            # save it
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
        
        
        
        return obj
    

    
        
    @in_thread('GuiThread', wait=False)    
    def show_invalid_parameter(self, e):
        if e.param_loc == 'SimSettings':
            shared.SimSettings(self, self.simulation_settings)
            loc = self
        elif e.param_loc == 'HdwSettings':
            shared.HdwSettings(self, self.hardware_settings)
            loc = self
        else:
            loc = self.frames[self.selected_test.get()]
            
        try:
            ctrl = loc.controls[e.parameter].m_ctrl
        except AttributeError:
            ctrl = None
        
        if ctrl is not None:
            # try to make the control red
            try:
                ctrl.configure(style='Error.' + ctrl.winfo_class())
            except:pass
            
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
        
            # save reference to be made not red again later
            self._red_controls.append(ctrl)
        
        # back to config
        self.set_step(1)
    
    
    
    @in_thread('GuiThread', wait=True)
    def pretest(self, root_cfg):
        if root_cfg['is_simulation']:
            tech = root_cfg['SimSettings']['channel_tech']
            rate = root_cfg['SimSettings']['channel_rate']
            # construct string for system name
            system = tech
            if rate is not None:
                system += " at " + str(rate)
            
            # auto-fill pre-test-notes
            self.frames['TestInfoGuiFrame'].btnvars.set({
                'Test Type' : 'Simulation',
                'Tx Device' : 'None',
                'Rx Device' : 'None',
                'System'    : system,
                'Test Loc'  : 'N/A',
                })
        self._pre_notes = None
        self._pre_notes_wait = True
        self.set_step(2)
        
    def _pretest_submit(self):
        # get test info from entry controls
        self._pre_notes = self.frames['TestInfoGuiFrame'].btnvars.get()
            
        txt_box = self.frames['TestInfoGuiFrame'].pre_notes
        # gets 'Pre Test Notes' from text widget
        self._pre_notes['Pre Test Notes'] = txt_box.get(1.0, tk.END)
        
        self._pre_notes_wait = False
        
    def _pretest_cancel(self):
        
        self._pre_notes_wait = False
        
        self.set_step(1)
            
    def run(self):
        gui_progress_update('pre', 0, 0)
                
        #retrieve configuration from controls
        root_cfg = self.get_cnf()
        
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
    
       
        
    def _post_test_submit(self):
        
        txt_box = self.frames['PostTestGuiFrame'].post_test
        
        # retrieve post_notes
        self.post_test_info = {'Post Test Notes': txt_box.get(1.0, tk.END)}
        
        
    def set_step(self, step, extra=None):
        self.step = step
        
        self._set_step(step, extra=extra)
        
    @in_thread('GuiThread')
    def _set_step(self, step, extra=None):
        
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
            next_btn = self.run
            back_btn = lambda : self.set_step(0)
        
        elif step == 2:
            # test info gui
            self.show_frame('TestInfoGuiFrame')
            next_btn_txt = 'Submit'
            next_btn = self._pretest_submit
            back_btn = self._pretest_cancel
            
        elif step == 3:
            # progress bar
            self.show_frame('TestProgressFrame')
            
            if isinstance(extra, GuiRecStop):
                next_btn_txt = 'Stop Recording'
                next_btn = extra.stop
            else:
                next_btn_txt = 'Abort Test'
                next_btn = lambda : self.set_step(4)
            back_btn = None
            
        elif step == 4:
            # in process of aborting
            self.show_frame('TestProgressFrame')
            self.frames['TestProgressFrame'].primary_text.set('Aborting...')
            
            next_btn_txt = 'Force Stop'
            next_btn = _thread.interrupt_main
            back_btn = lambda : self.set_step(3)
            back_btn_txt = 'Cancel Abort'
            
        elif step == 5:
            #post_test
            self.frames['PostTestGuiFrame'].set_error(extra)
            self.show_frame('PostTestGuiFrame')
            next_btn_txt = 'Submit'
            next_btn = self._post_test_submit
            back_btn = None
            
        
        elif step == 6:
            self.show_frame('PostProcessingFrame')
            next_btn_txt = 'Finish'
            next_btn = lambda : self.set_step(0)
            back_btn = lambda : self.set_step(1)
            back_btn_txt = 'Run Again'
            
        
        #changes function and text of the next button
        self.set_next_btn(next_btn_txt, next_btn)
        
        #changes back button
        self.set_back_btn(back_btn_txt, back_btn)
    
    @in_thread('GuiThread', wait=False)
    def clear_old_entries(self):
        """
        Clears pre-notes, post-notes, and invalid parameter controls
        to prepare for the next test

        

        """
        
        # clears pre_test and post_test notes
        self.frames['TestInfoGuiFrame'].pre_notes.delete(1.0, tk.END)
        self.frames['PostTestGuiFrame'].post_test.delete(1.0, tk.END)
        
        
        # clear any previous invalid parameters of redness
        for ctrl in self._red_controls:
            # unbind lost focus function
            ctrl.unbind_all('<FocusOut>')
            
            # reset style
            ctrl.configure(style=ctrl.winfo_class())
        self._red_controls = []





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

        # The window's minimum width at which the menu is shown. will be set later
        self.MenuShowWidth = np.inf

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
                        variable=sel_txt, value='IgtibyFrame').pack(fill=tk.X)
        
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
            'Test Type': 'Test Type:',
            'Tx Device': 'Transmit Device:',
            'Rx Device': 'Receive Device:',
            'System': 'System:',
            'Test Loc': 'Test Location:'
            }
        
        
        self.btnvars = btnvars
        
        
        
        padx = shared.PADX
        pady = shared.PADY
        
        ct = 0
        for k, label in labels.items():
            
            self.btnvars.add_entry(k, value='')
            
            
            ttk.Label(self, text=label).grid(column=0, row=ct,
                       sticky='W', padx=padx, pady=pady)
            
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
        self.columnconfigure(1, weight=1)
        self.rowconfigure(ct, weight=1)
        
        
        
class PostTestGuiFrame(ttk.Labelframe):
    """Replacement for PostTestGui
    
    """
    
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, text='Test Information', **kwargs)
        self.btnvars = btnvars
        
        
        self.error_text = tk.StringVar()
        
        ttk.Label(self, textvariable=self.error_text).grid(row=1,
            padx=shared.PADX, pady=shared.PADY, sticky='W')
        
        ttk.Label(self, text='Please enter post-test notes.').grid(row=0,
            padx=shared.PADX, pady=shared.PADY, sticky='W')
        
        
        self.post_test = tk.Text(self)
        self.post_test.grid(padx=shared.PADX, pady=shared.PADY,
            sticky='NSEW', row=2)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        
    def set_error(self, error):
        if error:
            err_name, err_msg = format_error(error)
            
            self.error_text.set(f'{err_name}: {err_msg}')
                
        else:
            self.error_text.set('')
                
        
       



class TestProgressFrame(tk.LabelFrame):
    
    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.pack_configure(expand=True, fill=tk.BOTH)
    
    def __init__(self, master, btnvars, *args, **kwargs):
        self.stopwatch = _StopWatch()
        self.stopwatch.start()
        
        self.pause_after = None
        self.rec_stop = None
        self._is_paused = False
        self.warnings = []
        
        self.btnvars = btnvars
        
        super().__init__(master, *args, text='', **kwargs)
        
        
        #pause button
        ttk.Button(self, text='Pause', command=self.pause).pack(padx=10, pady=10)
               
        
        # text above bar
        self.primary_text = txt = tk.StringVar()
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        
        
        # the progress bar
        self.bar = ttk.Progressbar(self, mode='indeterminate')
        self.bar.pack(fill=tk.X, padx=10, pady=10)
        
        
        
        #the text below the bar
        self.secondary_text = tk.StringVar()
        self.time_estimate_ = tk.StringVar()
        self.clip_name_     = tk.StringVar()
        self.file_          = tk.StringVar()
        self.delay_         = tk.StringVar()
        
        for txt in (self.secondary_text,
                    self.time_estimate_,
                    self.clip_name_,
                    self.file_,
                    self.delay_,
                    ):
                    
            ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
            
        
    
    def check_for_abort(self):
        if main.win.step == 4:
            # indicate that the test should not continue
            raise Abort_by_User()
        
        
    @in_thread('GuiThread', wait=True, do_exceptions=True)
    def gui_progress_update(self,
                prog_type,
                num_trials=0,
                current_trial=0,
                msg='',
                clip_name='',
                delay='',
                file='',
                new_file=''
                ) -> bool:
        
        self.check_for_abort()
        
        messages = {
            'pre' : ('Loading...', ''),
            
            'proc' : ('Processing test data...',
                      f'Processing trial {current_trial+1} of {num_trials}'),
            
            'test' : ('Performing trials...',
                      f'Trial {current_trial+1} of {num_trials}'),
            
            'check-fail' : ('Trial failed...',
                f'Trial {current_trial+1} of {num_trials}\n{msg}'),
            
            'check-resume' : ('Resuming test...',
                f'Trial {current_trial+1} of {num_trials}\n{msg}'),
            
            'status' : ('', msg)
            
            }
        
        
        if prog_type in messages:
        
            self.primary_text.set(messages[prog_type][0])
            self.secondary_text.set(messages[prog_type][1])
                
        
        if not num_trials:
            #indeterminate progress bar
            self.bar.configure(mode='indeterminate', maximum = 100)
            self.bar.start()
            self.time_estimate_.set('')
            
            
        elif prog_type in ('pre', 'proc', 'test'):
            # show current progress
            self.bar.stop()
            self.bar.configure(value=current_trial, maximum = num_trials,
                               mode='determinate')
            

            # estimate time remaining
            
            if current_trial == 0:
                # if on trial 0, start timer
                self.stopwatch.reset()
                self.time_estimate_.set('')
            else:
                time_left, time_unit = self.stopwatch.estimate_remaining(
                    current_trial, num_trials)
                
                time_est = f'{time_left} {time_unit} remaining...'
                
                if self.pause_after not in (None, np.inf) and prog_type == 'test':
                    
                    # time remaining until next pause
                    ct_in_set = (current_trial % self.pause_after) + 1
                    
                    next_stop = current_trial + self.pause_after - ct_in_set
                    
                    time_left_set, time_unit_set = self.stopwatch.estimate_remaining(
                        current_trial, next_stop)
                    
                    time_est = f'{time_est}\n{time_left_set} {time_unit_set} until next pause.'
                

                
                self.time_estimate_.set(time_est)
        
        
        
        
        if prog_type == 'pre':
            self.clip_name_.set('')
            self.file_.set('')
            self.delay_.set('')
            self._is_paused = False
            [w.destroy() for w in self.warnings]
            self.warnings = []
        
        elif prog_type == 'warning':
            w = WarningBox(self,
                       f'WARNING: {msg}',
                       color='yellow',
                       )
            if w not in self.warnings:
                self.warnings.append(w)
                w.pack()
            
            
            
        elif prog_type == 'csv-update':
            self.clip_name_.set(f'Current Clip: {clip_name}')
            self.file_.set(self._trim_text(f'Storing data in: "{file}"'))
        
        elif prog_type == 'acc-clip-update':
            self.clip_name_.set(f'Current Clip: {clip_name}')
            self.delay_.set(f'Delay : {delay:.3f}s\n')
            
        elif prog_type == 'csv-rename':
            self.file_.set(self._trim_text(f'Renaming "{file}"')+
                           '\n'+
                           self._trim_text(f'to "{new_file}"'))
        
        
        
        
        if self._is_paused:
            self._is_paused = False
            self.stopwatch.pause()
            tk.messagebox.showinfo('Test Paused',
                                   'Press OK to continue.')
            self.stopwatch.start()
            
        
        return True
    
    
    @in_thread('GuiThread', do_exceptions=True)
    def user_check(self,
                   reason,
                   message='',
                   trials=None,
                   time=None,
                   msg=None) -> bool:
        if msg is not None:
            message = msg
        if trials:
            self.pause_after = trials
        
        
        self.check_for_abort()
        
        
        
        # don't count paused time in time-remaining calculation
        self.stopwatch.pause()
        
        if reason == 'normal-stop':
            tk.messagebox.showinfo('Test Paused',
                                   message+'\n\n'+
                                   'Press OK to continue.')
            
        elif reason == 'problem-stop':
            tk.messagebox.showerror('Test Paused',
                                    message+'\n\n'+
                                    'Press OK to continue.')
            
        
        # resume timer
        self.stopwatch.start()
        
        return False
    
    
    def _trim_text(self, text):
        """remove characters to fit the width"""
        
        # pixel width that the text is confined to
        w = self.winfo_width() - 20
        
        #estimate a safe character limit based on w and font size
        w_char = round(w / shared.FONT_SIZE * 1.1)
        
        chop = len(text) - w_char
        if chop <= 0:
            # no chopping to do!
            new = text
        else:
            # replace 'chop + 3' characters with a '...'
            new = text[0:25] + '...' + text[25 + chop + 3: ]
        
        return new
    
    
    def pause(self):
        self._is_paused = True
        
    
class _StopWatch:
    def __init__(self):
        self.paused = True
        self.elapsed_time = 0
        self.start_time = 0
        
            
    def reset(self):
        self._update_elapsed_time()
        self.elapsed_time = 0
        
    def stop(self):
        self.pause()
        self.reset()
        
    def start(self):
        self._update_elapsed_time()
        self.paused = False
        
    def pause(self):
        self._update_elapsed_time()
        self.paused = True
    def get(self):
        self._update_elapsed_time()
        return self.elapsed_time
    
    def estimate_remaining(self, current_trial, num_trials):
        time_elapsed = self.get()
        
        time_total = time_elapsed * num_trials / current_trial
        
        time_left = time_total - time_elapsed
        
        time_left = time_left / 60
        
        if time_left < 60:
            time_left = round(time_left)
            if time_left == 0:
                time_left = 'Less than 1'
                time_unit = 'minute'
            elif time_left == 1:
                time_unit = 'minute'
            else:
                time_unit = 'minutes'
        elif time_left < 60 * 24:
            time_left = round(time_left // 60)
            time_unit = 'hours'
        else:
            time_left = round(time_left // 60 // 24)
            time_unit = 'days'
    
        return (time_left, time_unit)
    
    
    
        
    def _update_elapsed_time(self):
        now = time.time()
        
        # don't count the time since last update if the timer has been paused
        if not self.paused:
            new_elapsed = now - self.start_time
            
            self.elapsed_time = self.elapsed_time + new_elapsed
            
            
        self.start_time = now
        
class WarningBox(tk.Frame):
    def __init__(self, master, text, color='yellow', **kwargs):
        super().__init__(master, background=color)
        
        tk.Button(self, text='x', command=self.destroy, background=color).pack(
            side=tk.RIGHT, padx=10, pady=10)
        
        ttk.Label(self, text=text, background=color).pack(
            side=tk.LEFT, padx=10, pady=10)
        
        
        self.text = text
        
        
    def __eq__(self, other):
        return isinstance(other, WarningBox) and self.text == other.text
    
    def pack(self, *args, **kwargs):
        
        super().pack(*args, side=tk.BOTTOM, fill=tk.X, **kwargs)
        
        
        
        


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
        element :
            A string, matplotlib figure, or tk widget class to be added into
            the window

        """
        
        if isinstance(element, Figure):
            canvas = FigureCanvasTkAgg(element, master=self)
            widget = canvas.get_tk_widget()
            canvas.draw()
            self.canvasses.append(widget)
            
        elif isinstance(element, str):
            widget = ttk.Label(self, text=element)
            
        else:
            widget = element(self)

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
        dir_ = self.outdir
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
    

        
        
        
        
        
        
        
        
        
        
        
#----------------------- Running the tests -----------------------------------
    



@in_thread('MainThread', wait=False)
def test_audio(root_cfg, on_finish=None):
    
    try:
        
    
        sel_tst = root_cfg['selected_test']
    
        cfg = root_cfg[sel_tst]
        
        if 'channel_rate' in root_cfg['SimSettings'] and root_cfg[
            'SimSettings']['channel_rate'] == 'None':
            root_cfg['SimSettings']['channel_rate'] = None
        
        
        
        radio_interface, ap = get_interfaces(root_cfg)
        
        
        # get selected audio file
        if 'audio_files' in cfg and cfg['audio_files'] and cfg['audio_files'][0]:
            
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
        show_error(error)
    
    if on_finish:
        on_finish()

    





@in_thread('MainThread', wait=False)
def run(root_cfg):
    
    # attempt to free memory and delete old RadioInterface to free up port
    gc.collect(2)
    
    ppf = main.win.frames['PostProcessingFrame']
    tpf = main.win.frames['TestProgressFrame']
    tif = main.win.frames['TestInfoGuiFrame']
    
    constructors = {
        'M2eFrame': m2e_gui.M2E_fromGui,
        'AccssDFrame': accesstime_gui.Access_fromGui,
        'PSuDFrame' : psud_gui.PSuD_fromGui,
        'IgtibyFrame': intelligibility_gui.Igtiby_from_Gui,
            }
    
    
    # extract test configuration
    sel_tst = root_cfg['selected_test']
    cfg = root_cfg[sel_tst]
    is_sim = root_cfg['is_simulation']
    

    
    #initialize test object
    my_obj = constructors[sel_tst]()
    
    try:
        
        # open interfaces for testing
        try:
            ri, ap = get_interfaces(root_cfg)
        except (RuntimeError, ValueError) as e:
            show_error(e)
            return
        
        # prevent logging excess of information
        my_obj.no_log = my_obj.no_log + (
            'progress_update',
            'get_post_notes',
        )
        
        
        
        
        
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
            
            # prepare config and check for invalid parameters
            param_modify(root_cfg)
                        
            # put config into object
            _set_values_from_cfg(my_obj, cfg)
             
            # Check for value errors with instance variables
            # this is last resort and should not be needed after param_modify()
            my_obj.param_check()
        
                
        
        
        # set progress update callback
        my_obj.progress_update = gui_progress_update
        
        if 'pause_trials' in cfg:
            #set user check callback
            my_obj.user_check = tpf.user_check
            tpf.pause_after = my_obj.pause_trials
        else:
            tpf.pause_after = None
        
        tpf.rec_stop = ap.rec_stop
        
        # remove post-processing info from frame
        ppf.reset()
        
        

        
        # Gather pretest notes and parameters
        my_obj.info = get_pre_notes(root_cfg)
        if my_obj.info is None: 
            #user pressed 'back' in test info gui
            return
        
        if is_sim and root_cfg['SimSettings']['_enable_PBI']:
            
            pcfg = root_cfg['SimSettings']
                        
            my_obj.info['PBI P_a1']=str(pcfg['P_a1'])
            my_obj.info['PBI P_a2']=str(pcfg['P_a2'])
            my_obj.info['PBI P_r'] =str(pcfg['P_r'])
            my_obj.info['PBI interval']=str(pcfg['interval'])
        
        
        #show progress bar in gui
        main.win.set_step(3, extra=ap.rec_stop)
        
        # clear pretest notes from window
        main.win.clear_old_entries()
        
        # set post_notes callback
        my_obj.get_post_notes=get_post_notes
        
        
        
        
        
    
        my_obj.audio_interface = ap
       
        # Enter RadioInterface object
        with ri as my_obj.ri:
            
            
            # run the test
            result = my_obj.run()
            
                 
        if sel_tst == 'IgtibyFrame':
            #show intelligibility estimate
            ppf.add_element(f'Intelligibility Estimate: {result}')
        
        
        elif sel_tst == 'M2eFrame' and cfg['test'] == 'm2e_1loc':
            #show mean and std_dev
            mean_msg, std_msg = my_obj.get_mean_and_std()
            
            ppf.add_element(mean_msg)
            ppf.add_element(std_msg)
            
            # plots will leak memory without this
            if use_alternate_plot_rendering:
                
                #create "show plots" button
                class ShowPlots(ttk.Button):
                    def __init__(self, master):
                        super().__init__(master,
                            text='Show Plots',
                            command=self.plot)
                    
                    @in_thread('MainThread', wait=False)
                    def plot(self):my_obj.plot()
                
                ppf.add_element(ShowPlots)
            else:
                ppf.add_element('To show plots, please install PyQt5')
                
        elif sel_tst == 'M2eFrame' and my_obj.test == 'm2e_2loc_tx':
            ppf.add_element('Data collection complete, you may now stop data\n' +
                            'collection on the receiving end')

    
    except InvalidParameter as e:
        # highlight offending parameter in red
        main.win.show_invalid_parameter(e)
        return
        
    
        
    #gathers posttest notes without showing error
    except Abort_by_User: pass
    
    #gathers posttest notes without showing error
    except KeyboardInterrupt: pass
    
    #indicates end of test
    except SystemExit: pass
        
    except Exception as e:
        if main.last_error is not e:
            show_error(e)

    
        
    # put outdir folder into frame
    try: ppf.outdir = my_obj.outdir
    except AttributeError: ppf.outdir = ''
    
    
    #delete radio interface
    my_obj.ri = None
    ri = None
    
    #show post-processing frame
    main.win.set_step(6)
    
    


def param_modify(root_cfg):
    """parses user-entered data into acceptable formats for the measure obj vars
    and checks for errors
    
    Parameters are only changed and checked as needed.
    

    Parameters
    ----------
    root_cfg : dict
        the tree of entered data.

    Raises
    ------
    Abort_by_User
        if the user presses 'cancel' when asked to calibrate dev_dly.
    InvalidParameter
        if a parameter cannot be parsed, or if it is missing

    
    """
    sel_tst = root_cfg['selected_test']
    cfg = root_cfg[sel_tst]
    
    
    
    
    if 'dev_dly' in cfg:
        
        bad = False
        
        try: cfg['dev_dly'] = float(cfg['dev_dly'])
        except ValueError: bad = True
        
        if bad: raise InvalidParameter('dev_dly',
            message='Make sure to calibrate your device delay (recommended)\n\n'+
            'Or, enter your known device delay here.')
        
        
    
        
    if 'audio_files' in cfg and 'audio_path' in cfg:
        
        
        # full audio dir? looking for something like '<entire audio folder>' in audio_files parameter
        cfg['full_audio_dir'] = not (
            cfg['audio_files'] and
            cfg['audio_files'][0]
        
            ) or (
                
            len(cfg['audio_files']) == 1 and
            '<' in cfg['audio_files'][0] and
            '>' in cfg['audio_files'][0]
            )
        
        p = cfg['audio_path']
        
        
        
        
        if cfg['full_audio_dir']:
            
            if not path.isdir(p):
                raise InvalidParameter('audio_path',
                                   message = 'Folder does not exist.')
            # check for existence of at least one .wav file
            success = False
            for f in listdir(p):
                fp = path.join(p, f)
                
                if path.isfile(fp) and path.splitext(fp)[1].lower() == '.wav':
                    success = True
                    break
                
            if not success:
                raise InvalidParameter('audio_path',
                    message='Folder must contain .wav files') 
            
        else:
            
            
            # check: audio files should all exist
            for f in cfg['audio_files']:
                af = path.join(p, f)
                
                if not path.isfile(af):
                    raise InvalidParameter('audio_files',
                        message=f'"{af}" does not exist')
                    
                if not path.splitext(af)[1].lower() == '.wav':
                    raise InvalidParameter('audio_files',
                        message='All audio files must be .wav files')
                
    
    
    bad = False
    # relative outdirs will go into the default outdir
    cfg['outdir'] = path.join(DEFAULTS[sel_tst]['outdir'], cfg['outdir'])
    try: os.makedirs(cfg['outdir'], exist_ok=True)
    except OSError as e: 
        error = str(e)
        bad = True
        
    
    if bad:
        raise InvalidParameter('outdir',
            message = error)
        
    
    
    # make pause_trials an integer or np.inf
    bad_param = False
    if 'pause_trials' in cfg:
        try:
            cfg['pause_trials'] = int(cfg['pause_trials'])
        except ValueError:
            if 'inf' in cfg['pause_trials'].lower():
                cfg['pause_trials'] = np.inf
            else:
                bad_param = True
                
        if root_cfg['is_simulation']:
            
            # don't do pauses in a simulation in access time
            cfg['pause_trials'] = np.inf
            bad_param = False
            
        if bad_param:
            raise InvalidParameter('pause_trials',
                        message='Number of trials must be a whole number')
    
    
    
    
    # combine the 2 ptt_delays into a vector
    if '_ptt_delay_min' in cfg:
        cfg['ptt_delay'] = [cfg['_ptt_delay_min']]
        try:
            cfg['ptt_delay'].append(float(cfg['_ptt_delay_max']))
        except ValueError:pass
        
    
    # combine time_expand into a 2 vector
    if '_time_expand_i' in cfg:
        cfg['time_expand'] = [cfg['_time_expand_i']]
        try:
            cfg['time_expand'].append(float(cfg['_time_expand_f']))
        except ValueError:pass
        
        
        
        
        
        
    """# InvalidParameter() does not work in advanced window
    
    # check auto_stop with ptt_rep
    if ('auto_stop' in cfg) and ('ptt_rep' in cfg) and cfg['auto_stop'] and (
            cfg['ptt_rep'] < 16):
        raise InvalidParameter('ptt_rep',
                    message='Must be greater than 15 if auto-stop is enabled')
    """
    
    
    
    if root_cfg['is_simulation']:
        
        # ptt_gap and ptt_wait should be set to 0 in simulations
        
        for key in ('ptt_wait', 'ptt_gap'):
            if key in cfg:
                cfg[key] = 0
        
        
        
        
def gui_progress_update(prog_type,
             num_trials=0,
             current_trial=0,
             msg='',
             clip_name='',
             delay='',
             file='',
             new_file=''
             ) -> bool:
    """
    

    Parameters
    ----------
    prog_type : str
        the event type.
    num_trials : int, optional
        total trials. The default is 0.
    current_trial : int, optional
        the current working trial. The default is 0.
    msg : str, optional
        the message associated with some events. The default is ''.
    clip_name : str, optional
        the currently processed clip. The default is ''.
    delay : float, optional
        the current PTT delay for access_time. The default is ''.
    file : str, optional
        The default is ''.
    new_file : str, optional
        The default is ''.

    RAISES
    ------
    Abort_by_User
        to abort the test

    """
    
    tpf = main.win.frames['TestProgressFrame']
    
    return tpf.gui_progress_update(prog_type,
                                  num_trials,
                                  current_trial,
                                  msg,
                                  clip_name,
                                  delay,
                                  file,
                                  new_file,
                                  )
    
    




def get_pre_notes(root_cfg):
    main.win.pretest(root_cfg)
    
    #wait for user submit or program close
    while main.win._pre_notes_wait and not main.win.is_destroyed:
        time.sleep(0.1)
     
    return main.win._pre_notes
        
def get_post_notes(error_only=False):
    
    #get current error status, will be None if we are not handling an error
    error_type, error =sys.exc_info()[:2]
    
    # ignore BaseExceptions, etc.
    is_showable_error = isinstance(error, Exception)
    
    if error_only and not is_showable_error:
        #nothing to do, bye!
        return {}
    
        
    # show post_test_gui frame
    main.win.post_test_info = None
    main.win.set_step(5, extra=error)
    
    
    if is_showable_error:
        main.last_error = error
        show_error()
    
    # wait for completion or program close
    
    while main.win.post_test_info is None and not main.win.is_destroyed:
        time.sleep(0.1)
    
    # retrieve notes
    nts = main.win.post_test_info
    if nts is None:
        nts = {}
    return nts
    

    


def get_interfaces(root_cfg):
    
    sel_tst = root_cfg['selected_test']
    cfg = root_cfg[sel_tst]
    is_sim = root_cfg['is_simulation']
    
    sim_cfg = root_cfg['SimSettings']
    
    ri_needed = True
    rec_stop = None
    
    # if channel_rate should be None, make it so
    if 'channel_rate' in sim_cfg and sim_cfg['channel_rate'] == 'None':
        
        # turn str(None) into None
        sim_cfg['channel_rate'] = None
    
    
    # convert simulated m2e-latency to optional float
    try:
        sim_cfg['m2e_latency'] = float(
                sim_cfg['m2e_latency'])
    except ValueError:
        sim_cfg['m2e_latency'] = None
        
        
    #------------------------- set channels -----------------------------------
    
    if sel_tst in ('AccssDFrame',):
        channels = {
            'playback_chans' : {'tx_voice':0, 'start_signal':1},
            'rec_chans' : {'rx_voice':0, 'PTT_signal':1},
            }
    
    elif 'test' in cfg and cfg['test'] == 'm2e_2loc_tx':
        
        if is_sim:
            # 2loc_rx test not allowed in simulated
            raise ValueError('A 2-location test cannot be simulated.')
        
        channels = {
            'playback_chans' : {"tx_voice": 0},
            'rec_chans' : {"IRIGB_timecode": 1},
            }
        
    elif 'test' in cfg and cfg['test'] == 'm2e_2loc_rx':
        
        if is_sim:
            # 2loc_rx test not allowed in simulated
            raise ValueError('A 2-location test cannot be simulated.')
        
        
        channels = {
            'playback_chans' : {},
            'rec_chans' : {"rx_voice": 0, "IRIGB_timecode": 1},
            }
        ri_needed = False
        
        rec_stop = GuiRecStop()
        
    
    else:
        # keep defaults
        channels = {
            'playback_chans' : {'tx_voice':0},
            'rec_chans' : {'rx_voice':0},
            }
    
    
    # in case of simulation test
    if is_sim:
        
        sim = QoEsim(**channels)
        
        _set_values_from_cfg(sim, sim_cfg)
        
        if sim_cfg['_enable_PBI']:
            
            prob=simulation.PBI()
            
            prob.P_a1=sim_cfg['P_a1']
            prob.P_a2=sim_cfg['P_a2']
            prob.P_r=sim_cfg['P_r']
            prob.interval=sim_cfg['interval']
            

            
            sim.pre_impairment=prob.process_audio

        
        ri = sim
        ap = sim
        
        
    
    else:
        hdw_cfg = root_cfg['HdwSettings']
        
        
        if 'radioport' in hdw_cfg and hdw_cfg['radioport']:
            radioport = hdw_cfg['radioport']
        else:
            radioport = ''
        
        
        if not ri_needed:
            # a real radiointerface is not needed
            ri = _FakeRadioInterface()
        else:
            ri = hardware.RadioInterface(radioport)
        
        
        ap = hardware.AudioPlayer(**channels)
        
            
            
        _set_values_from_cfg(ap, hdw_cfg)
        
        
        ap.blocksize = hdw_cfg['blocksize']
        ap.buffersize = hdw_cfg['buffersize']
        ap.sample_rate = 48000
        
        
    ap.rec_stop = rec_stop
    
    return ri, ap


class _SingletonRadioInterface(hardware.RadioInterface):
    """ a radio_interface that will be left open based on its radioport
    
    NOT YET IMPLEMENTED
    """
    
    _interface_objects = {}
    
    def __new__(cls, radioport):
            
        if radioport in cls._interface_objects:
            self = cls._interface_objects[radioport]
        else:
            self = super().__new__(radioport)
            
        return self
    
class _FakeRadioInterface:
    def __enter__(self, *args, **kwargs): return self
    def __exit__(self, *args, **kwargs): return False
    
def _set_values_from_cfg(my_obj, cfg):
    for k, v in cfg.items():
        if hasattr(my_obj, k):
            setattr(my_obj, k, v)





        


# TODO: implement the following frame?
class char_dev_dly(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, title='Device Delay Characterization', **kwargs)
        
        ttk.Label(self, text='\
It seems like you have not yet done a characterization test. \
A characterization test is a Mouth-to-Ear test that is run with the audio output \
directly fed into the input, as shown below.\
').pack(fill=tk.X, wraplength=300, padx=10, pady=10)

        ttk.Label(self, text='Once finished, enter the device delay below')
        
        self.dev_dly = tk.DoubleVar()
        ttk.Entry(textvariable=self.dev_dly).pack(padx=10,pady=10)
        
        ttk.Button(text='Skip Characterization (not recommended)'
                   ).pack()
        
        
        
        self.finished = False
                   
    
    def skip(self):
        pass
        
        
    
def _get_dev_dly(ignore_error = True):
    
    try:
        dev_dly = loadandsave.Config('dev_dly.json').load()['dev_dly']
    except FileNotFoundError:
        if not ignore_error:
            raise
        dev_dly = 0
    else:
        main.win.frames['AccssDelay'].btnvars['dev_dly'].set(dev_dly)
    
        return dev_dly
    



class GuiRecStop:
    
    def __init__(self):
        self._stopped = False
    
    def stop(self):
        self._stopped = True
    
        
    def __enter__(self, *args, **kwargs):
        return self
    
    def __exit__(self, *args, **kwargs):
        return False
    
    def is_done(self):
        
        return self._stopped
        




def show_error(exc=None):
    
    
    traceback.print_exc()
    
    if exc is None:
        exc = sys.exc_info()[1]
    if isinstance(exc, tuple):
        exc = exc[1]
        
    if not exc:
        #no error
        return
    
    print(exc)
    
    err_name, msg = format_error(exc)
    
    _show_error(err_name, msg)
    

def format_error(exc):
    msg = str(exc)
    err_name = exc.__class__.__name__
    
    
    if not msg and isinstance(exc, Exception):
        if 'error' in err_name.lower():
            descriptor = ''
        else:
            descriptor = ' error'
        if err_name[0].lower() in 'aeiou':
            article = 'An'
        else:
            article = 'A'
            
        msg = f'{article} "{err_name}"{descriptor} occurred.'
        
        
        err_name = 'Error'
    elif isinstance(exc, Abort_by_User):
        err_name = 'Measurement Stopped'
        msg = 'Aborted by user.'
    
        
    return err_name, msg
    
    
    
@in_thread('GuiThread')
def _show_error(err_name, msg):
    tk.messagebox.showerror(err_name, msg)
    











#---------------------- Get default values for parameters --------------------


# declare values here to pull default values from measure (or interface) class
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
    
    
    'DevDlyCharFrame': [
        'audio_files',
        'audio_path',
        'bgnoise_file',
        'bgnoise_volume',
        'outdir',
        'ptt_wait',
        'ptt_gap',
        'test',
        'trials',
    ],
    
    'M2eFrame': [
        'audio_files',
        'audio_path',
        'bgnoise_file',
        'bgnoise_volume',
        'outdir',
        'ptt_wait',
        'ptt_gap',
        'test',
        'trials'
    ],

    'AccssDFrame': [
        'audio_files',
        'audio_path',
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
        'pause_trials',
        'dev_dly',
    ],
    
    'PSuDFrame' : [
        'audio_files',
        'audio_path',
        'audio_path',
        'trials',
        'outdir',
        'ptt_wait',
        'ptt_gap',
        'm2e_min_corr',
        'intell_est',
    ],
    
    'IgtibyFrame': [
        'trials',
        'outdir',
        'ptt_wait',
        'ptt_gap',
        'pause_trials',
        'intell_est',
        'save_tx_audio',
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
        
        '_enable_PBI',
        'P_a1',
        'P_a2',
        'P_r',
        'interval',
        
    ],
    
    'HdwSettings' : [
        
        'overplay',
        'radioport',
        'dev_dly',
        'blocksize',
        'buffersize',
        ],
}

initial_measure_objects = {
    'DevDlyCharFrame': m2e_gui.DevChar_Defaults(),
    'M2eFrame': m2e_gui.m2e.measure(),
    'AccssDFrame': accesstime_gui.adly.measure(),
    'PSuDFrame' : psud_gui.psud.measure(),
    'IgtibyFrame': intelligibility_gui.igtiby.measure(),
    'SimSettings': shared._SimPrototype(),
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
                
                
                
                
                
# ----------- Special default values different from measurement obj -----------
dir_names = {
    'DevDlyCharFrame': 'Device_Delay_Characterization',
    'M2eFrame': 'Mouth_2_Ear',
    'AccssDFrame': 'Access_Time',
    'PSuDFrame': 'PSuD',
    'IgtibyFrame': 'Intelligibility'
    }
for name_, cfg in DEFAULTS.items():
    if 'outdir' in cfg:
        cfg['outdir'] = path.join(path.expanduser("~"),
                                  'MCV-QoE',
                                  dir_names[name_])
        
        
        
    if 'audio_files' in cfg and 'audio_path' in cfg:
        
        cfg['audio_path'], cfg['audio_files'] = shared.format_audio_files(
            cfg['audio_path'], cfg['audio_files'])





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
DEFAULTS['AccssDFrame']['pause_trials'] = str(int(DEFAULTS['AccssDFrame']['pause_trials']))
DEFAULTS['IgtibyFrame']['pause_trials'] = str(int(DEFAULTS['IgtibyFrame']['pause_trials']))

try:
    DEFAULTS['AccssDFrame']['dev_dly'] = str(_get_dev_dly(ignore_error=False))
except FileNotFoundError:
    DEFAULTS['AccssDFrame']['dev_dly'] = ''


DEFAULTS['SimSettings']['channel_rate'] = str(DEFAULTS['SimSettings']['channel_rate'])
DEFAULTS['SimSettings']['m2e_latency'] = 'minimum'

# the following should be a float
DEFAULTS['SimSettings']['access_delay'] = float(DEFAULTS['SimSettings']['access_delay'])

for k in ('P_a1', 'P_a2', 'P_r', 'interval'):
    DEFAULTS['SimSettings'][k] = float(DEFAULTS['SimSettings'][k])



# the following do not have a default value
DEFAULTS['SimSettings']['_enable_PBI'] = False





#free initial objects
del initial_measure_objects
del obj












        

if __name__ == '__main__':
    


        
    
    main = Main(MCVQoEGui)
    main.main_loop()
