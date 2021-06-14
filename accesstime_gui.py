# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import tkinter.ttk as ttk

import shared
from shared import LabeledControl, TestCfgFrame, SubCfgFrame
from shared import radioport, audio_files, outdir

global _trials_control_btn


class AccssDFrame(TestCfgFrame):
    text = 'Access Delay Test'
    
    def get_controls(self):
        return (
            _limited_trials,
            trials,
            audio_files,
            PttDelay,
            ptt_step,
            ptt_rep,
            #data_file,
            outdir,
            advanced
            )
    
class AccDlyAdvanced(shared.AdvancedConfigGUI):
    text = 'Access Delay - Advanced'
    
    def get_controls(self):
        return (
            DetectFailure,
            TimeExpand,
            dev_dly,
            radioport
            )
    
    
    
class PttDelay(SubCfgFrame):
    text = 'PTT Delay (sec)'
    
    def get_controls(self):
        return (
            _ptt_delay_min,
            _ptt_delay_max
            )
    
    
class TimeExpand(SubCfgFrame):
    text = 'Time Expand'
    
    def get_controls(self):
        return (
            _time_expand_i,
            _time_expand_f,
            )
        
class DetectFailure(SubCfgFrame):
    text = 'Detecting Failed Transmission'   
    
    def get_controls(self):
        return (
            s_thresh,
            s_tries,
            auto_stop,
            stop_rep,
            )
        
    
    
    
#controls


class _limited_trials(LabeledControl):
    
    MCtrl = ttk.Checkbutton
    do_font_scaling = False
    variable_arg = 'variable'
    previous = '100'
    
    def __init__(self, *args, **kwargs):
        self.MCtrlkwargs = {'text': 'Limit Trials',
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
    pass
        
class auto_stop(LabeledControl):
    
    text = 'Success Streak behavior:'
    MCtrl = ttk.Checkbutton
    MCtrlkwargs = {'text': 'Auto Stop Test'}
    variable_arg = 'variable'
    do_font_scaling = False
    
class stop_rep(LabeledControl):
    text = 'Streak Length:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 1, 'to': 2**15-1}
    
    
class _ptt_delay_min(LabeledControl):
    text = 'Min Delay Time:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class _ptt_delay_max(LabeledControl):
    text = 'Max Delay Time:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}

class ptt_step(LabeledControl):
    text = 'Time Increase per Step:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class ptt_gap(LabeledControl):
    text = 'Pause Between Transmitions:'
    
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}

class ptt_rep(LabeledControl):
    text = '# of Trials per Step:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class dev_dly(LabeledControl):
    text = 'Device Delay:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.001}
    
class _time_expand_i(LabeledControl):
    text = 'Before Transmission:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class _time_expand_f(LabeledControl):
    text = 'After Transmission:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class s_thresh(LabeledControl):
    text = 'Min Allowed Volume (db):'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : -2**15 +1, 'to': 0, 'increment': 1}

class s_tries(LabeledControl):
    text = 'Retry Attempts:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 1}


class advanced(shared.advanced):
    toplevel = AccDlyAdvanced












 #TODO: convert _ptt_delay_* into ptt_delay, and multi-s into vectors


