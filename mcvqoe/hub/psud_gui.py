# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:06:49 2021

@author: MkZee
"""
import os
import mcvqoe.psud as psud
import tkinter as tk

from .shared import LabeledSlider, TestCfgFrame, AdvancedConfigGUI, SignalOverride
from .shared import audio_set
from .shared import format_audio_files
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


class audio_set(audio_set):
    """Included PSuD Audio set to use."""
    text = "Audio Set"
    default_sets, default_path = psud.measure.included_audio_sets()

    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, row, *args, **kwargs)
        # Grab included audio sets and paths from psud measure class
        sets, audio_path = psud.measure.included_audio_sets()
        # Set default to first set
        self.btnvar.set(self.default_sets[0])
        # Add all sets to drop down
        for audio_set in self.default_sets:
            self.menu.add_command(
                label=audio_set,
                command=lambda value=audio_set: self.update_audio_selection(value)
                )

    def update_audio_selection(self, audio_set):
        """Update audio files and audio paths based on audio set selection."""
        # update audio set button
        self.btnvar.set(audio_set)
        # TODO: Update audio_files and audio_path
        # tk._setit(self.btnvar, audio_set)
        path = os.path.join(self.default_path, audio_set)
        path_, files = format_audio_files(path_=path, files=[])
        self.master.btnvars['audio_files'].set(files)
        self.master.btnvars['audio_path'].set(path_)

# ---------------------- The main config frame --------------------------------

class PSuDFrame(TestCfgFrame):
    
    text = 'Probability of Successful Delivery Test'
    
    
    def get_controls(self):
        return (
            audio_set,
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
        
    
    
    
    
    
    