# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 16:22:33 2021

@author: MkZee
"""

import mcvqoe.intelligibility as igtiby

import shared
import tkinter.ttk as ttk


#--------------------------Controls-------------------------------------------

from shared import trials, outdir, ptt_wait
from shared import ptt_gap, RadioCheck, SaveAudio


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
    

# ---------------------- The main configuration frame -------------------------

class IgtibyFrame(shared.TestCfgFrame):
    text = 'Intelligibility Test'
    def get_controls(self):
        return (
            outdir,
            trials,
            ptt_wait,
            ptt_gap,
            SaveAudio,
            RadioCheck,
            intell_est,
            )

    
    





# ---------------------- Extending the measure class --------------------------

class Igtiby_from_Gui(shared.SignalOverride, igtiby.measure):
    def param_check(self):
        # future proof
        if hasattr(super(), 'param_check'):
            super().param_check()