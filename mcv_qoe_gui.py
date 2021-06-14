# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""

# basic configuration
import ctypes
import traceback
import time
import sys
import _thread
from threading import Thread
import json
import tkinter.messagebox as msb
import tkinter.filedialog as fdl
import tkinter.font as font
from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk
import shared
import loadandsave
import accesstime_gui
from accesstime_gui import AccssDFrame
import m2e_gui
from m2e_gui import M2eFrame
TITLE_ = 'MCV QoE'


WIN_SIZE = (870, 600)

# the initial values in all of the controls
DEFAULT_CONFIG = {
    'EmptyFrame': {},

    'M2eFrame': {
        'audio_files': '',
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
        'audio_files': [],
        'audio_path': "",
        'audio_player': None,
        'auto_stop': False,
        'bgnoise_file': "",
        'bgnoise_volume': 0.1,
        'blocksize': 512,
        'buffersize': 20,
        'data_file': "",
        'dev_dly': float(31e-3),
        'outdir': "",
        '_ptt_delay_min': 0.0,
        '_ptt_delay_max': 'auto',
        'ptt_gap': 3.1,
        'ptt_rep': 30,
        'ptt_step': float(20e-3),
        'radioport': "",
        's_thresh': -50,
        's_tries': 3,
        'stop_rep': 10,
        '_time_expand_i': float(100e-3 - 0.11e-3),
        '_time_expand_f': float(0.11e-3),
        'trials': 100,

    },
}


# on Windows, remove dpi scaling
if hasattr(ctypes, 'windll'):
    ctypes.windll.shcore.SetProcessDpiAwareness(1)


class MCVQoEGui(tk.Tk):
    """The main window


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        # change frame when this is changed
        self.selected_test.trace_add('write', self.frame_update)

        self.LeftFrame = LeftFrame(self, main_=self)
        self.LeftFrame.pack(side=tk.LEFT, fill=tk.Y)

        BottomButtons(master=self).pack(side=tk.BOTTOM, fill=tk.X,
                                        padx=10, pady=10)

        # keyboard shortcuts
        self.bind('<Configure>', self.LeftFrame.on_change_size)
        self.bind('<Control-s>', self.save)
        self.bind('<Control-S>', self.save)
        self.bind('<Control-o>', self.open_)
        self.bind('<Control-O>', self.open_)
        self.bind('<Control-Shift-s>', self.save_as)
        self.bind('<Control-Shift-S>', self.save_as)
        self.bind('<Control-w>', self.restore_defaults)
        self.bind('<Control-W>', self.restore_defaults)
        # when the user exits the program
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.frames = {}
        # Initialize test-specific frames
        for F in (EmptyFrame, M2eFrame, AccssDFrame):
            # loads the default values of the controls
            btnvars = loadandsave.StringVarDict(**DEFAULT_CONFIG[F.__name__])

            # initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=btnvars)

            # when user changes a control
            btnvars.on_change = self.on_change

        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        self.cnf_filepath = None

        self.testThread = TestThread(daemon=True)
        self.testThread.start()

    def frame_update(self, *args, **kwargs):
        # indicates a change in the user's selected test
        self.show_frame(self.selected_test.get())

    def show_frame(self, framename):
        # first hide the showing widget
        self.currentframe.pack_forget()
        try:
            self.currentframe = self.frames[framename]
        except KeyError:
            raise KeyError(f"Frame '{framename}' is not defined")
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

        if main.queue.is_running() and not tk.messagebox.askyesno(
                'Abort Test?', 'A test is currently running. Abort?'):
            # canceled by user
            return

        main.queue.stop()
        self.abort()
        self.destroy()

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
                frame.btnvars.set(dct[frame_name])

            self.is_simulation.set(dct['is_simulation'])
            self.selected_test.set(dct['selected_test'])

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

        return obj

    def run(self):

        main.queue.append(self.get_cnf())
        return

    def abort(self):
        _thread.interrupt_main()


class BottomButtons(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.master = master
        self.do_run = True
        self.run_textvar = tk.StringVar(value='Run Test')

        main.queue.update_run_btn = self.set_run_btn

        ttk.Button(master=self, textvariable=self.run_textvar,
                   command=self.stop_go).pack(
            side=tk.RIGHT)

        ttk.Button(master=self, text='Restore Defaults',
                   command=master.restore_defaults).pack(
            side=tk.RIGHT)

        ttk.Button(master=self, text='Load Config',
                   command=master.open_).pack(
            side=tk.RIGHT)

        ttk.Button(master=self, text='Save Config',
                   command=master.save).pack(
            side=tk.RIGHT)

    def stop_go(self):
        """Runs or aborts the test


        """
        if self.do_run:
            main.queue.append(self.master.get_cnf())
        else:
            self.master.abort()

    def set_run_btn(self, do_run):
        self.do_run = do_run
        if self.do_run:
            self.run_textvar.set('Run Test')
        else:
            self.run_textvar.set('Abort Test')


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


class EmptyFrame(tk.Frame):
    """An empty frame: shown when no test is selected yet

    """

    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btnvars = btnvars


def set_font(**cfg):
    """Globally changes the font on all tkinter windows.

    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)


