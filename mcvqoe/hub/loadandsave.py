# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 15:29:51 2021

@author: MkZee
"""

import os
from appdirs import user_data_dir as udd
import json
import tkinter as tk
import _tkinter
import atexit
from .tk_threading import InvalidParameter

import numpy as np


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
            
            elif np.issubdtype(type(value), np.floating):
                var_type = tk.DoubleVar
            elif type(value) == int:
                var_type = tk.IntVar
            elif type(value) == list:
                var_type = CommaSepList
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
            try:
                dict_[k] = v.get()
            except _tkinter.TclError:

                message = {
                    tk.BooleanVar: 'Must be either True or False',
                    tk.StringVar : 'Must be a string',
                    tk.DoubleVar : 'Must be a number',
                    tk.IntVar    : 'Must be a whole number',
                    CommaSepList : 'Must be a comma-separated list of strings',

                    }[type(v)]

                raise InvalidParameter(k, message) from None

        return dict_

    def on_change(self):
        # should be set by each instance
        pass

    def _on_change_pre(self, *args, **kwargs):
        self.on_change()


class Config(dict):
    """loads and saves a json file in the user's appdir folder"""

    appinf = {'appname': 'mcvqoe', 'appauthor': 'NIST'}

    def __init__(self, filename, /, **kwargs):
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
        return self


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
            lst.append(self.type_(one))

        return lst

    def set(self, v):

        self.zero.set(v[0])

        try:
            self.one.set(v[1])
        except IndexError:
            self.one.set('<default>')


class IntOrInf_OLD(tk.StringVar):

    def __init__(self, master=None, value=0, name=None):

        try:
            val = str(int(value))
        except OverflowError:
            val = 'inf'
        super().__init__(master, val, name)

    def set(self, value):
        try:
            val = str(int(value))
        except OverflowError:
            val = 'inf'
        super().set(val)

    def get(self):
        # return int_or_inf(super().get())
        pass


# ------------------------------------- caches --------------------------------

class BaseCache(Config):

    default = None

    def __init__(self, filename, *args, **kwargs):
        super().__init__(filename, *args, **kwargs)

        try:
            self.load()
        except FileNotFoundError:
            pass

        atexit.register(self.dump)

    def __getitem__(self, k):

        try:
            return super().__getitem__(k)
        except KeyError:
            return self.default


class FdlCache(BaseCache):

    def put(self, key, filepath):
        if os.path.isdir(filepath):
            self[key] = filepath
        elif os.path.isfile(filepath):
            self[key] = os.path.split(filepath)[0]

misc_cache = BaseCache('cache.json')
fdl_cache = FdlCache('file_dialog_cache.json')
dim_cache = BaseCache('window_cache.json')
hardware_settings = BaseCache('hardware_settings.json')
sync_settings = BaseCache('sync_settings.json')