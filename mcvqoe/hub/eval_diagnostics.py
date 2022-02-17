# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 08:20:53 2021

@author: cjg2
"""
from dash import dash_table
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

measurement = 'diagnostics'
layout = eval_shared.layout_template(measurement)

def format_diagnostic_results(diag_eval, digits=4):
    """
    Format results from Test_Stats to be in HTML.

    Parameters
    ----------
    diagnostics_eval : 
        DESCRIPTION.

    Returns
    -------
    children : html.Div
        DESCRIPTION.
    """
    df = diag_eval.data
    df.insert(0, 'Trial', df.index + 1)
    
    flagged = df.loc[(df['AW_flag'] == 1) | (df['FSF_flag'] == 1) | (df['Clip_flag'] == 1)]
    
    results = flagged.to_dict(orient='records')
    if len(results) == 0:
        children = [
            html.H3('Flagged Trials'),
            html.P('No flagged trials detected'),
            ]
        
    else:
        children = [
            html.H3('Flagged Trials'),
            html.Div([
            dash_table.DataTable(
                columns=[{'name': i, 'id': i} for i in results[0].keys()],
                data=results,
                page_action='native',
                page_size=12,
                )
            ],
            style=eval_shared.style_results,
            )
            ]
   
 
    return children
    
@app.callback(
    Output(f'{measurement}-measurement-results', 'children'),
    Output(f'{measurement}-measurement-formatting', 'children'),
    Output(f'{measurement}-aweight', 'figure'),
    Output(f'{measurement}-peak', 'figure'),
    Output(f'{measurement}-fsf', 'figure'),
    Input(f'{measurement}-json-data', 'data'),
    Input(f'{measurement}-measurement-digits', 'value'),
    )
def update_plots(jsonified_data,
                 meas_digits,):
    """
    Update all output and plots

    Parameters
    ----------
    jsonified_data : TYPE
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
                diag_eval = eval_shared.load_json_data(jsonified_data, f'{measurement}')

            fig_aweight = diag_eval.aw_plot()
            fig_peak = diag_eval.peak_dbfs_plot()
            fig_fsf = diag_eval.fsf_plot()
            
            res = format_diagnostic_results(diag_eval, digits=meas_digits)
            res_formatting = eval_shared.measurement_digits('grid', meas_digits,
                                                            measurement=measurement)
            
            return_vals = (
                res,
                res_formatting,
                fig_aweight,
                fig_peak,
                fig_fsf,
                )
        except Exception as e:
            print(e)
            return_vals = eval_shared.failed_process(measurement, msg=e.args)
        
    else:
        return_vals = eval_shared.failed_process(measurement, )
    return return_vals