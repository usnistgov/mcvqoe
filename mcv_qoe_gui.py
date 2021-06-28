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
from shared import Abort_by_User
import loadandsave
import accesstime_gui
from accesstime_gui import AccssDFrame
import m2e_gui
from m2e_gui import M2eFrame
import psud_gui
from psud_gui import PSuDFrame


# basic config
TITLE_ = 'MCV QoE'


WIN_SIZE = (900, 800)

    
    
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
 
        
         # create test-specific frames
        self._init_frames()
        
        # sets the current frame to be blank
        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        
        # instance vars
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
            
            M2eFrame,
            AccssDFrame,
            PSuDFrame,
            
    #TODO: add rest of frames
        ]
        
        
        self.frames = {}
        for F in frame_types:
            
            btnvars = loadandsave.TkVarDict()

            # initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=btnvars)

            # when user changes a control
            btnvars.on_change = self.on_change
        
        
        self.simulation_settings = loadandsave.TkVarDict()
        self.hardware_settings = loadandsave.TkVarDict()
        
        
        

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
                                   fill=tk.BOTH, padx=10, pady=10)

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
        main.stop()
        #waits for test to close gracefully, then destroys window
        self.after(50, self._wait_to_destroy)
        
        
    def _wait_to_destroy(self):
        if main.is_running:
            self.after(50, self._wait_to_destroy)
        else:
            self.destroy()
            
    def destroy(self, *args, **kwargs):
        super().destroy(*args, **kwargs)
        self.is_destroyed = True
            
    def restore_defaults(self, *args, **kwargs):
        if self.ask_save():
            # cancelled
            return
        
        current = self.currentframe.__class__.__name__
        
        #destroy all frames
        for frame_name, frame in self.frames.items():
            frame.destroy()
        
        # reconstruct frames as default
        self._init_frames()
        
        #keep the current frame displayed
        self.show_frame(current)

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
            'selected_test': self.selected_test.get()
        }

        for framename, frame in self.frames.items():
            obj[framename] = frame.btnvars.get()
        
        txt_box = self.frames['TestInfoGuiFrame'].pre_notes
        
        # gets 'Pre Test Notes' from text widget
        obj['TestInfoGuiFrame']['Pre Test Notes'] = txt_box.get(1.0, tk.END)
        
        
        
        return obj
    
        
    def pretest(self):
        self.set_step(2)

    def run(self):
        
        #set step to 'running'
        self.set_step(3)
        
        #retrieve configuration from controls
        cnf = self.get_cnf()
        
        #runs the test
        run(cnf)
                

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
        self.set_step(4)
        
        err_class, err_msg, trace = error
        if err_class:
            tk.messagebox.showerror(
               err_class.__name__, err_msg)
        
    def finish(self):
        
        txt_box = self.frames['PostTestGuiFrame'].post_test
        
        # retrieve post_notes
        self.post_test_info = {'Post Test Notes': txt_box.get(1.0, tk.END)}
                
        #back to config frame
        self.configure_test()
               
        
    def set_step(self, step):
        self.step = step
        if step == 0:
            self.selected_test.set('EmptyFrame')
            self.show_frame('EmptyFrame')
            next_btn_txt = 'Next'
            next_btn = None #disabled
            back_btn = None
        
        elif step == 1:
            self.show_frame(self.selected_test.get())
            next_btn_txt = 'Next'
            next_btn = lambda : self.set_step(2)
            back_btn = lambda : self.set_step(0)
        
        elif step == 2:
            self.show_frame('TestInfoGuiFrame')
            next_btn_txt = 'Run Test'
            next_btn = self.run
            back_btn = self.configure_test
        
        elif step == 3:
            self.show_frame('TestProgressFrame')
            next_btn_txt = 'Abort Test'
            next_btn = self.abort
            back_btn = None
            
        elif step == 4:
            self.show_frame('PostTestGuiFrame')
            next_btn_txt = 'Finish'
            next_btn = self.finish
            back_btn = None
            
        
        #changes function and text of the next button
        self.set_next_btn(next_btn_txt, next_btn)
        
        #changes back button
        self.set_back_btn(back_btn)
    
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
        
        self.master.set_next_btn = self.set_next_btn
        self.master.set_back_btn = self.set_back_btn
        
        # a text-changeable 'next', 'run' or 'abort' button
        self._nxt_btn_wgt = ttk.Button(
                   master=self, textvariable=self.run_textvar,
                   command=self._next_btn)
        self._nxt_btn_wgt.pack(side=tk.RIGHT)
        
        
        # Back Button
        self._bck_btn_wgt = ttk.Button(self, text='Back',
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
    
    def set_back_btn(self, callback):
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
        self._previous_bar_length = None
        self.start_time = time.time()
        self.btnvars = btnvars
        
        super().__init__(master, *args, text='', **kwargs)
        
        # text above bar
        self.primary_text = txt = tk.StringVar()
        
        
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        # the progress bar
        self.bar = ttk.Progressbar(self, mode='indeterminate')
        self.bar.pack(fill=tk.X)
        
        
        #the text below the bar
        
        self.secondary_text = txt = tk.StringVar()
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        self.tertiary_text = txt = tk.StringVar()
        ttk.Label(self, textvariable=txt).pack(padx=10, pady=10, fill='x')
        
        
    @in_thread('GuiThread', wait=True)
    def progress(self, prog_type, num_trials, current_trial, err_msg='') -> bool:
        
        
        messages = {
            'proc' : ('Processing test data...',
                      f'Processing trial {current_trial+1} of {num_trials}'),
            
            'test' : ('Performing tests...',
                      f'Trial {current_trial} of {num_trials}'),
            
            'check-fail' : ('Test encountered an error.',
                f'Trial {current_trial+1} of {num_trials}')
            
            }
        
        
    
        if num_trials != self._previous_bar_length:
            self._previous_bar_length = num_trials
            self.bar.configure(maximum=num_trials, mode='determinate')
        
        self.bar.configure(value=current_trial)
        
        self.primary_text.set(messages[prog_type][0])
        
        self.secondary_text.set(messages[prog_type][1])
        
        
        if num_trials != 0:
            if current_trial == 0:
                self.start_time = time.time()
                self.tertiary_text.set('')
            else:
                # estimate time remaining
                time_elapsed = time.time() - self.start_time
                
                time_total = time_elapsed * num_trials / current_trial
                
                time_left = time_total - time_elapsed
                
                time_left = time_left / 60
                
                if time_left <= 60:
                    time_left = round(time_left)
                    time_unit = 'minutes'
                else:
                    time_left = time_left // 60 + 1
                    time_unit = 'hours'
                
                self.tertiary_text.set(f'{time_left} {time_unit} remaining...')
        
        
        
        # indicate that the test should continue
        return True











#------------------------------  Appearance ----------------------------------

def set_font(**cfg):
    """Globally changes the font on all tkinter windows.

    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)


def set_styles():
    
    style_obj = ttk.Style()

    for style in ('TButton', 'TEntry.Label', 'TLabel', 'TLabelframe.Label',
                  'TRadiobutton', 'TCheckbutton'):
        style_obj.configure(style, font=('TkDefaultFont', shared.FONT_SIZE))
    
    
    # help button and tooltip styles
    style_obj.configure('McvHelpBtn.TLabel', font=('TkDefaultFont',
                round(shared.FONT_SIZE * 0.75)), relief='groove')
    style_obj.configure('McvToolTip.TLabel', 
                background='white')
    style_obj.configure('McvToolTip.TFrame',
                background='white', relief='groove')

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
def run(root_cfg):
    
    # TODO implement other tests here
    class_assoc = {
        'M2eFrame': m2e_gui.M2E_fromGui,
        'AccssDFrame': accesstime_gui.Access_fromGui,
        'PSuDFrame' : psud_gui.PSuD_fromGui
            }
    
    
    # extract test configuration and notes from root_cfg
    sel_tst = root_cfg['selected_test']
    is_sim = root_cfg['is_simulation']
    cfg = root_cfg[sel_tst]
    pre_notes = root_cfg['TestInfoGuiFrame']
    
    
    
    
    #initialize object
    my_obj = class_assoc[sel_tst]()
    
    try:
        
        #translate cfg items as necessary
        
        #TODO: include modifications for sim- and hdwr-settings
        param_modify(cfg, is_sim)
        
        
        my_obj.progress_update = main.win.frames['TestProgressFrame'].progress
        
        
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
            for k, v in cfg.items():
                if hasattr(my_obj, k):
                    setattr(my_obj, k, v)
             
             
             
            #TODO: change this when M2E implements multiple audio files
            if 'audio_files' in cfg and hasattr(my_obj, 'audio_file'):
                 my_obj.audio_file = cfg['audio_files'][0]
    
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
            #TODO: make sure to override pre_test and post_test guis
            my_obj.info.update(pre_notes)
    
    
            # Write pretest notes and info to tests.log
            write_log.pre(info=my_obj.info, outdir=my_obj.outdir)
            
        else:
            my_obj.info = pre_notes
    
        # clear notes from window
        main.win.clear_notes()
        
        # set post_notes callback
        my_obj.get_post_notes=get_post_notes
        
        
        
        
        # in case of simulation test
        if is_sim:
            # create simulator
            sim = QoEsim()
                
            #override these to simulate them
            RadioInterface = lambda *args, **kwargs : sim
            AudioPlayer = lambda *args, **kwargs : sim
        
            #TODO: the following is a workaround
            m2e_gui.m2e_class.AudioPlayer = AudioPlayer
        
        else:
            RadioInterface = hardware.RadioInterface
            AudioPlayer = hardware.AudioPlayer
        
    
        
        #TODO: set these values from the new hardware_settings
        #bs = my_obj.blocksize
        #bf = my_obj.buffersize
        #fs = my_obj.fs
        #ap = AudioPlayer(fs=my_obj.fs,blocksize=bs,buffersize=bf)
        ap = AudioPlayer()
        
        
        if hasattr(my_obj, 'audio_interface'):
            my_obj.audio_interface = ap
        elif hasattr(my_obj, 'audio_player'):
            my_obj.audio_player = ap
        
            my_obj.audio_player.playback_chans = {'tx_voice':0, 'start_signal':1}
            my_obj.audio_player.rec_chans = {'rx_voice':0, 'PTT_signal':1}
    
    
        # Open RadioInterface object
        #TODO: use radioport
        radioport = ''
        with RadioInterface(radioport) as my_obj.ri:
        
            #run test
            my_obj.run()
            

    
    except ValueError as e:
        tk.messagebox.showerror('Invalid Option', str(e))
        
        # go back to config screen
        main.win.configure_test()
        return
    
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
        return

    
    #PSuD handles this internally
    if sel_tst in ('M2eFrame', 'AccssDFrame'):
        # Gather posttest notes and write to log
        post_dict = get_post_notes()
        write_log.post(info=post_dict, outdir=my_obj.outdir)
    
    # leave gap in console for next test
    print('\n\n\n')
    
def param_modify(cfg, is_simulation):
    pass
    
        
def get_post_notes(error_only=False):
    
    #get current error status, will be None if we are not handling an error
    root_error=sys.exc_info()
    error = root_error[0]
    
    #check if there is no error and we should only show on error
    if( (not error) and error_only):
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
    
    

        

if __name__ == '__main__':
    
    # on Windows, remove dpi scaling (otherwise text is blurry)
    if hasattr(ctypes, 'windll'):
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

       
    
    Main()
