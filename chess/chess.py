"""
PyQt6 Chess Game - Satranç Oyunu
Özellikler:
- Kolay / Orta / Zor modlar
- Rastgele renk ataması
- Otomatik veya manuel (iki taraf da sen) oynama modu
"""

import sys, os
import random
import threading
from typing import Optional, Tuple, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame, QDialog, QMessageBox,
    QButtonGroup, QRadioButton, QSizePolicy, QGraphicsDropShadowEffect,
    QStackedWidget, QGroupBox, QSpacerItem
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontDatabase, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPixmap, QPainterPath,
    QPolygonF, QIcon
)
from PyQt6.QtCore import (
    Qt, QSize, QRect, QPoint, QTimer, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve, QPointF, QRectF
)

from chess_engine import ChessBoard, ChessAI, Move, Piece


# ─────────────────────────── RENKLER ────────────────────────────
DARK_BG      = QColor("#0D1117")
CARD_BG      = QColor("#161B22")
CARD_BORDER  = QColor("#30363D")
LIGHT_SQ     = QColor("#F0D9B5")
DARK_SQ      = QColor("#B58863")
SELECTED_SQ  = QColor("#7FC97F")
VALID_SQ     = QColor("#48A999")
LAST_MOVE    = QColor("#CDD26A")
CHECK_SQ     = QColor("#E83535")
ACCENT       = QColor("#2188FF")
ACCENT2      = QColor("#7C3AED")
TEXT_WHITE   = QColor("#E6EDF3")
TEXT_MUTED   = QColor("#8B949E")
SUCCESS      = QColor("#3FB950")
WARNING      = QColor("#D29922")
DANGER       = QColor("#F85149")

# Taş unicode semboller
PIECE_UNICODE = {
    ('white', 'K'): '♔',
    ('white', 'Q'): '♕',
    ('white', 'R'): '♖',
    ('white', 'B'): '♗',
    ('white', 'N'): '♘',
    ('white', 'P'): '♙',
    ('black', 'K'): '♚',
    ('black', 'Q'): '♛',
    ('black', 'R'): '♜',
    ('black', 'B'): '♝',
    ('black', 'N'): '♞',
    ('black', 'P'): '♟',
}

DIFFICULTY_NAMES = {
    'easy': 'Easy',
    'medium': 'Medium',
    'hard': 'Hard'
}


class AIWorker(QThread):
    """AI hesaplamalarını ayrı thread'de yap"""
    move_ready = pyqtSignal(object)

    def __init__(self, ai: ChessAI, board: ChessBoard, color: str):
        super().__init__()
        self.ai = ai
        self.board = board
        self.color = color

    def run(self):
        move = self.ai.get_best_move(self.board, self.color)
        self.move_ready.emit(move)


