# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import os

import mcvqoe.accesstime as adly

import tkinter as tk

from .shared import TestCfgFrame, SubCfgFrame
from .shared import LabeledNumber,LabeledCheckbox,EntryWithButton,AdvancedConfigGUI,SignalOverride, test
from .shared import advanced as shared_advanced
from .loadandsave import Vec1Or2Var


#------------------------------controls--------------------------------------

from .shared import audio_files, outdir, ptt_gap, time_expand
from .shared import BgNoise
from .shared import dev_dly, RadioCheck, audio_path, SaveAudio

      
class auto_stop(LabeledCheckbox):
    """Enable checking for access and stopping the test when it is detected."""
    
    middle_text = 'Enable Auto-Stop'


class stop_rep(LabeledNumber):
    """Number of times that access must be detected in a row before the
    test is completed."""
    
    text = 'Stop after __ successful:'
    
    min_ = 1
    
      
class ptt_delay(SubCfgFrame):
    text = 'PTT Delay (sec)'
    
    variable_type = Vec1Or2Var
    
    def get_controls(self):
        return (
            _ptt_delay_min,
            _ptt_delay_max
            )


class _ptt_delay_min(LabeledNumber):
    """The smallest ptt_delay"""
    
    text = 'Min Delay Time:'
    
    increment = 0.01
    
    
class _ptt_delay_max(LabeledNumber):
    """The largest ptt_delay. By default, this will be set to the end
    of the first word in the clip."""
    
    text = 'Max Delay Time:'
    
    increment = 0.01
    

class ptt_step(LabeledNumber):
    """Time difference in seconds between successive ptt_delays."""
    
    text = 'Time Increase per Step:'
    
    increment = 0.01
    

class ptt_rep(LabeledNumber):
    """Number of times to repeat a given PTT delay value. If auto_stop is
    used, this must be greater than 15."""
    
    text = 'Repeats per Step:'
    

class s_thresh(LabeledNumber):
    """The threshold of A-weight power for P2, in dB, below which a trial
    is considered to have no audio."""
    
    text = 'Min Allowed Volume (dB):'
    
    min_ = -2**15 +1
    max_ = 0


class s_tries(LabeledNumber):
    """Number of times to retry the test before giving up."""
    
    text = 'Retry Attempts:'
    
  
class data_file(EntryWithButton):
    """A temporary datafile to use to restart a test. If this is
    given all other parameters are ignored and the settings of the original
    test are used."""
    
    text = 'Recovery File:'
    
    button_text = 'Browse...'
    
    def on_button(self):
        
        outdir = self.master.btnvars['outdir'].get()
        recovery = os.path.join(outdir,'data', 'recovery')
        
        fp = tk.filedialog.askopenfilename(initialdir=recovery)
        if fp:
            self.btnvar.set(fp)


class AutoStop(SubCfgFrame):
    text = 'Auto-Stop'
    
    def get_controls(self):
        return (
            auto_stop,
            stop_rep,
            )
    
  
class DetectFailure(SubCfgFrame):
    text = 'Detecting Failed Transmission'   
    
    def get_controls(self):
        return (
            s_thresh,
            s_tries,
            )


class zip_audio(LabeledCheckbox):
    """ If checked audio will be zipped after test completes."""

    middle_text = "Zip Audio"
    

class bisect_midpoint(LabeledCheckbox):
    """If checked PTT times will be determined iteratively and will attempt to 
    converge around the PTT time associated with the intelligibility midpoint
    of the intelligibility curve. This will generally result in a much faster test,
    but may be more susceptible to generating an invalid intelligibility curve and
    access delay result in extreme circumstances.
    
    If unchecked PTT times will be uniformly spaced, and are predetermined based on
    other settings. This is the "safest" option in some ways, but generally 
    results in much longer tests.
    """
    text = "Bisect Midpoint"


# ------------------------ The main configuration frame -----------------------


class AccssDFrame(TestCfgFrame):
    text = 'Access Delay Test'
    
    
    def get_controls(self):
        return (
            audio_files,
            audio_path,
            outdir,
            ptt_step,
            ptt_gap,
            SaveAudio,
            RadioCheck,
            dev_dly,
            data_file,
            test,
            advanced,
            )


# -------------------------- The advanced window ------------------------------


class AccDlyAdvanced(AdvancedConfigGUI):
    text = 'Access Delay - Advanced'
    
    def get_controls(self):
        return (
            
            ptt_rep,
            zip_audio,
            ptt_delay,
            
            bisect_midpoint,
            
            AutoStop,
            BgNoise,
            DetectFailure,
            time_expand,
            )
        
    
class advanced(shared_advanced):
    toplevel = AccDlyAdvanced


class Access_fromGui(SignalOverride, adly.measure):
    pass
    

class Access_Eval_from_GUI(SignalOverride, adly.evaluate):
    
    def param_check(self):
        # future-proofing this param-check override
        if hasattr(super(), 'param_check'):
            super().param_check()
