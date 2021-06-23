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
import json
import datetime
import pickle

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

# the initial values in all of the controls
DEFAULT_CONFIG = {
    'EmptyFrame': {},
    
    'TestInfoGuiFrame': {
            'Test Type': '',
            'Tx Device': '',
            'Rx Device': '',
            'System': '',
            'Test Loc': ''
            },
    
    'PostTestGuiFrame': {},
    
    

    'M2eFrame': {
        'audio_files': "",
        'bgnoise_file': "",
        'bgnoise_volume': 0.1,
        'blocksize': 512,
        'buffersize': 20,
        'outdir': "",
        'overplay': 1.0,
        'ptt_wait': 0.68,
        'radioport': "",
        'test': "m2e_1loc",
        'trials': 100
    },

    'AccssDFrame': {
        'audio_files': "",
        'audio_path': "",
        'auto_stop': False,
        'bgnoise_file': "",
        'bgnoise_volume': 0.1,
        'blocksize': 512,
        'buffersize': 20,
        'data_file': "",
        'dev_dly': float(31e-3),
        'outdir': "",
        '_ptt_delay_min': 0.00,
        '_ptt_delay_max': 'auto',
        'ptt_gap': 3.1,
        'ptt_rep': 30,
        'ptt_step': 0.02,
        'radioport': "",
        's_thresh': -50,
        's_tries': 3,
        'stop_rep': 10,
        '_time_expand_i': float(100e-3 - 0.11e-3),
        '_time_expand_f': float(0.11e-3),
        '_limited_trials': True,
        'trials': '100', #this is a string because it may be 'inf'

    },
    
    'PSuDFrame' : {
        'audioFiles':'',
        'audioPath' : '',
        'overPlay':1.0,
        'trials' : 100,
        'blockSize':512,
        'bufSize':20,
        'outdir':'',
        'ptt_wait':0.68,
        'ptt_gap':3.1,
        '_time_expand_i' : float(100e-3 - 0.11e-3),
        '_time_expand_f' : float(0.11e-3),
        'm2e_min_corr' : 0.76,
        'intell_est':'trial',
        'radioport': ''
        
        #TODO: ask about the following:
        #'split_audio_dest':None,
        
    },
        
    'SimSettings': {
       #'sample_rate' : fs,
        'channel_tech':'clean',
        'channel_rate':'None', # none, str, or int. '<default>' should turn to None
        'm2e_latency':21.1e-3,
        'access_delay':0,
        'rec_snr':60,
        'PTT_sig_freq':409.6,
        'PTT_sig_aplitude':0.7,
    },
    
    'HdwSettings' : {}
}



    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    


