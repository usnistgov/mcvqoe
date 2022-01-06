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
import re
import tempfile 

from mcvqoe.hub.eval_app import app
from mcvqoe.hub.common import save_dir as default_data_dir

import mcvqoe.mouth2ear as mouth2ear
import mcvqoe.intelligibility as intell
import mcvqoe.psud as psud
import mcvqoe.accesstime as access
# --------------[Measurement Globals]-----------------------------------
measurements = [
    'm2e',
    'intell',
    'psud',
    'access',
    ]
# --------------[General Style]--------------------------------------------
plotly_default_color = '#edeef0'
style_links = {
    'width': '240px',
    # 'height': '60px',
    'display': 'block',
    # 'textAlign': 'center',
    'overflow-wrap': 'break-work',
    'lineHeight': '60px',
    'borderWidth': '1px',
    'borderStyle': 'solid',
    'borderRadius': '5px',
    'margin': '10px',
    'padding': '10px',
    'backgroundColor': '#E5ECF6',
        }
# --------------[Top of Page information]-----------------------

def mcv_headers(measurement):
    if measurement == 'm2e':
        full_meas = 'Mouth-to-ear latency'
    elif measurement == 'psud':
        full_meas = 'Probability of successful delivery'
    elif measurement == 'intell':
        full_meas = 'Speech intelligibility'
    elif measurement == 'access':
        full_meas = 'Access delay'
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
            # Load in data in fpath
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            except pd.errors.ParserError:
                # If parsing failed, access data, skip 3 rows
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), skiprows=3)
                
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
    if measurement == 'psud':
        eval_obj = psud.evaluate(json_data=jsonified_data)
    elif measurement == 'access':
        eval_obj = access.evaluate(json_data=jsonified_data)
    else:
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
            elif measurement == 'psud':
                eval_obj = psud.evaluate(outpaths)
        
    return eval_obj

