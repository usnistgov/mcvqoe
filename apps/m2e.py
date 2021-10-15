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

from app import app

import mcvqoe.mouth2ear as mouth2ear
import numpy as np
import os
import pandas as pd
import plotly.graph_objects as go

import time

def blank_fig():
    """
    Make a blank plotly figure for a placeholder prior to data load
    """
    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None)
    fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
    fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    
    return fig

# --------------------[Define Styles]----------------------
# TODO: These should probably move somewhere more general and be imported
radio_button_style = {'width': '15%', 'display': 'inline-block'}
dropdown_style = {'width': '45%', 'display': 'inline-block'}

#-----------------------[Begin layout]---------------------------
layout = html.Div([
    # TODO: This should probably be local or session
    # Element to store json representations of data
    dcc.Store(id='json-data',
              storage_type='memory',
              ),
    html.H1('MCV QoE Measurements Processing'),
    
    html.H3('Mouth-to-ear latency data analysis'),
    #--------------[Upload Data]------------------------------
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and drop or ',
            html.A('Select Files')
            ]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
            },
        multiple=True
        ),
    html.Div(id='output-data-upload'),
    html.Div('False',
             id='initial-data-passed'),
    html.Div(id='m2e-results'),
    # ----------------[Dropdowns]------------------
    html.Div([
        html.Label('Session Select'),
        dcc.Dropdown(
            id='session-select',
            multi=True
            )
        ], style=dropdown_style),
    html.Div([
        html.Label('Talker Select'),
        dcc.Dropdown(
            id='talker-select',
            multi=True,
            )
        ], style=dropdown_style),
    # --------------------[Radio Button Filtering]--------------------------
    html.Div([
        html.Label('Data thinning'),
        dcc.RadioItems(
            id='thin-select',
            options=[{'label': 'Thinned', 'value': 'True'},
                     {'label': 'All', 'value': 'False'}
                     ],
                     value='True',
                     labelStyle={'display': 'inline-block'}
            ),
        ], style=radio_button_style),
    html.Div([
        html.Label('X-axis'),
        dcc.RadioItems(
            id='x-axis',
            options = [{'label': 'Trial', 'value': 'index'},
                       {'label': 'Timestamp', 'value': 'Timestamp'},
                       ],
            value='index',
            labelStyle={'display': 'inline-block'}
            ),
    ], style=radio_button_style),
    # -------------------------[Plots]----------------------------------------
    html.Div([
        # ------------[Scatter Plot]---------------------
        html.Div([
            dcc.Graph(id='m2e_scatter',
                      figure=blank_fig(),
              ),
            ], className='twelve columns'),
        # ----------------[Histogram]---------------------
        html.Div([
            dcc.Graph(id='m2e_hist',
                      figure=blank_fig(),
              ),
            ], className='six columns'),
        ]),
    # ----------------------[Bottom Navigation]-------------------------
    html.Br(),
    html.Div([
        html.Hr(),
        dcc.Link('Load new data', href='/apps/measurement_select')
        ], className='twelve columns'),
    ])


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
    
    children = html.Div([
            html.Div(filename),
        ])
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
        ])
    return children

# --------------[Callback functions (order matters here!)]--------------------
@app.callback(
    Output('output-data-upload', 'children'),
    Output('json-data', 'data'),
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
        print('we hit data pass')
        # print(initial_data)
        final_json = initial_data
        children = html.Div('I need to do this part')
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
    return children, final_json

@app.callback(
    Output('m2e-results', 'children'),
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
            blank_fig(),
            blank_fig(),
            none_dropdown,
            none_dropdown
            )
        return return_vals


        