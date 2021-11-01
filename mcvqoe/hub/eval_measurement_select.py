# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:51:35 2021

@author: jkp4
"""
from dash import dcc
from dash import html
import dash

from mcvqoe.hub.eval_app import app
import mcvqoe.hub.eval_shared as eval_shared
# from .eval_app import app

layout = html.Div([
    html.H1('MCV QoE Measurements Processing'),
    
    html.H3('Select a measurement:'),
    
    dcc.Link('Access delay', href='/access',
             style=eval_shared.style_links,
             ),
    html.Br(),
    
    dcc.Link('Intelligibility', href='/intell',
             style=eval_shared.style_links,
             ),
    html.Br(),
    
    dcc.Link('Mouth-to-ear latency', href='/m2e',
             style=eval_shared.style_links,
             ),
    html.Br(),

    dcc.Link('Probability of Successful Delivery', href='/psud',
             style=eval_shared.style_links,
             ),
    html.Br(),
    
    html.Hr(),
    dcc.Link('Shutdown', href='shutdown',
             style=eval_shared.style_links,
             ),
    ])