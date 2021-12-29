# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 15:59:21 2021

@author: jkp4
"""
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 12:26:08 2021

@author: jkp4
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import base64
import io
import json
import numpy as np
import os
import pandas as pd
import tempfile 

from mcvqoe.hub.eval_app import app

import mcvqoe.hub.eval_shared as eval_shared
import mcvqoe.psud as psud



#-----------------------[Begin layout]---------------------------
# TODO: Say something about common thinning fctor if data can't be thined


layout = eval_shared.layout_template('access')

