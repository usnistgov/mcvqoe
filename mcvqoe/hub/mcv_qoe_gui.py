# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov

"""
# -----------------------------basic config------------------------------------
TITLE_ = 'MCV QoE'
appid = 'nist.mcvqoe.gui.1_0_0'


import ctypes
# on Windows:
if hasattr(ctypes, 'windll'):
    # remove dpi scaling (otherwise text is blurry)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
    
    # allows icon setting on taskbar
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    
import importlib.resources
import tkinter.messagebox as msb
import tkinter.filedialog as fdl
import tkinter.font as font
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk
import _tkinter

from .tk_threading import Main, in_thread
from .tk_threading import format_error, show_error, Abort_by_User, InvalidParameter
from .tk_threading import SingletonWindow
from .version import version as gui_version
import mcvqoe.hub.shared as shared
import mcvqoe.hub.loadandsave as loadandsave

import sounddevice as sd
import sys
import time
import _thread
import json
import pickle
import os
from os import path, listdir
import gc
import subprocess as sp
import traceback
import numpy as np

from pkg_resources import resource_filename

#                       -----------------------------
# !!!!!!!!!!!!!         MORE IMPORTS BELOW THE CLASS!       !!!!!!!!!!!!!!!!!!!
#                       -----------------------------

#---------------------------- The main window class---------------------------
class MCVQoEGui(tk.Tk):
    """The main window.
    
    This window serves as both the initial loading window and the primary
    window of the application (there were problems with having multiple
    instances of tk.Tk)


    """

    def __init__(self, *args, **kwargs):
        """Initializes the window as a loading window.
        
        Use self.init_as_mainwindow() to switch to the primary gui
        

        """
        
        super().__init__(*args, **kwargs)
        
        #---------------------- a loading window ------------------------------
        
        # remove title and taskbar icons
        self.overrideredirect(True)
        
        try:
            # on windows, add alwaysontop
            self.attributes('-topmost',True)
        except:
            pass
        
        # set dimensions and center
        screenw = self.winfo_screenwidth()
        screenh = self.winfo_screenheight()
        
        #get height of text
        txt_h = tk.font.Font(font='TkDefaultFont').metrics('linespace')
        #make sure we have room
        txt_h *= 2

        w = 470
        h = 250 + txt_h
        
        x = (screenw - w) // 2
        y = (screenh - h) // 2
        
        self.geometry(f'{w}x{h}+{x}+{y}')

        with importlib.resources.path('mcvqoe.hub','MCV-sm.ico') as icon:
            if icon:
                #set the title- and taskbar icon
                self.iconbitmap(icon)
            else:
                print('Could not find icon file')
        
        # when the user closes the window
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # set the dpi scaling based on the window size
        dpi_scaling()
        
        #add MCV sticker logo
        sticker = StickerFrame(self, width = w, height = h - txt_h)
        sticker.pack()
        
        self.text = tk.StringVar(value='Loading Libraries...')
        ttk.Label(self, textvariable = self.text).pack(
            side=tk.BOTTOM)
        
    def load_progress(self, text):
        self.text.set(text)

    # ------------------------- The main window ------------------------------
        
    @in_thread('GuiThread')
    def init_as_mainwindow(self):
        """Creates the primary widgets of the gui.
        

        """
        
        # prevents random window flashing
        self.withdraw()

        #show titlebar and taskbar items
        self.overrideredirect(False)
        try:
            # on windows, revoke alwaysontop
            self.attributes('-topmost',False)
        except: pass
        
        # clear old widgets
        for name_, widget in self.children.copy().items():
            widget.destroy()

        # tcl variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')
        
        # variable to determine selected audio interface
        self.audio_device = tk.StringVar(value='')

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
        self.init_frames()
        
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
        self._is_force_closing = False
        self._pre_notes = None
        self._old_selected_test = 'EmptyFrame'
        self.set_step('empty')
        
        # indicates that the user does not need to save the configuration
        self.set_saved_state(True)
        
        # show the window
        self.deiconify()

        # if the session closed unexpectedly last time, show a recovery prompt.
        if loadandsave.misc_cache['accesstime.need_recovery']:
            tk.messagebox.showwarning('Recovered Measurement',
                    'An Access Time measurement was recovered. '+
                    'You may recover it using the "Recovery File" entry '+
                    'in Access Time.')

    def _disable_left_frame(self, disabled : bool):
        """ updates the state of the buttons on the left frame based on
        whether or not a measurement is currenlty running.

        """
        state = ('!disabled', 'disabled')[disabled]
        
        for n_, w in self.LeftFrame.MenuFrame.TestTypeFrame.children.items():
            if isinstance(w, (ttk.Button, ttk.Radiobutton, ttk.Label)):
                w.configure(state=state)

    def _rm_waits_in_sim(self):
        """ disables ptt_wait and ptt_gap, etc controls in case of a simulation
        
        """
        # !disabled means not disabled
        state = ('!disabled', 'disabled')[self.is_simulation.get()]
        
        in_frames = (
            m2e,
            accesstime,
            psud,
            intelligibility,
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
            self.frames[m2e].btnvars['test'].set('m2e_1loc')

    def init_frames(self):
        """Consructs the test-specific frames.
        
        To add a scrollbar to a frame, put its class in the 
        frame_types_with_scrollbar list too.
        
        The instances are stored in dictionary self.frames, with their keys
        being their self.__class__.__name__
        
        
        The instance's "btnvars" attribute is a dict of tcl variables for each
        parameter. for instance:
            
            self.frames[M2E].btnvars['audio_path'].set('c:\\users\\my_folder')
            
        would set the mouth-to-ear audio_path parameter. similarly .get()
        """

        frame_types = [
            EmptyFrame,
            TestInfoGuiFrame,
            PostTestGuiFrame,
            TestProgressFrame,
            PostProcessingFrame,
            
            loader.DevDlyCharFrame,
            
            loader.M2eFrame,
            loader.AccssDFrame,
            loader.PSuDFrame,
            loader.IgtibyFrame,
        ]
        
        # frames from the above can be copied in here to give them scrollbar
        frame_types_with_scrollbar = []
        
        
        self.frames = {}
        for F in frame_types:
            
            # construct tcl variables for parameters and populate with default values
            btnvars = loadandsave.TkVarDict(**DEFAULTS[F.__name__])
            
            # determine master based on whether it should have a scrollbar
            master = (self, self.RightFrame)[F in frame_types_with_scrollbar]
            
            # initializes the frame, with its key being its own classname
            f = F(master=master, btnvars=btnvars)
            
            self.frames[f.__class__.__name__] = f

            # when user changes a parameter, run this callback
            btnvars.on_change = self.on_change
            
            
        # construct tcl variables for simulation- and hardware settings
        self.simulation_settings = loadandsave.TkVarDict(
            **DEFAULTS['SimSettings'])
        
        
        self.hardware_settings = loadandsave.TkVarDict(
            **DEFAULTS['HdwSettings'])
        
        # attempt to load device delay from disk
        _get_dev_dly()

    def _set_dimensions(self):
        """Algorithm to place and size the window on the screen.
        
        """
        
        # which frames should set the minimum size
        important_frame_types = (
            loader.DevDlyCharFrame,
            loader.M2eFrame,
            loader.PSuDFrame,
            loader.IgtibyFrame,
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
                except: 
                    pass

    def _cache_dimensions(self):
        """saves the window's placement and dimensions to a cache for later

        """
        loadandsave.dim_cache.update(
                           x = self.winfo_x(),
                           y = self.winfo_y(),
                           w = self.winfo_width(),
                           h = self.winfo_height()
            )

    def _select_test(self):
        """called when the user changes the 'Choose test:' radiobutton
        """
        
        # close the current config if the user is changing measurements
        new = self.selected_test.get()
        old = self._old_selected_test
        
        if old != new:
            #temporarily select old frame becore performing save
            self.selected_test.set(self._old_selected_test)
            
            if old != 'EmptyFrame' and self.restore_defaults():
                # True if cancelled: return to old.
                new = self._old_selected_test
                
                
            self.selected_test.set(new)
            
            if self.step in ('empty', 'config'):
                self.set_step('config')
        
                
        self._old_selected_test = new

    @in_thread('GuiThread')
    def show_frame(self, framename):
        """shows the specified frame on the right side of the gui.
        the frame must be in self.frames
        

        Parameters
        ----------
        framename : str
            the name of the frame's class (used as the key in self.frames)


        """
        # first hide the showing widget
        self.currentframe.pack_forget()
        try:
            # attempt to set the new frame
            self.currentframe = self.frames[framename]
        finally:
            self.currentframe.pack(side=tk.RIGHT,
                                   fill=tk.BOTH, padx=10, pady=10, expand=True)
        
        # for frames with a scrollbar, put the scrollbar canvas in
        if self.currentframe.master is self.RightFrame:
            self.RightFrame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        else:
            # otherwise, remove the scrollbar canvas
            self.RightFrame.pack_forget()

    def is_empty(self):
        return self.currentframe == self.frames['EmptyFrame']

    def on_change(self, *args, **kwargs):
        """called when the user changes a parameter.

        """
        # indicate that the config is not saved
        self.set_saved_state(False)

    def on_close(self):
        """Closes the window and stops the program.
        
        This is called when the user presses the close button on the window

        """
        
        # if this is the first time the user pressed close
        
        if not self._is_closing:
            if self.ask_save():
                # canceled by user
                return
            if self.step == 'in-progress' and self.abort():
                # abort was canceled by user
                return
        else:
            # if the user already pressed close
            self._is_force_closing = True
            
            
        self._is_closing = True
        
        # destroy elements in the ppf to prevent errors
        self.frames['PostProcessingFrame'].reset()
        
        # cache window dimensions and placement for later recovery
        self._cache_dimensions()
        
        
        # save hardware settings for later session
        try:
            loadandsave.hardware_settings.update(self.hardware_settings.get())
        except Exception as e:
            show_error(e)
            show_error(RuntimeError('Hardware Settings were not saved.'))
        
        # end the main-thread's event loop
        loader.tk_main.stop()
        
        #waits for main thread to close gracefully
        while loader.tk_main.is_running:

            # if get_post_notes() gets called, or if the measurement is aborting,
                # wait for user to enter notes post notes
            if self.step in ('aborting', 'post-notes'):
                self._wait_to_destroy()
                return
            
            
            
            time.sleep(0.1)
            
            # if the main thread is frozen, then this loop will freeze the
            # gui as well. This is intended, so that the user can force
            # quit the frozen application
        
        
        # destroy the window and stop the gui-thread's event loop.
        self.destroy()

    def _wait_to_destroy(self):
        """Waits for the abort to complete and then closes the application
        

        """
        if self.step == 'in-progress':
            # user canceled abort
            self._is_closing = False
            return
        
        if self.step == 'post-notes' and self._is_force_closing:
            
            # submit post notes to prevent freeze.
            self._post_test_submit()
        
        if loader.tk_main.is_running:
            # keep calling this function until the main-thread event loop stops
            self.after(50, self._wait_to_destroy)
            
        else:
            #destroy elements from ppf to avoid some errors
            self.frames['PostProcessingFrame'].reset()
            gc.collect(2)
            
            # destroy the window and stop the gui-thread's event loop.
            self.destroy()
            
    def destroy(self, *args, **kwargs):
        super().destroy(*args, **kwargs)
        self.is_destroyed = True
            
    def restore_defaults(self, *args, **kwargs):
        """Button to restore the default parameters
        
        RETURNS
        -------
        cancelled : bool
        
            if the operation was cancelled by the user

        """
        if self.ask_save():
            # cancelled
            return True
        
        for fname, f in self.frames.items():
            f.btnvars.set(DEFAULTS[fname])
            
        _get_dev_dly()
        
        # user shouldn't be prompted to save the default config
        self.set_saved_state(True)
        
        return False

    def open_(self, *args, **kwargs):
        """Button to load the parameters from a .json file
        """
        
        if self.step not in ('empty', 'config'):
            raise RuntimeError("Can't load while measurement is running.")
        
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
            
        # change selected test frame
        self.selected_test.set(dct['selected_test'])
        
        
        # fill in parameters
        for frame_name, frame in self.frames.items():
            if frame_name in dct:
                frame.btnvars.set(dct[frame_name])
        
        # whether it was a simulation
        self.is_simulation.set(dct['is_simulation'])
        
        # set simulation settings from test-specific settings
        self.simulation_settings.set(dct['SimSettings'])
        
        try:
            # attempt to load hardware settings from appdirs
            self.hardware_settings.set(
                loadandsave.Config('HdwSettings.json').load())
        except FileNotFoundError:
            pass
        
        # attempt to load device delay
        _get_dev_dly()
        
        self.set_step('config')

        # the user has not modified the new config, so it is saved
        self.set_saved_state(True)

        # 'save' will now save to this file
        self.cnf_filepath = fpath

    def save_as(self, *args, **kwargs) -> bool:
        """Prompts the user to save the parameters as a .json file

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
        """Saves config to .json file.
        
        If there is no loaded .json file, this is equivalent to save_as()

        Returns
        -------
        cancelled : bool
            True if the save was cancelled.

        """
        # if user hasnt saved or loaded a configuration, fall back to save_as
        if not self.cnf_filepath:
            return self.save_as()
        
        obj = self.get_cnf()

        with open(self.cnf_filepath, mode='w') as fp:
            
            json.dump(obj, fp)
            
            
        self.set_saved_state(True)
        return False

    def ask_save(self) -> bool:
        """Prompts the user to save the config, if it is not already saved.
        
        If this returns True, then the action that prompted this function call
        (such as an abort) should be cancelled.


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
    
    
    @in_thread('GuiThread', wait=True, except_=Exception)
    def get_cnf(self) -> dict:
        """

        Returns
        -------
        root_cfg : dict
            Contains every parameter in the whole gui,
            sorted into sub-dicts by their location.
            
            Obeys the same structure as the global variable DEFAULTS.

        """
        obj = {
            'is_simulation': self.is_simulation.get(),
            'selected_test': self.selected_test.get(),
            'SimSettings'  : self.simulation_settings.get(),
            'HdwSettings'  : self.hardware_settings.get(),
            'audio_device': self.audio_device.get()
        }

        for framename, frame in self.frames.items():
            obj[framename] = frame.btnvars.get()
        
        
        
        return obj

    @in_thread('GuiThread', wait=False)    
    def show_invalid_parameter(self, e : InvalidParameter):
        
        """Highlights an offending parameter in red, if its value is invalid.
        
        Is called when an InvalidParameter is raised from somewhere in run()
        
        
        This currently does not work for parameters in advanced,
        hardware settings, or simulation settings.

        Parameters
        ----------
        e : InvalidParameter
        """

        loc = self.frames[self.selected_test.get()]
        
        if not hasattr(loc, 'controls') or e.parameter not in loc.controls:
            
            if e.parameter in self.controls:
                loc = self
            else:
                # could not find offending control... show as error instead
                traceback.print_exc()
                tk.messagebox.showerror('Invalid Parameter', str(e))
                return
            
        try:
            ctrl = loc.controls[e.parameter].m_ctrl
        except AttributeError:
            
            show_error(e)
            return
        
        else:
            master = shared._get_master(ctrl)
            # if the control was in an advanced window
            if isinstance(master, shared.AdvancedConfigGUI):
                #recreate that window
                type(master)(master.master, btnvars=ctrl.master.btnvars)
                # get the new instance of ctrl
                ctrl = loc.controls[e.parameter].m_ctrl
                
            
            # try to make the control red, if applicable
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
            
        finally:
            # back to config
            self.set_step('config')
    
    
    
    @in_thread('GuiThread', wait=True)
    def pretest(self, root_cfg):
        """Shows the pre-test-notes frame.
        
        Parameters
        ----------
        root_cfg : dict
            see self.get_cnf()
        """
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
        self.set_step('pre-notes')
        
    def _pretest_submit(self):
        """Button to submit the pre-test notes
        


        """
        # get test info from entry controls
        self._pre_notes = self.frames['TestInfoGuiFrame'].btnvars.get()
            
        txt_box = self.frames['TestInfoGuiFrame'].pre_notes
        # gets 'Pre Test Notes' from text widget
        self._pre_notes['Pre Test Notes'] = txt_box.get(1.0, tk.END)
        
        self._pre_notes_wait = False
        
    def _pretest_cancel(self):
        """Button to cancel pre-test-notes submission and return to configuration
        
        """
        
        self._pre_notes_wait = False
        
        self.set_step('config')
            
    def run(self):
        """ Button to submit the configuration and start the measurement
        
        calls the main run() function.
        """
        
        # update the progress screen to say 'Loading...'
        gui_progress_update('pre', 0, 0)
        
        try:
            #retrieve parameters from entries
            root_cfg = self.get_cnf()
            
        except InvalidParameter as e:
                
                self.show_invalid_parameter(e)
                return
        
        #runs the test
        run(root_cfg)
        
        

    def abort(self):
        """Prompts the user to abort the test.

        Returns
        -------
        cancel : bool
            True if the user cancelled the abort.
        """
        
        if tk.messagebox.askyesno('Abort Test',
            'Are you sure you want to abort?'):
            self.set_step('aborting')
            return False
        else:
            # indicates cancelled by user
            return True
    
       
        
    def _post_test_submit(self):
        """Button to submit post-test-notes

        """
        txt_box = self.frames['PostTestGuiFrame'].post_test
        
        # retrieve post_notes
        self.post_test_info = {'Post Test Notes': txt_box.get(1.0, tk.END)}
        
        
    def set_step(self, step, extra=None):
        """Sets which part of the measurement the program is on.
        
        the current step can be accessed in self.step
        
        
        STEPS
        -----
        
        empty
            the user has not selected a measurement yet
        
        config
            setting parameters
        
        pre-notes
            pre-test notes
        
        in-progress
            the measurement is running and the progress bar is showing
        
        aborting 
            the gui is waiting for the current recording to complete
            and will then abort the measurement.
            
            in this step, the gui won't close.
        
        post-notes
            post-test notes. while these are showing
            
            in this step, the gui won't close
        
        post-process
            showing results, plots, outdir, etc
        
        

        Parameters
        ----------
        step : str
            one of the above options
        
        extra : ANY, optional
            extra info about the step.
            
            Example: rec_stop object for m2e_2loc_rx, which overrides the abort button
            to become a stop recording button
        """
        self.step = step
        
        self._set_step(step, extra=extra)
        
    @in_thread('GuiThread')
    def _set_step(self, step, extra=None):
        
        back_btn_txt = 'Back'
        
        if step == 'empty':
            # blank window
            self.selected_test.set('EmptyFrame')
            next_btn_txt = 'Next'
            next_btn = None #disabled
            back_btn = None
        
        elif step == 'config':
            # test configuration
            self.show_frame(self.selected_test.get())
            next_btn_txt = 'Next'
            next_btn = self.run
            back_btn = lambda : self.set_step('empty')
        
        
        elif step == 'pre-notes':
            # test info gui
            self.show_frame('TestInfoGuiFrame')
            next_btn_txt = 'Submit'
            next_btn = self._pretest_submit
            back_btn = self._pretest_cancel
            
        elif step == 'in-progress':
            # progress bar
            self.show_frame('TestProgressFrame')
            
            if isinstance(extra, GuiRecStop):
                next_btn_txt = 'Stop Recording'
                next_btn = extra.stop
            else:
                next_btn_txt = 'Abort Test'
                next_btn = self.abort
            back_btn = None
            
        elif step == 'aborting':
            # in process of aborting
            self.show_frame('TestProgressFrame')
            self.frames['TestProgressFrame'].primary_text.set('Aborting...')
            
            next_btn_txt = 'Force Stop'
            next_btn = _thread.interrupt_main
            back_btn = lambda : self.set_step('in-progress')
            back_btn_txt = 'Cancel Abort'
            
        elif step == 'post-notes':
            #post_test
            self.frames['PostTestGuiFrame'].set_error(extra)
            self.show_frame('PostTestGuiFrame')
            next_btn_txt = 'Submit'
            next_btn = self._post_test_submit
            back_btn = None
            
        
        elif step == 'post-process':
            self.show_frame('PostProcessingFrame')
            next_btn_txt = 'Finish'
            next_btn = lambda : self.set_step('empty')
            back_btn = lambda : self.set_step('config')
            back_btn_txt = 'Run Again'
            
        else:
            # invalid step
            raise ValueError(f'"{step}" is not a known step')

        #changes function and text of the next button
        self.set_next_btn(next_btn_txt, next_btn)
        
        #changes back button
        self.set_back_btn(back_btn_txt, back_btn)
        
        # disable or enable leftmost buttons depending on if they are functional
        self._disable_left_frame(step not in ('empty', 'config'))
    
    @in_thread('GuiThread', wait=False)
    def clear_old_entries(self):
        """
        Clears pre-notes, post-notes, and de-highlights invalid parameters
        to prepare for the next measurement
        """
        
        # clears pre_test and post_test notes
        self.frames['TestInfoGuiFrame'].pre_notes.delete(1.0, tk.END)
        self.frames['PostTestGuiFrame'].post_test.delete(1.0, tk.END)
        
        
        # clear any previous invalid parameters of redness
        for ctrl in self._red_controls:
            # unbind lost focus function
            ctrl.unbind_all('<FocusOut>')
            
            # reset style
            try:
                ctrl.configure(style=ctrl.winfo_class())
            except _tkinter.TclError: pass
        self._red_controls = []
        
# --------------------- END OF CLASS MCVQOEGUI -------------------------------

#sticker frame for MCV logo on loading screen
class StickerFrame(tk.Canvas):

    def __init__(self, master, width=150, height=170, *args, **kwargs):
        super().__init__(*args,
                         width=width,
                         height=height,
                         master=master,
                         **kwargs)
        
        try:
            with importlib.resources.path('mcvqoe.hub','MCV-logo.png') as sticker:
                self.stickerimg = ImageTk.PhotoImage(file=sticker)
                self.create_image(
                    width // 2, height // 2 + 10,
                    image=self.stickerimg
                )
        except FileNotFoundError:
            #fallback text
            self.create_text(width // 2, height // 2 + 10,
                        text="MCV logo not found")


# -------------------------------appearance-----------------------------------
def set_font(**cfg):
    """Globally changes the font on all tkinter windows.

    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)


