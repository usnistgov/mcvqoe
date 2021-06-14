# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""

import m2e_class
from mcvqoe.simulation.QoEsim import QoEsim

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as fdl

from shared import PADX, PADY, TestCfgFrame, LabeledControl
import shared


class M2eFrame(TestCfgFrame):
    
    text = 'Mouth-to-Ear Latency Test'
    
    def get_controls(self):
        return (
            test,
            audio_files,
            trials,
            ptt_wait,
            overplay,
            outdir,
            advanced
            
            )
        
        
        #------------------ Controls ----------------------


class _test(tk.Frame):
    def __init__(self, *args, textvariable, **kwargs):
        
        # tk.frame does not accept font settings
        if 'font' in kwargs:
            del kwargs['font']
        
        super().__init__(*args, **kwargs)
        
        assoc = {
            'm2e_1loc'   : '1 Location',
            'm2e_2loc_tx': '2 Location (transmit)',
            'm2e_2loc_rx': '2 Location (receive)'
            }
        
        #initialize
        for val, text in assoc.items():
            ttk.Radiobutton(self, variable=textvariable, value=val,
                text=text).pack(fill=tk.X)

class test(LabeledControl):
    text = 'Location Type:'
    MCtrl = _test
    

from shared import audio_files
            
            
class audio_file(LabeledControl):
    
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
    
    
from shared import trials, ptt_wait, outdir, advanced

class overplay(LabeledControl):
    text='Overplay Time (sec):'
    MCtrl = ttk.Spinbox
    MCtrlkwargs = {'increment':0.01, 'from_':0, 'to':2**15 -1}


class M2EAdvancedConfigGUI(shared.AdvancedConfigGUI):
    
    
    def get_controls(self):
        return (
            BgNoise,
            AudioSettings,
            radioport,
            )





class M2E_fromGui(m2e_class.M2E):
    
    def sig_handler(self, *args, **kwargs):
        #override signal's ability to close the application
        post_dict = m2e_class.test_info_gui.post_test()
        m2e_class.write_log.post(info=post_dict, outdir=self.outdir)
        raise shared.CtrlC_Stop()

def run(cnf, is_simulation):
    # override test_info_gui's ability to close all tkinter windows
    m2e_class.test_info_gui.TestInfoGui.quit = lambda s=None : None
    m2e_class.test_info_gui.PostTestGui.quit = lambda s=None : None
    
    
    
    
     
    o = M2E_fromGui()
    
    cnf['audio_file'] = cnf['audio_files'].split(', ')[0]
    ToDo = '' # The above should change when we implement multiple audio files
    
    for k, v in cnf.items():
         if hasattr(o, k):
             setattr(o, k, v)
     
    o.param_check()
     
    # Get start time and date
    time_n_date = m2e_class.datetime.datetime.now().replace(microsecond=0)
    o.info['Tstart'] = time_n_date

    # Add test to info dictionary
    o.info['test'] = o.test
    
    
    
    if is_simulation:
        sim = QoEsim()
        def get_sim(*args, **kwargs):
            return sim
        
        #override these to simulate them
        m2e_class.RadioInterface = get_sim
        m2e_class.AudioPlayer = get_sim
    
    # Open RadioInterface object for testing
    o.ri = m2e_class.RadioInterface(o.radioport)
    # Fill 'Arguments' within info dictionary
    o.info.update(m2e_class.write_log.fill_log(o))



    
    
    # Gather pretest notes and M2E parameters
    o.info.update(m2e_class.test_info_gui.pretest(outdir=o.outdir))

    # Write pretest notes and info to tests.log
    m2e_class.write_log.pre(info=o.info)
    
    # Run chosen M2E test
    if (o.test == "m2e_1loc"):
        o.m2e_1loc()
    elif (o.test == "m2e_2loc_tx"):
        o.m2e_2loc_tx()
    elif (o.test == "m2e_2loc_rx"):
        o.m2e_2loc_rx()
    else:
        raise ValueError("\nIncorrect test type")
    
    # Gather posttest notes and write to log
    post_dict = m2e_class.test_info_gui.post_test()
    m2e_class.write_log.post(info=post_dict, outdir=o.outdir)
    
    
     
     
     
     
     
     
class _QoEsim_Override(QoEsim):
    """ONLY TEMPORARY: makes QoEsim accept filename instead of positional
    
    """
    def play_record(*args, **kwargs):
        if 'filename' in kwargs:
            kwargs['out_name'] = kwargs['filename']
            del kwargs['filename']
        super().play_record(*args, **kwargs)
     

from shared import BgNoise, AudioSettings, radioport

