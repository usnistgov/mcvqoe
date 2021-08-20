# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import os

import mcvqoe.accesstime as adly

import tkinter as tk

import shared
from shared import TestCfgFrame, SubCfgFrame
import loadandsave


#------------------------------controls--------------------------------------

from shared import audio_files, outdir, ptt_gap, time_expand
from shared import BgNoise
from shared import dev_dly, RadioCheck, audio_path, SaveAudio


        
class auto_stop(shared.LabeledCheckbox):
    """Enable checking for access and stopping the test when it is detected."""
    
    middle_text = 'Enable Auto-Stop'
    
class stop_rep(shared.LabeledNumber):
    """Number of times that access must be detected in a row before the
    test is completed."""
    
    text = 'Stop after __ successful:'
    
    min_ = 1
    
    
    
    
    
    
    
class ptt_delay(SubCfgFrame):
    text = 'PTT Delay (sec)'
    
    variable_type = loadandsave.Vec1Or2Var
    
    def get_controls(self):
        return (
            _ptt_delay_min,
            _ptt_delay_max
            )
    
class _ptt_delay_min(shared.LabeledNumber):
    """The smallest ptt_delay"""
    
    text = 'Min Delay Time:'
    
    increment = 0.01
    
    
class _ptt_delay_max(shared.LabeledNumber):
    """The largest ptt_delay. By default, this will be set to the end
    of the first word in the clip."""
    
    text = 'Max Delay Time:'
    
    increment = 0.01
    

class ptt_step(shared.LabeledNumber):
    """Time difference in seconds between successive ptt_delays."""
    
    text = 'Time Increase per Step:'
    
    increment = 0.01
    


class ptt_rep(shared.LabeledNumber):
    """Number of times to repeat a given PTT delay value. If auto_stop is
    used, this must be greater than 15."""
    
    text = 'Repeats per Step:'
    
    

    
class s_thresh(shared.LabeledNumber):
    """The threshold of A-weight power for P2, in dB, below which a trial
    is considered to have no audio."""
    
    text = 'Min Allowed Volume (dB):'
    
    min_ = -2**15 +1
    max_ = 0

class s_tries(shared.LabeledNumber):
    """Number of times to retry the test before giving up."""
    
    text = 'Retry Attempts:'
    
    
    
class data_file(shared.EntryWithButton):
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
            advanced,
            )

# -------------------------- The advanced window ------------------------------

class AccDlyAdvanced(shared.AdvancedConfigGUI):
    text = 'Access Delay - Advanced'
    
    def get_controls(self):
        return (
            
            ptt_rep,
            ptt_delay,
            
            AutoStop,
            BgNoise,
            DetectFailure,
            time_expand,
            )
        
    
class advanced(shared.advanced):
    toplevel = AccDlyAdvanced
    
    








class Access_fromGui(shared.SignalOverride, adly.measure):
    
    def run(self, recovery = False):
        super().run(recovery)
    