def set_styles():

    for style in ('TButton', 'TEntry.Label', 'TLabel', 'TLabelframe.Label',
                  'TRadiobutton', 'TCheckbutton'):
        ttk.Style().configure(style, font=('TkDefaultFont', shared.FONT_SIZE))


def dpi_scaling(root):
    global dpi_scale
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        if screen_height < screen_width:
            dpi_scale = screen_height / 800
        else:
            dpi_scale = screen_width / 800
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


class TestThread(Thread):
    """NOT USED: allows the test to be run in a new thread

    """

    def __init__(self, *args, **kwargs):
        kwargs['daemon'] = True
        super().__init__(*args, **kwargs)
        self.setName('Test_Worker')

        self.test_queue = []
        self.current_test = None

    def run(self):
        while True:
            while not len(self.test_queue):
                self.current_test = None
                time.sleep(0.5)

            self.current_test = self.test_queue.pop(0)
            run(self.current_test)

    def add(self, test_config):
        self.test_queue.append(test_config)

    def is_running(self) -> bool:
        return bool(self.test_queue)


class TestQueue(list):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

        self.current_test = None
        self._break = False
    
    def append(self, *args, **kwargs):
        #only allows 1 item in queue
        if not self.is_running():
            super().append(*args, **kwargs)
            
            
    def main_loop(self):
        while not self._break:
            try:

                self.current_test = None
                if not len(self):
                    self.update_run_btn(True)
                while not len(self):
                    time.sleep(0.2)
                    
                self.update_run_btn(False)
                self.current_test = self.pop(0)
                run(self.current_test)
                
                
            except ValueError as e:
                tk.messagebox.showerror('Value Error', str(e))
            except shared.CtrlC_Stop:
                print('Test Aborted')
            except SystemExit:
                print('Test Failed')
            except KeyboardInterrupt:
                if self.is_running():
                    print('Test Aborted')
            except:
                # prints exception without exiting main thread
                traceback.print_exc()

    def is_running(self) -> bool:
        return bool(self) or bool(self.current_test)

    def stop(self):
        self._break = True
        
    def update_run_btn(self, *args, **kwargs): pass
    #overridden for a callback to change the text on the 'run'/'abort' btn


class Main():
    def __init__(self):
        global main
        main = self
        self.queue = TestQueue()

        # constructs gui in new thread
        self.gui_thread = Thread(
            target=self.gui_construct,
            name='Gui_Thread',
            daemon=True
        )
        self.gui_thread.start()

        self.queue.main_loop()

    def gui_construct(self):
        self.win = MCVQoEGui()
        self.win.mainloop()


def run(cfg):
    if cfg['selected_test'] == 'M2eFrame':
        m2e_gui.run(cfg['M2eFrame'], cfg['is_simulation'])

    ToDo = ''  # implement other tests here


if __name__ == '__main__':
    Main()
