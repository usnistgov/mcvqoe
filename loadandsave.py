# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 15:29:51 2021

@author: MkZee
"""

import os
from appdirs import user_data_dir as udd
import json
import tkinter as tk

from access_time import int_or_inf


class TkVarDict(dict):
    
    """A dict of tk variables with initial values given
    
    Used to save, load, and get states of tkinter widgets
    
    
    """
    
    def __init__(self, **initials):
        for k, v in initials.items():
            self.add_entry(k, v)
    
    def add_entry(self, key, value, var_type=None):
        if var_type is None:
            if type(value) == bool:
                var_type = tk.BooleanVar
            elif type(value) == str:
                var_type = tk.StringVar
            elif type(value) == float:
                var_type = tk.DoubleVar
            elif type(value) == int:
                var_type = tk.IntVar
            elif value is None:
                return
            else:
                print(key, 'has an invalid value. Ignoring.')
                return
            
        self[key] = var_type(value=value)
        self[key].trace_add('write', self._on_change_pre)
            
        return self[key]
    
    def set(self, dict_):
        """sets the values of the vars to the values given
        

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
        
        
        
        
        
        
        
        
        
        
        
        
        
# -------------------------------- Variable types----------------------------
        
class CommaSepList(tk.StringVar):
    """used for audio_files"""
    
    def __init__(self, master=None, value=[], name=None):
        super().__init__(master, ', '.join(value), name)
        
    
    def get(self):
        return [x.strip() for x in super().get().split(',')]
    
    def set(self, value):
        super().set(', '.join(value))
        
        
class Vec1Or2Var:
    """used for controls that accept a 1 - or - 2 length vector"""
    
    def __init__(self, value=[]):
        v = value.copy()
        
        self.type_ = type(v[0])
        
        self.zero = tk.StringVar(value=v[0])
        
        try:
            self.one = tk.StringVar(value=v[1])
        except IndexError:
            self.one = tk.StringVar(value='<default>')
    
    def trace_add(self, *args, **kwargs):
        
        self.zero.trace_add(*args, **kwargs)
        self.one.trace_add(*args, **kwargs)
        
    def get(self):
        lst = [self.type_(self.zero.get())]
        
        one = self.one.get()
        if one != '<default>':
            lst[1] = self.type_(one)
            
        return lst
    
    def set(self, v):
        
        self.zero.set(v[0])
        
        try:
            self.one.set(v[1])
        except IndexError:
            self.one.set('<default>')
        
        



class IntOrInf(tk.StringVar):
    
    def __init__(self, master=None, value=0, name=None):
        
        try:
            val = str(int(value))
        except OverflowError:
            val = 'inf'
        super().__init__(master, val, name)
        
    def set(self, value):
        try:
            val = str(int(super().get()))
        except OverflowError:
            val = 'inf'
        super().set(val)
        
    def get(self):
        return int_or_inf(super().get())
        
        