def set_styles():
    """modifies the appearance and size of tkinter.ttk widgets to make the gui
    look sweeeeet.

    """
    
    f = ttk.Style().configure
    g = ttk.Style().layout
        
    # set global font
    f('.', font=('TkDefaultFont', shared.FONT_SIZE))
    
    
    # help button and tooltip styles
    f('McvHelpBtn.TLabel', font=('TkDefaultFont',
                round(shared.FONT_SIZE * 0.75)), relief='groove')
    f('McvToolTip.TLabel', 
                background='white',
                font=('Courier', 16))
    f('McvToolTip.TFrame',
                background='white', relief='groove',)
    f('audio_drop.TMenubutton', font=('TkDefaultFont',
                                   round(shared.FONT_SIZE*0.75)))
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

def dpi_scaling():
    """ increases the size of everything on the gui proportional to the window size.
    
    this is required because we are operating without Windows' built-in scaling
    (which would make everything blurry)


    """
    global dpi_scale
    
    # a dummy frame to use its methods
    root = tk.Frame()
    
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
    
    root.destroy()

# aliases

dev_dly_char = 'DevDlyCharFrame'
m2e = 'M2eFrame'
accesstime = 'AccssDFrame'
psud = 'PSuDFrame'
intelligibility = 'IgtibyFrame'

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


