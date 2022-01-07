# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 12:26:08 2021

@author: jkp4
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash import dash_table
import base64
import io
import itertools
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

measurement = 'psud'
layout = eval_shared.layout_template(measurement)

# TODO: PSuD needs radio check buttons for:
    # AMI vs EWC
    # Message Length
    # Intelligibility threshold
    # Display results in a table
# --------------[Functions]----------------------------------
def format_psud_results(psud_eval,
                        thresholds,
                        message_lengths,
                        methods,
                        digits=6,
                        ):
    """
    Format results from psud.evaluate object to be in nice HTML.

    Parameters
    ----------
    psud_eval : mcvqoe.psud.evaluate
        DESCRIPTION.

    Returns
    -------
    children : html.Div
        DESCRIPTION.

    """
    # TODO: Make these controllable at top
    # thresholds = [0.5, 0.7]
    # message_lengths = [1, 3, 5, 10]
    # methods = ['EWC', 'AMI']

    results = []
    for method, thresh, msg_len, in itertools.product(methods, thresholds, message_lengths):
        val, ci = psud_eval.eval(thresh, msg_len, method=method)
        res = {
            'Method': method,
            'Intelligibility Threshold': thresh,
            'Message Length (s)': msg_len,
            'PSuD': eval_shared.pretty_numbers(val, digits),
            'Confidence Lower Bound': eval_shared.pretty_numbers(ci[0], digits),
            'Confidence Upper Bound': eval_shared.pretty_numbers(ci[1], digits),
            }
        results.append(res)
        
    # df_res = pd.DataFrame(results)
        
    # psud_v, psud_ci = psud_eval.eval(0.5, 3)
    # pretty_mean = eval_shared.pretty_numbers(psud_v, digits)
    # pretty_ci = eval_shared.pretty_numbers(psud_ci, digits)
    children = html.Div([
        dash_table.DataTable(
            columns=[{'name': i, 'id': i} for i in results[0].keys()],
            data=results,
            page_action='native',
            page_size=12,
            )
        # html.H6('Probability of successful delivery (scale of 0-1)'),
        # html.Div(f'{pretty_mean}'),
        # html.H6('95% Confidence Interval'),
        # html.Div(f'{pretty_ci}')
        ],
        style=eval_shared.style_results,
        # className='six columns',
        )
    return children

# --------------[Callback functions (order matters here!)]--------------------
@app.callback(
    Output(f'{measurement}-measurement-results', 'children'),
    Output(f'{measurement}-measurement-formatting', 'children'),
    Output(f'{measurement}-plot', 'figure'),
    Output(f'{measurement}-scatter', 'figure'),
    Output(f'{measurement}-hist', 'figure'),
    Output(f'{measurement}-talker-select', 'options'),
    Output(f'{measurement}-session-select', 'options'),
    Input(f'{measurement}-json-data', 'data'),
    Input(f'{measurement}-talker-select', 'value'),
    Input(f'{measurement}-session-select', 'value'),
    Input(f'{measurement}-x-axis', 'value'),
    Input(f'{measurement}-intell-type', 'value'),
    Input(f'{measurement}-measurement-digits', 'value'),
    Input(f'{measurement}-method', 'value'),
    Input(f'{measurement}-intelligibility-threshold', 'value'),
    Input(f'{measurement}-message-length', 'value'),
    )
def update_plots(jsonified_data, talker_select, session_select, x, intell_type,
                 meas_digits, method, threshold, message_length):
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
        try:
            json_data = json.loads(jsonified_data)
            if 'error' in json_data:
                error_out = '. '.join(json_data['error'])
                raise RuntimeError(error_out)
            else:
                psud_eval = eval_shared.load_json_data(jsonified_data, f'{measurement}')
            # thinned = thin == 'True'
            if x == 'index':
                x = None
            if talker_select == []:
                talker_select = None
            if session_select == []:
                session_select = None
            
            # TODO: Implement these
            # fig_scatter = eval_shared.blank_fig()
            fig_histogram = eval_shared.blank_fig()
            fig_plot = psud_eval.plot(methods=method,
                                           thresholds=threshold,
                                           )
            fig_scatter = psud_eval.plot_intelligibility(
                x=x,
                data=intell_type,
                talkers=talker_select,
                test_name=session_select,
                )
            fig_histogram = psud_eval.histogram()
            # fig_histogram = psud_eval.histogram(
            #     talkers=talker_select,
            #     test_name=session_select,
            #     )
            
            
            
            filenames = psud_eval.data['Filename']
            pattern = re.compile(r'([FM]\d)(?:_n\d+_s\d+_c\d+)')
            talkers = set()
            for fname in filenames:
                res = pattern.search(fname)
                if res is not None:
                    talkers.add(res.groups()[0])
            talkers = sorted(talkers)
            talker_options = [{'label': i, 'value': i} for i in talkers]
            
            sessions = psud_eval.test_names
            session_options = [{'label': i, 'value': i} for i in sessions]            
            
            if method != [] and threshold != [] and message_length != []:
                res = format_psud_results(psud_eval,
                                          digits=meas_digits,
                                          methods=method,
                                          thresholds=threshold,
                                          message_lengths=message_length,
                                          )
                res_formatting = eval_shared.measurement_digits('grid', meas_digits,
                                                                measurement=measurement)
            else:
                res = html.Div('Invalid filters selected')
                res_formatting = eval_shared.measurement_digits('none',
                                                                measurement=measurement)
            return_vals = (
                res,
                res_formatting,
                fig_plot,
                fig_scatter,
                fig_histogram,
                talker_options,
                session_options
                )
        except Exception as e:
            print(e)
            return_vals = eval_shared.failed_process(measurement, msg=e.args)
        
    else:
        return_vals = eval_shared.failed_process(measurement, )
    return return_vals