# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 15:59:21 2021

@author: jkp4
"""
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
import json
import numpy as np
import os
import pandas as pd
import tempfile 

from mcvqoe.hub.eval_app import app

import mcvqoe.hub.eval_shared as eval_shared
import mcvqoe.accesstime as access



#-----------------------[Begin layout]---------------------------
# TODO: Say something about common thinning fctor if data can't be thined
measurement = 'access'

layout = eval_shared.layout_template(measurement)

def format_access_results(access_eval,
                        alphas,
                        digits=6,
                        ):
    """
    Format results from access.evaluate object to be in nice HTML.

    Parameters
    ----------
    access_eval : mcvqoe.accesstime.evaluate
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
    for alpha in alphas:
        val, ci = access_eval.eval(alpha)
        intell = alpha * access_eval.fit_data.I0
        res = {
            'Alpha': alpha,
            'Intelligibility': intell,
            'Access Time': eval_shared.pretty_numbers(val, digits),
            'Confidence Lower Bound': eval_shared.pretty_numbers(ci[0], digits),
            'Confidence Upper Bound': eval_shared.pretty_numbers(ci[1], digits),
            }
        results.append(res)
        
    # df_res = pd.DataFrame(results)
        
    # access_v, access_ci = access_eval.eval(0.5, 3)
    # pretty_mean = eval_shared.pretty_numbers(access_v, digits)
    # pretty_ci = eval_shared.pretty_numbers(access_ci, digits)
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
    Output(f'{measurement}-talker-select', 'options'),
    Output(f'{measurement}-session-select', 'options'),
    Input(f'{measurement}-json-data', 'data'),
    Input(f'{measurement}-talker-select', 'value'),
    Input(f'{measurement}-session-select', 'value'),
    Input(f'{measurement}-x-axis', 'value'),
    Input(f'{measurement}-intell-type', 'value'),
    Input(f'{measurement}-alpha', 'value'),
    Input(f'{measurement}-measurement-digits', 'value'),
    )
def update_plots(jsonified_data, talker_select, session_select, x, intell_type,
                 alphas, meas_digits,):
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
        access_eval = eval_shared.load_json_data(jsonified_data, f'{measurement}')
        # thinned = thin == 'True'
        if x == 'index':
            x = None
        if talker_select == []:
            talker_select = None
        if session_select == []:
            session_select = None
        
        # TODO: Implement these
        fig_scatter = eval_shared.blank_fig()
        fig_plot = eval_shared.blank_fig()
        # fig_plot = access_eval.plot()
        # fig_scatter = access_eval.plot_intelligibility(
        #     x=x,
        #     data=intell_type,
        #     talkers=talker_select,
        #     test_name=session_select,
        #     )
        # fig_histogram = access_eval.histogram()
        # fig_histogram = access_eval.histogram(
        #     talkers=talker_select,
        #     test_name=session_select,
        #     )
        
        
        filenames = np.unique(access_eval.data['talker_word'])
        
        talker_options = [{'label': i, 'value': i} for i in filenames]
        
        sessions = access_eval.test_names
        session_options = [{'label': i, 'value': i} for i in sessions]            
        
        if alphas != []:
            res = format_access_results(access_eval,
                                      digits=meas_digits,
                                      alphas=alphas,
                                      )
            res_formatting = eval_shared.measurement_digits('grid', meas_digits,
                                                            measurement=measurement)
        else:
            res = html.Div('Invalid filters selected')
            res_formatting = eval_shared.measurement_digits('none',
                                                            measurement=measurement)
        
    else:
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        # return_vals = (
        res = html.Div('access object could not be processed.')
        res_formatting = eval_shared.measurement_digits('none',
                                                        measurement=measurement)
        fig_plot = eval_shared.blank_fig()
        fig_scatter = eval_shared.blank_fig()
        talker_options = none_dropdown
        session_options = none_dropdown
            # )
    return_vals = (
            res,
            res_formatting,
            fig_plot,
            fig_scatter,
            talker_options,
            session_options
            )
    return return_vals