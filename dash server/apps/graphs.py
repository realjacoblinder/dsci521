import plotly.express as px
import pandas as pd

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

def white_black_rating_diff(data, games, color, trendline='lowess', min_elo=0, max_elo=5000):
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
    return px.scatter(rating_diff_win_rate, col, 'white-black diff', color=c, trendline=trendline, hover_data=['black elo'])

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

def openings_by_elo(data, games, eco='All', min_elo=1000, max_elo=1500):
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
    c='winner'
    
    if white_first == None:
        return px.bar(four_moves, 'white first move', color=c).update_traces(hovertemplate=None, hoverinfo='skip')
    
    if black_first == None:
        four_moves = four_moves[four_moves['white first move'] == white_first]
        if four_moves.empty:
            c=None
        return px.bar(four_moves, 'black first move', color=c).update_traces(hovertemplate=None, hoverinfo='skip')
    
    if white_second == None:
        four_moves = four_moves[(four_moves['white first move'] == white_first) & (four_moves['black first move'] == black_first)]
        if four_moves.empty:
            c=None
        return px.bar(four_moves, 'white second move', color=c).update_traces(hovertemplate=None, hoverinfo='skip')
    
    else:
        four_moves = four_moves[(four_moves['white first move'] == white_first) & (four_moves['black first move'] == black_first) & (four_moves['white second move'] == white_second)]
        if four_moves.empty:
            c=None
        return px.bar(four_moves, 'black second move', color=c).update_traces(hovertemplate=None, hoverinfo='skip')

def pieces_captured(df):
    return px.bar(df, x='piece_type', y='capture_count', color='captured_piece_type')