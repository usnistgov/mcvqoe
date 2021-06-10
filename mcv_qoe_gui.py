# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""

# Basic configuration
Reduced_Error_Messages = False

TITLE_ = 'MCV QoE'

FONT_SIZE = 13

WIN_SIZE = (850, 700)

# the initial values in all of the controls
DEFAULT_CONFIG = {
    'EmptyFrame': {},

    'M2eFrame': {
        'audio_file': "test.wav",
        'bgnoise_file': "",
        'bgnoise_volume': 0.1,
        'blocksize': 512,
        'buffersize': 20,
        'fs': int(48e3),
        'no_log': ['test', 'ri'],
        'outdir': "",
        'overplay': 1.0,
        'ptt_wait': 0.68,
        'radioport': "",
        'test': "m2e_1loc",
        'trials': 100
    }
}





from m2e_gui import M2eFrame
import m2e_gui

import loadandsave

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import tkinter.font as font
import tkinter.filedialog as fdl
import tkinter.messagebox as msb

import json
from threading import Thread
import sys
import time
import traceback





class MCVQoEGui(tk.Tk):
    """The main window


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        set_font(size=FONT_SIZE)

        # the config starts unmodified
        self.set_saved_state(True)
        
        
        # dimensions
        self.minsize(width=600, height=370)
        self.geometry(f'{WIN_SIZE[0]}x{WIN_SIZE[1]}')
        
        
        # tk Variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')
        
        #change frame when this is changed
        self.selected_test.trace_add('write', self.frame_update)

        self.LeftFrame = LeftFrame(self, main_=self)
        self.LeftFrame.pack(side=tk.LEFT, fill=tk.Y)
        
        BottomButtons(master=self).pack(side=tk.BOTTOM, fill = tk.X,
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
        for F in (EmptyFrame, M2eFrame):
            # loads the default values of the controls
            btnvars = loadandsave.StringVarDict(**DEFAULT_CONFIG[F.__name__])

            # initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=btnvars,
                                        padx=10, pady=10)
            
            # when user changes a control
            btnvars.on_change = self.on_change
            
            
        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        self.cnf_filepath = None
        
        
        
        self.testThread = TestThread(daemon=True)
        self.testThread.start()
        
        
    def frame_update(self, *args, **kwargs):
        #indicates a change in the user's selected test
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
        # blocks closing if user cancels the save
        if not self.ask_save():
            self.destroy()
        
        
    def restore_defaults(self, *args, **kwargs):
        if self.ask_save():
            #cancelled
            return
        
        for frame_name, frame in self.frames.items():
            frame.btnvars.set(DEFAULT_CONFIG[frame_name])
        
        # user shouldn't be prompted to save the default config
        self.set_saved_state(True)
        
        
    def open_(self, *args, **kwargs):
        """Loads config from .json file
        """
        if self.ask_save():
            #cancelled
            return
        
        
        fpath = fdl.askopenfilename(
                filetypes=[('json files','*.json')]
                )
        
        if not fpath:
            #canceled by user
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
        fp = fdl.asksaveasfilename(filetypes=[('json files','*.json')],
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
            #no need to ask!
            return False
        
        out = msb.askyesnocancel(title='Warning',
            message='Would you like to save unsaved changes?')
        if out:
            return self.save()
        else:
            # true if user cancelled
            return out is None
            
            
        
        
    def set_saved_state(self, is_saved:bool = True):
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
        
        
        
        
        #OLD CODE
        if not self.testThread or not self.testThread.is_alive():
            #(re)start the thread
            self.testThread = TestThread()
            self.testThread.start()
        
        #if self.testThread.is_running() and not tk.messagebox.askyesno(
            #'Test Running',
            #'Another test is already running. Would you like to run this test'+
            #' after that one?'):
            
            ## add test to queue was canceled by user
            #return
        
        self.testThread.add(self.get_cnf())
        
    
    
    
class BottomButtons(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        ttk.Button(master=self, text = 'Run Test',
            command = master.run).pack(
            side=tk.RIGHT)
                
        ttk.Button(master=self, text='Restore Defaults',
            command = master.restore_defaults).pack(
            side=tk.RIGHT)      
        
        ttk.Button(master=self, text='Load Config',
            command = master.open_).pack(
            side=tk.RIGHT)
        
        ttk.Button(master=self, text='Save Config',
            command = master.save).pack(
            side=tk.RIGHT)
        
        
        
    
        
        

class LeftFrame(tk.Frame):
    """Can show and hide the MenuFrame using the MenuButton

    Only applies when the main window is small enough
    """
    # The window's minimum width at which the menu is shown
    MenuShowWidth = 850

    def __init__(self, master, main_, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # stores the main Tk window
        self.main_ = main_

        self.DoMenu = False
        self.MenuVisible = True

        self.MenuButton = MenuButton(self, command=self.on_button)

        # pass main_ down the chain to the TestTypeFrame
        self.MenuFrame = MenuFrame(self, main_)
        self.MenuFrame.pack(side=tk.LEFT, fill=tk.Y)

    def on_change_size(self, event):
        w = self.MenuShowWidth
        if event.width < 600 or event.height < 370:
            # unknown source of incorrect events
            return
        if event.width < w and not self.DoMenu:
            self.DoMenu = True
            self.MenuVisible = False
            self.MenuButton.pack(side=tk.LEFT, fill=tk.Y)
            self.MenuFrame.pack_forget()
            if self.main_.is_empty():
                self.MenuFrame.pack(side=tk.LEFT, fill=tk.Y)
                self.MenuVisible = True
        elif event.width >= w and self.DoMenu:
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


def create_arg_list(cfg, arg_assoc) -> list:
    """turns the configuration into command line arguments
    

    Parameters
    ----------
    cfg : dict
        associates keys to values.
    arg_assoc : dict
        associates keys to argument identifiers. Should 

    Returns
    -------
    list
        the formatted arguments

    """
    out = []
    for k, arg_prefix in arg_assoc.items():
        if arg_prefix and cfg[k]:
            out.append(arg_prefix)
        if cfg[k] is not bool:
            out.append(cfg[k])
            


og_args = sys.argv.copy()

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
        
        
    def main_loop(self):
        while not self._break:
            
            if not len(self):
                time.sleep(0.2)
                continue
                
            self.current_test = self.pop(0)
            try:
                run(self.current_test)     
            except ValueError as e:
                tk.messagebox.showerror('Value Error', str(e))
            except Exception:
                # prints exception without exiting main thread
                traceback.print_exc()
            
    def is_running(self) -> bool:
        return bool(self)

    def stop(self):
        self._break = True


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
                
                
    ToDo = '' # implement other tests here
    
if __name__ == '__main__':
    Main()