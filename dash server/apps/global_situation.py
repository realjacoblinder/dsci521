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
from tqdm import tqdm
import seaborn as sns
import numpy as np
sns.set(style="white")
from collections import Counter
import plotly.express as px
from apps import match
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
    
def first_winning_moves(games):
    first_moves = {'White':Counter(), 'Black':Counter()}
    for idx,match1 in games.items():
        winner = match1.winner
        if winner == 'Tie': continue
        white = match1.get_moves()[0]
        black = match1.get_moves()[1]
        first_moves[winner].update([white if winner == 'White' else black])
    return first_moves

def first_moves(games):
    first_moves = {'White':Counter(), 'Black':Counter()}
    for idx,match1 in games.items():
        white = match1.get_moves()[0]
        black = match1.get_moves()[1]
        first_moves['White'].update([white])
        first_moves['Black'].update([black])
    return first_moves

def move_win_rate_per_move(winners,moves):
    white_win_rates = {}
    black_win_rates = {}
    for i in moves['White'].keys():
        if i in winners['White']:
            white_win_rates[i] = winners['White'][i]/moves['White'][i]
        else:
            white_win_rates[i] = 0
    for i in moves['Black'].keys():
        if i in winners['Black']:
            black_win_rates[i] = winners['Black'][i]/moves['Black'][i]
        else:
            black_win_rates[i] = 0
    return white_win_rates,black_win_rates

def to_uci(square):
        square = int(square)
        letter = chr(ord('a') + ((square)%8)) 
        number = square//8+1
        return f"{letter}{number}"
    
def move_win_rate(winners,moves):
    white_win_rates = {}
    black_win_rates = {}
    white_wins = sum(winners['White'].values())
    white_moves = sum(moves['White'].values())
    black_wins = sum(winners['Black'].values())
    black_moves = sum(moves['Black'].values())
    for i in moves['White'].keys():
        legible_i = (to_uci(i[0]), to_uci(i[1]))
        if i in winners['White']:
            white_win_rates[legible_i] = (round(winners['White'][i]/moves['White'][i], 3), round(moves['White'][i]/white_moves, 3))
        else:
            white_win_rates[legible_i] = (0, round(moves['White'][i]/white_moves, 3))
    for i in moves['Black'].keys():
        legible_i = (to_uci(i[0]), to_uci(i[1]))
        if i in winners['Black']:
            black_win_rates[legible_i] = (round(winners['Black'][i]/moves['Black'][i], 3), round(moves['Black'][i]/black_moves, 3))
        else:
            black_win_rates[legible_i] = (0, round(moves['Black'][i]/black_moves, 3))
    return white_win_rates,black_win_rates

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


def checkmates(df, min_elo, max_elo):
    cm = df[df['Checkmate'] != False].copy()
    cm['Checkmate'] = cm['Checkmate'].apply(decolorizer)
    cm = cm[['game_id', 'mean_elo', 'Checkmate']].drop_duplicates().reset_index(drop=True)
    cm = cm[(cm['mean_elo'] < max_elo) & (cm['mean_elo'] > min_elo)]
    return cm

def decolorizer(piece):
    piece = piece[0]
    if piece in ['♕', '♛']:
        return 'Queen'
    if piece in ['♟', '♙']:
        return 'Pawn'
    if piece in ['♖', '♜']:
        return 'Rook'
    if piece in ['♘', '♞']:
        return 'Knight'
    if piece in ['♗', '♝']:
        return 'Bishop'

