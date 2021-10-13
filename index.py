# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:59:05 2021

@author: jkp4
"""
import os

from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from app import app
from apps import measurement_select, psud, m2e


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
    ])

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/apps/psud':
        return psud.layout
    elif pathname =='/apps/m2e':
        return m2e.layout
    elif pathname == '/apps/measurement_select':
        
        return measurement_select.layout
    else:
        
        # return '404'
        return measurement_select.layout

if __name__ == '__main__':
    app.run_server(debug=True)