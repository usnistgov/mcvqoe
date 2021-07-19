# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import os

import mcvqoe.accesstime as adly

import tkinter as tk
import tkinter.ttk as ttk

import shared
from shared import LabeledControl, TestCfgFrame, SubCfgFrame
from shared import outdir, ptt_gap, time_expand
from shared import BgNoise

from shared import Abort_by_User, InvalidParameter
import loadandsave


class AccssDFrame(TestCfgFrame):
    text = 'Access Delay Test'
    
    
    def get_controls(self):
        return (
            audio_files,
            outdir,
            ptt_step,
            ptt_rep,
            ptt_gap,
            dev_dly,
            RadioCheck,
            AutoStop,
            ptt_delay,
            data_file,
            advanced
            )
    
class AccDlyAdvanced(shared.AdvancedConfigGUI):
    text = 'Access Delay - Advanced'
    
    def get_controls(self):
        return (
            BgNoise,
            DetectFailure,
            time_expand,
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
    

    

        
class DetectFailure(SubCfgFrame):
    text = 'Detecting Failed Transmission'   
    
    def get_controls(self):
        return (
            s_thresh,
            s_tries,
            )
        
    
    
 
    
    
    
    
    
    
    
    
#------------------------------controls--------------------------------------
from shared import dev_dly

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
    
    def __init__(self, master, row, *args, **kwargs):
        self.MCtrlkwargs = {'text': 'Enable Radio Checks',}
                
        self.btnvar = tk.BooleanVar()
        
        super().__init__(master, row, *args, **kwargs)
        
        self.btnvar.trace_add('write', self.on_button)
        self.master.btnvars['trials'].trace_add('write', self.update)
        self.update()
        
        
    def on_button(self, *args, **kwargs):
        if self.btnvar.get():
            val = self.previous
        else:
            val = 'inf'
            
        self.master.btnvars['trials'].set(val)
    
    def update(self, *args, **kwargs):
        
        v = self.master.btnvars['trials'].get()
        
        other = v != 'inf'
        this = self.btnvar.get()
        
        if other:
            self.previous = v
            
        if other != this:
            self.btnvar.set(other)
        
        
        
    
        
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
    
    
    
    
    
    
    
class ptt_delay(SubCfgFrame):
    text = 'PTT Delay (sec)'
    
    variable_type = loadandsave.Vec1Or2Var
    
    def get_controls(self):
        return (
            _ptt_delay_min,
            _ptt_delay_max
            )
    
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
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 1}
    
  

    
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
    
    
class data_file(LabeledControl):
    """A temporary datafile to use to restart a test. If this is
    given all other parameters are ignored and the settings of the original
    test are used."""
    
    text = 'Recovery File:'
    
    RCtrl = ttk.Button
    RCtrlkwargs = {'text': 'Browse...'}
    
    def on_button(self):
        
        outdir = self.master.btnvars['outdir'].get()
        recovery = os.path.join(outdir,'data', 'recovery')
        
        fp = tk.filedialog.askopenfilename(initialdir=recovery)
        if fp:
            self.btnvar.set(fp)


class advanced(shared.advanced):
    toplevel = AccDlyAdvanced













class Access_fromGui(shared.SignalOverride, adly.measure):
   

    def run(self):
        self.test(recovery=False)
        #TODO: implement recovery
    



