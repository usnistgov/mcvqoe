# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:06:49 2021

@author: MkZee
"""

import shared

import mcvqoe.psud as psud




class PSuDFrame(shared.TestCfgFrame):
    
    text = 'Probability of Successful Delivery Test'
    
    
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




from shared import trials, _BrowseForFolder
from shared import outdir
from shared import ptt_wait
from shared import ptt_gap
from shared import time_expand

class audio_files(shared.audio_files):
    """Path to audio files to use for test. Cutpoint files must also be present.
    If a folder is entered instead, all audio files in the folder will be used"""
    
    
    
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
    pass
        
    
    
    
    
    
    