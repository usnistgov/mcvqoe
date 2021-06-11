# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import tkinter.ttk as ttk


from shared import LabeledControl, TestCfgFrame
from shared import audio_files, outdir, ptt_wait, advanced


class AccssDFrame(TestCfgFrame):
    text = 'Access Delay Test'
    
    def get_controls(self):
        return (
            audio_files,
            _ptt_delay_min,
            _ptt_delay_max,
            ptt_step,
            ptt_rep,
            auto_stop,
            stop_rep,
            dev_dly,
            #data_file,
            _time_expand_i,
            _time_expand_f,
            outdir,
            s_thresh,
            s_tries,
            advanced
            )
        
        
        
#controls

class auto_stop(LabeledControl):
    
    text = 'Success Streak behavior:'
    MCtrl = ttk.Checkbutton
    MCtrlkwargs = {'text': 'Stop Test'}
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
    MCtrlkwargs = {'from_' : 0, 'to': 2*15-1, 'increment': 0.01}
    
class dev_dly(LabeledControl):
    text = 'Dev_Dly????'
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
    MCtrlkwargs = {'from_' : -2*15 +1, 'to': 0, 'increment': 1}

class s_tries(LabeledControl):
    text = 'Retry Attempts:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 1}















 #TODO: convert _ptt_delay_* into ptt_delay



