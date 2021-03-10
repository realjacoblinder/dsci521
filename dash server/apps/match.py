from datetime import datetime
import chess.pgn
import numpy as np
from collections import Counter
import pandas as pd

class Match:
    def __init__(self, game):
        self.game = game
        self.white = game.headers.get('White')
        self.black = game.headers.get('Black')
        self.game_id = game.headers.get('Site').split('/')[-1]
        self.moves = self.get_moves()
        self.tracker = game.board().piece_map()
        self.start_tracker()
        self.black_elo = game.headers.get('BlackElo')
        self.white_elo = game.headers.get('WhiteElo')
        self.opening = game.headers.get('Opening')
        self.eco = game.headers.get('ECO')
        self.termination = game.headers.get('Termination')
        self.date = game.headers.get('UTCDate')
        self.winner = self.get_winner(game.headers.get('Result'))
        self.checkmate = True if str(game.mainline_moves())[-1] == '#' else False
        self.mainline_moves = game.mainline_moves()
        self.castle_tracker = {'white':0, 'black':0}
        self.check_tracker = []
    
    @staticmethod
    def get_winner(results):
        results = results.split('-')
        if results[0] == '1':
            return 'White'
        if results[0] == '1/2':
            return 'Tie'
        else:
            return 'Black'
        
    @staticmethod 
    def castling_move_rook(from_square, to_square):
        if from_square == 4:
            if to_square == 6:
                return {'piece':7, 'move':(7,5)}
            elif to_square == 2:
                return {'piece':0, 'move':(0,3)}
        elif from_square == 60:
            if to_square == 62:
                return {'piece':63, 'move':(63,61)}
            elif to_square == 58:
                return {'piece':56, 'move':(56,59)}
    
    def get_moves(self):
        moves = []
        for move in self.game.mainline_moves():
            from_m = move.from_square
            to_m = move.to_square
            moves.append((from_m, to_m))
            if '+' in str(move):
                mov_num = len(moves)
                self.check_tracker.append((mov_num-1, from_m, to_m))
        return moves
    
    @staticmethod
    def _to_uci(square):
        square = int(square)
        letter = chr(ord('a') + ((square)%8)) 
        number = square//8+1
        return f"{letter}{number}"
    
    def start_tracker(self):
        for key in self.tracker.keys():
            self.tracker[key] = {'piece': self.tracker[key].unicode_symbol()+'-'+str(self._to_uci(key)),\
                                 'moves':[], 'last_square':key,'captured':False, 'captures':[], 'move_nums':[]}
        
    def fill_tracker(self):
        for idx,mov in enumerate(self.moves):
            from_m, to_m = mov
            piece = [key for (key,value) in self.tracker.items() if value.get('last_square') == from_m and value.get('captured') is False][0]
            captured = [key for (key,value) in self.tracker.items() if value.get('last_square') == to_m and value.get('captured') is False]
            if len(captured) > 0:
                captured = captured[0]
                self.tracker[captured]['captured'] = True
                self.tracker[piece]['captures'].append(self.tracker[captured].get('piece'))
            self.tracker[piece]['moves'].append(to_m)
            if piece in [4,60] and abs(from_m - to_m) == 2:
                castled = self.castling_move_rook(from_m,to_m)
                self.tracker[castled['piece']]['moves'].append(castled['move'][1])
                self.tracker[castled['piece']]['last_square'] = castled['move'][1]
                self.castle_tracker['white' if piece == 4 else 'black'] += 1
            self.tracker[piece]['last_square'] = to_m
            self.tracker[piece]['move_nums'].append(idx)
        if self.checkmate == True:
            self.checkmate = self.tracker[piece]['piece']                
                
            
    def get_mean_elo(self):
        try:
            mean = (int(self.black_elo) + int(self.white_elo))/2
            return mean
        except:
            return np.nan
        
    def get_dataframe(self):
        df = pd.DataFrame.from_dict(self.tracker, orient='index')
        df['game_id'] = self.game_id
        df['mean_elo'] = self.get_mean_elo()
        df['Checkmate'] = self.checkmate
        df['Termination'] = self.termination
        
        return df