def white_black_rating_diff(data, color, trendline='lowess', min_elo=0, max_elo=5000):
    rating_diff_win_rate = data[['game_id']].copy()
    rating_diff_win_rate['white elo'] = rating_diff_win_rate['game_id'].apply(lambda x: int(games[x].white_elo) if games[x].white_elo != '?' else '?')
    rating_diff_win_rate['black elo'] = rating_diff_win_rate['game_id'].apply(lambda x: int(games[x].black_elo) if games[x].black_elo != '?' else '?')
    rating_diff_win_rate = rating_diff_win_rate[(rating_diff_win_rate['white elo'] != '?') & (rating_diff_win_rate['black elo'] != '?')]
    rating_diff_win_rate['winner'] = rating_diff_win_rate['game_id'].apply(lambda x: games[x].winner)
    rating_diff_win_rate['white-black diff'] = rating_diff_win_rate['white elo'] - rating_diff_win_rate['black elo']
    rating_diff_win_rate.drop_duplicates(inplace=True)
    rating_diff_win_rate.reset_index(inplace=True, drop=True)
    if color == 'white':
        col = 'white elo'
    else:
        col = 'black elo'
    rating_diff_win_rate = rating_diff_win_rate[(rating_diff_win_rate[col] >= min_elo) & (rating_diff_win_rate[col] <= max_elo)]
    c = 'winner'
    if rating_diff_win_rate.empty:
        c=None
    return px.scatter(rating_diff_win_rate, col, 'white-black diff', color=c, trendline=trendline)

def moves_per_piece(data, min_elo=1000, max_elo=1500):
    def piece_normalizer(row):
        piece = row['piece']
        if piece in  ['♟', '♙']:
            return row['number_of_moves']/8
        if piece in  ['♕', '♚', '♛', '♔']:
            return row['number_of_moves']
        else:
            return row['number_of_moves']/2

    mpr = data[['piece', 'move_nums', 'mean_elo']].copy()
    mpr['number_of_moves'] = mpr['move_nums'].apply(lambda x: len(x))
    mpr['piece'] = mpr['piece'].apply(lambda x: x[0])
    mpr = mpr[(mpr['mean_elo'] > min_elo) & (mpr['mean_elo'] < max_elo)].groupby('piece').sum().reset_index()
    mpr['normalized_moves'] = mpr.apply(piece_normalizer, axis=1)
    mpr['normalized_moves'] = mpr['normalized_moves']/mpr['normalized_moves'].sum()*100
    return px.bar(data_frame=mpr, x='piece', y='normalized_moves')

def openings_by_elo(data, eco='All', min_elo=1000, max_elo=1500):
    obe = data[['game_id', 'mean_elo']].copy()
    obe.drop_duplicates(inplace=True)
    obe['eco'] = obe['game_id'].apply(lambda x: games[x].eco)
    obe['open'] = obe['eco'].apply(lambda x: x[0])
    opening_name = {'A': 'Flank Openings', 'B': 'Semi-Open Games', 'C':'Open Games', 'D':'Closed Games and Semi-Closed Games', 'E':'Indian Defences'}
    obe['open name'] = obe['open'].apply(lambda x: opening_name[x])
    if eco == 'All':
        return px.pie(obe[(obe['mean_elo'] > min_elo) & (obe['mean_elo'] < max_elo)], 'open name')
    else:
        obe = obe[obe['open'] == eco]
        return px.pie(obe[(obe['mean_elo'] > min_elo) & (obe['mean_elo'] < max_elo)], 'eco')

def first_four_moves(four_moves, white_first = None, black_first = None, white_second = None):
	## need to have 
    if four_moves.empty:
        c=None
    if white_first == None:
        return px.bar(four_moves, 'white first move', color='winner').update_traces(hovertemplate=None, hoverinfo='skip')
    if four_moves.empty:
        c=None
    if black_first == None:
        return px.bar(four_moves[four_moves['white first move'] == white_first], 'black first move', color='winner').update_traces(hovertemplate=None, hoverinfo='skip')
    if four_moves.empty:
        c=None
    if white_second == None:
        four_moves = four_moves[(four_moves['white first move'] == white_first) & (four_moves['black first move'] == black_first)]
        return px.bar(four_moves, 'white second move', color='winner').update_traces(hovertemplate=None, hoverinfo='skip')
    if four_moves.empty:
        c=None
    else:
        four_moves = four_moves[(four_moves['white first move'] == white_first) & (four_moves['black first move'] == black_first) & (four_moves['white second move'] == white_second)]
        return px.bar(four_moves, 'black second move', color='winner').update_traces(hovertemplate=None, hoverinfo='skip')
    
    
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
        
