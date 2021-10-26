# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 12:26:08 2021

@author: jkp4
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import base64

import json
import io
import tempfile 

from mcvqoe.hub.eval_app import app
# from .eval_app import app
# from mcvqoe.hub.eval_shared import style_data_filename,format_data_filename, mcv_header
import mcvqoe.hub.eval_shared as eval_shared
import mcvqoe.mouth2ear as mouth2ear
import numpy as np
import os
import pandas as pd
import plotly.graph_objects as go

import time

#-----------------------[Begin layout]---------------------------
# TODO: Say something about common thinning fctor if data can't be thined


layout = eval_shared.layout_template('m2e')

def parse_contents(contents, filename):
    """
    Parse contents of uploaded data

    Parameters
    ----------
    contents : TYPE
        DESCRIPTION.
    filename : TYPE
        DESCRIPTION.
    date : TYPE
        DESCRIPTION.

    Returns
    -------
    children : TYPE
        HTML representations of filename or error string.
    df : pd.DataFrame
        Data stored as dataframe.

    """
    content_type, content_string = contents.split(',')
    # print(f'contents: {contents}')
    # print(f'content_type: {content_type}')
    decoded = base64.b64decode(content_string)
    fname, ext = os.path.splitext(filename)
    try:
        if ext == '.csv':
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8'))
                )
                
    except Exception as e:
        print(e)
        children =  html.Div([
            'There was an error processing this file'
            ])
        return children, None
    children = eval_shared.format_data_filename(filename)
    
    return children, df

def load_json_data(jsonified_data):
    """
    Load json data as mouth2ear.evaluate object

    Parameters
    ----------
    jsonified_data : str
        Jsonified dict of jsonified dataframes.

    Returns
    -------
    m2e_eval : mcvqoe.mouth2ear.evaluate
        Evaluate object of all stored data.

    """
    # Parse dict of dataframes
    test_dict = json.loads(jsonified_data)
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Initialize tmpdir
        os.makedirs(os.path.join(tmpdirname, 'csv'))
        outpaths = []
        for test_name in test_dict:
            # Read json of dict element as a dataframe
            test_df = pd.read_json(test_dict[test_name])
            tmpname = os.path.join(tmpdirname, 'csv', test_name)
            # Store temporary file
            test_df.to_csv(tmpname, index=False)
            outpaths.append(tmpname)
        # Load temporary files
        m2e_eval = mouth2ear.evaluate(outpaths)
        return m2e_eval
    
def format_m2e_results(m2e_eval):
    """
    Format results from mouth2ear.evaluate object to be in nice HTML.

    Parameters
    ----------
    m2e_eval : mcvqoe.mouth2ear.evaluate
        DESCRIPTION.

    Returns
    -------
    children : html.Div
        DESCRIPTION.

    """
    children = html.Div([
        html.H6('Mean mouth-to-ear latency'),
        html.Div(f'{m2e_eval.mean} seconds'),
        html.H6('95% Confidence Interval'),
        html.Div(f'{m2e_eval.ci} seconds')
        ],
        style={
            'backgroundColor': '#E5ECF6',
            'width': '50%',
            'borderWidth': '1px',
            'borderStyle': 'sokid',
            'borderRadius': '5px',
            'textAlign': 'left',
            'margin': '10px'
            })
    return children

# --------------[Callback functions (order matters here!)]--------------------
@app.callback(
    Output('output-data-upload', 'children'),
    Output('json-data', 'data'),
    Output('initial-data-passed', 'children'),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    State('initial-data-passed', 'children'),
    State('json-data', 'data'),
    )
def update_output(list_of_contents, list_of_names,
                  initial_data_flag, initial_data):
    """
    Process uploaded data and store csv files as json

    Parameters
    ----------
    list_of_contents : TYPE
        DESCRIPTION.
    list_of_names : TYPE
        DESCRIPTION.
    list_of_dates : TYPE
        DESCRIPTION.

    Returns
    -------
    children : TYPE
        DESCRIPTION.
    final_json : TYPE
        DESCRIPTION.

    """
    # print('sleeping in update_output')
    # print(initial_data_flag)
    if initial_data_flag == 'True':
        final_json = initial_data
        test_dict = json.loads(final_json)
        children = []
        for filename in test_dict:
            children.append(eval_shared.format_data_filename(filename))
        # children = html.Div('I need to do this part')
    else:
        # time.sleep(3)
        if list_of_contents is not None:
            children = []
            dfs = []
            for c, n in zip(list_of_contents, list_of_names):
                child, df = parse_contents(c, n)
                children.append(child)
                dfs.append(df)
            with tempfile.TemporaryDirectory() as tmpdirname:
                    os.makedirs(os.path.join(tmpdirname, 'csv'))
                    
                    out_json = {}
                    for filename, df in zip(list_of_names, dfs):
                        out_json[filename] = df.to_json()
                        
            final_json = json.dumps(out_json)
        else:
            children = None
            final_json = None
        # print(final_json)
    # print(children)
    initial_data_flag = html.Div('False')
    return children, final_json, initial_data_flag

@app.callback(
    Output('measurement-results', 'children'),
    Output('m2e_scatter', 'figure'),
    Output('m2e_hist', 'figure'),
    Output('talker-select', 'options'),
    Output('session-select', 'options'),
    Input('json-data', 'data'),
    Input('thin-select', 'value'),
    Input('talker-select', 'value'),
    Input('session-select', 'value'),
    Input('x-axis', 'value'),
    )
def update_plots(jsonified_data, thin, talker_select, session_select, x):
    """
    Update all plots

    Parameters
    ----------
    jsonified_data : TYPE
        DESCRIPTION.
    thin : TYPE
        DESCRIPTION.
    talker_select : TYPE
        DESCRIPTION.
    session_select : TYPE
        DESCRIPTION.
    x : TYPE
        DESCRIPTION.

    Returns
    -------
    return_vals : TYPE
        DESCRIPTION.

    """
    
    if jsonified_data is not None:
    
        m2e_eval = load_json_data(jsonified_data)
        
        thinned = thin == 'True'
        if x == 'index':
            x = None
        if talker_select == []:
            talker_select = None
        if session_select == []:
            session_select = None
        
        fig_scatter = m2e_eval.plot(
            x=x,
            thinned=thinned,
            talkers=talker_select,
            test_name=session_select,
            )
        fig_histogram = m2e_eval.histogram(
            thinned=thinned,
            talkers=talker_select,
            test_name=session_select,
            )
        
        talkers = np.unique(m2e_eval.data['Filename'])
        talker_options = [{'label': i, 'value': i} for i in talkers]
        
        sessions = m2e_eval.test_names
        session_options = [{'label': i, 'value': i} for i in sessions]
        
        res = format_m2e_results(m2e_eval)
        
        return_vals = (
            res,
            fig_scatter,
            fig_histogram,
            talker_options,
            session_options
            )
        return return_vals
    else:
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        return_vals = (
            html.Div('Mouth-to-ear latency object could not be processed.'),
            eval_shared.blank_fig(),
            eval_shared.blank_fig(),
            none_dropdown,
            none_dropdown
            )
        return return_vals


        