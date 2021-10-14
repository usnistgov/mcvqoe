# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 12:26:08 2021

@author: jkp4
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from ipywidgets import widgets
from plotly.subplots import make_subplots


import base64
import dash

import datetime
import io

from app import app

import mcvqoe.mouth2ear as mouth2ear
import numpy as np
import os
import pandas as pd
import plotly.graph_objects as go

# test_data = 'D:\MCV_671DRDOG\mouth2ear-internal\data\csv\capture_QoE board baseline_21-Sep-2021_15-09-04.csv'
test_data = ['D:\MCV_671DRDOG\mouth2ear-internal\data\csv\capture_QoE board baseline_21-Sep-2021_15-09-04.csv',
             'D:\MCV_671DRDOG\mouth2ear-internal\data\csv\capture_AD-QoE-Board-Validation_04-Oct-2021_09-19-43.csv',
             ]
def load_data(test_data):
    
    m2e_eval = mouth2ear.evaluate(test_data)
    return m2e_eval

def session_labels(m2e_eval):
    label_ix = np.arange(len(m2e_eval.data))
    labels = [f'Session {ix}' for ix in label_ix]
    return labels, label_ix


    
m2e_eval = load_data(test_data)
m2e_mean, m2e_ci = m2e_eval.eval()

sesh_labels, sesh_label_ix = session_labels(m2e_eval)

radio_button_style = {'width': '15%', 'display': 'inline-block'}
dropdown_style = {'width': '45%', 'display': 'inline-block'}

layout = html.Div([
    html.H1('MCV QoE Measurements Processing'),
    
    html.H3('Mouth-to-ear latency data analysis'),
    
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
    
    html.H4(f'Evaluating session(s): {m2e_eval.test_names}'),
    html.P(f'Mean mouth-to-ear latency: {m2e_mean} s'),
    html.P(f'95% Confidence Interval: {m2e_ci} s'),
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
    
    html.Div([
        html.Label('My Fake Button'),
        html.Button('Click me',
            id='fake-button',
            n_clicks=0
            ),
        ], style=radio_button_style),
    # dcc.Graph(id='plots',
    #           ),
    html.Div([
        # ------------[Scatter Plot]---------------------
        html.Div([
            dcc.Graph(id='m2e_scatter',
              figure=m2e_eval.plot(x='Timestamp')
              ),
            ], className='twelve columns'),
        # ----------------[Histogram]---------------------
        html.Div([
            dcc.Graph(id='m2e_hist',
              figure=m2e_eval.histogram()
              ),
            ], className='six columns'),
        ]),
    

    dcc.Link('Load new data', href='/apps/measurement_select')
    ])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8'))
                )
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file'
            ])
    return html.Div([
            html.H5(filename),
            html.H6(datetime.datetime.fromtimestamp(date)),
            
            dash.dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                page_size=10,
                ),
            html.Hr(),
            
            # For debugging, display the raw contents provided by the web browser
            html.Div('Raw Content'),
            html.Pre(contents[0:200] + '...', style={
                'whiteSpace': 'pre-wrap',
                'wordBreak': 'break-all'
            })
        ])

@app.callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    Input('upload-data', 'last_modified'),
    )
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
    return children

@app.callback(
    Output('m2e_scatter', 'figure'),
    Input('thin-select', 'value'),
    Input('talker-select', 'value'),
    Input('session-select', 'value'),
    Input('x-axis', 'value'),
    )
def update_scatter(thin, talker_select, session_select, x):
    if x == 'index':
        x = None
    thinned = thin == 'True'
    if talker_select == []:
        talker_select = None
    if session_select == []:
        session_select = None
    fig = m2e_eval.plot(x=x,
                        thinned=thinned,
                        talkers=talker_select,
                        test_name=session_select,
                        )
    return fig

@app.callback(
    Output('m2e_hist', 'figure'),
    Input('thin-select', 'value'),
    Input('talker-select', 'value'),
    )
def update_hist(thin, talker_select):
    
    thinned = thin == 'True'
    fig = m2e_eval.histogram(thinned=thinned)
    return fig

@app.callback(
    Output('talker-select', 'options'),
    Output('session-select', 'options'),
    Input('fake-button', 'n_clicks')
    )
def update_talker_dropdown(fake_button):
    # TODO: Figure out how to genreate this dynamically
    # talkers = ['F1_harvard_phrases',
    #            'F2_harvard_phrases',
    #            'M1_harvard_phrases',
    #            'M2_harvard_phrases'
    #            ]
    talkers = np.unique(m2e_eval.data['Filename'])
    remove = len(talkers) - fake_button
    
    if remove > 0:
        options = [{'label': i, 'value': i} for i in talkers[:remove]]
    else:
        options = [{'label': talkers[0], 'value': talkers[0]}]
    
    sesh_names = np.unique(m2e_eval.data['name'])
    sesh_options = [{'label': i, 'value': i} for i in sesh_names]
    return options, sesh_options
        