class PromotionDialog(QDialog):
    """Piyon terfisi dialog"""
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.selected_piece = 'Q'
        self.setWindowTitle("Pawn Promotion")
        self.setModal(True)
        self.setFixedSize(380, 160)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DARK_BG.name()};
                border: 2px solid {CARD_BORDER.name()};
                border-radius: 12px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Choose stone for promotion:")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {TEXT_WHITE.name()}; font-size: 16px; font-weight: 600;")
        layout.addWidget(title)

        pieces_layout = QHBoxLayout()
        pieces_layout.setSpacing(10)

        for piece_type in ['Q', 'R', 'B', 'N']:
            btn = QPushButton(PIECE_UNICODE[(self.color, piece_type)])
            btn.setFixedSize(72, 72)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {CARD_BG.name()};
                    border: 2px solid {CARD_BORDER.name()};
                    border-radius: 10px;
                    font-size: 36px;
                    color: {'white' if self.color == 'white' else '#111'};
                }}
                QPushButton:hover {{
                    border-color: {ACCENT.name()};
                    background: #1F2937;
                }}
            """)
            btn.clicked.connect(lambda checked, pt=piece_type: self._select(pt))
            pieces_layout.addWidget(btn)

        layout.addLayout(pieces_layout)

    def _select(self, piece_type: str):
        self.selected_piece = piece_type
        self.accept()


class ChessBoardWidget(QWidget):
    """Satranç tahtası widget'ı"""
    move_made = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board: Optional[ChessBoard] = None
        self.player_color: str = 'white'
        self.selected_sq: Optional[Tuple[int, int]] = None
        self.valid_moves: List[Move] = []
        self.last_move: Optional[Move] = None
        self.flipped = False
        self.interactive = True
        self.setMinimumSize(520, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_board(self, board: ChessBoard, player_color: str):
        self.board = board
        self.player_color = player_color
        self.flipped = (player_color == 'black')
        self.selected_sq = None
        self.valid_moves = []
        self.last_move = None
        self.update()

    def set_last_move(self, move: Optional[Move]):
        self.last_move = move
        self.update()

    def sq_size(self) -> int:
        return min(self.width(), self.height()) // 8

    def sq_to_screen(self, row: int, col: int) -> Tuple[int, int]:
        sq = self.sq_size()
        if self.flipped:
            return (7 - col) * sq, (7 - row) * sq
        return col * sq, row * sq

    def screen_to_sq(self, x: int, y: int) -> Tuple[int, int]:
        sq = self.sq_size()
        file = x // sq
        rank = y // sq
        if self.flipped:
            return 7 - rank, 7 - file
        return rank, file

    def paintEvent(self, event):
        if not self.board:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        sq = self.sq_size()

        # Kareleri çiz
        for row in range(8):
            for col in range(8):
                x, y = self.sq_to_screen(row, col)
                is_light = (row + col) % 2 == 0
                color = LIGHT_SQ if is_light else DARK_SQ

                # Son hamle vurgusu
                if self.last_move:
                    if (row, col) in [self.last_move.from_sq, self.last_move.to_sq]:
                        color = LAST_MOVE

                # Seçili kare
                if self.selected_sq == (row, col):
                    color = SELECTED_SQ

                # Şah tehdidi
                if self.board and self.board.is_in_check(self.board.current_turn):
                    king_pos = self.board.get_king_pos(self.board.current_turn)
                    if (row, col) == king_pos:
                        color = CHECK_SQ

                painter.fillRect(x, y, sq, sq, color)

                # Geçerli hamle noktaları
                for move in self.valid_moves:
                    if move.to_sq == (row, col):
                        if move.captured:
                            # Yeme hamlesi - çerçeve
                            pen = QPen(VALID_SQ, 3)
                            painter.setPen(pen)
                            painter.setBrush(Qt.BrushStyle.NoBrush)
                            painter.drawRect(x + 2, y + 2, sq - 4, sq - 4)
                        else:
                            # Normal hamle - nokta
                            painter.setBrush(QBrush(VALID_SQ))
                            painter.setPen(Qt.PenStyle.NoPen)
                            dot_r = sq // 5
                            painter.drawEllipse(
                                x + sq // 2 - dot_r, y + sq // 2 - dot_r,
                                dot_r * 2, dot_r * 2
                            )

                # Koordinat etiketleri
                if col == 0:
                    rank_label = str(8 - row) if not self.flipped else str(row + 1)
                    lbl_color = DARK_SQ if is_light else LIGHT_SQ
                    painter.setPen(QPen(lbl_color))
                    f = QFont("Arial", max(8, sq // 8))
                    f.setBold(True)
                    painter.setFont(f)
                    painter.drawText(x + 2, y + sq // 4 + 2, rank_label)

                if row == 7:
                    file_labels = 'abcdefgh'
                    fl = file_labels[col] if not self.flipped else file_labels[7 - col]
                    is_light2 = (row + col) % 2 == 0
                    lbl_color = DARK_SQ if is_light2 else LIGHT_SQ
                    painter.setPen(QPen(lbl_color))
                    painter.drawText(x + sq - sq // 5, y + sq - 2, fl)

        # Taşları çiz
        for row in range(8):
            for col in range(8):
                piece = self.board.board[row][col]
                if not piece:
                    continue
                x, y = self.sq_to_screen(row, col)
                symbol = PIECE_UNICODE.get((piece.color, piece.type), '?')

                # Gölge
                painter.setPen(Qt.PenStyle.NoPen)
                shadow_color = QColor(0, 0, 0, 60)
                painter.setBrush(QBrush(shadow_color))
                painter.drawEllipse(x + sq//6 + 2, y + sq//2 + 2, sq * 2 // 3, sq // 4)

                # Taş metni
                font_size = max(14, int(sq * 0.72))
                font = QFont("Segoe UI Symbol", font_size)
                painter.setFont(font)

                # Beyaz taş için dış çizgi (görünürlük için)
                if piece.color == 'white':
                    painter.setPen(QPen(QColor(80, 60, 40, 120), 2))
                else:
                    painter.setPen(QPen(QColor(255, 255, 255, 80), 1))

                text_rect = QRect(x, y, sq, sq)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, symbol)

                if piece.color == 'white':
                    painter.setPen(QPen(QColor(255, 255, 255)))
                else:
                    painter.setPen(QPen(QColor(30, 20, 10)))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, symbol)

        painter.end()

    def mousePressEvent(self, event):
        if not self.board or not self.interactive:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return

        x = int(event.position().x())
        y = int(event.position().y())
        row, col = self.screen_to_sq(x, y)

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board.board[row][col]

        if self.selected_sq:
            # Hamle dene
            move = self._find_move(self.selected_sq, (row, col))
            if move:
                # Terfi kontrolü
                if move.promotion and move.promotion == 'Q':
                    # Terfi dialogu göster
                    dialog = PromotionDialog(piece.color if piece else
                                            self.board.board[self.selected_sq[0]][self.selected_sq[1]].color,
                                            self)
                    promo_piece = self.board.board[self.selected_sq[0]][self.selected_sq[1]]
                    dialog2 = PromotionDialog(promo_piece.color if promo_piece else 'white', self)
                    if dialog2.exec():
                        # Seçilen terfi ile hamleyi bul
                        promo_move = self._find_move(self.selected_sq, (row, col), dialog2.selected_piece)
                        if promo_move:
                            move = promo_move
                        else:
                            move.promotion = dialog2.selected_piece

                self.selected_sq = None
                self.valid_moves = []
                self.move_made.emit(move)
                self.update()
                return

            # Başka taş seç
            if piece and piece.color == self.board.current_turn:
                self.selected_sq = (row, col)
                self.valid_moves = [m for m in self.board.generate_legal_moves(piece.color)
                                    if m.from_sq == (row, col)]
                self.update()
            else:
                self.selected_sq = None
                self.valid_moves = []
                self.update()
        else:
            # Taş seç
            if piece and piece.color == self.board.current_turn:
                self.selected_sq = (row, col)
                self.valid_moves = [m for m in self.board.generate_legal_moves(piece.color)
                                    if m.from_sq == (row, col)]
                self.update()

    def _find_move(self, from_sq, to_sq, promotion='Q') -> Optional[Move]:
        for move in self.valid_moves:
            if move.from_sq == from_sq and move.to_sq == to_sq:
                if move.promotion:
                    if move.promotion == promotion:
                        return move
                else:
                    return move
        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()


class GameSettingsWidget(QWidget):
    """Oyun ayarları ekranı"""
    game_start = pyqtSignal(str, str, str)  # difficulty, opponent_mode, player_color

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Başlık
        title = QLabel("♟ CHESS GAME ♟")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 48px;
            font-weight: 800;
            color: #E6EDF3;
            letter-spacing: 8px;
        """)
        layout.addWidget(title)

        # Ana kart
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG.name()};
                border: 1px solid {CARD_BORDER.name()};
                border-radius: 16px;
                padding: 24px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(22)
        card_layout.setContentsMargins(30, 30, 30, 30)

        # ── Zorluk Seçimi ──
        diff_group = self._make_group("🎯  Difficulty")
        diff_h = QHBoxLayout()
        diff_h.setSpacing(10)

        self.diff_btns = {}
        diff_options = [('easy', '😊  Easy'), ('medium', '🧠  Medium'), ('hard', '🔥  Hard')]
        self.diff_bg = QButtonGroup(self)

        for i, (key, label) in enumerate(diff_options):
            rb = QRadioButton(label)
            rb.setStyleSheet(self._radio_style())
            self.diff_bg.addButton(rb, i)
            self.diff_btns[key] = rb
            diff_h.addWidget(rb)
            if key == 'medium':
                rb.setChecked(True)

        diff_group.layout().addLayout(diff_h)
        card_layout.addWidget(diff_group)

        # ── Rakip Modu ──
        opp_group = self._make_group("🤖  Opponent Mode")
        opp_h = QHBoxLayout()
        opp_h.setSpacing(10)

        self.opp_btns = {}
        opp_options = [('ai', '🤖  AI'), ('manual', '👥  Manual (You Play)')]
        self.opp_bg = QButtonGroup(self)

        for i, (key, label) in enumerate(opp_options):
            rb = QRadioButton(label)
            rb.setStyleSheet(self._radio_style())
            self.opp_bg.addButton(rb, i)
            self.opp_btns[key] = rb
            opp_h.addWidget(rb)
            if key == 'ai':
                rb.setChecked(True)

        opp_group.layout().addLayout(opp_h)
        card_layout.addWidget(opp_group)

        # ── Renk Seçimi ──
        color_group = self._make_group("🎨  Color Selection")
        color_h = QHBoxLayout()
        color_h.setSpacing(10)

        self.color_btns = {}
        color_options = [('random', '🎲  Random'), ('white', '⬜  White'), ('black', '⬛  Black')]
        self.color_bg = QButtonGroup(self)

        for i, (key, label) in enumerate(color_options):
            rb = QRadioButton(label)
            rb.setStyleSheet(self._radio_style())
            self.color_bg.addButton(rb, i)
            self.color_btns[key] = rb
            color_h.addWidget(rb)
            if key == 'random':
                rb.setChecked(True)

        color_group.layout().addLayout(color_h)
        card_layout.addWidget(color_group)

        layout.addWidget(card)

        # ── Başlat Butonu ──
        start_btn = QPushButton("  START GAME  ")
        start_btn.setFixedHeight(56)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT.name()}, stop:1 {ACCENT2.name()});
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: 700;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3AA0FF, stop:1 #9B59B6);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1A80EF, stop:1 #6C3493);
            }}
        """)
        start_btn.clicked.connect(self._start_game)
        layout.addWidget(start_btn)

    def _make_group(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: 1px solid {CARD_BORDER.name()};
                border-radius: 10px;
                padding: 4px;
            }}
        """)
        vl = QVBoxLayout(frame)
        vl.setSpacing(8)
        vl.setContentsMargins(14, 10, 14, 14)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #8B949E; border: none;")
        vl.addWidget(lbl)
        return frame

    def _radio_style(self) -> str:
        return f"""
            QRadioButton {{
                color: {TEXT_WHITE.name()};
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 8px;
                background: transparent;
            }}
            QRadioButton:hover {{
                background: #21262D;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {CARD_BORDER.name()};
                background: transparent;
            }}
            QRadioButton::indicator:checked {{
                background: {ACCENT.name()};
                border-color: {ACCENT.name()};
            }}
        """

    def _start_game(self):
        diff = next((k for k, v in self.diff_btns.items() if v.isChecked()), 'medium')
        opp = next((k for k, v in self.opp_btns.items() if v.isChecked()), 'ai')
        color = next((k for k, v in self.color_btns.items() if v.isChecked()), 'random')

        if color == 'random':
            color = random.choice(['white', 'black'])

        self.game_start.emit(diff, opp, color)


class MoveListWidget(QWidget):
    """Hamle listesi widget'ı"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.moves: List[str] = []
        self.setFixedWidth(180)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("📋 Hamleler")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {TEXT_WHITE.name()};
            font-size: 13px;
            font-weight: 600;
            padding: 8px;
            background: {CARD_BG.name()};
            border-bottom: 1px solid {CARD_BORDER.name()};
            border-radius: 8px 8px 0 0;
        """)
        layout.addWidget(title)

        self.move_container = QWidget()
        self.move_container.setStyleSheet(f"background: {CARD_BG.name()};")
        self.move_layout = QVBoxLayout(self.move_container)
        self.move_layout.setContentsMargins(8, 8, 8, 8)
        self.move_layout.setSpacing(2)
        self.move_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.move_container)

        self.setStyleSheet(f"""
            background: {CARD_BG.name()};
            border: 1px solid {CARD_BORDER.name()};
            border-radius: 8px;
        """)

    def add_move(self, move_num: int, white_move: str, black_move: str = ''):
        text = f"{move_num}. {white_move}"
        if black_move:
            text += f"  {black_move}"
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {TEXT_WHITE.name()};
            font-size: 12px;
            font-family: monospace;
            padding: 3px 6px;
            border-radius: 4px;
            background: {'#21262D' if move_num % 2 == 0 else 'transparent'};
        """)
        self.move_layout.addWidget(lbl)

    def clear_moves(self):
        while self.move_layout.count():
            item = self.move_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class GameWidget(QWidget):
    """Oyun ekranı"""
    back_to_menu = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board: Optional[ChessBoard] = None
        self.ai: Optional[ChessAI] = None
        self.player_color: str = 'white'
        self.opponent_mode: str = 'ai'
        self.difficulty: str = 'medium'
        self.ai_worker: Optional[AIWorker] = None
        self.game_over: bool = False
        self.move_count: int = 0
        self.ai_thinking: bool = False
        self._setup_ui()

    def _setup_ui(self):
        main = QHBoxLayout(self)
        main.setSpacing(16)
        main.setContentsMargins(16, 16, 16, 16)

        # Sol panel
        left = QVBoxLayout()
        left.setSpacing(10)

        # Üst bilgi
        self.info_bar = QWidget()
        self.info_bar.setFixedHeight(52)
        self.info_bar.setStyleSheet(f"""
            background: {CARD_BG.name()};
            border: 1px solid {CARD_BORDER.name()};
            border-radius: 10px;
        """)
        info_h = QHBoxLayout(self.info_bar)
        info_h.setContentsMargins(16, 8, 16, 8)
        info_h.setSpacing(16)

        self.turn_label = QLabel("⬜ White's Turn")
        self.turn_label.setStyleSheet(f"color: {TEXT_WHITE.name()}; font-size: 15px; font-weight: 600;")
        info_h.addWidget(self.turn_label)

        info_h.addStretch()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED.name()}; font-size: 13px;")
        info_h.addWidget(self.status_label)

        left.addWidget(self.info_bar)

        # Siyah oyuncu bilgisi
        self.black_info = self._player_bar('black')
        left.addWidget(self.black_info)

        # Tahta
        self.chess_board = ChessBoardWidget()
        self.chess_board.move_made.connect(self.on_move_made)
        left.addWidget(self.chess_board)

        # Beyaz oyuncu bilgisi
        self.white_info = self._player_bar('white')
        left.addWidget(self.white_info)

        main.addLayout(left, stretch=3)

        # Sağ panel
        right = QVBoxLayout()
        right.setSpacing(10)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Bilgi kartı
        info_card = QFrame()
        info_card.setStyleSheet(f"""
            QFrame {{
                background: {CARD_BG.name()};
                border: 1px solid {CARD_BORDER.name()};
                border-radius: 10px;
                padding: 4px;
            }}
        """)
        info_v = QVBoxLayout(info_card)
        info_v.setContentsMargins(14, 14, 14, 14)
        info_v.setSpacing(8)

        self.diff_label = QLabel("Difficulty: —")
        self.diff_label.setStyleSheet(f"color: {TEXT_MUTED.name()}; font-size: 12px;")

        self.mode_label = QLabel("Mode: —")
        self.mode_label.setStyleSheet(f"color: {TEXT_MUTED.name()}; font-size: 12px;")

        self.color_label = QLabel("Color: —")
        self.color_label.setStyleSheet(f"color: {TEXT_MUTED.name()}; font-size: 12px;")

        self.ai_status = QLabel("")
        self.ai_status.setStyleSheet(f"color: {WARNING.name()}; font-size: 12px; font-weight: 600;")

        for lbl in [self.diff_label, self.mode_label, self.color_label, self.ai_status]:
            info_v.addWidget(lbl)

        right.addWidget(info_card)

        # Hamle listesi
        self.move_list = MoveListWidget()
        right.addWidget(self.move_list)

        # Butonlar
        btn_style_primary = f"""
            QPushButton {{
                background: {ACCENT.name()};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
            }}
            QPushButton:hover {{ background: #3AA0FF; }}
            QPushButton:pressed {{ background: #1A80EF; }}
        """
        btn_style_danger = f"""
            QPushButton {{
                background: {CARD_BG.name()};
                color: {DANGER.name()};
                border: 1px solid {DANGER.name()};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
            }}
            QPushButton:hover {{ background: #2D1B1B; }}
        """
        btn_style_neutral = f"""
            QPushButton {{
                background: {CARD_BG.name()};
                color: {TEXT_WHITE.name()};
                border: 1px solid {CARD_BORDER.name()};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px;
            }}
            QPushButton:hover {{ background: #21262D; }}
        """

        new_game_btn = QPushButton("🔄  New Game")
        new_game_btn.setStyleSheet(btn_style_primary)
        new_game_btn.clicked.connect(self.back_to_menu.emit)
        right.addWidget(new_game_btn)

        flip_btn = QPushButton("🔃  Flip Board")
        flip_btn.setStyleSheet(btn_style_neutral)
        flip_btn.clicked.connect(self._flip_board)
        right.addWidget(flip_btn)

        resign_btn = QPushButton("🏳  Resign")
        resign_btn.setStyleSheet(btn_style_danger)
        resign_btn.clicked.connect(self._resign)
        right.addWidget(resign_btn)

        right.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(200)
        main.addWidget(right_widget)

    def _player_bar(self, color: str) -> QWidget:
        w = QWidget()
        w.setFixedHeight(46)
        w.setStyleSheet(f"""
            background: {CARD_BG.name()};
            border: 1px solid {CARD_BORDER.name()};
            border-radius: 8px;
        """)
        h = QHBoxLayout(w)
        h.setContentsMargins(12, 6, 12, 6)
        h.setSpacing(10)

        symbol = "⬜" if color == 'white' else "⬛"
        name = QLabel(f"{symbol}  {'White' if color == 'white' else 'Black'}")
        name.setStyleSheet(f"color: {TEXT_WHITE.name()}; font-size: 14px; font-weight: 600;")
        h.addWidget(name)
        h.addStretch()

        role = QLabel("")
        role.setObjectName(f"{color}_role")
        role.setStyleSheet(f"color: {TEXT_MUTED.name()}; font-size: 12px;")
        h.addWidget(role)

        setattr(self, f"{color}_role_label", role)
        return w

    def start_game(self, difficulty: str, opponent_mode: str, player_color: str):
        self.difficulty = difficulty
        self.opponent_mode = opponent_mode
        self.player_color = player_color
        self.board = ChessBoard()
        self.ai = ChessAI(difficulty)
        self.game_over = False
        self.move_count = 0
        self.ai_thinking = False

        self.chess_board.set_board(self.board, player_color)
        self.chess_board.interactive = True
        self.move_list.clear_moves()

        # Bilgi güncelle
        self.diff_label.setText(f"Difficulty: {DIFFICULTY_NAMES.get(difficulty, difficulty)}")

        if opponent_mode == 'ai':
            mode_text = "Mode: vs AI"
        else:
            mode_text = "Mode: Manual (Two Players)"
        self.mode_label.setText(mode_text)

        color_icon = '⬜' if player_color == 'white' else '⬛'
        self.color_label.setText(f"Color: {color_icon} {'White' if player_color == 'white' else 'Black'}")

        # Oyuncu rolleri
        if opponent_mode == 'ai':
            self.white_role_label.setText("👤 You" if player_color == 'white' else "🤖 AI")
            self.black_role_label.setText("🤖 AI" if player_color == 'white' else "👤 You")
        else:
            self.white_role_label.setText("👤 Player")
            self.black_role_label.setText("👤 Player")

        self._update_turn_label()

        # AI siyah ise başta hamle yap
        if opponent_mode == 'ai' and player_color == 'white':
            # Beyaz ilk başlar, biz oynayacağız
            pass
        elif opponent_mode == 'ai' and player_color == 'black':
            # AI beyaz, hemen oynasın
            QTimer.singleShot(500, self._trigger_ai_move)

    def _update_turn_label(self):
        if not self.board:
            return
        turn = self.board.current_turn
        icon = "⬜" if turn == 'white' else "⬛"
        turn_name = "White" if turn == 'white' else "Black"
        self.turn_label.setText(f"{icon}  {turn_name}'s Turn")

        if self.board.is_in_check(turn):
            self.status_label.setText("⚠️ CHECK!")
            self.status_label.setStyleSheet(f"color: {DANGER.name()}; font-size: 13px; font-weight: 700;")
        else:
            self.status_label.setText("")

    def on_move_made(self, move: Move):
        """Kullanıcı hamle yaptı"""
        if self.game_over or not self.board:
            return

        # Manuel modda her iki taraf da oynayabilir,
        # AI modunda sadece oyuncunun sırasında hamle yapılır
        if self.opponent_mode == 'ai' and self.board.current_turn != self.player_color:
            return

        # Hamlenin geçerli olup olmadığını tekrar doğrula
        legal = self.board.generate_legal_moves(self.board.current_turn)
        if move not in legal:
            return

        # Hamleyi uygula
        self._apply_move(move)

        # Oyun bitti mi?
        over, winner = self.board.is_game_over()
        if over:
            self._game_over(winner)
            return

        # AI sırası
        if self.opponent_mode == 'ai' and self.board.current_turn != self.player_color:
            QTimer.singleShot(300, self._trigger_ai_move)

    def _apply_move(self, move: Move):
        if not self.board:
            return

        current = self.board.current_turn
        piece = self.board.board[move.from_sq[0]][move.from_sq[1]]
        self.board.apply_move(move)
        self.chess_board.set_last_move(move)
        self.chess_board.selected_sq = None
        self.chess_board.valid_moves = []
        self.chess_board.update()
        self._update_turn_label()

        # Hamle listesine ekle (terfi sembolü)
        move_str = str(move)
        if move.promotion:
            move_str += f"={move.promotion}"
        if move.is_castling:
            cols_diff = move.to_sq[1] - move.from_sq[1]
            move_str = "O-O" if cols_diff > 0 else "O-O-O"

        if current == 'white':
            self.move_count += 1
            self._pending_white = move_str
        else:
            white_m = getattr(self, '_pending_white', '—')
            self.move_list.add_move(self.move_count, white_m, move_str)
            self._pending_white = None

    def _trigger_ai_move(self):
        if self.game_over or not self.board or not self.ai or self.ai_thinking:
            return

        self.ai_thinking = True
        self.ai_status.setText("🤔 AI düşünüyor...")
        self.chess_board.interactive = False

        self.ai_worker = AIWorker(self.ai, self.board.copy(), self.board.current_turn)
        self.ai_worker.move_ready.connect(self._on_ai_move)
        self.ai_worker.start()

    def _on_ai_move(self, move: Optional[Move]):
        self.ai_thinking = False
        self.ai_status.setText("")
        # Manuel modda her zaman interaktif, AI modunda oyuncu sırası gelince interaktif
        self.chess_board.interactive = True

        if move is None or self.game_over or not self.board:
            return

        self._apply_move(move)

        over, winner = self.board.is_game_over()
        if over:
            self._game_over(winner)

    def _game_over(self, winner: Optional[str]):
        self.game_over = True
        self.chess_board.interactive = False

        # Bekleyen beyaz hamlesini listeye ekle
        pending = getattr(self, '_pending_white', None)
        if pending:
            self.move_list.add_move(self.move_count, pending, '')
            self._pending_white = None

        if winner is None:
            title = "Draw!"
            msg = "The game ended in a draw. (Stalemate / 50-move rule)"
            icon = "🤝"
        elif self.opponent_mode == 'manual':
            winner_name = "White" if winner == 'white' else "Black"
            title = f"{winner_name} Wins!"
            msg = f"{winner_name} won the game! Congratulations! 👑"
            icon = "🏆"
        elif winner == self.player_color:
            title = "Congratulations!"
            msg = "You won! Great gameplay! 🎉"
            icon = "🏆"
        else:
            title = "AI Won"
            msg = "The AI defeated you. Try again!"
            icon = "🤖"

        self.turn_label.setText(f"{icon}  {title}")
        self.turn_label.setStyleSheet(f"color: {SUCCESS.name()}; font-size: 15px; font-weight: 700;")
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {TEXT_MUTED.name()}; font-size: 13px;")

        QTimer.singleShot(800, lambda: self._show_game_over_dialog(icon, title, msg))

    def _show_game_over_dialog(self, icon: str, title: str, msg: str):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(f"{icon}\n\n{title}\n\n{msg}")
        dialog.setInformativeText("What would you like to do?")
        dialog.addButton("🔄 New Game", QMessageBox.ButtonRole.AcceptRole)
        dialog.addButton("❌ Close", QMessageBox.ButtonRole.RejectRole)
        dialog.setStyleSheet(f"""
            QMessageBox {{
                background: {DARK_BG.name()};
                color: {TEXT_WHITE.name()};
            }}
            QLabel {{
                color: {TEXT_WHITE.name()};
                font-size: 16px;
            }}
            QPushButton {{
                background: {ACCENT.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #3AA0FF; }}
        """)
        result = dialog.exec()
        if result == 0:
            self.back_to_menu.emit()

    def _flip_board(self):
        self.chess_board.flipped = not self.chess_board.flipped
        self.chess_board.update()

    def _resign(self):
        if self.game_over:
            return
        reply = QMessageBox.question(
            self, "Resign",
            "Are you sure you want to resign?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            loser = self.player_color if self.opponent_mode == 'ai' else self.board.current_turn
            winner = 'black' if loser == 'white' else 'white'
            self._game_over(winner)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICONS_DIR = os.path.join(_BASE_DIR)

def _icon(name: str) -> QIcon:
    """İkon klasöründen QIcon döndürür."""
    return QIcon(os.path.join(_ICONS_DIR, name))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("♟ Chess Game ♟")
        self.setMinimumSize(860, 720)
        self.resize(1000, 780)
        self._apply_global_style()
        self._setup_ui()
        self.setWindowIcon(_icon("chess.png"))

    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {DARK_BG.name()};
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            }}
            QScrollBar:vertical {{
                background: {CARD_BG.name()};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {CARD_BORDER.name()};
                border-radius: 4px;
            }}
        """)

    def _setup_ui(self):
        self.stacked = QStackedWidget()
        self.setCentralWidget(self.stacked)

        self.settings_widget = GameSettingsWidget()
        self.settings_widget.game_start.connect(self._start_game)

        self.game_widget = GameWidget()
        self.game_widget.back_to_menu.connect(self._back_to_menu)

        self.stacked.addWidget(self.settings_widget)
        self.stacked.addWidget(self.game_widget)
        self.stacked.setCurrentIndex(0)

    def _start_game(self, difficulty: str, opponent_mode: str, player_color: str):
        self.game_widget.start_game(difficulty, opponent_mode, player_color)
        self.stacked.setCurrentIndex(1)

    def _back_to_menu(self):
        self.stacked.setCurrentIndex(0)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Chess Game")
    app.setStyle("Fusion")

    # Font ayarla
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
