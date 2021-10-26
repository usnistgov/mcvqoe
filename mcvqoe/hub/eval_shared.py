# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 11:52:45 2021

@author: jkp4
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import plotly.graph_objects as go
# --------------[Top of Page information]-----------------------

def mcv_headers(measurement):
    if measurement == 'm2e':
        full_meas = 'Mouth-to-ear latency'
    # TODO: Add other measurements
    children = [
        html.H1('MCV QoE Measurements Processing'),
        html.H3(f'{full_meas} data analysis')
        ]
    return children
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
#-------------------[Filter Styles]----------------------------------------
radio_button_style = {'width': '15%', 'display': 'inline-block'}
radio_labels_style = {'display': 'inline-block'}
dropdown_style = {'width': '45%', 'display': 'inline-block'}

def dropdown_filters(measurement):
    if measurement == 'm2e':
        children = [html.Div([
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
                ]
    return children

def radio_filters(measurement):
    if measurement == 'm2e':
        children = [
            html.Div([
                html.Label('Data thinning'),
                dcc.RadioItems(
                    id='thin-select',
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
                    id='x-axis',
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
            ]
    return children
#-------------[Create Layout Template]-------------------------
def layout_template(measurement):
    layout = html.Div([
        # TODO: This should probably be local or session
        # Element to store json representations of data
        dcc.Store(id='json-data',
                  storage_type='memory',
                  ),
        html.Div(
            mcv_headers(measurement),
            id='headers',),
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
                 id='initial-data-passed',
                 style={'display': 'none'}),
        html.Hr(),
        html.Div(id='measurement-results'),
        html.Br(),
        # ----------------[Dropdowns]------------------
        html.Div(
            dropdown_filters(measurement),
            id='filters-dropdown'
            ),
        # --------------------[Radio Button Filtering]--------------------------
        html.Div(
            radio_filters(measurement),
            id='filters-buttons',
            ),
        # -------------------------[Plots]----------------------------------------
        html.Div(
            measurement_plots(measurement),
            id='plots',
            ),
        # ----------------------[Bottom Navigation]-------------------------
        html.Br(),
        html.Div([
            html.Hr(),
            dcc.Link('Load new data', href='/measurement_select')
            ], className='twelve columns'),
        ])
    return layout