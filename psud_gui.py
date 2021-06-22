# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:06:49 2021

@author: MkZee
"""

import shared

import PSuD as psud

from tkinter import ttk
from tkinter import filedialog
from os import path
import os


class PSuDFrame(shared.TestCfgFrame):
    
    text = 'Probability of Successful Delivery Test'
    
    
    def get_controls(self):
        return (
            audioFiles,
            _BrowseForFolder,
            trials,
            overPlay,
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
            AudioSettings,
            TimeExpand,
            m2e_min_corr,
            radioport
            )
    
    

    
    




#----------------------------controls-----------------------------------------




from shared import trials
from shared import outdir
from shared import ptt_wait
from shared import ptt_gap
from shared import TimeExpand
from shared import radioport

class audioFiles(shared.audio_files):
    """Path to audio files to use for test. Cutpoint files must also be present.
    If a folder is entered instead, all audio files in the folder will be used"""
    
class overPlay(shared.overplay):
    """The number of seconds to play silence after the audio is complete
    This allows for all of the audio to be recorded when there is delay
    in the system"""
    
class blockSize(shared.blocksize):
    """Block size for transmitting audio"""
    
class bufSize(shared.buffersize):
    """Number of blocks used for buffering audio"""


class _BrowseForFolder(shared.LabeledControl):
    text = ''
    MCtrl = None
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse for Folder...'}
    
    def __init__(self, master, row):
        super().__init__(master, row)
        self.r_ctrl.grid_forget()
        self.r_ctrl.grid(columnspan=2,
                padx=self.padx, pady=self.pady, column=1, row=row, sticky='E')
    
    def on_button(self):
        fp = filedialog.askdirectory()
        if fp:
            self.master.btnvars['audioFiles'].set(fp)
    
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

    

class AudioSettings(shared.SubCfgFrame):
    
    text = 'Audio Settings'
    
    def get_controls(self):
        return (
            blockSize,
            bufSize,
            )
    
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
    
    
    
    
    