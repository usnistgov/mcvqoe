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
    
    def get_controls(self):
        return (
            test,
            audio_files,
            trials,
            ptt_wait,
            outdir,
            advanced
            
            )
        
        
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
            
from shared import BgNoise, AudioSettings, radioport
            
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
            radioport,
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
    
    
        
        

def run(cnf, is_simulation, pretest,):
    
    o = M2E_fromGui()
    
    cnf['audio_file'] = cnf['audio_files'][0]
    # TODO: The above should change when we implement multiple audio files
    
    
    for k, v in cnf.items():
         if hasattr(o, k):
             setattr(o, k, v)
    
    o.param_check()
     
    # Get start time and date
    time_n_date = m2e_class.datetime.datetime.now().replace(microsecond=0)
    o.info['Tstart'] = time_n_date

    # Add test to info dictionary
    o.info['test'] = o.test
    
    
    
    
    # Open RadioInterface object for testing
    o.ri = m2e_class.RadioInterface(o.radioport)
    # Fill 'Arguments' within info dictionary
    o.info.update(m2e_class.write_log.fill_log(o))



    
    
    # Gather pretest notes and M2E parameters
    o.info.update(pretest(outdir=o.outdir))

    # Write pretest notes and info to tests.log
    m2e_class.write_log.pre(info=o.info)
    
    
    