# TODO: Make these leverage evaluate classes better, rather than redoing work...
def find_cutpoints(fname, df, measurement):
    '''
    Try to find cutpoints based on fname.
    
    Looks for cutpoints in:
        * mcvqoe.hub.common.save_dir as default_data_dir
        * sees if it can find matching cutpoints from measurement default/included audio
    If cannot find it in either needs to do something smart to inform user of limitation
      * Say open data from measurement gui/make sure that they have stuff stored appropriately (Reference?)
    '''
    
    data_dir = os.path.join(default_data_dir, measurement, 'data')
    # Identify session identification string
    session_pattern = re.compile(r'(capture_.+_\d{2}-\w{3}-\d{4}_\d{2}-\d{2}-\d{2})(?:.*\.csv)')
    session_search = session_pattern.search(fname)
    if session_search is not None:
        session_id = session_search.groups()[0]
    else:
        # TODO: Be smarter than this
        raise RuntimeError('No valid session id found in uploaded data')
   
    # Construct wav folder path based off capture id
    wav_dir = os.path.join(data_dir, 'wav', session_id)
    # Determine if wav directory exists
    if os.path.exists(wav_dir):        
        # Initialize cutpoints dictionary
        cps = dict()
        # TODO: This logic only works for PSuD, extract from access data file
        for file in np.unique(df['Filename']):
            # Construct path to cutpoint file
            cp_name = f'Tx_{file}.csv'
            cp_path = os.path.join(wav_dir, cp_name)
            
            # Load cutpoints
            cp = pd.read_csv(cp_path)
            
            # Store as json in dict
            cps[file] = cp.to_json()
    else:
        # Try to find the cutpoints from the defaults included in the package
        if measurement == 'psud':
            print('Trying to find default cps')
            # Get default audio sets and audio path
            [default_audio_sets, default_audio_path] = psud.measure.included_audio_sets()
            # Initialize cutpoints dictionary
            cps = dict()
            
            # Search string extract set number from filenames
            set_search = re.compile(r'(?:[FM]\d_n\d+_s)(\d+)(?:_c\d+)')
            for file in np.unique(df['Filename']):
                # Search for set
                search_res = set_search.search(file)
                if search_res is not None:
                    aset = 'set' + search_res.groups()[0]
                    # Make sure it is in default audio sets
                    if aset in default_audio_sets:
                        # Construct path to cutpoint file
                        cp_name = f'{file}.csv'
                        cp_path = os.path.join(default_audio_path, aset, cp_name)
                        
                        # Load cutpoints
                        cp = pd.read_csv(cp_path)
                        
                        # Store in json dict
                        cps[file] = cp.to_json()
                    else:
                        # TODO: Figure out how to flag this for users
                        raise RuntimeError('Cannot find cutpoints, say something to user')
                else:
                    # TODO: Figure out how to flag this for users
                    raise RuntimeError('Cannot find cutpoints, say something to user')
        if measurement == 'access':
            print('Trying to find default cps for access')
            # Get default audio sets and audio path
            default_audio_path = access.measure.included_audio_path()
            default_files = os.listdir(default_audio_path)
            
            # Extract talker word combo from file name
            tw_search_str = r'([FM]\d)(_b\d{1,2}_w\d_)(\w+)(?:.csv)'
            tw_search_var = re.compile(tw_search_str)
            tw_search = tw_search_var.search(fname)
            if tw_search is None:
                raise RuntimeError(f'Unable to determine talker word from filename {fname}')
            
            # Get talker word identifier for cutpoitns
            talker_word_name = tw_search.group()
            
            # Get talker word combo for storing
            talker, bw_index, word = tw_search.groups()
            talker_word = talker + ' ' +  word
            
            # Get matching cutpoitn file name from defaults
            cp_name = [x for x in default_files if talker_word_name in x]
            if len(cp_name) == 1:
                cp_name = cp_name[0]
            else:
                # TODO: Figure out how to flag this for users
                raise RuntimeError('Cannot find cuptpoints, say something to user')
            cp_path = os.path.join(default_audio_path, cp_name)
            
            # Load cutpoints file
            cp = pd.read_csv(cp_path)
            
            # Save in dict as json
            cps = {talker_word: cp.to_json()}
            
            # Extract session id from file name
            name = fname.replace('_' + talker_word_name, '')
            # TODO: fs hardcoded...not ideal
            fs = 48000
            
            # Determine length of T from cutpoints
            T = cp.loc[0]['End']/fs
            
            # Store PTT time relative to start of P1 
            df['time_to_P1'] = T - df['PTT_time']
            # Store session name
            df['name'] = name
            # Store talker word combo
            df['talker_word'] = talker_word
        # Store all measurement data and cutpoints for this session file
    
    out_json = {
        'measurement': df.to_json(),
        'cutpoints': cps,
        }
    return out_json


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
                      initial_data_flag, initial_data, measurement=measurement):
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
        # TODO: Add comments for this stuff
        if initial_data_flag == 'True':
            final_json = initial_data
            test_dict = json.loads(final_json)
            children = []
            if 'error' in test_dict:
                filenames = test_dict['test_info']
            elif measurement == 'access':    
                filenames = json.loads(test_dict['test_info']).keys()
            else:
                filenames = test_dict
            
            for filename in filenames:
                children.append(format_data_filename(filename))
        else:
            # TODO: Figure out what to do with cutpoints here...
            if list_of_contents is not None:
                try:
                    children = []
                    dfs = []
                    # TODO: Figure out a better variable name/place to store this
                    out_json = {}
                    for c, filename in zip(list_of_contents, list_of_names):
                        child, df = parse_contents(c, filename)
                        children.append(child)
                        dfs.append(df)
                        
                        if measurement == 'psud':
                            out_json[filename] = find_cutpoints(filename, df, measurement)
                            
                        elif measurement == 'access':
                            out_json[filename] = find_cutpoints(filename, df, measurement)
                        else:
                            out_json[filename] =  df.to_json()
                            
                    
                    if measurement == 'access':
                        # Initialize dataframe for storing all data
                        access_df = pd.DataFrame()
                        # Initialize cutpoints dict
                        cps = dict()
                        for sesh, sesh_dict in out_json.items():
                            # Load data frame
                            df = pd.read_json(sesh_dict['measurement'])
                            # Add to main dataframe
                            access_df = access_df.append(df)
                            
                            # Merge talker word cutpoints into main cutpoints dict
                            cps = {**cps, **sesh_dict['cutpoints']}
                        
                        # Make unique index for each trial
                        nrow, _ = access_df.shape
                        access_df.index = np.arange(nrow)
                        
                        # Make a dummy test_info (required by access.load_json just not super relevant here)
                        test_info = {'uploaded-access-data': {
                            'data_path': 'unknown-upload',
                            'data_file': list_of_names,
                            'cp_path': 'unknown-upload'
                            }
                                     }
                        # Store in dictionary used by access.load_json()
                        prep_json = {
                            'measurement': access_df.to_json(),
                            'cps': cps,
                            'test_info': json.dumps(test_info)
                                }
                        # Dump dict to json
                        final_json = json.dumps(prep_json)
                    else:
                        final_json = json.dumps(out_json)
                except Exception as e:
                    out_info = {'test_info': list_of_names,
                            'error': e.args,
                        }
                    print(f'e.args: {e.args}')
                    final_json = json.dumps(out_info)
                    
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

