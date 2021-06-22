# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import access_time as adly

import tkinter.ttk as ttk

import shared
from shared import LabeledControl, TestCfgFrame, SubCfgFrame
from shared import radioport, outdir, ptt_gap
from shared import TimeExpand
from shared import AudioSettings, BgNoise


class AccssDFrame(TestCfgFrame):
    text = 'Access Delay Test'
    
    def get_controls(self):
        return (
            audio_files,
            outdir,
            ptt_step,
            ptt_rep,
            ptt_gap,
            RadioCheck,
            AutoStop,
            PttDelay,
            #data_file,
            advanced
            )
    
class AccDlyAdvanced(shared.AdvancedConfigGUI):
    text = 'Access Delay - Advanced'
    
    def get_controls(self):
        return (
            BgNoise,
            DetectFailure,
            TimeExpand,
            AudioSettings,
            dev_dly,
            radioport
            )
    
class RadioCheck(SubCfgFrame):
    text = 'Regular Radio Checks'
    
    def get_controls(self):
        return (
            _limited_trials,
            trials,
            )
    
    
class AutoStop(SubCfgFrame):
    text = 'Auto-Stop'
    
    def get_controls(self):
        return (
            auto_stop,
            stop_rep,
            )
class PttDelay(SubCfgFrame):
    text = 'PTT Delay (sec)'
    
    def get_controls(self):
        return (
            _ptt_delay_min,
            _ptt_delay_max
            )
    
    

        
class DetectFailure(SubCfgFrame):
    text = 'Detecting Failed Transmission'   
    
    def get_controls(self):
        return (
            s_thresh,
            s_tries,
            )
        
    
    
    
#controls


class audio_files(shared.audio_files):
    """Audio files to use for testing.
    The cutpoints for the file must exist in the same directory with
    the same name and a .csv extension. If a multiple audio files
    are given, then the test is run in succession for each file."""

class _limited_trials(LabeledControl):
    """When disabled, sets the number of trials to infinite"""
    
    
    MCtrl = ttk.Checkbutton
    do_font_scaling = False
    variable_arg = 'variable'
    previous = '100'
    
    def __init__(self, *args, **kwargs):
        self.MCtrlkwargs = {'text': 'Enable Radio Checks',
                            'command': self.on_button}
        super().__init__(*args, **kwargs)
        
        self.previous = '100'
        
    def on_button(self):
        if self.btnvar.get():
            val = self.previous
        else:
            self.previous = self.master.btnvars['trials'].get()
            val = 'inf'
            
        self.master.btnvars['trials'].set(val)
        
class trials(shared.trials):
    """Number of trials to run before pausing to perform a radio check."""
    
    text = 'Trials between check:'
        
class auto_stop(LabeledControl):
    """Enable checking for access and stopping the test when it is detected."""
    
    MCtrl = ttk.Checkbutton
    MCtrlkwargs = {'text': 'Enable Auto-Stop'}
    variable_arg = 'variable'
    do_font_scaling = False
    
class stop_rep(LabeledControl):
    """Number of times that access must be detected in a row before the
    test is completed."""
    
    text = 'Stop after __ successful:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 1, 'to': 2**15-1}
    
    
class _ptt_delay_min(LabeledControl):
    """The smallest ptt_delay"""
    text = 'Min Delay Time:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class _ptt_delay_max(LabeledControl):
    """The largest ptt_delay. By default, this will be set to the end
    of the first word in the clip."""
    
    text = 'Max Delay Time:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}

class ptt_step(LabeledControl):
    """Time difference in seconds between successive ptt_delays."""
    text = 'Time Increase per Step:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    


class ptt_rep(LabeledControl):
    """Number of times to repeat a given PTT delay value. If auto_stop is
    used, this must be greater than 15."""
    
    text = 'Repeats per Step:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class dev_dly(LabeledControl):
    """Delay in seconds of the audio path with no communication device
    present."""
    
    text = 'Device Delay:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.001}
    

    
class s_thresh(LabeledControl):
    """The threshold of A-weight power for P2, in dB, below which a trial
    is considered to have no audio."""
    
    text = 'Min Allowed Volume:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : -2**15 +1, 'to': 0, 'increment': 1}

class s_tries(LabeledControl):
    """Number of times to retry the test before giving up."""
    
    text = 'Retry Attempts:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 1}


class advanced(shared.advanced):
    toplevel = AccDlyAdvanced













class Access_fromGui(shared.SignalOverride, adly.Access):
    
    def param_check(self):
        
        #change trials from str to int_or_inf
        if self.trials.lower() == 'inf':
            self.trials = adly.np.inf
        else:
            self.trials = int(self.trials)
        
        super().param_check()
    
    def run(self):
        #TODO: implement recovery
        self.test(recovery=False)
    
    
 #TODO:...
     #convert _ptt_delay_* into ptt_delay, and multi-s into vectors
     #convert audio_files into audio_files and audio_path
     #convert time_expand into vectors
     #

    
    
