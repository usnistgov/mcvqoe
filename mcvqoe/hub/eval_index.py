# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:59:05 2021

@author: jkp4
"""
import argparse
import base64
import json
import os
import urllib

import pandas as pd

from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from flask import request

from mcvqoe.hub.eval_app import app
from mcvqoe.hub.eval_shared import style_data_filename

import mcvqoe.hub.eval_intell as intell
import mcvqoe.hub.eval_measurement_select as measurement_select
import mcvqoe.hub.eval_m2e as m2e
import mcvqoe.hub.eval_psud as psud
# from .eval_app import app
# from .apps import measurement_select, psud, m2e

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    ])


def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def format_data(fpaths):
    out_json = {}
    
    for fpath in fpaths:
        fname = os.path.basename(fpath)
        df = pd.read_csv(fpath)
        out_json[fname] = df.to_json()
        
    
    final_json = json.dumps(out_json)
    return final_json

def update_page_data(layout, final_json, measurement):
    """
    Update relevant json-data element and initial data flag
    """
    if final_json is not None:
        for child in layout.children:
            if hasattr(child, 'id'):
                if child.id == f'{measurement}-json-data':
                    child.data = final_json
                elif child.id == f'{measurement}-initial-data-passed':
                    child.children = 'True'
    else:
        for child in layout.children:
            if hasattr(child, 'id'):
                # Act like no data loaded yet
                if child.id == f'{measurement}-initial-data-passed':
                    child.children = 'False'

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    
    pathparts = pathname.split(';')
    test_type = pathparts[0]
    if len(pathparts) > 1:
        # We have data to load
        data_files_url = pathparts[1:]
        data_files = [urllib.request.url2pathname(x) for x in data_files_url]
        final_json = format_data(data_files)
    else:
        final_json = None

    measurement = test_type[1:]
    if test_type == '/psud':
        layout = psud.layout
        
    elif test_type =='/m2e':
        layout = m2e.layout
        # Update relevant layout children
        update_page_data(layout, final_json, measurement)
                
    elif test_type == '/intell':
        layout = intell.layout
    elif test_type == '/measurement_select' or test_type == '/':
        layout = measurement_select.layout
    elif test_type == '/shutdown':
        shutdown()
        layout=html.H3('Successfully shutdown MCV QoE Data App')
    else:
        layout = '404'
    return layout



def main():
    parser = argparse.ArgumentParser(
        description=__doc__
        )
    parser.add_argument('--port',
                        default='8050',
                        type=str,
                        help='Port for dash server')
    
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Run dash server in debug mode')
    args = parser.parse_args()
    
    app.run_server(debug=args.debug,
                   port=args.port)
if __name__ == '__main__':
    main()