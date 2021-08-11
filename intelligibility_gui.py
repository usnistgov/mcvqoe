# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 16:22:33 2021

@author: MkZee
"""

import mcvqoe.intelligibility as igtiby

import shared
import tkinter.ttk as ttk


class IgtibyFrame(shared.TestCfgFrame):
    text = 'Intelligibility Test'
    def get_controls(self):
        return (
            outdir,
            trials,
            ptt_wait,
            ptt_gap,
            RadioCheck,
            intell_est,
            save_tx_audio,
            )





#--------------------------Controls-------------------------------------------

from shared import trials, outdir, ptt_wait
from shared import ptt_gap, RadioCheck


class intell_est(shared.MultiChoice):
    """Control when, and how, intelligibility and mouth to ear estimations are
        done.
        
        During Test:
            Compute intelligibility estimation for audio at end of each trial
        After Test:
            Compute intelligibility on audio after test is complete
        Never:
            don't compute intelligibility for audio
            
    """
    
    text = 'Compute Intelligibility:'
    association = {'trial': 'During Test',
                   'aggregate': 'After Test',
                   'none': 'Never',
                   }
    
class save_tx_audio(shared.LabeledControl):
    
    MCtrl = ttk.Checkbutton
    MCtrlkwargs = {'text': 'Save Transmitted Audio'}
    
    variable_arg = 'variable'
    
    do_font_scaling = False
    
    
    
    







class Igtiby_from_Gui(shared.SignalOverride, igtiby.measure):
    def param_check(self):
        pass