# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 11:52:45 2021

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
import plotly.graph_objects as go
import tempfile 

from mcvqoe.hub.eval_app import app

import mcvqoe.mouth2ear as mouth2ear
import mcvqoe.intelligibility as intell
# --------------[Measurement Globals]-----------------------------------
measurements = [
    'm2e',
    'intell',
    # TODO: Add rest of measurements
    ]
# --------------[General Style]--------------------------------------------
plotly_default_color = '#E5ECF6'

# --------------[Top of Page information]-----------------------

def mcv_headers(measurement):
    if measurement == 'm2e':
        full_meas = 'Mouth-to-ear latency'
    elif measurement == 'psud':
        full_meas = 'Probability of successful delivery'
    elif measurement == 'intell':
        full_meas = 'Speech intelligibility'
    else:
        full_meas = 'Undefined measurement'
            
    # TODO: Add other measurements
    children = [
        html.H1('MCV QoE Measurements Processing'),
        html.H3(f'{full_meas} data analysis')
        ]
    return children
#---------------[Parsing Data]----------------------------
def parse_contents(contents, filename):
    """
    Parse contents of uploaded data

    Parameters
    ----------
    contents : TYPE
        DESCRIPTION.
    filename : TYPE
        DESCRIPTION.

    Returns
    -------
    children : TYPE
        HTML representations of filename or error string.
    df : pd.DataFrame
        Data stored as dataframe.

    """
    content_type, content_string = contents.split(',')
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
    children = format_data_filename(filename)
    
    return children, df

def load_json_data(jsonified_data, measurement):
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
        if measurement == 'm2e':
            # Load temporary files
            eval_obj = mouth2ear.evaluate(outpaths)
        elif measurement == 'intell':
            eval_obj = intell.evaluate(outpaths)
        
        return eval_obj
