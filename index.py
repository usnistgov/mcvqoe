# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:59:05 2021

@author: jkp4
"""
import base64
import json
import os

import pandas as pd

from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from app import app
from apps import measurement_select, psud, m2e

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
    ])

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/apps/psud':
        return psud.layout
    elif pathname =='/apps/m2e':
        layout = m2e.layout
        
        fpaths = ['../mouth2ear-internal/data/csv/capture_AD-QoE-Board-Validation_04-Oct-2021_09-19-43.csv',
                  '../mouth2ear-internal/data/csv/capture_QoE board baseline_21-Sep-2021_15-09-04.csv',
                  ]
        out_json = {}
        children = []
        for fpath in fpaths:
            fname = os.path.basename(fpath)
            df = pd.read_csv(fpath)
            out_json[fname] = df.to_json()
            
            child = html.Div([
                html.Div(fname),
                ])
            children.append(child)
        
        final_json = json.dumps(out_json)
        layout.children[0].data = final_json
        layout.children[4].children = children
        
        layout.children[5].children = 'True'
        
        return layout
        # return m2e.layout
    elif pathname == '/apps/measurement_select':
        
        return measurement_select.layout
    else:
        
        # return '404'
        return measurement_select.layout

if __name__ == '__main__':
    app.run_server(debug=True)