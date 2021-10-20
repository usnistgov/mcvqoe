# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:59:05 2021

@author: jkp4
"""
import argparse
import base64
import json
import os

import pandas as pd

from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from flask import request

from mcvqoe.hub.eval_app import app
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
    return children, final_json

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    global app
    print(f'First Load: {app.first_load}')
    
    has_data = (app.test_type is not None) and (app.test_files != [])
    if app.first_load and has_data:
        fpaths = app.test_files
        pathname = '/' + app.test_type
    else:
        fpaths = None
    app.first_load = False
    print(pathname)
    if pathname == '/psud':
        return psud.layout
    elif pathname =='/m2e':
        layout = m2e.layout
        if fpaths is not None:
            children, final_json = format_data(fpaths)
            layout.children[0].data = final_json
            layout.children[4].children = children
            
            layout.children[5].children = 'True'
        
        return layout
        # return m2e.layout
    elif pathname == '/measurement_select' or pathname == '/':
        return measurement_select.layout
    elif pathname == '/shutdown':
        # TODO: Figure out if we can show people something acknowledging they quit
        shutdown()
    else:
        return '404'
        # return measurement_select.layout



def main():
    global app
    parser = argparse.ArgumentParser(
        description=__doc__
        )
    parser.add_argument('--port',
                        default='8050',
                        type=str,
                        help='Port for dash server')
    parser.add_argument('--test-type',
                        default=None,
                        type=str,
                        help='Test type, one of {m2e, access, intell, or psud}'
                        )
    parser.add_argument('--test-files',
                        type=str,
                        nargs="+",
                        action="extend",
                        help="Files to process, absolute paths")
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Run dash server in debug mode')
    args = parser.parse_args()
    
    
    app.test_type = args.test_type
    app.test_files = args.test_files
    
    app.first_load = True
    app.run_server(debug=args.debug,
                   port=args.port)
if __name__ == '__main__':
    main()