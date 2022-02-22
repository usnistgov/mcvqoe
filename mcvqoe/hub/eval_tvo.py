# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 11:42:08 2022

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

import mcvqoe.hub.eval_shared as eval_shared

from mcvqoe.hub.eval_app import app

#-----------------------[Begin layout]---------------------------
# TODO: Say something about common thinning fctor if data can't be thined

measurement = 'tvo'
layout = eval_shared.layout_template(measurement)

# --------------[Functions]----------------------------------
def format_tvo_results(tvo_eval, digits=2):
    """
    Format results from tvo.evaluate object to be in nice HTML.

    Parameters
    ----------
    intell_eval : mcvqoe.intelligibility.evaluate
        DESCRIPTION.

    Returns
    -------
    children : html.Div
        DESCRIPTION.

    """
    print(f'Opt keys: {tvo_eval.optimal.keys()}')
    pretty_opt = eval_shared.pretty_numbers(tvo_eval.optimal.loc[0, 'Optimum [dB]'], digits)
    pretty_low = eval_shared.pretty_numbers(tvo_eval.optimal.loc[0, 'Lower_Interval [dB]'], digits)
    pretty_up = eval_shared.pretty_numbers(tvo_eval.optimal.loc[0, 'Upper_Interval [dB]'], digits)
    
    children = html.Div([
        html.H6('Optimum transmit Volume (dB)'),
        html.Div(f'{pretty_opt}'),
        html.H6('Optimum interval (dB)'),
        html.Div(f'{[pretty_low, pretty_up]}')
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
        try:
            json_data = json.loads(jsonified_data)
            if 'error' in json_data:
                error_out = '. '.join(json_data['error'])
                raise RuntimeError(error_out)
            else:
                tvo_eval = eval_shared.load_json_data(jsonified_data, f'{measurement}')
            
            # thinned = thin == 'True'
            if x == 'index':
                x = None
            if talker_select == []:
                talker_select = None
            if session_select == []:
                session_select = None
            
            # TODO: Implement these
            fig_plot = tvo_eval.plot(
                talkers=talker_select,
                x=x,
                color_palette=eval_shared.plotly_color_palette,
                )
            # fig_plot = eval_shared.blank_fig()
            
            filenames = np.unique(tvo_eval.data['Filename'])
            
            talker_options = [{'label': i, 'value': i} for i in filenames]
            
            sessions = tvo_eval.test_name
            session_options = [{'label': i, 'value': i} for i in sessions]
            
            res = format_tvo_results(tvo_eval, meas_digits)
            res_formatting = eval_shared.measurement_digits('grid', meas_digits,
                                                            measurement=measurement)
            return_vals = (
                res,
                res_formatting,
                fig_plot,
                talker_options,
                session_options
                )
        except Exception as e:
            print(e)
            return_vals = eval_shared.failed_process(measurement, msg=e.args)
    else:
        return_vals = eval_shared.failed_process(measurement, )
        
    return return_vals