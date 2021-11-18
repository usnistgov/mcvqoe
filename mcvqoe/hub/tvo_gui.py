# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 13:04:07 2021

@author: jkp4
"""
import os
import mcvqoe.tvo as tvo
import tkinter as tk
import tkinter.filedialog as fdl

from .shared import SubCfgFrame, TestCfgFrame, AdvancedConfigGUI, SignalOverride
from .shared import LabeledNumber, LabeledCheckbox, LabeledSlider
from .shared import format_audio_files, _get_master
from .shared import advanced as shared_advanced

#----------------------------controls-----------------------------------------

from .shared import trials, audio_files, audio_path, outdir
from .shared import ptt_wait, ptt_gap, time_expand
from .shared import SaveAudio, MultiChoice


class ptt_rep(LabeledNumber):
    """Number of times to repeat at a given volume level."""
    
    text = 'Repeats per volume level:'

class dev_volume(LabeledNumber):
    """
    Volume level of audio output from the audio interface. This is typically
    set using controls specific to individual audio interfaces, and cannot be
    set programatically.
    """
    max_=0
    min_=-100
    text = "Audio Interface Output Volume (dB)"
    
class smax(LabeledNumber):
    """Maximum number of sample volumes to use."""
    
    text = 'Max sample values'

class tol(LabeledNumber):
    """
    The minimum volume difference between any two evaluated points. Smaller 
    values results in more iterations, larger values results in a coarser 
    optimal volume estimate.
    """
    min_ = 0
    increment = 0.01
    text = 'Volume tolerance (dB):'

# ----------------Volume Levels---------------------------
class Volumes(SubCfgFrame):
    
    text = 'Volume Levels'
    toggleable_controls = [
        '_num_volumes',
        ]
    def __init__(self, master, *args, **kwargs):
        
        super().__init__(master, *args, **kwargs)
        
        btv = self.btnvars['_enable_Fixed_Volumes']
        trace_id = btv.trace_add('write',lambda *a,**k:self.update())
        
        # mark the trace for deletion, otherwise causes errors
        _get_master(self).traces_.append((btv, trace_id))
        
        self.update()
    def get_controls(self):
        return (
            _enable_Fixed_Volumes,
            _min_volume,
            _max_volume,
            _num_volumes,
            )
    
    def update(self):
        
        state = ('disabled', '!disabled')[self.btnvars['_enable_Fixed_Volumes'].get()]
        
        # disable other controls
        for ctrlname in self.toggleable_controls:
            ctrl = self.controls[ctrlname]
            
        # for ctrlname, ctrl in self.controls.items():
        #     if ctrlname == '_enable_Fixed_Volumes':
        #         continue
            
            ctrl.m_ctrl.configure(state=state)
class _enable_Fixed_Volumes(LabeledCheckbox):
    """
    Use fixed volumes defined by minimum, maximum, and number of volumes below.
    If enabled, an array with number of volume uniformly spaced volumes 
    between minimum volume and maximum volume is for evaluation.
    
    If disabled, evaluation volumes are determined algorithmically during a test.
    Initial volumes for consideration will be between the minimum and maximum 
    volumes set here.
    """
    text = 'Use fixed volume levels'


class _min_volume(LabeledNumber):
    """
    TODO: write this
    """
    max_ = 0
    text = "Minimum volume to evaluate"

class _max_volume(LabeledNumber):
    """
    TODO: Write this
    """
    max_ = 0
    text = "Maximum volume to evaluate"

class _num_volumes(LabeledNumber):
    """
    Number of volumes to evaluate if use fixed volumes selected
    """
    min_ = 2
    max_ = 30
    text = "Number of volumes"
# ---------------------- The main config frame --------------------------------

class TVOFrame(TestCfgFrame):
    
    text = 'Transmit Volume Optimization Procedure'
    
    def get_controls(self):
        return (
            audio_files,
            audio_path,
            outdir,
            SaveAudio,
            ptt_wait,
            ptt_gap,
            advanced,
            )
    
class TVOAdvanced(AdvancedConfigGUI):
    
    text = 'TVO - Advanced'
    
    def get_controls(self):
        return (
            dev_volume,
            ptt_rep,
            smax,
            tol,
            Volumes,
            # TODO: volumes
            # volumes,
            # Scaling, smax, tol
            )

class advanced(shared_advanced):
    toplevel = TVOAdvanced
    
#-------------------------Running the test------------------------------------

class TVO_fromGui(SignalOverride, tvo.measure):
    
    def param_check(self):
        # future-proofing this param-check override
        if hasattr(super(), 'param_check'):
            super().param_check()