class MCVQoEGui(tk.Tk):
    """The main window


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        frame_types = [
            EmptyFrame,
            TestInfoGuiFrame,
            PostTestGuiFrame,
            
            M2eFrame,
            AccssDFrame,
            PSuDFrame,
    #TODO: add rest of frames
        ]
        
        # when the user exits the program
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # dpi scaling
        dpi_scaling(self)

        # the config starts unmodified
        self.set_saved_state(True)

        # dimensions
        self.minsize(width=600, height=370)
        self.geometry(f'{WIN_SIZE[0]}x{WIN_SIZE[1]}')

        # tk Variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')

        # change test frame when user selects a test
        self.selected_test.trace_add(
            'write', lambda a, b, c: self.frame_update())

        self.LeftFrame = LeftFrame(self, main_=self)
        self.LeftFrame.pack(side=tk.LEFT, fill=tk.Y)

        BottomButtons(master=self).pack(side=tk.BOTTOM, fill=tk.X,
                                        padx=10, pady=10)

        # keyboard shortcuts/even handlers
        self.bind('<Configure>', self.LeftFrame.on_change_size)
        self.bind('<Control-s>', self.save)
        self.bind('<Control-S>', self.save)
        self.bind('<Control-o>', self.open_)
        self.bind('<Control-O>', self.open_)
        self.bind('<Control-Shift-s>', self.save_as)
        self.bind('<Control-Shift-S>', self.save_as)
        self.bind('<Control-w>', self.restore_defaults)
        self.bind('<Control-W>', self.restore_defaults)
 

        self.frames = {}
        # Initialize test-specific frames
        for F in frame_types:
            # loads the default values of the controls
            btnvars = loadandsave.StringVarDict(**DEFAULT_CONFIG[F.__name__])

            # initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=btnvars)

            # when user changes a control
            btnvars.on_change = self.on_change
        
        
        
        # retrieve settings for 
        self.global_settings = {
            'SimSettings' : loadandsave.StringVarDict(
                **DEFAULT_CONFIG['SimSettings']),
            
            'HdwSettings' : loadandsave.StringVarDict(
                **DEFAULT_CONFIG['HdwSettings'])
            }

        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        self.cnf_filepath = None
        self.is_destroyed = False
        self.set_step(0)

        
    def frame_update(self):
        # indicates a change in the user's selected test
        self.show_frame(self.selected_test.get())
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

        for frame_name, frame in self.frames.items():
            frame.btnvars.set(DEFAULT_CONFIG[frame_name])

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
    
    def make_empty(self):
        self.selected_test.set('EmptyFrame')
        self.set_step(0)
    
    def pretest(self):
        self.show_frame('TestInfoGuiFrame')
        self.set_step(2)

    def run(self):
        
        #set step to 'running'
        self.set_step(3)
        
        #retrieve configuration from controls
        cnf = self.get_cnf()
        
        #runs the test in the main thread, passing cnf as configuration
        main.callback(lambda: run(cnf))
                

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
        
    def post_test(self, error):
        self.set_step(4)
        self.show_frame('PostTestGuiFrame')
        
        err_class, err_msg, trace = error
        if err_class:
            tk.messagebox.showerror(
               err_class.__name__, err_msg)
        
    def finish(self):
        
        txt_box = self.frames['PostTestGuiFrame'].post_test
        
        # retrieve post_notes
        self.post_test_info = {'Post Test Notes': txt_box.get(1.0, tk.END)}
                
        #back to config frame
        self.frame_update()
               
        
    def set_step(self, step):
        self.step = step
        if step == 0:
            self.show_frame('EmptyFrame')
            next_btn_txt = 'Next'
            next_btn = None #disabled
            back_btn = None
        
        elif step == 1:
            next_btn_txt = 'Next'
            next_btn = self.pretest
            back_btn = self.make_empty
        
        elif step == 2:
            next_btn_txt = 'Run Test'
            next_btn = self.run
            back_btn = self.frame_update
        
        elif step == 3:
            #TODO: show running test frame
            next_btn_txt = 'Abort Test'
            next_btn = self.abort
            back_btn = None
            
        elif step == 4:
            #TODO: show post_test
            next_btn_txt = 'Finish'
            next_btn = self.finish
            back_btn = None
            
        
        #changes function and text of the next button
        self.set_next_btn(next_btn_txt, next_btn)
        
        #changes back button
        self.set_back_btn(back_btn)
        
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
                self.main_, self.main_.global_settings['SimSettings'])
        else:
            shared.HdwSettings(
                self.main_, self.main_.global_settings['HdwSettings'])
        

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
        
        
        #TODO: check audio button
        #self.check_audio_btn = ttk.Button(text='Check Audio',
                #command=self._check_audio)
        
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
        
class _test_info_gui_override:
    """Container for test_info_gui overrides
    """
            
    def pretest(self, outdir='', check_function=None):
        pass
    
    def post_test(self, error_only=False):
        return get_post_notes(error_only)
        




    
    
















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
        """Calls a function in the GUI_Thread
        

        Parameters
        ----------
        function : callable
        
        """
        self._callbacks.insert(0, function)
    
     
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setName('Gui_Thread')
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
        param_modify(cfg, is_sim)
        
        
        # if recovery
        if (cfg['data_file'] != ""):
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
    
            # Gather pretest notes and M2E parameters
            my_obj.info.update(pre_notes)
    
    
            # Write pretest notes and info to tests.log
            write_log.pre(info=my_obj.info, outdir=my_obj.outdir)
            
        else:
            my_obj.info = pre_notes
    
        # clear notes from window
        main.gui_thread.callback(main.win.clear_notes)
        
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
        
    
        # open audio_player
        if hasattr(my_obj, 'blocksize'):
            bs = my_obj.blocksize
        elif hasattr(my_obj, 'blockSize'):
            bs = my_obj.blockSize
            
        if hasattr(my_obj, 'buffersize'):
            bf = my_obj.buffersize
        elif hasattr(my_obj, 'bufSize'):
            bf = my_obj.bufSize
            
        ap = AudioPlayer(fs=my_obj.fs,
                         blocksize=bs,
                         buffersize=bf)
        
        
        if hasattr(my_obj, 'audioInterface'):
            my_obj.audioInterface = ap
        elif hasattr(my_obj, 'audio_player'):
            my_obj.audio_player = ap
        
            my_obj.audio_player.playback_chans = {'tx_voice':0, 'start_signal':1}
            my_obj.audio_player.rec_chans = {'rx_voice':0, 'PTT_signal':1}
    
    
        # Open RadioInterface object
        with RadioInterface(cfg['radioport']) as my_obj.ri:
        
            #run test
            my_obj.run()
            

    
    except ValueError as e:
        tk.messagebox.showerror('Invalid Option', str(e))
        
        # go back to config screen
        main.gui_thread.callback(main.win.frame_update)
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
    
    
    # convert audio files string into a list
    for af in ('audio_files', 'audioFiles'):
        if af in cfg:
            # turns comma-separated list into list
            cfg[af] = [x.strip() for x in cfg[af].split(',')]
    
            #must enter at least 1 audio file
            if not cfg[af][0]:
                raise ValueError('Please select an audio file')
            
    if '_ptt_delay_min' in cfg:
        cfg['ptt_delay'] = [cfg['_ptt_delay_min']]
        try:
            cfg['ptt_delay'].append(float(cfg['_ptt_delay_max']))
        except ValueError:pass
    
    if '_time_expand_i' in cfg:
        cfg['time_expand'] = [cfg['_time_expand_i'], cfg['_time_expand_f']]
        
def get_post_notes(error_only=False):
    
    #get current error status, will be None if we are not handling an error
    root_error=sys.exc_info()
    error = root_error[0]
    
    #check if there is no error and we should only show on error
    if( (not error) and error_only):
        #nothing to do, bye!
        return {}
    
    
    # call post_test in Gui_Thread
    main.gui_thread.callback(lambda : main.win.post_test(root_error))
    
    # wait for completion or program close
    main.win.post_test_info = None
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

    #override test_info_gui in each module
    #TODO: add rest of modules
    for module in [m2e_gui.m2e_class, accesstime_gui.adly]:
        module.test_info_gui = _test_info_gui_override
    
    
    Main()
