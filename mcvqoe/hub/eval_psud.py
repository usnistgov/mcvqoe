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
    
    html.H3('PSuD Page'),
    
    dcc.Dropdown(
        id='psud-dropdown',
        options=[
            {'label': f'{i}', 'value': i} for i in [
                'What', 'am', 'I', 'doing'
                ]
            ]
        ),
    html.Div(id='psud-display'),
    dcc.Link('Go to Data Loading', href='/apps/measurement_select')
    ])

@app.callback(
    dash.dependencies.Output('psud-display', 'children'),
    dash.dependencies.Input('psud-dropdown', 'value'))
def display_psud_value(value):
    return f'You have selected {value}'