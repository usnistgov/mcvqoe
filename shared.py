# -*- coding: utf-8 -*-
"""
Created on Wed Jun  9 11:03:39 2021

@author: MkZee
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

import signal

PADX = 10
PADY = 10

FONT_SIZE = 11

class LabeledControl():
    """A one-row grid consisting of a label, control, and optional 2nd control
    
    Sub-classes should redefine any of the class variables, as well as the
        setup() method
    
    
    
    row : int
        the row that the controls should be gridded in
    
    """
    text = ''
    
    do_font_scaling = True
    
    MCtrl = ttk.Entry
    MCtrlargs = []
    MCtrlkwargs = {}
    
    variable_arg = 'textvariable'
    
    #usually the browse button
    RCtrl = None
    RCtrlkwargs = {}
    
    padx = PADX
    pady = PADY
    
    def setup(self):
        pass
    
    
    
    def __init__(self, master, row):
        self.master = master
        
        
        
    
        ttk.Label(master, text=self.text).grid(
            padx=self.padx, pady=self.pady, column=0, row=row, sticky='E')
        
        MCtrlkwargs = self.MCtrlkwargs.copy()
        MCtrlargs = self.MCtrlargs.copy()
        RCtrlkwargs = self.RCtrlkwargs.copy()
        
        try:
            self.btnvar = master.btnvars[self.__class__.__name__]
        except KeyError:
            self.btnvar = None
            
            
        self.setup()
        #some controls require more flexibility, so they don't use self.MCtrl
        if self.MCtrl:
            if self.variable_arg:
                MCtrlkwargs[self.variable_arg] = self.btnvar
            
            else:
                MCtrlargs.insert(0, self.btnvar)
            
            if self.do_font_scaling:
                MCtrlkwargs['font'] = f'{FONT_SIZE}'
                
            
            # initialize the control
            self.MCtrl(master, *MCtrlargs, **MCtrlkwargs).grid(
                column=1, row=row, padx=self.padx, pady=self.pady, sticky='WE')
        
        
        if self.RCtrl:
            #add command to button
            if self.RCtrl in (ttk.Button, tk.Button):
                RCtrlkwargs['command'] = self.on_button
            
            # initialize the control
            self.RCtrl(master, **RCtrlkwargs).grid(
                padx=self.padx, pady=self.pady, column=2, row=row, sticky='WE')
            
            
            
    def on_button(self):
        pass
            







class _SignalOverride():
    """
    Prevents test modules from using signal.signal, which breaks the
    multithreading process
    """
    def signal(*args, **kwargs): pass
    SIGINT = None
    
    