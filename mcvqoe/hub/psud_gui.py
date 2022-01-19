# -*- coding: utf-8 -*-
"""
Created on Thu Jun 17 14:06:49 2021

@author: MkZee
"""
import os
import mcvqoe.psud as psud
import tkinter as tk
import tkinter.filedialog as fdl

from .shared import LabeledSlider, TestCfgFrame, AdvancedConfigGUI, SignalOverride
from .shared import Audio_Set
from .shared import format_audio_files, test
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


class audio_set(Audio_Set):
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
        for aset in self.default_sets:
            self.menu.add_command(
                label=aset,
                command=lambda value=aset: self.update_audio_selection(value)
                )
        # Disable number of trials button

    def update_audio_selection(self, aset):
        """Update audio files and audio paths based on audio set selection."""
        # update audio set button
        self.btnvar.set(aset)
        # Get path to audio set
        path = os.path.join(self.default_path, aset)
        path_, files = format_audio_files(path_=path, files=[])
        # Update audio files and audio paths
        self.master.btnvars['psud_audio_files'].set(files)
        self.master.btnvars['psud_audio_path'].set(path_)
        # Update true controls
        self.master.btnvars['audio_files'].set(files)
        self.master.btnvars['audio_path'].set(path_)
        # Disable Number of trials button
        self.master.controls['psud_trials'].m_ctrl['state'] = 'disable'

class psud_audio_files(audio_files):
    __doc__ = audio_files.__doc__

    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, row, *args, **kwargs)

    def on_button(self):
        super().on_button()
        # Set psud_audio path to updated path
        new_path = self.master.btnvars['audio_path'].get()
        self.master.btnvars['psud_audio_path'].set(new_path)
        # Update real control for audio files
        self.master.btnvars['audio_files'].set(self.btnvar.get())
        # Enable trials button
        self.master.controls['psud_trials'].m_ctrl['state'] = 'normal'



class psud_audio_path(audio_path):
    __doc__ = audio_path.__doc__
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, row, *args, **kwargs)
    
    def on_button(self):
        super().on_button()
        # Update psud audio files
        new_files = self.master.btnvars['audio_files'].get()
        self.master.btnvars['psud_audio_files'].set(new_files)
        # Update real control for audio path
        self.master.btnvars['audio_path'].set(self.btnvar.get())
        # Disable trials
        self.master.controls['psud_trials'].m_ctrl['state'] = 'disable'



class psud_trials(trials):
    __doc__ = trials.__doc__
    
    def __init__(self, master, row, *args, **kwargs):
        super().__init__(master, row, *args, **kwargs)
        self.m_ctrl['state'] = 'disable'
    
    
# ---------------------- The main config frame --------------------------------

class PSuDFrame(TestCfgFrame):
    
    text = 'Probability of Successful Delivery Test'
    
    def get_controls(self):
        return (
            audio_set,
            psud_audio_files,
            psud_audio_path,
            outdir,
            psud_trials,
            SaveAudio,
            ptt_wait,
            ptt_gap,
            intell_est,
            test,
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

class PSuD_Eval_from_GUI(SignalOverride, psud.evaluate):
    
    def param_check(self):
        # future-proofing this param-check override
        if hasattr(super(), 'param_check'):
            super().param_check()