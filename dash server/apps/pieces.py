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
limit = 1000 # for testing
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

openings_dict = {'white first move':[], 'white second move':[], 'black first move':[], 'black second move':[], 'winner':[], 'game_id':[]}
for game in games.values():
    move_counter = 0
    moves = []
    for move in game.mainline_moves:
        moves.append(str(move))
        if move_counter == 3:
            break
        move_counter += 1
    if len(moves) == 4:
        openings_dict['white first move'].append(moves[0])
        openings_dict['black first move'].append(moves[1])
        openings_dict['white second move'].append(moves[2])
        openings_dict['black second move'].append(moves[3])
        openings_dict['winner'].append(game.winner)
        openings_dict['game_id'].append(game.game_id)
four_moves = pd.DataFrame(openings_dict)

whitefirstdict = []

blackfirstdict = []
whiteseconddict = []

#******************************************************************************************************************
#Graphzone
    
    
#******************************************************************************************************************
#panic
for i in four_moves['white first move'].unique():
        whitefirstdict.append({'label': i, 'value': i})
    
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
        dbc.Col(dbc.Card(html.H3(children='Winning checkmate takes by piece, contrained by ELO',
                                 className="text-center text-white bg-dark"), body=True, color="dark")
        , className="mt-4 mb-4")
    ]),
        
    dbc.Row([
        dbc.Col(dcc.Graph(id='captures_by_piece'), width=12)
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
        dbc.Col(dbc.Card(html.H3(children='Overall piece capture rates, normalized by piece type count',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
        , className="mb-4")
        ]),

    dbc.Row([
        dbc.Col(html.H5(children='Pieces are normalized by piece count. For example, the number for pawns was divided by 8, while rooks were divided by two.', className="text-center"),
                className="mt-4"),
    ]),

    dcc.Graph(id='pieces_captured'),

]) # container


]) # overall

# page callbacks
@app.callback([Output('pieces_captured', 'figure'),
               Output('captures_by_piece', 'figure')],
              [Input('my-range-slider', 'value')])

def update_graph(slider_range):
    elo_min, elo_max = slider_range
    
    #Pieces captured
    fig = graphs.pieces_captured(new_df)
    
    #Mating pieces
    fig2 = go.Figure()
    fig2 = px.histogram(data_frame=graphs.checkmates(data, elo_min, elo_max), x='Checkmate')
    fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    
    return fig, fig2
