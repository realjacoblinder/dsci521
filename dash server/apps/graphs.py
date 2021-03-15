import plotly.express as px
import plotly.graph_objects as go
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

def white_black_rating_diff(data, games, color, trendline='ols', min_elo=0, max_elo=5000):
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
    return px.scatter(rating_diff_win_rate, col, 'white-black diff', color=c, trendline=trendline, hover_data=['black elo'], labels={"white elo": "White Rating", "black elo" : "Black Rating", "white-black diff" : "Rating Differential", "winner" : "Winner"})

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
    return px.bar(data_frame=mpr, x='piece', y='normalized_moves', labels={"piece": "Piece", "normalized_moves" : "Normalized Move Count"})

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

def four_moves_helper(data):
    fig = go.Figure(data = [
        go.Bar(name = 'White', x=data[data.columns[0]], y=data['white'], text=data['white'], textposition='auto', hovertemplate="White wins: %{y}"),
        go.Bar(name = 'Black', x=data[data.columns[0]], y=data['black'], text=data['black'], textposition='auto', hovertemplate="Black wins: %{y}"),
        go.Bar(name = 'Tie', x=data[data.columns[0]], y=data['tie'], text=data['tie'], textposition='auto', hovertemplate="Tie games: %{y}")
    ], )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'}, yaxis_title='Count')
    return fig

def first_four_moves(four_moves, white_first = None, black_first = None, white_second = None):
    four_moves = four_moves.copy()
    if white_first == None:
        four_moves = four_moves[['white first move', 'white', 'black', 'tie']]
        four_moves['white'] = four_moves.groupby('white first move')['white'].transform('sum')
        four_moves['black'] = four_moves.groupby('white first move')['black'].transform('sum')
        four_moves['tie'] = four_moves.groupby('white first move')['tie'].transform('sum')
        four_moves.drop_duplicates(inplace=True)
        fig = four_moves_helper(four_moves).update_layout(xaxis_title='White First Move')
        return fig
    
    if black_first == None:
        four_moves = four_moves[four_moves['white first move'] == white_first][['black first move', 'white', 'black', 'tie']]
        four_moves['white'] = four_moves.groupby('black first move')['white'].transform('sum')
        four_moves['black'] = four_moves.groupby('black first move')['black'].transform('sum')
        four_moves['tie'] = four_moves.groupby('black first move')['tie'].transform('sum')
        four_moves.drop_duplicates(inplace=True)
        fig = four_moves_helper(four_moves).update_layout(xaxis_title='Black First Move')
        return fig
    
    if white_second == None:
        four_moves = four_moves[(four_moves['white first move'] == white_first) & (four_moves['black first move'] == black_first)]
        four_moves = four_moves[['white second move', 'white', 'black', 'tie']]
        four_moves['white'] = four_moves.groupby('white second move')['white'].transform('sum')
        four_moves['black'] = four_moves.groupby('white second move')['black'].transform('sum')
        four_moves['tie'] = four_moves.groupby('white second move')['tie'].transform('sum')
        four_moves.drop_duplicates(inplace=True)
        fig = four_moves_helper(four_moves).update_layout(xaxis_title='White Second Move')
        return fig
    
    else:
        four_moves = four_moves[(four_moves['white first move'] == white_first) & (four_moves['black first move'] == black_first) & (four_moves['white second move'] == white_second)]
        four_moves = four_moves[['black second move', 'white', 'black', 'tie']]
        four_moves['white'] = four_moves.groupby('black second move')['white'].transform('sum')
        four_moves['black'] = four_moves.groupby('black second move')['black'].transform('sum')
        four_moves['tie'] = four_moves.groupby('black second move')['tie'].transform('sum')
        four_moves.drop_duplicates(inplace=True)
        fig = four_moves_helper(four_moves).update_layout(xaxis_title='Black Second Move')
        return fig

def pieces_captured(df):
    return px.bar(df, x='piece_type', y='capture_count', color='captured_piece_type', labels={"piece_type": "Capturing Piece", "capture_count" : "Number of Pieces Captured", "captured_piece_type" : "Captured Piece Type"})


def row_col(square):
    row = square//8
    col = square % 8
    return row,col
def board_heatmap(data, min_elo, max_elo):
    data = data[(data['mean_elo'] >= min_elo) & (data['mean_elo'] <= max_elo)]
    board = [
    [0]*8,
    [0]*8,
    [0]*8,
    [0]*8,
    [0]*8,
    [0]*8,
    [0]*8,
    [0]*8]
    for item in data['moves'].values:
        for square in item:
            row,col = row_col(square)
            board[row][col] += 1
    board.reverse()
    fig = px.imshow(board, labels=dict(x="Column", y="Row", color="Frequency"), x=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'], y=['8','7','6','5','4','3','2','1'])
    return fig