style_result_filters_dropdown = {
    'width': '30%',
    'display': 'inline-block'
    }
def measurement_results_filters(measurement):
    if measurement == 'psud':
        raw_intell_options = np.arange(0.5, 1.01, 0.1)
        intell_options = [{'label': np.round(x, 1), 'value': np.round(x, 1)} for x in raw_intell_options]
        default_intell_options=[0.5,]
        
        raw_msg_len_options = np.arange(1, 11, 1)
        msg_len_options = [{'label': x, 'value': x} for x in raw_msg_len_options]
        default_msg_len = [1, 3, 5, 10]
        
        children = html.Div([
            html.Div([
                html.Label('Method'),
                dcc.Dropdown(
                    id=f'{measurement}-method',
                    options=[
                        {'label': 'Every Word Critical (EWC)', 'value': 'EWC'},
                        {'label': 'Average Message Intelligibility (AMI)', 'value': 'AMI'},
                        ],
                    multi=True,
                    value=['EWC', 'AMI'],
                    ),
                ],
                style=style_result_filters_dropdown,
                ),
            html.Div([
                html.Label('Intelligibility Threshold'),
                dcc.Dropdown(
                    id=f'{measurement}-intelligibility-threshold',
                    options=intell_options,
                    multi=True,
                    value=default_intell_options,
                    
                    ),
                ],
                style=style_result_filters_dropdown,
                ),
            html.Div([
                html.Label('Message Length'),
                dcc.Dropdown(
                    id=f'{measurement}-message-length',
                    options=msg_len_options,
                    multi=True,
                    value=default_msg_len,
                    ),
                ],
                style=style_result_filters_dropdown,
                )
            ])
    elif measurement == 'access':
        raw_alpha_options = np.arange(0.5, 1, 0.01)
        alpha_options = [{'label': np.round(x, 2), 'value': np.round(x, 2)} for x in raw_alpha_options]
        default_alpha_options = [0.9,]
        children = html.Div([
            html.Div([
                html.Label('Alpha'),
                dcc.Dropdown(
                    id=f'{measurement}-alpha',
                    options=alpha_options,
                    multi=True,
                    value=default_alpha_options,
                    ),
                ],
                style=style_result_filters_dropdown,
                )
            ])
    else:
        children = None
    return children

digit_range = [1, 6]
digit_default = 4

def measurement_digits(display, digits=digit_default, measurement=''):
    style = style_measurement_format
    
    style['display'] = display
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
            pretty_vals.append(pretty_numbers(xv, digits=digits))
    else:
        pretty_vals = np.round(x, digits)
    return pretty_vals
#-------------------[Filter Styles]----------------------------------------
radio_button_style = {'width': '15%', 'display': 'inline-block'}
radio_labels_style = {'display': 'inline-block'}
dropdown_style = {'width': '45%', 'display': 'inline-block'}

