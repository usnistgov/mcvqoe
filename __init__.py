# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""
from m2e_gui import M2eFrame

import loadandsave
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import tkinter.font as font
import tkinter.filedialog as fdl
import json


# Basic configuration
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


class MCV_QoE_Gui(tk.Tk):
    """The main Gui


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        set_font(size=FONT_SIZE)

        self.title(TITLE_)
        # dimensions
        self.minsize(width=600, height=370)
        self.geometry(f'{WIN_SIZE[0]}x{WIN_SIZE[1]}')
        
        
        # tk Variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')

        self.LeftFrame = LeftFrame(self, main_=self)
        self.LeftFrame.pack(side=tk.LEFT, fill=tk.Y)

        self.bind('<Configure>', self.LeftFrame.on_change_size)
        
        
        
        BottomButtons(master=self).pack(side=tk.BOTTOM, fill = tk.X)
        
        
        

        self.frames = {}
        # Initialize test-specific frames
        for F in (EmptyFrame, M2eFrame):
            # loads the default values of the controls
            svd = loadandsave.StringVarDict(**DEFAULT_CONFIG[F.__name__])

            # initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=svd,
                                        padx=10, pady=10)

        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
        self.cnf_filepath = None

    def show_frame(self, framename):
        # hide the showing widget
        self.currentframe.pack_forget()

        self.currentframe = self.frames[framename]
        self.currentframe.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

    def is_empty(self):
        return self.currentframe == self.frames['EmptyFrame']
    
    
        
    def load(self):
        """Loads config from .json file
        """
        
        fpath = fdl.askopenfile(
                'r',
                filetypes=[('.json files','*.json')]
                )
        
        if fpath is None:
            #canceled by user
            return
        
        with fpath as fp:
        
            dct = json.load(fp)
            for frame_name, frame in self.frames.items():
                frame.btnvars.set(dct[frame_name])
                
                
            
            self.is_simulation.set(dct['is_simulation'])
            self.selected_test.set(dct['selected_test'])
    
    
    
    def save_as(self):
        
        fp = fdl.asksaveasfilename(filetypes=[('.json files','*.json')])
        if fp is not None:
            self.cnf_filepath = fp
            self.save()
        
        
        
    def save(self):
        """Saves config to .json file

        """
        if self.cnf_filepath is None:
            self.save_as()
            return
        
        with open(self.cnf_filepath, mode='w') as fp:
            
            obj = {
                'is_simulation': self.is_simulation.get(),
                'selected_test': self.selected_test.get()
                }
            
            
            for framename, frame in self.frames.items():
                obj[framename] = frame.btnvars.get()
                
            json.dump(obj, fp)
            
            
        
        
        
        
        
    def run(self):
        pass
        
        
class BottomButtons(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        ttk.Button(master=self, text='Load Config',
            command = master.load).pack(
            side=tk.RIGHT)
        
        ttk.Button(master=self, text='Save Config',
            command = master.save).pack(
            side=tk.RIGHT)
        
        ttk.Button(master=self, text = 'Run Test',
            command = master.run).pack(
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
        if event.width < 600:
            # potential case of invalid event
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
        ttk.Label(self, text='Choose Test Type:').pack(fill=tk.X)

        # hardware test
        ttk.Radiobutton(self, text='Hardware Test',
                        variable=is_sim, value=False).pack(fill=tk.X)

        # simulation test
        ttk.Radiobutton(self, text='Simulation Test',
                        variable=is_sim, value=True).pack(fill=tk.X)

        ttk.Separator(self).pack(fill=tk.X, pady=20)

        # Choose Test
        ttk.Label(self, text='Choose Test:').pack(fill=tk.X)

        # Change test frame when user changes this option
        cmd = self.change_frame

        ttk.Radiobutton(self, text='M2E Latency', command=cmd,
                        variable=sel_txt, value='M2eFrame').pack(fill=tk.X)

        ttk.Radiobutton(self, text='Access Delay', command=cmd,
                        variable=sel_txt, value='AccssDFrame').pack(fill=tk.X)

        ttk.Radiobutton(self, text='PSuD', command=cmd,
                        variable=sel_txt, value='PSuDFrame').pack(fill=tk.X)

        ttk.Radiobutton(self, text='Intelligibility', command=cmd,
                        variable=sel_txt, value='IntgblFrame').pack(fill=tk.X)

    def change_frame(self):
        self.main_.show_frame(self.main_.selected_test.get())


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




if __name__ == '__main__':
    wn = MCV_QoE_Gui()
