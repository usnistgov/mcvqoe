# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:50:45 2021

@author: MkZee
"""

import Python_access_time as adly
from mcvqoe.simulation.QoEsim import QoEsim

import tkinter.ttk as ttk

import shared
from shared import LabeledControl, TestCfgFrame, SubCfgFrame
from shared import radioport, audio_files, outdir
from shared import AudioSettings, BgNoise
from shared import Abort_by_User


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
            )
        
    
    
    
#controls


class _limited_trials(LabeledControl):
    
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
    text = 'Trials between check:'
        
class auto_stop(LabeledControl):
    
    MCtrl = ttk.Checkbutton
    MCtrlkwargs = {'text': 'Enable Auto-Stop'}
    variable_arg = 'variable'
    do_font_scaling = False
    
class stop_rep(LabeledControl):
    text = 'Stop after __ successful:'
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
    text = 'Time Between Trials:'
    
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}

class ptt_rep(LabeledControl):
    text = 'Repeats per Step:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class dev_dly(LabeledControl):
    text = 'Device Delay:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.001}
    
class _time_expand_i(LabeledControl):
    text = 'Front Expand:'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'from_' : 0, 'to': 2**15-1, 'increment': 0.01}
    
class _time_expand_f(LabeledControl):
    text = 'Back Expand:'
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













class Access_fromGui(shared.SignalOverride, adly.Access):
    
    def run(self):
        #TODO: implement recovery
        self.test(recovery=False)
    
    
 #TODO:...
     #convert _ptt_delay_* into ptt_delay, and multi-s into vectors
     #convert audio_files into audio_files and audio_path
     #convert time_expand into vectors
     #

    
    
