# -*- coding: utf-8 -*-
"""
Created on Wed May 26 15:53:57 2021

@author: marcus.zeender@nist.gov
"""

import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk

class ButtonArea(tk.Frame):

    def __init__(self, master, buttons):

        super().__init__(master=master, padx=4, pady=4)
        self.btns = []
        for i in range(len(buttons)):
            btninf = buttons[i].copy()
            dodefault = False
            dodefault2 = True
            
            if 'width' not in btninf:
                btninf['width'] = 15
                
            if 'default' in btninf:
                dodefault = btninf['default']
                del btninf['default']
            
            btn = ttk.Button(self, **btninf)
            if dodefault or (
                    dodefault2 and ('text' in btninf) and
                    btninf['text'] in 'Finish Next ->'):
                
                dodefault2 = False
                btn.focus()
                
           
            btn.pack(side=tk.RIGHT)
            self.btns.append(btn)
        
        
class CrestFrame(tk.Canvas):
    
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
            
            
            
class WindowType(tk.Tk):
    """
        

    Parameters
    ----------
    master : 
        a tkinter widget
    buttons : list
    a list of DICTs with the (optional) keys 'text', 'command', 'image', etc
    
        Including 'default': True will set the button as default
    
    
    

    """
    
    def __init__(self,
                 title="MCV QoE",
                 buttons=[]):
        
        super().__init__()
        self.title(title)
        self.minsize(width=600, height=370)
        
        self.crestwidget = CrestFrame(master=self)
        self.crestwidget.pack(side=tk.LEFT, fill=tk.Y)
        if len(buttons):
            self.buttonarea = ButtonArea(self, buttons)
            self.buttonarea.pack(side=tk.BOTTOM, fill=tk.X)
   


if __name__ == '__main__':
    #wn = WindowType(buttons=[{'text':'Next'}, {'text':'previous'}])
    wn = WindowType()
    
