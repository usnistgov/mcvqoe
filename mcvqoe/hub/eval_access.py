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

from mcvqoe.hub.eval_app import app

import mcvqoe.hub.eval_shared as eval_shared
import mcvqoe.accesstime as access



#-----------------------[Begin layout]---------------------------
# TODO: Figure out how to handle correction data (non-default)
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

    results = []
    for alpha in alphas:
        val, ci = access_eval.eval(alpha)
        intell = alpha * access_eval.fit_data.I0
        res = {
            'Alpha': alpha,
            'Intelligibility': intell,
            'Access Time [seconds]': eval_shared.pretty_numbers(val, digits),
            'Confidence Lower Bound [seconds]': eval_shared.pretty_numbers(ci[0], digits),
            'Confidence Upper Bound [seconds]': eval_shared.pretty_numbers(ci[1], digits),
            }
        results.append(res)
        

    children = html.Div([
        dash_table.DataTable(
            columns=[{'name': i, 'id': i} for i in results[0].keys()],
            data=results,
            page_action='native',
            page_size=12,
            )
        ],
        style=eval_shared.style_results,
        )
    return children


# --------------[Callback functions (order matters here!)]--------------------
@app.callback(
    Output(f'{measurement}-measurement-results', 'children'),
    Output(f'{measurement}-measurement-formatting', 'children'),
    Output(f'{measurement}-plot', 'figure'),
    Output(f'{measurement}-intell', 'figure'),
    Output(f'{measurement}-talker-select', 'options'),
    Input(f'{measurement}-json-data', 'data'),
    Input(f'{measurement}-talker-select', 'value'),
    Input(f'{measurement}-show-raw', 'value'),
    Input(f'{measurement}-intell-type', 'value'),
    Input(f'{measurement}-sowc', 'value'),
    Input(f'{measurement}-alpha', 'value'),
    Input(f'{measurement}-measurement-digits', 'value'),
    )
def update_plots(jsonified_data, talker_select, show_raw, intell_type, sowc,
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
        
        try:
            # Initialize access eval object
            # access_eval = eval_shared.load_json_data(jsonified_data, f'{measurement}')
            json_data = json.loads(jsonified_data)
            if 'error' in json_data:
                error_out = '. '.join(json_data['error'])
                raise RuntimeError(error_out)
            else:
                access_eval = access.evaluate(json_data=jsonified_data)
            # Translate show_raw, talker_select, intell_type options
            if show_raw == 'True':
                show_raw = True
            elif show_raw == 'False':
                show_raw = False
    
            if talker_select == []:
                talker_select = None
                
            if intell_type == 'intelligibility':
                raw_intell = True
            else:
                raw_intell = False
            
            if sowc == 'True':
                fit_type = 'COR'
            else:
                fit_type = 'NoCOR'
            # Make access plot
            fig_plot = access_eval.plot(raw_intell=raw_intell,
                                        talkers=talker_select,
                                        fit_type=fit_type,
                                        )
            # Make intell plot
            fig_intell = access_eval.plot_intell(talkers=talker_select,
                                                 show_raw=show_raw,
                                                 fit_type=fit_type,
                                                 color_palette=eval_shared.plotly_color_palette,
                                                 )
            
            # Get talker word combos
            filenames = np.unique(access_eval.data['talker_word'])
            # Initialize dropdown options
            talker_options = [{'label': i, 'value': i} for i in filenames]
            
            # Format table results
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
            return_vals = (
                res,
                res_formatting,
                fig_plot,
                fig_intell,
                talker_options,
                )
        except Exception as e:
            print(e)
            return_vals = eval_shared.failed_process(measurement, msg=e.args)
        
        
    else:
        return_vals = eval_shared.failed_process(measurement, )
    
    return return_vals