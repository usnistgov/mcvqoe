# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""

import tkinter as tk
from PIL import Image, ImageTk
import tkinter.font as font


default_config = {
    'm2e': {    'audio_file'      : "test.wav",
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






def set_font(**cfg):
    """Globally changes the font on all tkinter windows.
    
    Accepts parameters like size, weight, font, etc.

    """
    font.nametofont('TkDefaultFont').config(**cfg)


        
        
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
            
            
            
class MCV_QoE_Gui(tk.Tk):
    """
        

    Parameters
    ----------
    
    buttons : list
    a list of DICTs with the (optional) keys 'text', 'command', 'image', etc
    
        Including 'default': True will set the button as default
    
    
    

    """
    title_ = 'MCV QoE'
    
    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        self.title(self.title_)
        self.minsize(width=600, height=370)
        
        crestwidget = LogoFrame(master=self)
        crestwidget.pack(side=tk.LEFT, fill=tk.Y)




if __name__ == '__main__':
    #wn = WindowType(buttons=[{'text':'Next'}, {'text':'previous'}])
    wn = MCV_QoE_Gui()
    set_font(size=20)
    
