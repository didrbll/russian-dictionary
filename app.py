import dash
from dash.html.Button import Button
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import plotly.express as px
from pages import  startpage, about
import atexit
import os

from connection import close_connection

app=dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.title='RRS'
server=app.server



app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
    ]
                      )


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'))

def display_page(pathname):
    if pathname == '/':
        return startpage.layout
    elif pathname == '/about':
        return about.layout
    else:
        return '404'

#Регистрация функции закрытия соединения при завершении работы приложения
atexit.register(close_connection)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8050))
    app.run_server(host='0.0.0.0', port=port)
