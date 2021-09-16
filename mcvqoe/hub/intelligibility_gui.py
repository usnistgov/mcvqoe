# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 16:22:33 2021

@author: MkZee
"""

import mcvqoe.intelligibility as igtiby

import tkinter.ttk as ttk

from .shared import LabeledSlider, TestCfgFrame, SignalOverride, MultiChoice
from .shared import advanced as shared_advanced

#--------------------------Controls-------------------------------------------

from .shared import trials, outdir, ptt_wait
from .shared import ptt_gap, RadioCheck, SaveAudio


class intell_est(MultiChoice):
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

class intell_trials(trials):
    """
Estimated errors and test time for different number of tests.

Simulations will run faster than estimated times.

N	RMS Deviation	Maximum Absolute Deviation	Estimated Test Time
16	    0.017	           0.053	            1.75 minutes
32	    0.009	           0.033                    3.5 minutes
64	    0.005	           0.014	            7 minutes
128	    0.003	           0.008	            14 minutes
256	    0.002	           0.004                    28 minutes
512         0.001                  0.002	            56 minutes
1200        0.000                  0.000	            131 minutes
"""
    __doc__ = trials.__doc__ + __doc__
# ---------------------- The main configuration frame -------------------------

class IgtibyFrame(TestCfgFrame):
    text = 'Intelligibility Test'
    def get_controls(self):
        return (
            outdir,
            intell_trials,
            ptt_wait,
            ptt_gap,
            SaveAudio,
            RadioCheck,
            intell_est,
            )

# ---------------------- Extending the measure class --------------------------

class Igtiby_from_Gui(SignalOverride, igtiby.measure):
    def param_check(self):
        # future proof
        if hasattr(super(), 'param_check'):
            super().param_check()