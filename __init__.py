# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""
from m2e_gui import M2eFrame

import loadandsave
import tkinter as tk
from PIL import Image, ImageTk
import tkinter.font as font

#Basic configuration
TITLE_ = 'MCV QoE'
FONT_SIZE = 14
DEFAULT_CONFIG = {
    'EmptyFrame': {},
    
    'M2eFrame': {    'audio_file'      : "test.wav",
                'bgnoise_file'    : "",
                'bgnoise_volume'  : 0.1,
                'blocksize'       : 512,
                'buffersize'      : 20,
                'fs'              : int(48e3),
                'info'            : {},
                'no_log'          : ['test', 'ri'],
                'outdir'          : "",
                'overplay'        : 1.0,
                'ptt_wait'        : 0.68,
                'radioport'       : "",
                'ri'              : None,
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
        self.minsize(width=600, height=370)
        
        LogoFrame(master=self).pack(side=tk.LEFT, fill=tk.Y)
        
        self.frames = {}
        
        
        #Initialize frames for the window
        for F in (EmptyFrame, M2eFrame):
            #loads the default values of the controls
            svd = loadandsave.StringVarDict(**DEFAULT_CONFIG[F.__name__])
            
            #initializes the frame, with its key being its own classname
            self.frames[F.__name__] = F(master=self, btnvars=svd)
        
        
        self.currentframe = self.frames['EmptyFrame']
        self.currentframe.pack()
            
        

    def show_frame(self, frame):
        #hide the showing widget
        self.currentframe.pack_forget()
        
        self.currentframe = self.frames[frame]
        self.currentframe.pack(fill=tk.BOTH)



def set_font(**cfg):
    """Globally changes the font on all tkinter windows.
    
    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)



class EmptyFrame(tk.Frame):
    """An empty frame
    
    """
    def __init__(self, btnvars, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    
    
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
            
            
            



if __name__ == '__main__':
    wn = MCV_QoE_Gui()
    