#Dropdown menu
#******************************************************************************************************************
# choose eco

        
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
        style={'width': '50%'}
        ),
        
        dcc.Dropdown(
        id='whitefirst',
        options=whitefirstdict,
        value=None,
        multi=False,
        style={'width': '50%'}
        ),
        
        dcc.Dropdown(
        id='blackfirst',
        value=None,
        multi=False,
        style={'width': '50%'}
        ),
        
        dcc.Dropdown(
        id='whitesecond',
        value=None,
        multi=False,
        style={'width': '25%'}
        ),
#******************************************************************************************************************
        
#Block headers
#******************************************************************************************************************        
    dbc.Row([
        dbc.Col(dbc.Card(html.H3(children='Most popular openings by color',
                                 className="text-center text-white bg-dark"), body=True, color="dark")
        , className="mt-4 mb-4")
    ]),
        
    #dbc.Row([
    #    dbc.Col(html.H5(children='Latest update: 7 June 2020', className="text-center"),
    #                     width=4, className="mt-4"),
    #    dbc.Col(html.H5(children='Daily figures since 31 Dec 2019', className="text-center"), width=8, className="mt-4"),
    #    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='ECO_graph'), width=12),
        ]),
        
        dbc.Row([
            
            dbc.Col(html.H5(children='Latest update: 7 June 2020', className="text-center"),
                    width=4, className="mt-4"),
            dbc.Col(html.H5(children='Cumulative figures since 31 Dec 2019', className="text-center"), width=8,
                    className="mt-4"),
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
        dbc.Col(dbc.Card(html.H3(children='Figures by country (per 1 million people)',
                                 className="text-center text-light bg-dark"), body=True, color="dark")
        , className="mb-4")
        ]),

    dbc.Row([
        dbc.Col(html.H5(children='Daily figures', className="text-center"),
                className="mt-4"),
    ]),

    dcc.Graph(id='cases_or_deaths_country'),

    dcc.RadioItems(
        id='color',
        options=[{'label': i, 'value': i} for i in ['white', 'black']],
        value='white',
        labelStyle={'display': 'inline-block'}
    ),

    dbc.Row([
        dbc.Col(html.H5(children='Cumulative figures', className="text-center"),
                className="mt-4"),
    ]),

    dcc.Graph(id='another graph'),

])


])

# page callbacks
@app.callback([Output('captures_by_piece', 'figure'),
               Output('another graph', 'figure'),
               Output('arrmatey', 'figure'),
               Output('ECO_graph', 'figure'),
               Output('blackfirst', 'options'),
               Output('whitesecond', 'options')],
              [Input('ECO', 'value'),
               Input('color','value'),
               Input('my-range-slider', 'value'),
               Input('my-range-slider1', 'value'),
               Input('whitefirst','value'),
               Input('blackfirst','value'),
               Input('whitesecond','value')])

def update_graph(ECO, color, slider_range, slider_range1, whitefirst, blackfirst, whitesecond):
    elo_min, elo_max = slider_range
    elo_min1, elo_max1 = slider_range1
    
    #Pieces captured
    #fig = px.bar(new_df, x='piece_type', y='capture_count', color='captured_piece_type')
    
    #White v Black by elo differential
    fig4 = white_black_rating_diff(data, color, min_elo=elo_min, max_elo=elo_max)
    fig4.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    
    #Mating pieces
    fig2 = go.Figure()
    fig2 = px.histogram(data_frame=checkmates(data, elo_min, elo_max), x='Checkmate')
    fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)', template = new_template, margin = dict(t=0))
    
    
    fig3 = openings_by_elo(data, eco=ECO, min_elo=elo_min1, max_elo=elo_max1)
    
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
    
    
    
    
    fig5 = first_four_moves(four_moves, whitefirst, blackfirst, whitesecond)
    
    return fig2, fig4, fig3, fig5, blackfirsty, whitefirsty
