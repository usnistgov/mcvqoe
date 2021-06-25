# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:06:49 2021

@author: MkZee
"""

import shared

import mcvqoe.psud as psud

from tkinter import ttk
from tkinter import filedialog
from os import path
import os


class PSuDFrame(shared.TestCfgFrame):
    
    text = 'Probability of Successful Delivery Test'
    
    default_test_obj = psud.measure()
    
    def get_controls(self):
        return (
            audio_files,
            _BrowseForFolder,
            trials,
            ptt_wait,
            ptt_gap,
            intell_est,
            outdir,
            advanced,
            )
    
class PSuDAdvanced(shared.AdvancedConfigGUI):
    
    text = 'PSuD - Advanced'
    
    def get_controls(self):
        return (
            time_expand,
            m2e_min_corr,
            )
    
    

    
    




#----------------------------controls-----------------------------------------




from shared import trials
from shared import outdir
from shared import ptt_wait
from shared import ptt_gap
from shared import time_expand

class audio_files(shared.audio_files):
    """Path to audio files to use for test. Cutpoint files must also be present.
    If a folder is entered instead, all audio files in the folder will be used"""
    
    

class _BrowseForFolder(shared.LabeledControl):
    text = ''
    MCtrl = None
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse for Folder...'}
    no_default_value = True
    
    def __init__(self, master, row, default, *args, **kwargs):
        super().__init__(master, row, default, *args, **kwargs)
        self.r_ctrl.grid_forget()
        self.r_ctrl.grid(columnspan=2,
                padx=self.padx, pady=self.pady, column=2, row=row, sticky='E')
    
    def on_button(self):
        fp = filedialog.askdirectory()
        if fp:
            self.master.btnvars['audio_files'].set([fp])
    
class m2e_min_corr(shared.LabeledSlider):
    """Minimum correlation value for acceptable mouth 2 ear measurement"""
    text = 'Min Corr. for Success:'
    
    
class intell_est(shared.MultiChoice):
    """Compute Intelligibility estimation on audio:
    At the end of each trial,
    After test is complete,
    OR
    Don't compute intelligibility."""
    
    text = 'Compute Intelligibility:'
    
    association = {
        'trial' : 'During Test',
        'post'  : 'After Test',
        'none'  : 'Never',
        }

    

    
class advanced(shared.advanced):
    toplevel = PSuDAdvanced
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#-------------------------Running the test------------------------------------

class PSuD_fromGui(shared.SignalOverride, psud.measure):
    
        
    def param_check(self):
        # check if user chose a full folder instead of a list of files
        if path.isdir(self.audioFiles[0]):
            self.audioPath = self.audioFiles[0]
            self.audioFiles = []
            self.full_audio_dir = True
            
            #check for the existence of .wav files
            p = self.audioPath
            success = False
            for f in os.listdir(p):
                fp = path.join(p, f)
                if path.isfile(fp) and path.splitext(fp)[1].lower() == '.wav':
                    success = True
                    break
            if not success:
                raise ValueError('Audio Source Folder contains no .wav files.') 
    
    
    
    
    