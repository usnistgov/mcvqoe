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


#Basic configuration
TITLE_ = 'MCV QoE'
FONT_SIZE = 14

# the initial values in all of the controls
DEFAULT_CONFIG = {
    'EmptyFrame': {},
    
    'M2eFrame'  : {
                'audio_file'      : "test.wav",
                'bgnoise_file'    : "",
                'bgnoise_volume'  : 0.1,
                'blocksize'       : 512,
                'buffersize'      : 20,
                'fs'              : int(48e3),
                'no_log'          : ['test', 'ri'],
                'outdir'          : "",
                'overplay'        : 1.0,
                'ptt_wait'        : 0.68,
                'radioport'       : "",
                'test'            : "m2e_1loc",
                'trials'          : 100
            }
    }

class MCV_QoE_Gui(tk.Tk):
    """The main Gui
    

    """
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        set_font(size=FONT_SIZE)
        
        self.title(TITLE_)
        #dimensions
        self.minsize(width=600, height=370)
        
        
        
        LogoFrame(master=self).pack(side=tk.LEFT, fill=tk.Y)
        
        #tk Variables to determine what test to run and show config for
        self.is_simulation = tk.BooleanVar(value=False)
        self.selected_test = tk.StringVar(value='EmptyFrame')
        
        TestTypeFrame(master=self, padx=10, pady=10).pack(
            side=tk.LEFT, fill=tk.Y)
        
        self.frames = {}
        
        
        #Initialize test-specific frames for the window
        for F in (EmptyFrame, M2eFrame):
            #loads the default values of the controls
            svd = loadandsave.StringVarDict(**DEFAULT_CONFIG[F.__name__])
            
            #initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=svd,
                                        padx=10, pady=10)
        
        
        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
            
        

    def show_frame(self, framename):
        #hide the showing widget
        self.currentframe.pack_forget()
        
        self.currentframe = self.frames[framename]
        self.currentframe.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

        

class EmptyFrame(tk.Frame):
    """An empty frame
    
    """
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    

class TestTypeFrame(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        
        #StringVars to determine what test to run and show config for
        is_sim  = master.is_simulation
        sel_txt = master.selected_test
        
        
        
        # Test Type
        ttk.Label(self, text='Choose Test Type:').pack(fill=tk.X)
        
        #hardware test
        ttk.Radiobutton(self, text='Hardware Test',
            variable=is_sim, value=False).pack(fill=tk.X)
        
        #simulation test
        ttk.Radiobutton(self, text='Simulation Test',
            variable=is_sim, value=True).pack(fill=tk.X)
                
                
        ttk.Separator(self).pack(fill=tk.X,pady=20)
        
        #Choose Test
        ttk.Label(self, text='Choose Test:').pack(fill=tk.X)
        
        #Change test frame when user changes this option
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
        self.master.show_frame(self.master.selected_test.get())
        

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
        if crest != None:
            
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
            
            
            

def set_font(**cfg):
    """Globally changes the font on all tkinter windows.
    
    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)



if __name__ == '__main__':
    wn = MCV_QoE_Gui()
    
