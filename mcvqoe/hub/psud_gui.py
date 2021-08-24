# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:06:49 2021

@author: MkZee
"""

import mcvqoe.psud as psud

from .shared import LabeledSlider, TestCfgFrame, AdvancedConfigGUI, SignalOverride
from .shared import advanced as shared_advanced

#----------------------------controls-----------------------------------------

from .shared import trials, audio_files, audio_path, outdir
from .shared import ptt_wait, ptt_gap, time_expand
from .shared import SaveAudio, MultiChoice

class m2e_min_corr(LabeledSlider):
    """Minimum correlation value for acceptable mouth 2 ear measurement"""
    text = 'Min Corr. for Success:'
    
    
class intell_est(MultiChoice):
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

# ---------------------- The main config frame --------------------------------

class PSuDFrame(TestCfgFrame):
    
    text = 'Probability of Successful Delivery Test'
    
    
    def get_controls(self):
        return (
            audio_files,
            audio_path,
            outdir,
            trials,
            SaveAudio,
            ptt_wait,
            ptt_gap,
            intell_est,
            advanced,
            )
    
class PSuDAdvanced(AdvancedConfigGUI):
    
    text = 'PSuD - Advanced'
    
    def get_controls(self):
        return (
            time_expand,
            m2e_min_corr,
            )

class advanced(shared_advanced):
    toplevel = PSuDAdvanced
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
#-------------------------Running the test------------------------------------

class PSuD_fromGui(SignalOverride, psud.measure):
    
    def param_check(self):
        # future-proofing this param-check override
        if hasattr(super(), 'param_check'):
            super().param_check()
        
    
    
    
    
    
    