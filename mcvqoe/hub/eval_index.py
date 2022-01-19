# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:59:05 2021

@author: jkp4
"""
import argparse
import base64
import importlib
import json
import os
import re
import urllib

import numpy as np
import pandas as pd

from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from flask import request

from mcvqoe.hub.eval_app import app, server
from mcvqoe.hub.eval_shared import style_data_filename

import mcvqoe.hub.eval_intell as intell
import mcvqoe.hub.eval_measurement_select as measurement_select
import mcvqoe.hub.eval_m2e as m2e
import mcvqoe.hub.eval_psud as psud
import mcvqoe.hub.eval_access as access

import mcvqoe.accesstime

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    ])

@server.route('/shutdown_request', methods=["GET"])
def shutdown_request():
    shutdown()
    # As far as I can tell doesn't matter what this returns, just needs to return something that is not None
    return 'shutting down'
    
def shutdown():
    """
    Shutdown the server so users do not have to hit CTRL+C in terminal
    """
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def format_data(fpaths, cutpoint, measurement):
    """
    Load local data and store as single json file with cutpoints if applicable.

    Parameters
    ----------
    fpaths : str
        Local paths to data.
    cutpoint : bool
        Flag for if cutpoints are applicable for this measurement or not.

    Raises
    ------
    RuntimeError
        DESCRIPTION.

    Returns
    -------
    final_json : str
        JSON string representation of all required data for measurement loading.

    """
    # Initialize dictionary for json info
    modules = {'access': 'mcvqoe.accesstime',
               'intell': 'mcvqoe.intelligibility',
               'm2e': 'mcvqoe.mouth2ear',
               'psud': 'mcvqoe.psud',
               }
    try:
        eval_obj = importlib.import_module(modules[measurement]).evaluate(fpaths)
        # eval_obj = eval(modules[measurement]).evaluate(fpaths)
        final_json = eval_obj.to_json()
    except Exception as e:
        out_info = {'test_info': fpaths,
                    'error': e.args,
                    }
        final_json = json.dumps(out_info)

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
    measurement = test_type[1:]
    if len(pathparts) > 1:
        # We have data to load
        data_files_url = pathparts[1:]
        data_files = [urllib.request.url2pathname(x) for x in data_files_url]
        if measurement in ['psud', 'access', 'accesstime']:
            cutpoints = True
        else:
            cutpoints = False
        final_json = format_data(data_files, cutpoints, measurement)
    else:
        final_json = None

    
    if test_type == '/psud':
        layout = psud.layout
        update_page_data(layout, final_json, measurement)
    
    elif test_type in ['/m2e', '/mouth2ear']:
        layout = m2e.layout
        # Update relevant layout children
        update_page_data(layout, final_json, measurement)
                
    elif test_type in ['/intell', '/intelligibility']:
        layout = intell.layout
        update_page_data(layout, final_json, measurement)
        
    elif test_type in ['/access', '/accesstime']:
        layout = access.layout
        update_page_data(layout, final_json, measurement)
        
    elif test_type in ['/measurement_select', '/']:
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