def dropdown_filters(measurement):
    if measurement == 'access':
        children = [html.Div([
                    html.Label('Talker Select'),
                    dcc.Dropdown(
                        id=f'{measurement}-talker-select',
                        multi=True,
                        )
                    ], style=dropdown_style),
                ]
    elif measurement in measurements:
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
    elif measurement == 'psud':
        children = [
            # TODO: Generalize this
            html.Div([
                html.Label('Intelligibility'),
                dcc.RadioItems(
                    id=f'{measurement}-intell-type',
                    options = [
                        {'label': 'Message', 'value': 'message'},
                        {'label': 'Word', 'value': 'word'},
                        ],
                    value='message',
                    labelStyle=radio_labels_style,
                    ),
                ],
                style=radio_button_style,
                ),
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
    elif measurement == 'access':
        children = [
            # TODO: Generalize this
            html.Div([
                html.Label('Intelligibility'),
                dcc.RadioItems(
                    id=f'{measurement}-intell-type',
                    options = [
                        {'label': 'Relative to asymptotic', 'value': 'relative'},
                        {'label': 'Raw Intelligibility', 'value': 'intelligibility'},
                        ],
                    value='relative',
                    labelStyle=radio_labels_style,
                    ),
                ],
                style=radio_button_style,
                ),
            html.Div([
                html.Label('Plot raw data points'),
                dcc.RadioItems(
                    id=f'{measurement}-show-raw',
                    options = [{'label': 'True', 'value': 'True'},
                               {'label': 'False', 'value': 'False'},
                               ],
                    value='True',
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
    elif measurement == 'psud':
        children = [
            # --------------[PSuD vs msg length Plot] ---------
            html.Div([
                dcc.Graph(id=f'{measurement}-plot',
                          figure=blank_fig(),
                          ),
                ], className='twelve columns'),
            # --------------[Intell Scatter Plot]------------
            html.Div([
                dcc.Graph(id=f'{measurement}-scatter',
                          figure=blank_fig(),
                          ),
                ], className='twelve columns'),
            # ----------------[Test chain histogram]-------------
            html.Div([
                dcc.Graph(id=f'{measurement}-hist',
                          figure=blank_fig(),
                          ),
                ], className='twelve columns'),
            ]
    elif measurement == 'access':
        children = [
            # --------------[Access plot] ---------
            html.Div([
                dcc.Graph(id=f'{measurement}-plot',
                          figure=blank_fig(),
                          ),
                ], className='twelve columns'),
            # --------------[Intell Scatter Plot]------------
            html.Div([
                dcc.Graph(id=f'{measurement}-intell',
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
        html.Div(
            measurement_results_filters(measurement),
            id=f'{measurement}-results-filters', # Unused for m2e and intell, only for psud and access
            className='twelve columns',
            ),
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
            dcc.Link('Return to measurement selection', href='/measurement_select',
                     style=style_links,
                )
            ],
            className='twelve columns',
            
            ),
        ])
    return layout

def failed_process(measurement, msg=('', )):
    if measurement == 'access':
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        
        default_msg = ('Access object could not be processed.\n', )
        if msg[0] == 'Optimal parameters not found: Number of calls to function has reached maxfev = 600.':
            debug_help = ('This measurement is invalid. Try rerunning the test with a smaller Time Increase per Step to increase resolution.', )
        else:
            debug_help = ('', )
        msg = default_msg + msg + debug_help
        res = html.Div(msg)
        res_formatting = measurement_digits('none',
                                            measurement=measurement,
                                            )
        fig_plot = blank_fig()
        fig_intell = blank_fig()
        talker_options = none_dropdown
        
        return_vals = (
                res,
                res_formatting,
                fig_plot,
                fig_intell,
                talker_options,
                )
    elif measurement == 'm2e':
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        default_msg = ('Mouth-to-ear latency object could not be processed.\n', )
        debug_help = ('', )
        msg = default_msg + msg + debug_help
        res = html.Div(msg)
        res_formatting = measurement_digits('none',
                                                        measurement=measurement)
        fig_scatter = blank_fig()
        fig_histogram = blank_fig()
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
    elif measurement == 'psud':
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        # return_vals = (
        default_msg = ('PSuD object could not be processed.\n', )
        debug_help = ('', )
        msg = default_msg + msg + debug_help
        res = html.Div(msg)
        res_formatting = measurement_digits('none',
                                                        measurement=measurement)
        fig_plot = blank_fig()
        fig_scatter = blank_fig()
        fig_histogram = blank_fig()
        talker_options = none_dropdown
        session_options = none_dropdown
            # )
        return_vals = (
                res,
                res_formatting,
                fig_plot,
                fig_scatter,
                fig_histogram,
                talker_options,
                session_options
                )
    elif measurement == 'intell':
        none_dropdown = [{'label': 'N/A', 'value': 'None'}]
        # return_vals = (
        default_msg = ('Intelligibility object could not be processed.\n', )
        debug_help = ('', )
        msg = default_msg + msg + debug_help
        res = html.Div(default_msg)
        res_formatting = measurement_digits('none',
                                                        measurement=measurement)
        fig_scatter = blank_fig()
        fig_histogram = blank_fig()
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