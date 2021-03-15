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
import numpy as np

from collections import Counter
import plotly.express as px
from apps import match, graphs
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

openings_dict = {'white first move':[], 'white second move':[], 'black first move':[], 'black second move':[], 'white':[], 'black':[], 'tie':[]}
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
        if game.winner == 'White':
            openings_dict['white'].append(1)
            openings_dict['black'].append(0)
            openings_dict['tie'].append(0)
        elif game.winner == 'Black':
            openings_dict['white'].append(0)
            openings_dict['black'].append(1)
            openings_dict['tie'].append(0)
        else:
            openings_dict['white'].append(0)
            openings_dict['black'].append(0)
            openings_dict['tie'].append(1)
four_moves = pd.DataFrame(openings_dict)

whitefirstdict = []

blackfirstdict = []
whiteseconddict = []
    
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
        
#Block headers
#******************************************************************************************************************        
    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Four move opening sequences',
                                 className="text-center text-white bg-dark"), body=True, color="dark")
        , className="mt-4 mb-4"), 
        dbc.Col(dbc.Card("Starting with White's move, select a move in the menus from left to right to update the win rates of the graph below", body=True), align='center')
    ]),
        
    #dbc.Row([
    #    dbc.Col(html.H5(children='Latest update: 7 June 2020', className="text-center"),
    #                     width=4, className="mt-4"),
    #    dbc.Col(html.H5(children='Daily figures since 31 Dec 2019', className="text-center"), width=8, className="mt-4"),
    #    ]),

    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='whitefirst',
                options=whitefirstdict,
                value=None,
                multi=False
            )
        ),
        dbc.Col(
            dcc.Dropdown(
                id='blackfirst',
                value=None,
                multi=False
            )
        ),
        dbc.Col(
            dcc.Dropdown(
                id='whitesecond',
                value=None,
                multi=False
            )
        )],
        align = 'center'
    ), 

    dbc.Row([
        dbc.Col(dcc.Graph(id='ECO_graph'), width=12),
        ]),
        
        dbc.Row([
            dbc.Col(
                  dcc.Dropdown(
                    id='ECO',
                    options=[
                        {'label': 'All Openings ', 'value': 'All'},
                        {'label': 'A: Flank Openings', 'value': 'A'},
                        {'label': 'B: Semi-Open Games', 'value': 'B'},
                        {'label': 'C: Open Games', 'value': 'C'},
                        {'label': 'D: Closed and Semi-Closed Games', 'value': 'D'},
                        {'label': 'E: Indian Defences', 'value': 'E'}
                    ],
                    value='All',
                    multi=False,
                    style={'width': '75%'}
                    ),
                ),
            
            dbc.Col(html.H5(children='Openings By ECO code', className="text-center"),
                    className="mt-4"
                    ),
        ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='arrmatey'), width=12)
    ]),
     dcc.RangeSlider(
        id='my-range-slider1',
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
        vertical=False,
        value=[1300, 1700]
        ),
        

    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Winning player trends vs ELO diffrentials',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
        , className="mb-4")
        ]),

    dbc.Row([
        dbc.Col(html.H5(children='White vs Black ELO difference', className="text-center"),
                className="mt-4"),
    ]),

    dbc.Row([
        dbc.Col('Change player perspective', className="text-right"),
        dbc.Col(
            dcc.RadioItems(
                id='color',
                options=[{'label': ' White  ', 'value': 'white'}, {'label': ' Black', 'value':'black'}],
                value='white',
            )
        )
    ]),

    dcc.Graph(id='another graph'),

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
        vertical=False,
        value=[100, 2900]
        )

])


])

# page callbacks
@app.callback([Output('another graph', 'figure'),
               Output('arrmatey', 'figure'),
               Output('ECO_graph', 'figure'),
               Output('blackfirst', 'options'),
               Output('whitesecond', 'options')],
              [Input('ECO', 'value'),
               Input('color','value'),
               Input('my-range-slider1', 'value'),
               Input('whitefirst','value'),
               Input('blackfirst','value'),
               Input('whitesecond','value'),
               Input('my-range-slider', 'value')])

def update_graph(ECO, color, slider_range1, whitefirst, blackfirst, whitesecond, slider_range):
    elo_min1, elo_max1 = slider_range1
    elo_min, elo_max = slider_range
    
    #White v Black by elo differential
    fig4 = graphs.white_black_rating_diff(data, games, color, min_elo=elo_min, max_elo=elo_max)
    fig4.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    
    
    fig3 = graphs.openings_by_elo(data, games, eco=ECO, min_elo=elo_min1, max_elo=elo_max1)
    
    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       template = new_template,
                       margin=dict(t=0))    
    blackfirsty = []
    for i in four_moves[(four_moves['white first move'] == whitefirst)]['black first move'].unique():
        blackfirsty.append({'label': i, 'value': i})
        
    whitefirsty = []
    for i in four_moves[(four_moves['white first move'] == whitefirst) & (four_moves['black first move'] == blackfirst)]['white second move'].unique():
        whitefirsty.append({'label': i, 'value': i})
    
    fig5 = graphs.first_four_moves(four_moves, whitefirst, blackfirst, whitesecond)
    fig5.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                       template = new_template,
                       margin=dict(t=0))
    
    return fig4, fig3, fig5, blackfirsty, whitefirsty