# --------------------------- IMPORTS -----------------------------------------


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

class ImportLoader():
    def __init__(self):
        self.tk_main = None

    def measure_imports(self):
        import_progress = {
            'Base Libraries' : {
                                'mcvqoe_base' : 'mcvqoe.base',
                                },
            'ABC_MRT (Intelligibility Estimator)' : {'abcmrt' : 'abcmrt'},
            'Loading Hardware Interfaces' : {
                                              'simulation' : 'mcvqoe.simulation',
                                              'hardware' : 'mcvqoe.hardware',
                                            },
            'Mouth 2 Ear' : {
                              'm2e_gui' : 'mcvqoe.hub.m2e_gui',
                              'DevDlyCharFrame' : ('mcvqoe.hub.m2e_gui','DevDlyCharFrame'),
                              'M2eFrame' : ('mcvqoe.hub.m2e_gui','M2eFrame'),
                            },
            'Access Time' : {
                             'accesstime_gui' : 'mcvqoe.hub.accesstime_gui',
                             'AccssDFrame' : ('mcvqoe.hub.accesstime_gui','AccssDFrame'),
                            },
            'PSuD' : {
                        'psud_gui' : 'mcvqoe.hub.psud_gui',
                        'PSuDFrame' : ('mcvqoe.hub.psud_gui','PSuDFrame'),
                     },
            'Intelligibility' : {
                                 'intelligibility_gui' : 'mcvqoe.hub.intelligibility_gui',
                                 'IgtibyFrame' : ('mcvqoe.hub.intelligibility_gui','IgtibyFrame'),
                                },
            'Plotting' : {
                            'Figure' : ('matplotlib.figure','Figure'),
                            'FigureCanvasTkAgg' : ('matplotlib.backends.backend_tkagg','FigureCanvasTkAgg'),
                         },
        }

        try:
            self.tk_main = Main(MCVQoEGui)

            # function to update the loading-window's text
            prog = self.tk_main.win.load_progress

            for step in import_progress:
                prog(f'Loading : {step}...')

                for name in import_progress[step]:
                    source = import_progress[step][name]
                    if isinstance(source, tuple):
                        module = source[0]
                        member = source[1]
                        value = getattr(importlib.import_module(module), member)
                    else:
                        value = importlib.import_module(source)
                    setattr(self, name, value)

            prog('Finalizing...')
            import matplotlib
            #alternate rendering for pyplot to avoid conflicts with tkinter
            loader.use_alternate_plot_rendering = True
            try:
                #TODO : figure out why this doesn't seem to work now???
                #also TODO : fix this abomination of using two GUI toolkits
                import PyQt5
                matplotlib.use('Qt5Agg')
            except Exception as e:
                print(f'Error while switching to Qt5Agg backend : \'{e}\' plotting not enabled')
                #there was a problem, don't do plots
                self.use_alternate_plot_rendering = False

        except Exception as e:
            show_error(e)
            if self.tk_main is not None:
                self.tk_main.stop()
                self.tk_main.gui_thread.stop()

            raise SystemExit(1)


