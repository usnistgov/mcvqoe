# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:51:35 2021

@author: jkp4
"""
from dash import dcc
from dash import html
import dash

from mcvqoe.hub.eval_app import app
# from .eval_app import app

layout = html.Div([
    html.H1('MCV QoE Measurements Processing'),
    
    html.H3('Loading Page'),
    
    dcc.Dropdown(
        id='measurement-select-dropdown',
        options=[
            {'label': f'{i}', 'value': i} for i in [
                'Mouth2Ear', 'Access-Time', 'PSuD', 'Intelligibility'
                ]
            ]
        ),
    html.Div(id='measurement-select-display'),
    dcc.Link('Go to PSuD', href='/psud'),
    html.Br(),
    dcc.Link('Go to M2E', href='/m2e'),
    ])

@app.callback(
    dash.dependencies.Output('measurement-select-display', 'children'),
    dash.dependencies.Input('measurement-select-dropdown', 'value'))
def display_value(value):
    return f'You have selected {value}'