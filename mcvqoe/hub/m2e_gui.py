# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""

import mcvqoe.mouth2ear.m2e as m2e
import mcvqoe.mouth2ear

from .shared import TestCfgFrame
from .shared import advanced as shared_advanced
from .shared import AdvancedConfigGUI, MultiChoice, SignalOverride, test

import csv
import numpy as np
  
#------------------------------- Controls -------------------------------------

from .shared import audio_files, audio_path
from .shared import BgNoise, SaveAudio, dev_dly
from .shared import trials, ptt_wait, ptt_gap, outdir


class M2EAdvancedConfigGUI(AdvancedConfigGUI):
    text = 'M2E Latency - Advanced'
    
    def get_controls(self):
        return (
            BgNoise,
            )


class advanced(shared_advanced):
    toplevel = M2EAdvancedConfigGUI


# -------------------------- The mouth-to-ear frame ---------------------------

class M2eFrame(TestCfgFrame):
    
    text = 'Mouth-to-Ear Latency Test'
        
    def get_controls(self):
        return (
            audio_files,
            audio_path,
            outdir,
            trials,
            ptt_wait,
            ptt_gap,
            SaveAudio,
            dev_dly,
            test,
            advanced
            )
    

# --------------------- using the m2e measure class ---------------------------

class M2E_fromGui(SignalOverride, m2e.measure):

    def get_mean_and_std(self,name=None):
        
        if( not name):
            name=self.data_filename
        
        with open(name,'rt') as csv_f:
            #create dict reader
            reader=csv.DictReader(csv_f)
            #empty list for M2E data
            m2e_dat=[]
            #
            for row in reader:
                m2e_dat.append(float(row['m2e_latency']))

        #convert to numpy array
        m2e_dat=np.array(m2e_dat)
        
        # Overall mean delay
        ovrl_dly = np.mean(m2e_dat)
        
        # Get standard deviation
        std_delay = np.std(m2e_dat, dtype=np.float64)
        std_delay = std_delay*(1e6)
        
        return ovrl_dly, std_delay
        

class M2E_Eval_from_GUI(SignalOverride, mcvqoe.mouth2ear.evaluate):
    pass


#-----------------------------Dev dly characterization------------------------

class DevDlyCharFrame(M2eFrame):
    
    text = 'Device Delay Characterization'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # disable all parameters except for outdir
        for k, v in self.controls.items():
            if k != 'outdir':
                if hasattr(v, 'm_ctrl'):
                    try:
                        v.m_ctrl['state'] = 'disabled'
                    except: pass
                    
                if hasattr(v, 'r_ctrl'):
                    try:
                        v.r_ctrl.configure(state='disabled')
                    except: pass


# contains the default values for the measurement
class DevChar_Defaults(m2e.measure):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.test     = '1loc'
        self.trials   = 400
        self.ptt_wait = 0.001
        self.ptt_gap  = 0.31
        

class DevChar_fromGui(M2E_fromGui): pass