loader = ImportLoader()

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

#-----------------------------The Left side of the gui ------------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

class McvQoeAbout(tk.Toplevel, metaclass = SingletonWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.title('Version Information')
        
        text = {
            'GUI:'  : gui_version,
            'Mouth to ear:'  : loader.m2e_gui.m2e.version,
            'Access time:'   : loader.accesstime_gui.adly.version,
            'PSuD:'          : loader.psud_gui.psud.version,
            'Intelligibility': loader.intelligibility_gui.igtiby.version,
            
            'MCV QoE Base Library:': loader.mcvqoe_base.version,
            'ABC MRT:'             : loader.abcmrt.version,
            #'Hardware Interface:'  : loader.hardware.version,
            #'Simulation Interface:':loader.simulation.version,
            }
        
        index = 0
        for a, b in text.items():
            for i, txt in {1: a, 2:b}.items():
                ttk.Label(self, text=txt).grid(column=i, row=index, padx=10, pady=10, sticky='W')
            index += 1

class BottomButtons(tk.Frame):
    """The row of buttons on the bottom right
    """
    
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
        """captures size-changing events and changes state of LeftFrame
        accordingly

        """
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
        """Button to toggle the state 

        """
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

        self.TestTypeFrame = TestTypeFrame(master=self,
                                           main_=main_,
                                           padx=10, pady=10)
        
        self.TestTypeFrame.pack(side=tk.LEFT, fill=tk.Y)

class MenuButton(tk.Frame):
    def __init__(self, master, *args, command=None, **kwargs):
        super().__init__(master, *args, **kwargs,)

        #TODO: put an image here?

        tk.Button(master=self, text='...', command=command).pack()


class TestTypeFrame(tk.Frame):
    """Allows the user to choose hardware/simulation and which test to perform

    """

    def __init__(self, master, main_, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.main_ = main_

        # StringVars to determine what test to run and show config for
        is_sim = main_.is_simulation
        sel_txt = main_.selected_test
        self.audio_device = main_.audio_device

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
        
        # ------[ Audio Interface Dropdown ]-------
        ttk.Label(self, text = 'Audio Device').pack(fill=tk.X)
        
        # Find umc device if it exists
        umc_flag = False
        for ad in self.valid_devices:
            if 'UMC' in ad['name']:
                dev = ad
                umc_flag = True
        # Otherwise grab first valid device
        if not umc_flag:
            dev = self.valid_devices[0]
        
        self.audio_device.set(dev['name'])
        
        self.audio_select = ttk.OptionMenu(
            self,
            self.audio_device,
            dev['name'],
            '',
            style='audio_drop.TMenubutton',
            )
        # TODO: Figure out how to make menu selection text smaller
        self.audio_select['menu'].config(font=(10, ))
        self.audio_select.pack(fill=tk.X)
        self.refresh_audio_devices()
        
        ttk.Separator(self).pack(fill=tk.X, pady=20)

        # Choose Test
        ttk.Label(self, text='Choose Test:').pack(fill=tk.X)

        ttk.Radiobutton(self, text='M2E Latency',
                        variable=sel_txt, value=m2e).pack(fill=tk.X)

        ttk.Radiobutton(self, text='Access Delay',
                        variable=sel_txt, value=accesstime).pack(fill=tk.X)

        ttk.Radiobutton(self, text='PSuD',
                        variable=sel_txt, value=psud).pack(fill=tk.X)

        ttk.Radiobutton(self, text='Intelligibility',
                        variable=sel_txt, value=intelligibility).pack(fill=tk.X)
        
        
        # version information
        
        ttk.Button(self, text='About', command=McvQoeAbout).pack(
            side=tk.BOTTOM, fill=tk.X)
    
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

    @property
    def audio_device_options(self):
        menu = self.audio_select['menu']
        ix = 0
        items = []
        while(ix == menu.index(ix)):
            items.append(menu.entrycget(ix, "label"))
            ix += 1
        return items

    def refresh_audio_devices(self):
        """Delete, requery, and refresh audio device options."""
        print('hit refresh')
        menu = self.audio_select['menu']
        for dev in self.audio_device_options:
            menu.delete(dev)
        sd._terminate()
        sd._initialize()
        self.update_audio_devices()

    def update_audio_devices(self):
        """Update audio device list with valid devices"""
        valid_devices = self.valid_devices
        menu = self.audio_select['menu']
        for dev in valid_devices:
            menu.add_command(
                label=dev['name'],
                command=lambda val=dev['name']: self.select_audio_device(val))

    def select_audio_device(self, val):
        self.audio_device.set(val)

    @property
    def valid_devices(self):
        """ List of audio devices with at least 1 input and 1 output"""
        audio_devices = sd.query_devices()
        valid_devices = []
        for device in audio_devices:
            if(device["max_output_channels"] >= 1
               and device["max_input_channels"] >= 1):
                valid_devices.append(device)
        if valid_devices == []:
            valid_devices.append({'name': '<no valid audio devices>'})
        return valid_devices
        

class LogoFrame(tk.Canvas):

    def __init__(self, master, width=150, height=170, *args, **kwargs):
        super().__init__(*args,
                         width=width,
                         height=height,
                         master=master,
                         bg='white',
                         **kwargs)

        with importlib.resources.path('mcvqoe.hub','pscr_logo.png') as crest:
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

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

#-------------------------The right side of the gui----------------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

class EmptyFrame(tk.Frame):
    """An empty frame: shown when no test is selected yet

    """

    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btnvars = btnvars
        
    def run(self, *args, **kwargs):
        raise ValueError('Please select a test.')


class TestInfoGuiFrame(ttk.Labelframe):
    """Replacement for the TestInfoGui. Collects pre-test notes
    
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
    """Replacement for PostTestGui. Collects post-test notes.
    
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
    """Reports on the measurement's progress by handling progress_update events.
    
    see the gui_progress_update() function
    """

    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        self.pack_configure(expand=True, fill=tk.BOTH)

    def __init__(self, master, btnvars, *args, **kwargs):
        # a stopwatch to help estimate time remaining
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
        """Checks to see if the user pressed abort, and if so, aborts.
        

        Raises
        ------
        Abort_by_User
            a BaseException that aborts the measurement.


        """
        if loader.tk_main.win.step == 'aborting':
            # indicate that the test should not continue
            raise Abort_by_User()
        
        
    @in_thread('GuiThread', wait=True, except_=Abort_by_User)
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
        
        """ see gui_progress_update() in the main namespace
        """
        
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
            
            # set text based on above messages
            self.primary_text.set(messages[prog_type][0])
            self.secondary_text.set(messages[prog_type][1])

        if not num_trials:
            #make an indeterminate progress bar
            self.bar.configure(mode='indeterminate', maximum = 100)
            self.bar.start()
            self.time_estimate_.set('')

        elif prog_type in ('pre', 'proc', 'test'):
            # show current progress on a determinate progress bar
            self.bar.stop()
            self.bar.configure(value=current_trial, maximum = num_trials,
                               mode='determinate')

            # estimate time remaining
            
            if current_trial == 0:
                # if on trial 0, start timer
                self.stopwatch.reset()
                self.time_estimate_.set('')
            else:
                
                # get time estimate
                time_left, time_unit = self.stopwatch.estimate_remaining(
                    current_trial, num_trials)
                
                # format text
                time_est = f'{time_left} {time_unit} remaining...'
                
                if self.pause_after not in (None, np.inf) and prog_type == 'test':
                    
                    # time remaining until next pause
                    ct_in_set = (current_trial % self.pause_after) + 1
                    
                    next_stop = current_trial + self.pause_after - ct_in_set
                    
                    time_left_set, time_unit_set = self.stopwatch.estimate_remaining(
                        current_trial, next_stop)
                    
                    # format text
                    time_est = f'{time_est}\n{time_left_set} {time_unit_set} until next pause.'

                # set text for time estimate
                self.time_estimate_.set(time_est)

        if prog_type == 'pre':
            # remove all info from the frame to prepare for next measurement
            self.clip_name_.set('')
            self.file_.set('')
            self.delay_.set('')
            self._is_paused = False
            
            # remove all warnings
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
            else:
                w.destroy()

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

        # if the user pressed pause button, pause
        if self._is_paused:
            self._is_paused = False
            self.stopwatch.pause()
            tk.messagebox.showinfo('Test Paused',
                                   'Press OK to continue.')
            self.stopwatch.start()

        return True

    @in_thread('GuiThread', except_=Abort_by_User)
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

        # pause the stopwatch to preserve time estimate accuracy
        self.stopwatch.pause()
        
        if reason == 'normal-stop':
            tk.messagebox.showinfo('Test Paused',
                                   message+'\n\n'+
                                   'Press OK to continue.')
            
        elif reason == 'problem-stop':
            tk.messagebox.showerror('Test Paused',
                                    message+'\n\n'+
                                    'Press OK to continue.')

        # resume stopwatch
        self.stopwatch.start()
        
        return False
    
    
    def _trim_text(self, text):
        """remove characters from text to fit the width of the window"""
        
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
        """Pause button
        """
        self._is_paused = True
        
    
class _StopWatch:
    """A working stopwatch.
    """
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
        """estimates the time remaining on a test based on its current progress
        

        Parameters
        ----------
        current_trial : int
            the current trial.
        num_trials : int
            total trials.

        Returns
        -------
        time_left : int
            the time until completion
            
        time_unit : str
            the unit in which to measure time_left.

        """
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
        """updates the stopwatch based on current time

        """
        now = time.time()
        
        # don't count the time since last update if the timer has been paused
        if not self.paused:
            new_elapsed = now - self.start_time
            
            self.elapsed_time = self.elapsed_time + new_elapsed
 
        self.start_time = now
        
class WarningBox(tk.Frame):
    """
    A colored warning box that shows a message and an X button
    """
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
    """
    A frame to show results, plot data, open the output folder, etc.
    
    Elements can be added to the frame using the add_element method (see below)
    """
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
        """
        Adds an element to the post-processing frame
        
        Parameters
        ----------
        element :
            A string, matplotlib figure, or tk widget class to be added into
            the window

        """
        
        if isinstance(element, loader.Figure):
            canvas = loader.FigureCanvasTkAgg(element, master=self)
            widget = canvas.get_tk_widget()
            canvas.draw()
            self.canvasses.append(widget)
            
        elif isinstance(element, str):
            widget = ttk.Label(self, text=element)
            
        else:
            widget = element(self)

        widget.pack(fill=tk.X, padx=10, pady=10)
        
        self.elements.append(widget)
    
    @in_thread('GuiThread', wait=True)
    def reset(self):
        """
        Removes all elements from the post-processing-frame

        """
        
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
            except (FileNotFoundError, OSError):
                pass
        
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
#------------------------------ Test Audio ------------------------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

@in_thread('MainThread', wait=False)
def test_audio(root_cfg, on_finish=None):
    """
    Button to test the audio setup

    Parameters
    ----------
    root_cfg : dict
        see MCVQoEGui.get_cnf()
        
    on_finish : func, optional
        function to run on completion

    Raises
    ------
    ValueError
        Audio file could not be found.

    """
    try:
        
        # get selected test
        sel_tst = root_cfg['selected_test']
        
        # get selected test's parameters
        cfg = root_cfg[sel_tst]
        
        # set proper channel rate
        if 'channel_rate' in root_cfg['SimSettings'] and root_cfg[
            'SimSettings']['channel_rate'] == 'None':
            root_cfg['SimSettings']['channel_rate'] = None

        radio_interface, ap = get_interfaces(root_cfg)

        # get selected audio file
        if 'audio_files' in cfg:
            
            fp = ''

            # get individual audio file
            if cfg['audio_files'][0] and not (
                    '<' in cfg['audio_files'][0] and
                    '>' in cfg['audio_files'][0]
                    ):
                f = np.random.choice(cfg['audio_files'])

                fp = path.join(cfg['audio_path'], f)

            # in case of full_audio_dir
            elif cfg['audio_path']:

                files = [f for f in listdir(cfg['audio_path'])
                         if path.splitext(f)[1] == '.wav']
                # Choose a random file
                f = np.random.choice(files)
                fp = path.join(cfg['audio_path'], f)

            else:
                # uses default file for single_play()
                fp = None
                    
            if (not fp or not path.isfile(fp)) and fp is not None:
                raise ValueError('Audio File not found')
        elif sel_tst == intelligibility:
            # If running intelligibility grab a random clip
            apath = resource_filename('mcvqoe.intelligibility',
                                      'audio_clips')
            files = listdir(apath)
            f = np.random.choice(files)
            fp = path.join(apath, f)
        else:
            # use default file for single_play()
            fp = None
        with radio_interface as ri:
            
            # check if there is a ptt_wait to use, otherwise use default
            ptt_wait_arg = {}
            if 'ptt_wait' in cfg and not root_cfg['is_simulation']:
                ptt_wait_arg['ptt_wait'] = cfg['ptt_wait']

            #play the audio through the system
            loader.hardware.PTT_play.single_play(ri, ap, fp,
                    playback=root_cfg['is_simulation'], **ptt_wait_arg)

    except Exception as error:
        show_error(error)
    
    if on_finish is not None:
        # call the is_finished callback
        on_finish()

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
#-------------------------- Running the measurements --------------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@in_thread('MainThread', wait=False)
def run(root_cfg):
    """
    Runs the measurement:
    
    Constructs the measure class and sets its instance variables
    based on the given configuration, collects pre-notes, runs the .run() function,
    displays the results, and handles any errors.

    Parameters
    ----------
    root_cfg : dict
        the parameters to use. see MCVQoEGui.get_cnf().

    """
    
    # attempt to free memory and delete old RadioInterface to free up port
    # this may be not needed anymore???
    gc.collect(2)
    
    ppf = loader.tk_main.win.frames['PostProcessingFrame']
    tpf = loader.tk_main.win.frames['TestProgressFrame']
    
    # subclasses of the measure() classes for each measurement
    constructors = {
        dev_dly_char : loader.m2e_gui.DevChar_fromGui,
        
        m2e: loader.m2e_gui.M2E_fromGui,
        accesstime: loader.accesstime_gui.Access_fromGui,
        psud : loader.psud_gui.PSuD_fromGui,
        intelligibility: loader.intelligibility_gui.Igtiby_from_Gui,
            }

    # extract test configuration:
        
    # the selected measurement
    sel_tst = root_cfg['selected_test']
    # the selected measurement's parameters
    cfg = root_cfg[sel_tst]
    # is it a simulation?
    is_sim = root_cfg['is_simulation']

    #initialize test object
    my_obj = constructors[sel_tst]()

    #-------------- Begin try statement for error handling --------------------
    try:
        
        #---------------------- open interfaces -------------------------------
        try:
            ri, ap = get_interfaces(root_cfg)
        except (RuntimeError, ValueError) as e:
            show_error(e)
            
            # return to prevent showing post-processing frame
            return
        
        # prevent logging excess of information
        my_obj.no_log = my_obj.no_log + (
            'progress_update',
            'get_post_notes',
        )

        #--------------------------- Recovery ---------------------------------
        if sel_tst == accesstime:
            #if the program closes between now and end of function, 
            # prompt for recovery on next session.
            loadandsave.misc_cache['accesstime.need_recovery'] = True
            loadandsave.misc_cache.dump()

        if 'data_file' in cfg and cfg['data_file'] != "":
            my_obj.data_file = cfg['data_file']
            with open(my_obj.data_file, "rb") as pkl:
                my_obj.rec_file = pickle.load(pkl)
            
            
            skippy = ['rec_file']
            # load config from recovery file into object
            for k, v in my_obj.rec_file.items():
                if hasattr(my_obj, k) and (k not in skippy):
                    setattr(my_obj, k, v)
            
            # load pause-trials from recovery file for use in time-estimation
            cfg['pause_trials'] = my_obj.rec_file['self.pause_trials']
            
            # pass keyword argument to my_obj.run()
            recovery_kw = {'recovery': True}
        
        else:
            # don't pass recovery kw argument to my_obj.run()
            recovery_kw = {}
            
            # prepare config and check for invalid parameters
            param_modify(root_cfg)
                        
            # put config into object
            _set_values_from_cfg(my_obj, cfg)
             
            # Check for value errors with instance variables
            # this is last resort and should not be needed after param_modify()
            my_obj.param_check()
 
        #-------------------- Setting Callbacks -------------------------------
        
        # set post_notes callback
        my_obj.get_post_notes=get_post_notes
        
        
        # set progress update callback
        my_obj.progress_update = gui_progress_update

        if 'pause_trials' in cfg:
            #set user check callback
            my_obj.user_check = tpf.user_check
            tpf.pause_after = cfg['pause_trials']
        else:
            tpf.pause_after = None
        
        # set the rec_stop for 2-location rx
        tpf.rec_stop = ap.rec_stop

        # ----------- Gather pretest notes and parameters ---------------------
        my_obj.info = get_pre_notes(root_cfg)
        if my_obj.info is None: 
            #user pressed 'back' in test info gui
            return
        
        
        # fill probabilityizer into info
        if is_sim and root_cfg['SimSettings']['_enable_PBI']:
            
            pcfg = root_cfg['SimSettings']
                        
            my_obj.info['PBI P_a1']=str(pcfg['P_a1'])
            my_obj.info['PBI P_a2']=str(pcfg['P_a2'])
            my_obj.info['PBI P_r'] =str(pcfg['P_r'])
            my_obj.info['PBI interval']=str(pcfg['interval'])

        #------------- Set up progress and post-process frames ----------------
        
        #show progress bar in gui
        loader.tk_main.win.set_step('in-progress', extra=ap.rec_stop)
        
        # clear pretest notes from window
        loader.tk_main.win.clear_old_entries()
        
        # remove any old post-processing info from frame
        ppf.reset()
        
        #----------------------- RUN THE TEST ---------------------------------
        
        my_obj.audio_interface = ap
       
        # Enter RadioInterface object
        with ri as my_obj.ri:
            
            # run the test
            result = my_obj.run(**recovery_kw)
            
            # prevent freezing if user is trying desperately to close window
            if loader.tk_main.win._is_force_closing:
                return

        #------------------- Show post-processing data ------------------------
        """
        use ppf.add_element() to add something to the post-processing-frame.
        
        see PostProcessingFrame.add_element.__doc__ for details
        
        """

        # intelligibility estimate
        if sel_tst == intelligibility:
            ppf.add_element(f'Intelligibility Estimate: {result}')

        # M2e: mean, std, and plots
        elif sel_tst in (m2e, dev_dly_char) and cfg['test'] == 'm2e_1loc':
            #show mean and std_dev
            mean, std = my_obj.get_mean_and_std()
            
            ppf.add_element("Mean: %.5fs" % mean)
            ppf.add_element("StD: %.2fus" % std)
            
            # plots will leak memory if this is false.
            if loader.use_alternate_plot_rendering:
                
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

        # M2e: 2-loc-tx prompt to stop rx
        elif sel_tst == m2e and my_obj.test == 'm2e_2loc_tx':
            ppf.add_element('Data collection complete, you may now stop data\n' +
                            'collection on the receiving end')

        # device delay characterization: show new device delay
        if sel_tst == dev_dly_char:
            
            dev_dly = calculate_dev_dly(my_obj, is_simulation = is_sim)
            
            ppf.add_element(f'Device Delay: {dev_dly}')
            
            if is_sim:
                show_error(Warning('Device Delay will not be saved, '+
                                   'because this is a simulation.'))

    # ------------------------- Error handling --------------------------------
    
    except InvalidParameter as e:
        # highlight offending parameter in red
        loader.tk_main.win.show_invalid_parameter(e)
        return

    #if the measurement was in some way aborted
    except (Abort_by_User, KeyboardInterrupt, SystemExit):
        if sel_tst == accesstime:
            ppf.add_element('You may view recover your test using the \n'+
                            '"recovery file" entry in the configuration.')
        
    except Exception as e:
        if loader.tk_main.last_error is not e:
            show_error(e)
        
        if sel_tst == accesstime:
            ppf.add_element('You may recover your test using the \n'+
                            '"recovery file" entry in the configuration.')


    # ---------------------- Last things to do --------------------------------
    
    if sel_tst == accesstime:
        #don't prompt for recovery on next session.
        loadandsave.misc_cache['accesstime.need_recovery'] = False
        
        
    #delete radio interface (not sure if this is still needed or not)
    my_obj.ri = None
    ri = None

    # put outdir folder into frame
    try: ppf.outdir = my_obj.outdir
    except AttributeError: ppf.outdir = ''
    
    
    #show post-processing frame
    loader.tk_main.win.set_step('post-process')
    
# ------------------------- END OF RUN FUNCTION -------------------------------


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@



#@@@@@@@@@@@@@@@@@@@@@@@@@@ Call-back functions @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
# ------------------------- Gui Progress Update -------------------------------
        
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
    
    tpf = loader.tk_main.win.frames['TestProgressFrame']
    
    return tpf.gui_progress_update(prog_type,
                                  num_trials,
                                  current_trial,
                                  msg,
                                  clip_name,
                                  delay,
                                  file,
                                  new_file,
                                  )


# ------------------- Pretest Notes and Posttest Notes ------------------------

def get_pre_notes(root_cfg):
    loader.tk_main.win.pretest(root_cfg)
    
    #wait for user submit or program close
    while loader.tk_main.win._pre_notes_wait and not loader.tk_main.win._is_closing and not loader.tk_main.win.is_destroyed:
        time.sleep(0.1)
     
    return loader.tk_main.win._pre_notes
        
def get_post_notes(error_only=False):
    
    #get current error status, will be None if we are not handling an error
    error_type, error =sys.exc_info()[:2]
    
    # ignore BaseExceptions, etc.
    is_showable_error = isinstance(error, Exception)
    
    if error_only and not is_showable_error:
        #nothing to do, bye!
        return {}
    
    # show post_test_gui frame
    loader.tk_main.win.post_test_info = None
    loader.tk_main.win.set_step('post-notes', extra=error)
    
    
    if is_showable_error:
        loader.tk_main.last_error = error
        show_error()
    
    # wait for completion or program close
    
    while loader.tk_main.win.post_test_info is None and not loader.tk_main.win._is_force_closing:
        time.sleep(0.1)
    
    # retrieve notes
    nts = loader.tk_main.win.post_test_info
    if nts is None:
        nts = {}
    return nts


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
#--------------------------- Parameter Modification ---------------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

def param_modify(root_cfg):
    """parses user-entered data into acceptable formats for the measure obj vars
    and checks for errors
    
    Parameters are only changed and checked as needed. All entries in root_cfg
    begin as instances of (bool, int, float, str, list). Any instance variable
    that requires any other type must be modified in this function.
    

    Parameters
    ----------
    root_cfg : dict
        see MCVQoEGui.get_cnf()

    Raises
    ------
    Abort_by_User
        if the user presses 'cancel' when asked to calibrate dev_dly.
    InvalidParameter
        if a parameter cannot be parsed, or if it is missing

    
    """
    
    
    sel_tst = root_cfg['selected_test']
    is_sim = root_cfg['is_simulation']
    cfg = root_cfg[sel_tst]
    
    if sel_tst == psud:
        # Overwrite generic names with the psud specific controls
        cfg['audio_files'] = cfg['psud_audio_files']
        cfg['audio_path'] = cfg['psud_audio_path']
        cfg['trials'] = cfg['psud_trials']
    # ensure the user is only doing default settings for dev dly characterization
        # except for outdir
    if sel_tst == intelligibility:
        cfg['trials'] = cfg['intell_trials']
    if sel_tst == dev_dly_char:
        
        default_cfg = DEFAULTS[sel_tst].copy()
        del default_cfg['outdir']
        
        cfg.update(default_cfg)


    # device delay should be either entered manually or characterized.
    if 'dev_dly' in cfg:
        
        bad = False
        
        try: cfg['dev_dly'] = float(cfg['dev_dly'])
        except ValueError: bad = True
        
        if bad: raise InvalidParameter('dev_dly',
            message='Make sure to calibrate your device delay (recommended)\n\n'+
            'Or, enter your known device delay here.')
        
    # audio files should exist and should be .wav files
    if 'audio_files' in cfg and 'audio_path' in cfg:
        
        if not cfg['audio_files'][0] and not cfg['audio_path']:
            raise InvalidParameter('audio_files',
                           message = 'Audio Files are required.')
        
        # check for full audio dir
        cfg['full_audio_dir'] = not cfg['audio_files'][0] or (
            
            #looking for '<entire audio folder>' or emptiness
            len(cfg['audio_files']) == 1 and
            '<' in cfg['audio_files'][0] and
            '>' in cfg['audio_files'][0]
            )
        
        p = cfg['audio_path']
        
        if cfg['full_audio_dir']:
            # we are finding our own audio files now
            cfg['audio_files'] = []
            
            
            # folder must exist
            if not p:
                raise InvalidParameter('audio_path',
                                message='Audio Folder is required.')
            if not path.isdir(p):
                raise InvalidParameter('audio_path',
                                   message = 'Folder does not exist.')
                
                
            # find wav files in the folder
            success = False
            for f in listdir(p):
                fp = path.join(p, f)
                
                if path.isfile(fp) and path.splitext(fp)[1].lower() == '.wav':
                    
                    success = True
                    cfg['audio_files'].append(f)
                    
                
            if not success:
                # folder must have at least one wav file
                raise InvalidParameter('audio_path',
                    message='Folder must contain .wav files') 
            
        else: #if not full_audio_dir

            # check: audio files should all exist
            for f in cfg['audio_files']:
                af = path.join(p, f)
                
                if not path.isfile(af):
                    raise InvalidParameter('audio_files',
                        message=f'"{af}" does not exist')
                    
                if not path.splitext(af)[1].lower() == '.wav':
                    raise InvalidParameter('audio_files',
                        message='All audio files must be .wav files')

    
    # relative outdirs will go into the default outdir
    cfg['outdir'] = path.join(DEFAULTS[sel_tst]['outdir'], cfg['outdir'])
    try: os.makedirs(cfg['outdir'], exist_ok=True)
    except OSError as e: 
        error = str(e)
        raise InvalidParameter('outdir', message = error) from None
        
    # turn multi-choice SaveAudio into 2 booleans
    if 'SaveAudio' in cfg:
        cfg['save_audio']    = (cfg['SaveAudio'] != 'no_audio')
        cfg['save_tx_audio'] = (cfg['SaveAudio'] == 'all_audio') 

    # make pause_trials an integer or np.inf
    if 'pause_trials' in cfg:
        
        if is_sim:
            cfg['pause_trials'] = np.inf
        else:
            
            try:
                cfg['pause_trials'] = int(cfg['pause_trials'])
            except ValueError:
                if 'inf' in cfg['pause_trials'].lower():
                    cfg['pause_trials'] = np.inf
                else:
                    raise InvalidParameter('pause_trials',
                        message='Number of trials must be a whole number') from None

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
    
    # check auto_stop with ptt_rep
    if ('auto_stop' in cfg) and ('ptt_rep' in cfg) and cfg['auto_stop'] and (
            cfg['ptt_rep'] < 16):
        raise InvalidParameter('ptt_rep',
                    message='Must be greater than 15 if auto-stop is enabled')
    
    
    
    
    if is_sim:
        
        # ptt_gap and ptt_wait should be set to 0 in simulations
        
        for key in ('ptt_wait', 'ptt_gap'):
            if key in cfg:
                cfg[key] = 0
        
        
        
        
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
#------------------------- Construct Interfaces -------------------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def get_interfaces(root_cfg):
    """Construct and configure the hardware interfaces or QoEsim object
    

    Parameters
    ----------
    root_cfg : dict
        see MCVQoEGui.get_cnf.__doc__

    Raises
    ------
    ValueError
        if there is a problem with the configuration.

    Returns
    -------
    ri : RadioInterface, QoEsim
        
    ap : AudioPlayer, QoEsim
        

    """
    
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
    
    if sel_tst in (accesstime,):
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
        
        sim = loader.simulation.QoEsim(**channels)
        
        _set_values_from_cfg(sim, sim_cfg)
        
        plname = sim_cfg['_impairment_plugin']
        if plname:
            
            try:
                plugin = __import__(plname)
            except ImportError:
                raise InvalidParameter('_impairment_plugin',
                        f'could not import "{plname}"')
            else:
                success = False
                for attr in ('pre_impairment', 'post_impairment', 'channel_impairment'):
                    if hasattr(plugin, attr):
                        setattr(sim, attr, getattr(plugin, attr))
                        success = True
                if not success:
                    raise InvalidParameter('_impairment_plugin',
                            'Module must contain at least one appropriate function')
                
        if sim_cfg['_enable_PBI']:
            
            prob=loader.simulation.PBI()
            
            prob.P_a1=sim_cfg['P_a1']
            prob.P_a2=sim_cfg['P_a2']
            prob.P_r=sim_cfg['P_r']
            prob.interval=sim_cfg['interval']
            if sim_cfg['pre_vs_post'] == 'pre':
                sim.pre_impairment = prob.process_audio
            else:
                sim.post_impairment = prob.process_audio


        
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
            ri = loader.hardware.RadioInterface(radioport)
        
        audio_device = root_cfg['audio_device']
        ap = loader.hardware.AudioPlayer(device_str=audio_device,
                                         **channels)
            
            
        _set_values_from_cfg(ap, hdw_cfg)
        
        
        ap.blocksize = hdw_cfg['blocksize']
        ap.buffersize = hdw_cfg['buffersize']
        ap.sample_rate = 48000
        
        
    ap.rec_stop = rec_stop
    
    return ri, ap

    
class _FakeRadioInterface:
    def __enter__(self, *args, **kwargs): return self
    def __exit__(self, *args, **kwargs): return False

def _set_values_from_cfg(my_obj, cfg):
    """sets the attributes of an object using the keys of a dict
    

    Parameters
    ----------
    my_obj : any
    cfg : dict


    """
    for k, v in cfg.items():
        if hasattr(my_obj, k):
            setattr(my_obj, k, v)

def _get_dev_dly(ignore_error = True):
    """
    

    Parameters
    ----------
    ignore_error : bool, optional
        whether to ignore file-not-found errors. The default is True.

    Returns
    -------
    dev_dly : float

    """
    # attempts to get saved dev_dly from disk.
    
    try:
        # load from disk
        dev_dly = loadandsave.Config('dev_dly.json').load()['dev_dly']
    except FileNotFoundError:
        if not ignore_error:
            raise
        dev_dly = 0
    else:
        # put value into dev_dly entry
        loader.tk_main.win.frames[accesstime].btnvars['dev_dly'].set(dev_dly)
    
        return dev_dly
    
    
def calculate_dev_dly(test_obj, is_simulation = False):
    """
    Calculates the device delay using the data found in test_obj

    Parameters
    ----------
    test_obj : measure
        
    is_simulation : bool, optional
        whether the measurement was a simulation (the result should be ignored)

    Returns
    -------
    dev_dly : float
        

    """
    # TODO: improve the calculation. currently just gets the mean.
    
    dev_dly = test_obj.get_mean_and_std()[0]
        
    
    if not is_simulation: # simulations don't show real dev_dly!!!
        # save the device delay to file
        loadandsave.Config('dev_dly.json', dev_dly = dev_dly).dump()
        
        # put value into field
        loader.tk_main.win.frames[accesstime].btnvars['dev_dly'].set(dev_dly)
    
    
    return dev_dly

class GuiRecStop:
    """uses an event generated in the GuiThread to stop the recording in the main-thread
    
    """
    
    def __init__(self):
        self._stopped = False
    
    def stop(self):
        self._stopped = True
    
        
    def __enter__(self, *args, **kwargs):
        self._stopped = False
        return self
    
    def __exit__(self, *args, **kwargs):
        return False
    
    def is_done(self):
        
        return self._stopped


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

#---------------------- Get default values for parameters ---------------------

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


#empty dictionary for defaults, filled with load_defaults
DEFAULTS = {}

def load_defaults():
    
    #check if defaults have already been loaded
    if DEFAULTS:
        print('Defaults have alread been loaded!')
        return

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
        
        
        dev_dly_char: [
            'audio_files',
            'audio_path',
            'bgnoise_file',
            'bgnoise_volume',
            'outdir',
            'ptt_wait',
            'ptt_gap',
            'test',
            'trials',
            'save_tx_audio',
            'save_audio',
        ],
        
        m2e: [
            'audio_files',
            'audio_path',
            'bgnoise_file',
            'bgnoise_volume',
            'outdir',
            'ptt_wait',
            'ptt_gap',
            'test',
            'trials',
            'save_tx_audio',
            'save_audio',
            'save_tx_audio',
            'save_audio',
        ],

        accesstime: [
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
            'save_tx_audio',
            'save_audio',
        ],
        
        psud: [
            '_default_audio_sets',
            'audio_set',
            'audio_files',
            'audio_path',
            'audio_path',
            'trials',
            'psud_trials',
            'outdir',
            'ptt_wait',
            'ptt_gap',
            'm2e_min_corr',
            'intell_est',
            'save_tx_audio',
            'save_audio',
        ],
        
        intelligibility: [
            'trials',
            'outdir',
            'ptt_wait',
            'ptt_gap',
            'pause_trials',
            'intell_est',
            'save_tx_audio',
            'save_audio',
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
            'pre_vs_post',
            'P_a1',
            'P_a2',
            'P_r',
            'interval',
            
            '_impairment_plugin',
            
        ],
        
        'HdwSettings' : [
            
            'overplay',
            'radioport',
            'dev_dly',
            'blocksize',
            'buffersize',
            ],
    }

    # the objects to pull the default values from
    initial_measure_objects = {
        dev_dly_char: loader.m2e_gui.DevChar_Defaults(),
        m2e: loader.m2e_gui.m2e.measure(),
        accesstime: loader.accesstime_gui.adly.measure(),
        psud : loader.psud_gui.psud.measure(),
        intelligibility: loader.intelligibility_gui.igtiby.measure(),
        'SimSettings': shared._SimPrototype(),
        'HdwSettings': shared._HdwPrototype()
        }

    # ----------------------load default values from objects-----------------------
    for name_, key_group in control_list.items():
        
        DEFAULTS[name_] = {}

        if name_ in initial_measure_objects:
            obj = initial_measure_objects[name_]

            for key in key_group:
                if hasattr(obj, key):
                    DEFAULTS[name_][key] = getattr(obj, key)

    # loads previous session's hardware settings from disk, if applicable
    DEFAULTS['HdwSettings'].update(loadandsave.hardware_settings)

    # ----------- Special default values different from measurement obj -----------

    # set the default outdir directories
    dir_names = {
        dev_dly_char: 'Device_Delay_Characterization',
        m2e: 'Mouth_2_Ear',
        accesstime: 'Access_Time',
        psud: 'PSuD',
        intelligibility: 'Intelligibility'
        }
    for name_, cfg in DEFAULTS.items():
        if 'outdir' in cfg:
            cfg['outdir'] = path.join(path.expanduser("~"),
                                      'MCV-QoE',
                                      dir_names[name_])

        # formats audio_files and audio_path to make them more readable
        if 'audio_files' in cfg and 'audio_path' in cfg:

            if cfg['audio_files'] or cfg['audio_path']:

                cfg['audio_path'], cfg['audio_files'] = shared.format_audio_files(
                    cfg['audio_path'], cfg['audio_files'])

        # create a multi-choice option based on bool-options for save-audio
        if 'save_tx_audio' in cfg and 'save_audio' in cfg:

            if not cfg['save_audio']:
                cfg['SaveAudio'] = 'no_audio'
            elif cfg['save_tx_audio']:
                cfg['SaveAudio'] = 'all_audio'
            else:
                cfg['SaveAudio'] = 'rx_only'

    #values that require more than one control
    DEFAULTS[accesstime]['_ptt_delay_min'] = initial_measure_objects[
        accesstime].ptt_delay[0]
    try:
        DEFAULTS[accesstime]['_ptt_delay_max'] = str(initial_measure_objects[
            accesstime].ptt_delay[1])
    except IndexError:
        DEFAULTS[accesstime]['_ptt_delay_max'] = '<default>'

    for k in (accesstime,psud):
        DEFAULTS[k]['_time_expand_i'] = initial_measure_objects[k].time_expand[0]
        try:
            DEFAULTS[k]['_time_expand_f'] = str(initial_measure_objects[
                k].time_expand[1])
        except IndexError:
            DEFAULTS[k]['_time_expand_f'] = '<default>'

    #the following should be a string, not any other type
    DEFAULTS[accesstime]['pause_trials'] = str(int(DEFAULTS[accesstime]['pause_trials']))
    DEFAULTS[intelligibility]['pause_trials'] = str(int(DEFAULTS[intelligibility]['pause_trials']))

    DEFAULTS[accesstime]['dev_dly'] = ''

    DEFAULTS['SimSettings']['channel_rate'] = str(DEFAULTS['SimSettings']['channel_rate'])
    DEFAULTS['SimSettings']['m2e_latency'] = 'minimum'

    # the following should be a float
    DEFAULTS['SimSettings']['access_delay'] = float(DEFAULTS['SimSettings']['access_delay'])

    for k in ('P_a1', 'P_a2', 'P_r', 'interval'):
        DEFAULTS['SimSettings'][k] = float(DEFAULTS['SimSettings'][k])

    # the following do not have a default value
    DEFAULTS['SimSettings']['_enable_PBI'] = False
    DEFAULTS['SimSettings']['pre_vs_post'] = 'post'
    
    # Set PSuD wrapper class defaults
    DEFAULTS[psud]['audio_set'] = DEFAULTS[psud]['_default_audio_sets'][0]
    DEFAULTS[psud]['psud_trials'] = DEFAULTS[psud]['trials']
    DEFAULTS[psud]['psud_audio_files'] = DEFAULTS[psud]['audio_files']
    DEFAULTS[psud]['psud_audio_path'] = DEFAULTS[psud]['audio_path']
    
    # Set Intelligibility wrapper class defaults
    DEFAULTS[intelligibility]['intell_trials'] = DEFAULTS[intelligibility]['trials']

def main():

    #import measurement things
    loader.measure_imports()

    #load default values from measurements
    load_defaults()

    try:
        loader.tk_main.win.init_as_mainwindow()
    except e:
        show_error()
        raise SystemExit(1)
    
    loader.tk_main.main_loop()

if __name__ == '__main__':
    main()
