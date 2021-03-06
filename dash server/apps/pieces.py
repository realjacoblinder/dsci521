import plotly.graph_objects as go
import plotly.io as pio
import plotly as plt
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from app import app
from datetime import datetime
import chess.pgn
from apps import match, graphs
import numpy as np

from collections import Counter
import plotly.express as px

import pandas as pd

new_template = pio.templates['plotly_white']
new_template['layout']['scene']['xaxis']['gridcolor'] = '#222222'
new_template['layout']['scene']['yaxis']['gridcolor'] = '#222222'

#This wholeass section is for data processing
#******************************************************************************************************************
# preparing various dataframes for visualisation
    
games = {}
limit = 10000 # for testing
with open('./apps/data/lichess_db_standard_rated_2013-02.pgn', 'r') as pgn_file:
    game = chess.pgn.read_game(pgn_file)
    L = 0
    while game != None:
        match1 = match.Match(game)
        idx = match1.game_id
        games[idx] = match1
        game = chess.pgn.read_game(pgn_file)
        L += 1
        if L == limit: break
            
for game in games.values():
    game.fill_tracker()
data = pd.concat([i.get_dataframe() for i in games.values()])

def to_uci(square):
        square = int(square)
        letter = chr(ord('a') + ((square)%8)) 
        number = square//8+1
        return f"{letter}{number}"
    

captures_df = (data.explode('captures').groupby(['piece','captures'])['game_id'].nunique()).to_frame().reset_index().sort_values('game_id', ascending=False).assign(piece_type = lambda df: df['piece'].str.split('-').str.get(0))
captures_df['captured_piece_type'] = captures_df['captures'].apply(lambda x: x[0])
new_df = captures_df[['piece_type', 'captured_piece_type']].drop_duplicates()

new_df['capture_count'] = new_df.apply(lambda x: sum(captures_df[(captures_df['piece_type'] == x['piece_type']) & (captures_df['captured_piece_type'] == x['captured_piece_type'])]['game_id']), axis=1)
new_df['color'] = new_df['piece_type'].apply(lambda x: 'white' if ord(x) >= 9812 or ord(x) <= 9817 else 'black')
    
#Page header
#******************************************************************************************************************

layout = html.Div([
    dbc.Container([
        dbc.Row([
        dbc.Col(html.H1(children='Chess gang'), className="mb-2")
        ]),
        dbc.Row([
            dbc.Col(html.H6(children='Visualising trends across the board'), className="mb-4")]),

#******************************************************************************************************************
        
#Block headers
#******************************************************************************************************************        
    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Set the desired ELO rating range for the following graphs',
                                 className="text-center text-white bg-dark"), body=True, color="dark")
        , className="mt-4 mb-4")
    ]),
    dcc.RangeSlider(
        id='my-range-slider',
        min=100,
        max=2900,
        step=100,
        marks={
        100: '100',
        500: '500',
        900: '900',
        1300: '1300',
        1700: '1700',
        2100: '2100',
        2500: '2500',
        2900: '2900'
        },
        value=[1300, 1700]
        ),
    
    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Winning checkmate takes by piece, contrained by ELO',
                                 className="text-center text-white bg-dark"), body=True, color="dark")
        , className="mt-4 mb-4")
    ]),
        
    dbc.Row([
        dbc.Col(dcc.Graph(id='captures_by_piece'), width=12)
    ]),

    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Overall piece capture rates',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
        , className="mb-4")
        ]),
    dcc.Graph(id='pieces_captured'),
    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Moves per piece',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
        , className="mb-4")
        ]),
    dbc.Row([
        dbc.Col(html.H5(children='Pieces are normalized by piece count. For example, the number for pawns was divided by 8, while rooks were divided by two.', className="text-center"),
                className="mt-4"),
    ]),
    dcc.Graph(id='moves_per_piece'),
    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Board Heatmap',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
        , className="mb-4")
        ]),
    dbc.Row([
        dbc.Col(html.H5(children='Heatmap of the most popular squares on the board. Starting positions were not counted towards this calculation.', className="text-center"),
                className="mt-4"),
    ]),
    dcc.Graph(id='piece heatmap')

]) # container


]) # overall

# page callbacks
@app.callback([Output('pieces_captured', 'figure'),
               Output('captures_by_piece', 'figure'),
               Output('moves_per_piece', 'figure'),
               Output('piece heatmap', 'figure')],
              [Input('my-range-slider', 'value')])

def update_graph(slider_range):
    elo_min, elo_max = slider_range
    
    #Pieces captured
    fig = graphs.pieces_captured(new_df)
    fig.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    #Mating pieces
    fig2 = px.histogram(data_frame=graphs.checkmates(data, elo_min, elo_max), x='Checkmate')
    fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0), xaxis={'categoryorder' : 'array', 'categoryarray':['Queen', 'Rook', 'Pawn', 'Knight','Bishop']})

    fig3 = graphs.moves_per_piece(data, elo_min, elo_max)
    fig3.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    fig4 = graphs.board_heatmap(data, elo_min, elo_max)
    fig4.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    
    return fig, fig2, fig3, fig4
