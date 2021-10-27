# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 12:26:08 2021

@author: jkp4
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import json
import numpy as np
import os
import pandas as pd
import tempfile 

from mcvqoe.hub.eval_app import app

import mcvqoe.hub.eval_shared as eval_shared



#-----------------------[Begin layout]---------------------------
# TODO: Say something about common thinning fctor if data can't be thined


layout = eval_shared.layout_template('m2e')

    
def format_m2e_results(m2e_eval, digits=6):
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
    pretty_mean = eval_shared.pretty_numbers(m2e_eval.mean, digits)
    pretty_ci = eval_shared.pretty_numbers(m2e_eval.ci, digits)
    children = html.Div([
        html.H6('Mean mouth-to-ear latency'),
        html.Div(f'{pretty_mean} seconds'),
        html.H6('95% Confidence Interval'),
        html.Div(f'{pretty_ci} seconds')
        ],
        style=eval_shared.style_results,
        # className='six columns',
        )
    return children

# --------------[Callback functions (order matters here!)]--------------------
@app.callback(
    Output('m2e-output-data-upload', 'children'),
    Output('m2e-json-data', 'data'),
    Output('m2e-initial-data-passed', 'children'),
    Input('m2e-upload-data', 'contents'),
    Input('m2e-upload-data', 'filename'),
    State('m2e-initial-data-passed', 'children'),
    State('m2e-json-data', 'data'),
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
                child, df = eval_shared.parse_contents(c, n)
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
    initial_data_flag = html.Div('False')
    return children, final_json, initial_data_flag

@app.callback(
    Output('m2e-measurement-results', 'children'),
    Output('m2e-measurement-formatting', 'children'),
    Output('m2e-scatter', 'figure'),
    Output('m2e-hist', 'figure'),
    Output('m2e-talker-select', 'options'),
    Output('m2e-session-select', 'options'),
    Input('m2e-json-data', 'data'),
    Input('m2e-thin-select', 'value'),
    Input('m2e-talker-select', 'value'),
    Input('m2e-session-select', 'value'),
    Input('m2e-x-axis', 'value'),
    Input('m2e-measurement-digits', 'value'),
    )
def update_plots(jsonified_data, thin, talker_select, session_select, x, meas_digits):
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
    
        m2e_eval = eval_shared.load_json_data(jsonified_data, 'm2e')
        
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
        
        res = format_m2e_results(m2e_eval, meas_digits)
        res_formatting = eval_shared.measurement_digits('grid', meas_digits,
                                                        measurement='m2e')
        
    else:
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        # return_vals = (
        res = html.Div('Mouth-to-ear latency object could not be processed.')
        res_formatting = eval_shared.measurement_digits('none',
                                                        measurement='m2e')
        fig_scatter = eval_shared.blank_fig()
        fig_histogram = eval_shared.blank_fig()
        talker_options = none_dropdown
        session_options = none_dropdown
            # )
    return_vals = (
            res,
            res_formatting,
            fig_scatter,
            fig_histogram,
            talker_options,
            session_options
            )
    return return_vals
        


        