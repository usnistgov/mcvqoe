# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 16:22:33 2021

@author: MkZee
"""

import mcvqoe.intelligibility as igtiby

import shared


class IgtibyFrame(shared.TestCfgFrame):
    text = 'Intelligibility Test'
    def get_controls(self):
        return (
            audio_files,
            _BrowseForFolder,
            trials,
            ptt_wait,
            ptt_gap,
            intell_est,
            outdir,
            )





#--------------------------Controls-------------------------------------------

from shared import audio_files, _BrowseForFolder, trials, outdir, ptt_wait
from shared import ptt_gap


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







class Igtiby_from_Gui(shared.SignalOverride, igtiby.measure):
    def param_check(self):
        pass