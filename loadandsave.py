# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 15:29:51 2021

@author: MkZee
"""

import os
from appdirs import user_data_dir as udd
import json
from tkinter import StringVar
import tkinter as tk


class StringVarDict(dict):
    
    """A dict of tk variables with initial values given
    
    Used to save, load, and get states of tkinter widgets
    
    'StringVarDict' is a misnomer because it actually takes all types
    
    """
    
    def __init__(self, **initials):
        for k, v in initials.items():
            if type(v) == str:
                self[k] = StringVar(value=v)
            elif type(v) == float:
                self[k] = tk.DoubleVar(value=v)
            elif type(v) == int:
                self[k] = tk.IntVar(value=v)
            else:
                continue
            self[k].trace_add('write', self._on_change_pre)
        
    def set(self, dict_):
        """sets the values of the StrVars to the values given
        

        Parameters
        ----------
        dict_ : dict
            

       
        """
        for k, v in dict_.items():
            if k in self:
                self[k].set(v)
    
    def get(self):
        """converts the values back into a dict
    

        Returns
        -------
        dict_ : dict
            

        """
        dict_ = {}
        for k, v in self.items():
            dict_[k] = v.get()
        return dict_
        
    def on_change(self):
        # should be set by each instance
        pass

    def _on_change_pre(self, *args, **kwargs):
        self.on_change()
        
        

class Config(dict):
    
    appinf = {'appname': 'MCV-QoE', 'appauthor': 'NIST'}
    
    def __init__(self, /, filename, **kwargs):
        super().__init__(**kwargs)
        
        self.filename = filename
        folder = udd(self.appinf['appname'], self.appinf['appauthor'])
        self.filepath = os.path.join(folder, filename)
        
        os.makedirs(folder, exist_ok=True)
        
        
        
    def dump(self):
       
        with open(self.filepath, 'w') as fp:
            json.dump(fp=fp, obj=self, indent=1)
            
        
    def load(self):
        self.clear()
        
        with open(self.filepath, 'r+') as fp:
            for k, v in json.load(fp=fp).items():
                self[k] = v
        
        