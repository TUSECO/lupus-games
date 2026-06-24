"""
Chess Engine - Satranç motoru
Hamle üretimi, kural kontrolü ve AI (Minimax + Alpha-Beta)
"""

import random
import copy
from typing import List, Tuple, Optional

# Taş değerleri
PIECE_VALUES = {
    'P': 100,   # Piyon
    'N': 320,   # At
    'B': 330,   # Fil
    'R': 500,   # Kale
    'Q': 900,   # Vezir
    'K': 20000  # Şah
}

# Pozisyon bonusları (beyaz için, siyah için ters çevrilir)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE_MID = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

PIECE_TABLES = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
    'K': KING_TABLE_MID,
}


class Piece:
    def __init__(self, piece_type: str, color: str):
        self.type = piece_type  # P, N, B, R, Q, K
        self.color = color      # 'white' veya 'black'
        self.has_moved = False

    def __repr__(self):
        prefix = 'w' if self.color == 'white' else 'b'
        return f"{prefix}{self.type}"

    def copy(self):
        p = Piece(self.type, self.color)
        p.has_moved = self.has_moved
        return p


class Move:
    def __init__(self, from_sq: Tuple[int, int], to_sq: Tuple[int, int],
                 piece: 'Piece', captured: Optional['Piece'] = None,
                 promotion: Optional[str] = None,
                 is_en_passant: bool = False,
                 is_castling: bool = False,
                 castling_rook_from: Optional[Tuple[int, int]] = None,
                 castling_rook_to: Optional[Tuple[int, int]] = None):
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.piece = piece
        self.captured = captured
        self.promotion = promotion
        self.is_en_passant = is_en_passant
        self.is_castling = is_castling
        self.castling_rook_from = castling_rook_from
        self.castling_rook_to = castling_rook_to

    def __repr__(self):
        cols = 'abcdefgh'
        fr, fc = self.from_sq
        tr, tc = self.to_sq
        return f"{cols[fc]}{8-fr}{cols[tc]}{8-tr}"

    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        return (self.from_sq == other.from_sq and
                self.to_sq == other.to_sq and
                self.promotion == other.promotion)


