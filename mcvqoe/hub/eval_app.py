# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 14:02:51 2021

@author: jkp4
"""
import dash

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets)
server = app.server
