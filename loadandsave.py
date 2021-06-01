# -*- coding: utf-8 -*-
"""
Created on Tue Jun  1 15:29:51 2021

@author: MkZee
"""

import os
from appdirs import user_data_dir as udd
import json

class Config(dict):
    
    appinf = {'appname': 'MCV-QoE', 'appauthor': 'NIST'}
    
    def __init__(self, /, filename, **kwargs):
        super().__init__(**kwargs)
        
        self.filename = filename
        folder = udd(self.appinf['appname'], self.appinf['appauthor'])
        self.filepath = folder + os.path.sep + filename
        
        os.makedirs(folder, exist_ok=True)
        
        
        
    def dump(self):
       
        with open(self.filepath, 'w') as fp:
            json.dump(fp=fp, obj=self, indent=1)
            
        
    def load(self):
        self.clear()
        
        with open(self.filepath, 'r+') as fp:
            for k, v in json.load(fp=fp).items():
                self[k] = v
        
        