class ChessBoard:
    def __init__(self):
        self.board = [[None] * 8 for _ in range(8)]
        self.current_turn = 'white'
        self.en_passant_sq = None  # Geçerken alma karesi
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history: List[Move] = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self._setup_board()

    def _setup_board(self):
        """Taşları başlangıç pozisyonuna yerleştir"""
        # Siyah taşlar (üst)
        back_row = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for col, pt in enumerate(back_row):
            self.board[0][col] = Piece(pt, 'black')
            self.board[7][col] = Piece(pt, 'white')

        for col in range(8):
            self.board[1][col] = Piece('P', 'black')
            self.board[6][col] = Piece('P', 'white')

    def copy(self) -> 'ChessBoard':
        new_board = ChessBoard.__new__(ChessBoard)
        new_board.board = [[p.copy() if p else None for p in row] for row in self.board]
        new_board.current_turn = self.current_turn
        new_board.en_passant_sq = self.en_passant_sq
        new_board.halfmove_clock = self.halfmove_clock
        new_board.fullmove_number = self.fullmove_number
        new_board.move_history = list(self.move_history)
        new_board.white_king_pos = self.white_king_pos
        new_board.black_king_pos = self.black_king_pos
        return new_board

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def is_in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < 8 and 0 <= col < 8

    def get_king_pos(self, color: str) -> Tuple[int, int]:
        return self.white_king_pos if color == 'white' else self.black_king_pos

    def is_square_attacked(self, row: int, col: int, by_color: str) -> bool:
        """Bir karenin belirli renk tarafından tehdit altında olup olmadığını kontrol et"""
        enemy = by_color
        # At saldırısı
        knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, dc in knight_moves:
            r, c = row+dr, col+dc
            if self.is_in_bounds(r, c):
                p = self.board[r][c]
                if p and p.color == enemy and p.type == 'N':
                    return True

        # Düz çizgi (Kale, Vezir)
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            r, c = row+dr, col+dc
            while self.is_in_bounds(r, c):
                p = self.board[r][c]
                if p:
                    if p.color == enemy and p.type in ('R', 'Q'):
                        return True
                    break
                r += dr; c += dc

        # Çapraz (Fil, Vezir)
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            r, c = row+dr, col+dc
            while self.is_in_bounds(r, c):
                p = self.board[r][c]
                if p:
                    if p.color == enemy and p.type in ('B', 'Q'):
                        return True
                    break
                r += dr; c += dc

        # Piyon saldırısı
        pawn_dir = 1 if enemy == 'white' else -1
        for dc in [-1, 1]:
            r, c = row + pawn_dir, col + dc
            if self.is_in_bounds(r, c):
                p = self.board[r][c]
                if p and p.color == enemy and p.type == 'P':
                    return True

        # Şah saldırısı
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row+dr, col+dc
                if self.is_in_bounds(r, c):
                    p = self.board[r][c]
                    if p and p.color == enemy and p.type == 'K':
                        return True

        return False

    def is_in_check(self, color: str) -> bool:
        king_pos = self.get_king_pos(color)
        enemy = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(king_pos[0], king_pos[1], enemy)

    def generate_pseudo_moves(self, color: str) -> List[Move]:
        """Şah durumunu dikkate almadan tüm hamleleri üret"""
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    moves.extend(self._piece_moves(row, col, piece))
        return moves

    def _piece_moves(self, row: int, col: int, piece: Piece) -> List[Move]:
        moves = []
        if piece.type == 'P':
            moves = self._pawn_moves(row, col, piece)
        elif piece.type == 'N':
            moves = self._knight_moves(row, col, piece)
        elif piece.type == 'B':
            moves = self._sliding_moves(row, col, piece, [(1,1),(1,-1),(-1,1),(-1,-1)])
        elif piece.type == 'R':
            moves = self._sliding_moves(row, col, piece, [(0,1),(0,-1),(1,0),(-1,0)])
        elif piece.type == 'Q':
            moves = self._sliding_moves(row, col, piece,
                                        [(1,1),(1,-1),(-1,1),(-1,-1),(0,1),(0,-1),(1,0),(-1,0)])
        elif piece.type == 'K':
            moves = self._king_moves(row, col, piece)
        return moves

    def _pawn_moves(self, row: int, col: int, piece: Piece) -> List[Move]:
        moves = []
        direction = -1 if piece.color == 'white' else 1
        start_row = 6 if piece.color == 'white' else 1
        promo_row = 0 if piece.color == 'white' else 7

        # İleri hareket
        new_row = row + direction
        if self.is_in_bounds(new_row, col) and not self.board[new_row][col]:
            if new_row == promo_row:
                for promo in ['Q', 'R', 'B', 'N']:
                    moves.append(Move((row, col), (new_row, col), piece, promotion=promo))
            else:
                moves.append(Move((row, col), (new_row, col), piece))

            # Çift adım
            if row == start_row:
                new_row2 = row + 2 * direction
                if not self.board[new_row2][col]:
                    moves.append(Move((row, col), (new_row2, col), piece))

        # Çapraz yeme
        for dc in [-1, 1]:
            new_col = col + dc
            new_row = row + direction
            if self.is_in_bounds(new_row, new_col):
                target = self.board[new_row][new_col]
                if target and target.color != piece.color:
                    if new_row == promo_row:
                        for promo in ['Q', 'R', 'B', 'N']:
                            moves.append(Move((row, col), (new_row, new_col), piece,
                                             captured=target, promotion=promo))
                    else:
                        moves.append(Move((row, col), (new_row, new_col), piece, captured=target))
                # Geçerken alma
                elif (new_row, new_col) == self.en_passant_sq:
                    cap_piece = self.board[row][new_col]
                    moves.append(Move((row, col), (new_row, new_col), piece,
                                     captured=cap_piece, is_en_passant=True))
        return moves

    def _knight_moves(self, row: int, col: int, piece: Piece) -> List[Move]:
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            r, c = row+dr, col+dc
            if self.is_in_bounds(r, c):
                target = self.board[r][c]
                if not target or target.color != piece.color:
                    moves.append(Move((row, col), (r, c), piece, captured=target))
        return moves

    def _sliding_moves(self, row: int, col: int, piece: Piece, directions) -> List[Move]:
        moves = []
        for dr, dc in directions:
            r, c = row+dr, col+dc
            while self.is_in_bounds(r, c):
                target = self.board[r][c]
                if target:
                    if target.color != piece.color:
                        moves.append(Move((row, col), (r, c), piece, captured=target))
                    break
                moves.append(Move((row, col), (r, c), piece))
                r += dr; c += dc
        return moves

    def _king_moves(self, row: int, col: int, piece: Piece) -> List[Move]:
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                r, c = row+dr, col+dc
                if self.is_in_bounds(r, c):
                    target = self.board[r][c]
                    if not target or target.color != piece.color:
                        moves.append(Move((row, col), (r, c), piece, captured=target))

        # Rok
        if not piece.has_moved:
            enemy = 'black' if piece.color == 'white' else 'white'
            # Kısa rok (kingside)
            rook = self.board[row][7]
            if (rook and rook.type == 'R' and rook.color == piece.color and
                    not rook.has_moved and
                    not self.board[row][5] and not self.board[row][6] and
                    not self.is_square_attacked(row, 4, enemy) and
                    not self.is_square_attacked(row, 5, enemy) and
                    not self.is_square_attacked(row, 6, enemy)):
                moves.append(Move((row, col), (row, 6), piece,
                                  is_castling=True,
                                  castling_rook_from=(row, 7),
                                  castling_rook_to=(row, 5)))

            # Uzun rok (queenside)
            rook = self.board[row][0]
            if (rook and rook.type == 'R' and rook.color == piece.color and
                    not rook.has_moved and
                    not self.board[row][1] and not self.board[row][2] and
                    not self.board[row][3] and
                    not self.is_square_attacked(row, 4, enemy) and
                    not self.is_square_attacked(row, 3, enemy) and
                    not self.is_square_attacked(row, 2, enemy)):
                moves.append(Move((row, col), (row, 2), piece,
                                  is_castling=True,
                                  castling_rook_from=(row, 0),
                                  castling_rook_to=(row, 3)))
        return moves

    def generate_legal_moves(self, color: str) -> List[Move]:
        """Yasal hamleleri üret (şah durumu kontrolüyle)"""
        legal = []
        pseudo = self.generate_pseudo_moves(color)
        for move in pseudo:
            board_copy = self.copy()
            board_copy.apply_move(move)
            if not board_copy.is_in_check(color):
                legal.append(move)
        return legal

    def apply_move(self, move: Move):
        """Hamleyi tahtaya uygula"""
        fr, fc = move.from_sq
        tr, tc = move.to_sq
        piece = self.board[fr][fc]

        # Geçerken alma
        if move.is_en_passant:
            self.board[fr][tc] = None

        # Rok
        if move.is_castling:
            rfr, rfc = move.castling_rook_from
            rtr, rtc = move.castling_rook_to
            rook = self.board[rfr][rfc]
            self.board[rtr][rtc] = rook
            self.board[rfr][rfc] = None
            if rook:
                rook.has_moved = True

        # Terfi
        if move.promotion:
            piece = Piece(move.promotion, piece.color)

        self.board[tr][tc] = piece
        self.board[fr][fc] = None
        if piece:
            piece.has_moved = True

        # Şah pozisyonunu güncelle
        if piece and piece.type == 'K':
            if piece.color == 'white':
                self.white_king_pos = (tr, tc)
            else:
                self.black_king_pos = (tr, tc)

        # En passant karesi
        if piece and piece.type == 'P' and abs(tr - fr) == 2:
            self.en_passant_sq = ((fr + tr) // 2, fc)
        else:
            self.en_passant_sq = None

        # Sıra değiştir
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        self.move_history.append(move)

    def is_checkmate(self, color: str) -> bool:
        return self.is_in_check(color) and len(self.generate_legal_moves(color)) == 0

    def is_stalemate(self, color: str) -> bool:
        return not self.is_in_check(color) and len(self.generate_legal_moves(color)) == 0

    def is_game_over(self) -> Tuple[bool, Optional[str]]:
        """Oyun bitti mi? (bitti mi, kazanan)"""
        color = self.current_turn
        if self.is_checkmate(color):
            winner = 'black' if color == 'white' else 'white'
            return True, winner
        if self.is_stalemate(color):
            return True, None  # Berabere
        if self.halfmove_clock >= 100:
            return True, None  # 50 hamle kuralı
        return False, None


class ChessAI:
    def __init__(self, difficulty: str = 'medium'):
        self.difficulty = difficulty
        self.depth_map = {'easy': 1, 'medium': 3, 'hard': 5}
        self.nodes_evaluated = 0

    def get_best_move(self, board: ChessBoard, color: str) -> Optional[Move]:
        depth = self.depth_map.get(self.difficulty, 2)
        legal_moves = board.generate_legal_moves(color)
        if not legal_moves:
            return None

        if self.difficulty == 'easy':
            # Kolay: rastgele hamle seç (bazen iyi hamle yap)
            if random.random() < 0.3:
                return self._minimax_best(board, color, 1)
            return random.choice(legal_moves)

        return self._minimax_best(board, color, depth)

    def _minimax_best(self, board: ChessBoard, color: str, depth: int) -> Optional[Move]:
        legal_moves = board.generate_legal_moves(color)
        if not legal_moves:
            return None

        maximize = (color == 'white')
        best_score = float('-inf') if maximize else float('inf')
        best_move = None

        # Hamleleri sırala (daha iyi budama için)
        legal_moves = self._order_moves(legal_moves, board, color)

        for move in legal_moves:
            board_copy = board.copy()
            board_copy.apply_move(move)
            score = self._minimax(board_copy, depth - 1, float('-inf'), float('inf'),
                                  not maximize)
            if maximize:
                if score > best_score:
                    best_score = score
                    best_move = move
            else:
                if score < best_score:
                    best_score = score
                    best_move = move

        return best_move

    def _minimax(self, board: ChessBoard, depth: int, alpha: float, beta: float,
                 maximizing: bool) -> float:
        game_over, winner = board.is_game_over()
        if game_over:
            if winner == 'white':
                return 100000
            elif winner == 'black':
                return -100000
            else:
                return 0

        if depth == 0:
            return self._evaluate(board)

        color = 'white' if maximizing else 'black'
        moves = board.generate_legal_moves(color)
        moves = self._order_moves(moves, board, color)

        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                bc = board.copy()
                bc.apply_move(move)
                ev = self._minimax(bc, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                bc = board.copy()
                bc.apply_move(move)
                ev = self._minimax(bc, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval

    def _order_moves(self, moves: List[Move], board: ChessBoard, color: str) -> List[Move]:
        """Hamleleri değere göre sırala (budama verimliliği için)"""
        def score_move(m):
            s = 0
            if m.captured:
                s += PIECE_VALUES.get(m.captured.type, 0) * 10 - PIECE_VALUES.get(m.piece.type, 0)
            if m.promotion:
                s += PIECE_VALUES.get(m.promotion, 0)
            return s
        return sorted(moves, key=score_move, reverse=True)

    def _evaluate(self, board: ChessBoard) -> float:
        """Pozisyon değerlendirmesi"""
        score = 0
        for row in range(8):
            for col in range(8):
                piece = board.board[row][col]
                if not piece:
                    continue
                value = PIECE_VALUES.get(piece.type, 0)
                table = PIECE_TABLES.get(piece.type, None)
                if table:
                    if piece.color == 'white':
                        pos_bonus = table[row * 8 + col]
                    else:
                        pos_bonus = table[(7 - row) * 8 + col]
                    value += pos_bonus

                if piece.color == 'white':
                    score += value
                else:
                    score -= value
        return score
