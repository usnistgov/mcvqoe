# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 15:46:41 2021

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
import re
import tempfile 

from mcvqoe.hub.eval_app import app

import mcvqoe.hub.eval_shared as eval_shared
import mcvqoe.psud as psud



#-----------------------[Begin layout]---------------------------
# TODO: Say something about common thinning fctor if data can't be thined

measurement = 'intell'
layout = eval_shared.layout_template(f'{measurement}')

# --------------[Functions]----------------------------------
def format_intell_results(intell_eval, digits=6):
    """
    Format results from intelligibility.evaluate object to be in nice HTML.

    Parameters
    ----------
    intell_eval : mcvqoe.intelligibility.evaluate
        DESCRIPTION.

    Returns
    -------
    children : html.Div
        DESCRIPTION.

    """
    pretty_mean = eval_shared.pretty_numbers(intell_eval.mean, digits)
    pretty_ci = eval_shared.pretty_numbers(intell_eval.ci, digits)
    children = html.Div([
        html.H6('Mean intelligibility (scale of 0-1)'),
        html.Div(f'{pretty_mean}'),
        html.H6('95% Confidence Interval'),
        html.Div(f'{pretty_ci}')
        ],
        style=eval_shared.style_results,
        # className='six columns',
        )
    return children

# --------------[Callback functions (order matters here!)]--------------------
@app.callback(
    Output(f'{measurement}-measurement-results', 'children'),
    Output(f'{measurement}-measurement-formatting', 'children'),
    Output(f'{measurement}-scatter', 'figure'),
    Output(f'{measurement}-hist', 'figure'),
    Output(f'{measurement}-talker-select', 'options'),
    Output(f'{measurement}-session-select', 'options'),
    Input(f'{measurement}-json-data', 'data'),
    Input(f'{measurement}-talker-select', 'value'),
    Input(f'{measurement}-session-select', 'value'),
    Input(f'{measurement}-x-axis', 'value'),
    Input(f'{measurement}-measurement-digits', 'value'),
    )
def update_plots(jsonified_data, talker_select, session_select, x, meas_digits):
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
    
        intell_eval = eval_shared.load_json_data(jsonified_data, f'{measurement}')
        
        # thinned = thin == 'True'
        if x == 'index':
            x = None
        if talker_select == []:
            talker_select = None
        if session_select == []:
            session_select = None
        
        # TODO: Implement these
        fig_scatter = intell_eval.plot(
            x=x,
            talkers=talker_select,
            test_name=session_select,
            )
        fig_histogram = intell_eval.histogram(
            talkers=talker_select,
            test_name=session_select,
            )
        
        
        
        filenames = intell_eval.data['Filename']
        pattern = re.compile(r'([FM]\d)(?:_b\d{1,2}_w\d)')
        talkers = set()
        for fname in filenames:
            res = pattern.search(fname)
            if res is not None:
                talkers.add(res.groups()[0])
        talkers = sorted(talkers)
        talker_options = [{'label': i, 'value': i} for i in talkers]
        
        sessions = intell_eval.test_names
        session_options = [{'label': i, 'value': i} for i in sessions]
        
        res = format_intell_results(intell_eval, meas_digits)
        res_formatting = eval_shared.measurement_digits('grid', meas_digits,
                                                        measurement=measurement)
        
    else:
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        # return_vals = (
        res = html.Div('Intelligibility object could not be processed.')
        res_formatting = eval_shared.measurement_digits('none',
                                                        measurement=measurement)
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