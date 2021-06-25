# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""

import m2e_class

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdl

from shared import TestCfgFrame, LabeledControl
import shared


class M2eFrame(TestCfgFrame):
    
    text = 'Mouth-to-Ear Latency Test'
    
    default_test_obj = m2e_class.M2E()
    
    def get_controls(self):
        return (
            test,
            audio_files,
            trials,
            ptt_wait,
            outdir,
            advanced
            
            )
    
    
# TODO: remove this when M2E support multiple audio files
M2eFrame.default_test_obj.audio_files = ''
        
        
        #------------------ Controls ----------------------


class test(shared.MultiChoice):
    """M2E test to perform. Options are: 1 Location (m2e_1loc), 
    2 Location transmit (m2e_2loc_tx), and 2 Location receive (m2e_2loc_rx)."""

    text = 'Location Type:'
    
    association = {
            'm2e_1loc'   : '1 Location',
            'm2e_2loc_tx': '2 Location (transmit)',
            'm2e_2loc_rx': '2 Location (receive)'
            }
    

from shared import audio_files
            
from shared import BgNoise, AudioSettings
            
class audio_file(LabeledControl):
    """NOT USED - use audio_files instead"""
    def on_button(self):
        fp = fdl.askopenfilename(parent=self.master,
                initialfile=self.btnvar.get(),
                filetypes=[('WAV files', '*.wav')])
        if fp:
            self.btnvar.set(fp)
    
    
    text='Audio File:'
    RCtrl = ttk.Button
    RCtrlkwargs = {
        'text'   : 'Browse...'
        }
    
    
from shared import trials, ptt_wait, outdir



class M2EAdvancedConfigGUI(shared.AdvancedConfigGUI):
    text = 'M2E Latency - Advanced'
    
    def get_controls(self):
        return (
            BgNoise,
            AudioSettings,
            )


class advanced(shared.advanced):
    toplevel = M2EAdvancedConfigGUI
























class M2E_fromGui(shared.SignalOverride, m2e_class.M2E):
    
    def run(self):
              
        
        # Run chosen M2E test
        if (self.test == "m2e_1loc"):
            self.m2e_1loc()
        elif (self.test == "m2e_2loc_tx"):
            self.m2e_2loc_tx()
        elif (self.test == "m2e_2loc_rx"):
            self.m2e_2loc_rx()
        else:
            raise ValueError("\nIncorrect test type")
            
        
    
    


