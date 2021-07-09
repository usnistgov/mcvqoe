# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 08:52:09 2021

@author: MkZee
"""

import mcvqoe.mouth2ear.m2e as m2e

import tkinter.ttk as ttk
import tkinter.filedialog as fdl

from shared import TestCfgFrame, LabeledControl
import shared


import csv
from matplotlib.figure import Figure
import numpy as np


class M2eFrame(TestCfgFrame):
    
    text = 'Mouth-to-Ear Latency Test'
        
    def get_controls(self):
        return (
            audio_files,
            _BrowseForFolder,
            outdir,
            trials,
            test,
            ptt_wait,
            advanced
            )
    
            
        
        #------------------ Controls ----------------------
from shared import audio_files, _BrowseForFolder
from shared import BgNoise
from shared import trials, ptt_wait, outdir



class test(shared.MultiChoice):
    """M2E test to perform. Options are: 1 Location (m2e_1loc), 
    2 Location transmit (m2e_2loc_tx), and 2 Location receive (m2e_2loc_rx)."""

    text = 'Location Type:'
    
    association = {
            'm2e_1loc'   : '1 Location',
            'm2e_2loc_tx': '2 Location (transmit)',
            'm2e_2loc_rx': '2 Location (receive)'
            }
    


            
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
    




class M2EAdvancedConfigGUI(shared.AdvancedConfigGUI):
    text = 'M2E Latency - Advanced'
    
    def get_controls(self):
        return (
            BgNoise,
            )


class advanced(shared.advanced):
    toplevel = M2EAdvancedConfigGUI
























class M2E_fromGui(shared.SignalOverride, m2e.measure):
    
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
            
        
    def plot(self,name=None):
        
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
        
        #----------------------------[Generate Plots]------------------------------
        
        # Overall mean delay
        ovrl_dly = np.mean(m2e_dat)
        
        # Get standard deviation
        std_delay = np.std(m2e_dat, dtype=np.float64)
        std_delay = std_delay*(1e6)
        
        # Print StD to terminal
        
        std_msg = "StD: %.2fus" % std_delay
        
        print(std_msg, flush=True)
        
        
        # Create trial scatter plot
        fig1 = Figure()
        a = fig1.add_subplot()
        
        x2 = range(1, len(m2e_dat)+1)
        a.scatter(x2,m2e_dat, color='blue')
        a.set_xlabel("Trial Number")
        a.set_ylabel("Delay(s)")
        
        
        # Create histogram for mean
        fig2 = Figure()
        a = fig2.add_subplot()
        uniq = np.unique(m2e_dat)
        dlymin = np.amin(m2e_dat)
        dlymax = np.amax(m2e_dat)
        a.hist(m2e_dat, bins=len(uniq), range=(dlymin, dlymax), rwidth=0.5)
        fig2.suptitle("Mean: %.5fs" % ovrl_dly)
        a.set_xlabel("Delay(s)")
        a.set_ylabel("Frequency of indicated delay")
        
        
        #show this info in window
        self.gui_show_element(std_msg)
        self.gui_show_element(fig1)
        self.gui_show_element(fig2)