for measurement in measurements:
    @app.callback(
        Output(f'{measurement}-output-data-upload', 'children'),
        Output(f'{measurement}-json-data', 'data'),
        Output(f'{measurement}-initial-data-passed', 'children'),
        Input(f'{measurement}-upload-data', 'contents'),
        Input(f'{measurement}-upload-data', 'filename'),
        State(f'{measurement}-initial-data-passed', 'children'),
        State(f'{measurement}-json-data', 'data'),
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
                children.append(format_data_filename(filename))
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
        
        initial_data_flag = html.Div('False')
        return children, final_json, initial_data_flag
# --------------[Data Filename Formattting]-----------------------
style_data_filename = {
            'fontSize': 12,
            }

def format_data_filename(filename):
    children = html.Div([
        html.P([filename])
        ],
        style=style_data_filename)
    return children
#-------------------[Results Styles]-------------------------------------
style_results = {
    'backgroundColor': plotly_default_color,
    'width': '100%',
    'borderWidth': '1px',
    'borderStyle': 'solid',
    'borderRadius': '5px',
    'textAlign': 'left',
    'margin': '10px',
    'padding': '10px',
    }
style_measurement_format = {
    'fontSize': 12,
    'backgroundColor': plotly_default_color,
    'width': '50%',
    'borderWidth': '1px',
    'borderStyle': 'solid',
    'borderRadius': '5px',
    'marginTop': '10px',
    'marginRight': '10px',
    'padding': '10px',
    }
digit_range = [1, 6]
digit_default = 4
def measurement_digits(display, digits=digit_default, measurement=''):
    style = style_measurement_format
    
    style['display'] = display
    # print(f'In measurement_digits: measurement-{measurement}, style[display]: {style["display"]}')
    children = html.Div([
        html.Label(f'Number of Digits in Results ({digit_range[0]} - {digit_range[1]}):'),
        dcc.Input(id=f'{measurement}-measurement-digits',
                  value=digits,
                  type='number',
                  min=digit_range[0],
                  max=digit_range[1],
                  style={
                      'backgroundColor': '#f0f2f5',
                      # 'width': '100%',
                      }
                  ),
        ],
        style=style_measurement_format,
        )
    return children
def pretty_numbers(x, digits=digit_default):
    if isinstance(x, list):
        pretty_vals = []
        for xv in x:
            pretty_vals.append(pretty_numbers(xv))
    else:
        pretty_vals = np.round(x, digits)
    return pretty_vals
#-------------------[Filter Styles]----------------------------------------
radio_button_style = {'width': '15%', 'display': 'inline-block'}
radio_labels_style = {'display': 'inline-block'}
dropdown_style = {'width': '45%', 'display': 'inline-block'}

def dropdown_filters(measurement):
    if measurement == 'm2e' or measurement == 'intell':
        children = [html.Div([
                    html.Label('Session Select'),
                    dcc.Dropdown(
                        id=f'{measurement}-session-select',
                        multi=True
                        )
                    ], style=dropdown_style),
                html.Div([
                    html.Label('Talker Select'),
                    dcc.Dropdown(
                        id=f'{measurement}-talker-select',
                        multi=True,
                        )
                    ], style=dropdown_style),
                ]
    else:
        children = [html.Div('Undefined Measurement')]
    return children

def radio_filters(measurement):
    if measurement == 'm2e':
        children = [
            html.Div([
                html.Label('Data thinning'),
                dcc.RadioItems(
                    id=f'{measurement}-thin-select',
                    options=[{'label': 'Thinned', 'value': 'True'},
                             {'label': 'All', 'value': 'False'}
                             ],
                             value='True',
                             labelStyle=radio_labels_style,
                    ),
                ], style=radio_button_style),
            html.Div([
                html.Label('X-axis'),
                dcc.RadioItems(
                    id=f'{measurement}-x-axis',
                    options = [{'label': 'Trial', 'value': 'index'},
                               {'label': 'Timestamp', 'value': 'Timestamp'},
                               ],
                    value='index',
                    labelStyle=radio_labels_style,
                    ),
                ],
                style=radio_button_style
                ),
            ]
    elif measurement == 'intell':
        children = [
            # TODO: Generalize this
            html.Div([
                html.Label('X-axis'),
                dcc.RadioItems(
                    id=f'{measurement}-x-axis',
                    options = [{'label': 'Trial', 'value': 'index'},
                               {'label': 'Timestamp', 'value': 'Timestamp'},
                               ],
                    value='index',
                    labelStyle=radio_labels_style,
                    ),
                ],
                style=radio_button_style
                ),
            ]
    else:
         children = [html.Div('Undefined measurement')]   
    return children
#------------------------[Figure and Plots]----------------------------
def blank_fig():
    """
    Make a blank plotly figure for a placeholder prior to data load
    """
    fig = go.Figure(go.Scatter(x=[], y = []))
    fig.update_layout(template = None)
    fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
    fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    
    return fig

def measurement_plots(measurement):
    if measurement == 'm2e':
        children = [
            # ------------[Scatter Plot]---------------------
            html.Div([
                dcc.Graph(id=f'{measurement}-scatter',
                          figure=blank_fig(),
                  ),
                ], className='twelve columns'),
            # ----------------[Histogram]---------------------
            html.Div([
                dcc.Graph(id=f'{measurement}-hist',
                          figure=blank_fig(),
                  ),
                ], className='six columns'),
            ]
    elif measurement == 'intell':
        children = [
            # ------------[Scatter Plot]---------------------
            html.Div([
                dcc.Graph(id=f'{measurement}-hist',
                          figure=blank_fig(),
                  ),
                ], className='twelve columns'),
            # ----------------[Histogram]---------------------
            html.Div([
                dcc.Graph(id=f'{measurement}-scatter',
                          figure=blank_fig(),
                  ),
                ], className='twelve columns'),
            ]
    else:
        
        children = [html.Div('Undefined measurement')]   
    return children
#-------------[Create Layout Template]-------------------------
def layout_template(measurement):
    layout = html.Div([
        # TODO: This should probably be local or session
        # Element to store json representations of data
        dcc.Store(id=f'{measurement}-json-data',
                  storage_type='memory',
                  ),
        html.Div(
            mcv_headers(measurement),
            id=f'{measurement}-headers',),
        #--------------[Upload Data]------------------------------
        dcc.Upload(
            id=f'{measurement}-upload-data',
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
        html.Div(id=f'{measurement}-output-data-upload'),
        html.Div('False',
                 id=f'{measurement}-initial-data-passed',
                 style={'display': 'none'}),
        html.Hr(),
        html.Div([
            html.Div(
                id=f'{measurement}-measurement-results',
                className='eight columns',
                ),
            html.Div(
                measurement_digits(display='none', measurement=measurement),
                id=f'{measurement}-measurement-formatting',
                className='four columns',
                ),
            ]),
        html.H3('Plotting Dashboard',
                # style={
                #     'topMargin': '10px',
                #     },
                className='twelve columns'),
        # html.Br(),
        # html.Br(),
        # html.Br(),
        # ----------------[Dropdowns]------------------
        html.Div(
            dropdown_filters(measurement),
            id=f'{measurement}-filters-dropdown',
            style={
                'marginTop': '10px',
                },
            ),
        # --------------------[Radio Button Filtering]--------------------------
        html.Div(
            radio_filters(measurement),
            id=f'{measurement}-filters-buttons',
            ),
        # -------------------------[Plots]----------------------------------------
        html.Div(
            measurement_plots(measurement),
            id=f'{measurement}-plots',
            ),
        # ----------------------[Bottom Navigation]-------------------------
        html.Br(),
        html.Div([
            html.Hr(),
            dcc.Link('Load new data', href='/measurement_select')
            ], className='twelve columns'),
        ])
    return layout