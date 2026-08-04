import sys, os, random, time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFrame, QDialog, QComboBox,
    QSlider, QSpinBox, QFormLayout, QMessageBox, QSizePolicy,
    QGraphicsDropShadowEffect, QToolButton, QStatusBar
)
from PyQt6.QtCore import (
    Qt, QTimer, QSize, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QLinearGradient,
    QBrush, QPen, QRadialGradient, QFontMetrics, QPixmap,
    QCursor
)


# ─────────────────────────────────────────────────────────────────────────────
# THEME / PALETTE
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":        "#0d0f1a",
    "bg_panel":       "#141627",
    "bg_card":        "#1a1d30",
    "accent":         "#6c63ff",
    "accent_glow":    "#8b84ff",
    "accent2":        "#00d4aa",
    "danger":         "#ff4757",
    "warning":        "#ffa502",
    "success":        "#2ed573",
    "cell_hidden":    "#1e2240",
    "cell_hover":     "#252848",
    "cell_revealed":  "#0f1120",
    "cell_border":    "#2d3260",
    "text_primary":   "#e8eaf6",
    "text_secondary": "#8b92c9",
    "flag":           "#ff4757",
    "mine":           "#ff2d55",
    "number_colors": ["", "#4fc3f7", "#69f0ae", "#ef5350", "#7986cb",
                      "#ff7043", "#26c6da", "#ec407a", "#bdbdbd"],
}

DIFFICULTY_PRESETS = {
    "Beginner":     {"rows": 9,  "cols": 9,  "mines": 10},
    "Intermediate": {"rows": 16, "cols": 16, "mines": 40},
    "Expert":       {"rows": 16, "cols": 30, "mines": 99},
    "Custom":       {"rows": 10, "cols": 10, "mines": 15},
}

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICONS_DIR = os.path.join(_BASE_DIR)

def _icon(name: str) -> QIcon:
    return QIcon(os.path.join(_ICONS_DIR, name))


# ─────────────────────────────────────────────────────────────────────────────
# CELL WIDGET
# ─────────────────────────────────────────────────────────────────────────────
class CellButton(QPushButton):
    right_clicked = pyqtSignal(int, int)

    def __init__(self, row: int, col: int, cell_size: int = 36, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.cell_size = cell_size
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.is_questioned = False
        self.neighbor_count = 0
        self._hovering = False

        self.setFixedSize(cell_size, cell_size)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._apply_hidden_style()

    def _apply_hidden_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #252848, stop:1 #1e2240);
                border: 1px solid #2d3260;
                border-radius: 4px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #2e3360, stop:1 #252848);
                border: 1px solid {COLORS['accent']};
            }}
            QPushButton:pressed {{
                background: #141627;
                border: 1px solid {COLORS['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.row, self.col)
        else:
            super().mousePressEvent(event)

    def update_visual(self, game_over=False, show_mines=False):
        size = self.cell_size
        fs = max(8, int(size * 0.42))
        icon_fs = max(10, int(size * 0.50))

        if self.is_flagged and not self.is_revealed:
            self.setText("🚩")
            self.setFont(QFont("Segoe UI Emoji", icon_fs))
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #3a1f2e, stop:1 #2a1520);
                    border: 1px solid {COLORS['flag']};
                    border-radius: 4px;
                    color: {COLORS['flag']};
                }}
            """)
            return

        if self.is_questioned and not self.is_revealed:
            self.setText("?")
            self.setFont(QFont("Arial", fs, QFont.Weight.Bold))
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 #2a2830, stop:1 #1e1d28);
                    border: 1px solid {COLORS['warning']};
                    border-radius: 4px;
                    color: {COLORS['warning']};
                }}
            """)
            return

        if not self.is_revealed:
            if show_mines and self.is_mine:
                self.setText("💣")
                self.setFont(QFont("Segoe UI Emoji", icon_fs))
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: #3a0010;
                        border: 1px solid {COLORS['mine']};
                        border-radius: 4px;
                    }}
                """)
            else:
                self._apply_hidden_style()
                self.setText("")
            return

        # Revealed
        if self.is_mine:
            self.setText("💣")
            self.setFont(QFont("Segoe UI Emoji", icon_fs))
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qradialgradient(cx:0.5,cy:0.5,radius:0.8,
                        fx:0.5,fy:0.5,
                        stop:0 #5a0020, stop:1 #2a0010);
                    border: 2px solid {COLORS['mine']};
                    border-radius: 4px;
                }}
            """)
        elif self.neighbor_count > 0:
            color = COLORS["number_colors"][self.neighbor_count]
            self.setText(str(self.neighbor_count))
            self.setFont(QFont("Arial", fs, QFont.Weight.Bold))
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['cell_revealed']};
                    border: 1px solid #1a1d30;
                    border-radius: 4px;
                    color: {color};
                }}
            """)
        else:
            self.setText("")
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['cell_revealed']};
                    border: 1px solid #1a1d30;
                    border-radius: 4px;
                }}
            """)

    def resize_cell(self, new_size: int):
        self.cell_size = new_size
        self.setFixedSize(new_size, new_size)
        self.update_visual()


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM DIFFICULTY DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Minesweeper")
        self.setFixedSize(340, 240)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_panel']};
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QSpinBox {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['cell_border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                min-width: 80px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {COLORS['accent']};
                border-radius: 3px;
                width: 18px;
            }}
            QPushButton {{
                background: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['accent_glow']};
            }}
            QPushButton#cancel_btn {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['cell_border']};
            }}
            QPushButton#cancel_btn:hover {{
                background: {COLORS['cell_hover']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("⚙  Custom Game Settings")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent_glow']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(5, 30)
        self.rows_spin.setValue(10)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(5, 50)
        self.cols_spin.setValue(10)

        self.mines_spin = QSpinBox()
        self.mines_spin.setRange(1, 500)
        self.mines_spin.setValue(15)

        form.addRow("Rows:", self.rows_spin)
        form.addRow("Columns:", self.cols_spin)
        form.addRow("Mines:", self.mines_spin)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Start Game")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel_btn")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def get_values(self):
        r = self.rows_spin.value()
        c = self.cols_spin.value()
        m = min(self.mines_spin.value(), r * c - 9)
        return r, c, max(1, m)


# ─────────────────────────────────────────────────────────────────────────────
# STATS / WIN DIALOG
# ─────────────────────────────────────────────────────────────────────────────
class ResultDialog(QDialog):
    def __init__(self, won: bool, elapsed: int, mines: int, flags: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Over" if not won else "You Won!")
        self.setFixedSize(380, 280)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_panel']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QPushButton {{
                border: none;
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 13px;
                font-weight: bold;
                color: white;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        if won:
            emoji = "🏆"
            headline = "You Win!"
            color = COLORS["success"]
        else:
            emoji = "💥"
            headline = "Boom! Game Over"
            color = COLORS["danger"]

        em_label = QLabel(emoji)
        em_label.setFont(QFont("Segoe UI Emoji", 42))
        em_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(em_label)

        hl = QLabel(headline)
        hl.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.setStyleSheet(f"color: {color};")
        layout.addWidget(hl)

        mins, secs = divmod(elapsed, 60)
        stats = QLabel(
            f"⏱  Time: {mins:02d}:{secs:02d}     💣 Mines: {mines}     🚩 Flags: {flags}"
        )
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(stats)

        btn_row = QHBoxLayout()

        again_btn = QPushButton("Play Again")
        again_btn.setStyleSheet(f"background: {color};")
        again_btn.clicked.connect(lambda: self.done(1))

        menu_btn = QPushButton("Main Menu")
        menu_btn.setStyleSheet(
            f"background: {COLORS['bg_card']}; color: {COLORS['text_secondary']};"
            f"border: 1px solid {COLORS['cell_border']};"
        )
        menu_btn.clicked.connect(lambda: self.done(2))

        btn_row.addWidget(menu_btn)
        btn_row.addWidget(again_btn)
        layout.addLayout(btn_row)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN GAME WINDOW
# ─────────────────────────────────────────────────────────────────────────────
class MinesweeperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minesweeper")
        self.setMinimumSize(500, 400)
        self.setWindowIcon(_icon("favicon.png"))

        # Game state
        self.rows = 9
        self.cols = 9
        self.total_mines = 10
        self.cell_size = 36
        self.difficulty = "Beginner"

        self.cells: list[list[CellButton]] = []
        self.mine_positions: set[tuple[int, int]] = set()
        self.revealed_count = 0
        self.flag_count = 0
        self.game_started = False
        self.game_over = False
        self.elapsed = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        self._build_ui()
        self._new_game()

    # ── UI Construction ────────────────────────────────────────────────────
    def _build_ui(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {COLORS['bg_dark']};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QWidget#root {{
                background: {COLORS['bg_dark']};
            }}
        """)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Top bar ────────────────────────────────────────────────────────
        topbar = self._make_topbar()
        outer.addWidget(topbar)

        # ── Control bar ────────────────────────────────────────────────────
        ctrlbar = self._make_ctrlbar()
        outer.addWidget(ctrlbar)

        # ── Board area ─────────────────────────────────────────────────────
        self.board_container = QWidget()
        self.board_container.setStyleSheet(f"background: {COLORS['bg_dark']};")
        self.board_layout_outer = QHBoxLayout(self.board_container)
        self.board_layout_outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.board_frame = QFrame()
        self.board_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_panel']};
                border: 2px solid {COLORS['cell_border']};
                border-radius: 16px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(COLORS["accent"]))
        shadow.setOffset(0, 0)
        self.board_frame.setGraphicsEffect(shadow)

        self.board_grid = QGridLayout(self.board_frame)
        self.board_grid.setSpacing(2)
        self.board_grid.setContentsMargins(12, 12, 12, 12)

        self.board_layout_outer.addWidget(self.board_frame)
        outer.addWidget(self.board_container, 1)

        # ── Status bar ─────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {COLORS['bg_panel']};
                color: {COLORS['text_secondary']};
                font-size: 11px;
                border-top: 1px solid {COLORS['cell_border']};
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Left click to reveal  ·  Right click to flag  ·  Middle click / flag+click to chord")

    def _make_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(72)
        bar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['bg_panel']}, stop:1 #12152a);
                border-bottom: 1px solid {COLORS['cell_border']};
            }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)

        title = QLabel("💣 MINESWEEPER")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"""
            color: {COLORS['accent_glow']};
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)
        h.addWidget(title)
        h.addStretch()

        # Mine counter
        self.mine_lcd = self._make_lcd_label("💣  010")
        h.addWidget(self.mine_lcd)
        h.addSpacing(24)

        # New Game button
        self.face_btn = QPushButton("🙂")
        self.face_btn.setFixedSize(46, 46)
        self.face_btn.setFont(QFont("Segoe UI Emoji", 22))
        self.face_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.face_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                border: 2px solid {COLORS['accent']};
                border-radius: 23px;
            }}
            QPushButton:hover {{
                background: {COLORS['cell_hover']};
                border-color: {COLORS['accent_glow']};
            }}
            QPushButton:pressed {{
                background: {COLORS['bg_dark']};
            }}
        """)
        self.face_btn.clicked.connect(self._new_game)
        h.addWidget(self.face_btn)
        h.addSpacing(24)

        # Timer
        self.timer_lcd = self._make_lcd_label("⏱  000")
        h.addWidget(self.timer_lcd)

        return bar

    def _make_ctrlbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(54)
        bar.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_dark']};
                border-bottom: 1px solid #1a1d2e;
            }}
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
            QComboBox {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['cell_border']};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 13px;
                min-width: 130px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent']};
                border: 1px solid {COLORS['cell_border']};
                outline: none;
            }}
            QSlider::groove:horizontal {{
                background: {COLORS['bg_card']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(20)

        # Difficulty
        h.addWidget(QLabel("Difficulty:"))
        self.diff_combo = QComboBox()
        for name in DIFFICULTY_PRESETS:
            self.diff_combo.addItem(name)
        self.diff_combo.currentTextChanged.connect(self._on_difficulty_changed)
        h.addWidget(self.diff_combo)

        h.addSpacing(16)

        # Zoom
        h.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(20, 60)
        self.zoom_slider.setValue(36)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        h.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("36px")
        self.zoom_label.setFixedWidth(38)
        h.addWidget(self.zoom_label)

        h.addStretch()

        # Quick new game button
        new_btn = QPushButton("⚡  New Game")
        new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['accent_glow']};
            }}
            QPushButton:pressed {{
                background: #5550cc;
            }}
        """)
        new_btn.clicked.connect(self._new_game)
        h.addWidget(new_btn)

        return bar

    def _make_lcd_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Courier New", 15, QFont.Weight.Bold))
        lbl.setFixedWidth(110)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                background: {COLORS['bg_dark']};
                color: {COLORS['accent2']};
                border: 2px solid {COLORS['cell_border']};
                border-radius: 8px;
                padding: 4px 8px;
                letter-spacing: 2px;
            }}
        """)
        return lbl

    # ── Game Logic ─────────────────────────────────────────────────────────
    def _new_game(self):
        self.timer.stop()
        self.elapsed = 0
        self.game_started = False
        self.game_over = False
        self.revealed_count = 0
        self.flag_count = 0
        self.mine_positions = set()

        self._update_mine_counter()
        self._update_timer()
        self.face_btn.setText("🙂")

        self._build_board()

    def _build_board(self):
        # Clear old cells
        while self.board_grid.count():
            item = self.board_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cells = []

        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                cell = CellButton(r, c, self.cell_size)
                cell.clicked.connect(lambda _, rr=r, cc=c: self._on_cell_click(rr, cc))
                cell.right_clicked.connect(self._on_right_click)
                self.board_grid.addWidget(cell, r, c)
                row_cells.append(cell)
            self.cells.append(row_cells)

        # Resize window to fit
        board_w = self.cols * (self.cell_size + 2) + 24
        board_h = self.rows * (self.cell_size + 2) + 24
        self.board_frame.setMinimumSize(board_w, board_h)

    def _place_mines(self, safe_r: int, safe_c: int):
        safe_zone = set()
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = safe_r + dr, safe_c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    safe_zone.add((nr, nc))

        all_cells = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in safe_zone
        ]
        chosen = random.sample(all_cells, min(self.total_mines, len(all_cells)))
        self.mine_positions = set(chosen)

        for r, c in self.mine_positions:
            self.cells[r][c].is_mine = True

        # Count neighbors
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.cells[r][c].is_mine:
                    cnt = sum(
                        1 for dr in range(-1, 2)
                        for dc in range(-1, 2)
                        if 0 <= r+dr < self.rows
                        and 0 <= c+dc < self.cols
                        and self.cells[r+dr][c+dc].is_mine
                    )
                    self.cells[r][c].neighbor_count = cnt

    def _on_cell_click(self, r: int, c: int):
        if self.game_over:
            return
        cell = self.cells[r][c]
        if cell.is_flagged or cell.is_questioned:
            return
        if cell.is_revealed:
            # Chord: if flags around == neighbor count, reveal neighbors
            self._chord(r, c)
            return

        if not self.game_started:
            self.game_started = True
            self._place_mines(r, c)
            self.timer.start(1000)

        self._reveal(r, c)
        if not self.game_over:
            self._check_win()

    def _on_right_click(self, r: int, c: int):
        if self.game_over:
            return
        cell = self.cells[r][c]
        if cell.is_revealed:
            return

        if not cell.is_flagged and not cell.is_questioned:
            cell.is_flagged = True
            self.flag_count += 1
        elif cell.is_flagged:
            cell.is_flagged = False
            cell.is_questioned = True
            self.flag_count -= 1
        else:
            cell.is_questioned = False

        cell.update_visual()
        self._update_mine_counter()

    def _chord(self, r: int, c: int):
        """Reveal all non-flagged neighbors if correct flag count around."""
        cell = self.cells[r][c]
        if not cell.is_revealed or cell.neighbor_count == 0:
            return
        flag_cnt = sum(
            1 for dr in range(-1, 2)
            for dc in range(-1, 2)
            if 0 <= r+dr < self.rows
            and 0 <= c+dc < self.cols
            and self.cells[r+dr][c+dc].is_flagged
        )
        if flag_cnt == cell.neighbor_count:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        nb = self.cells[nr][nc]
                        if not nb.is_revealed and not nb.is_flagged:
                            self._reveal(nr, nc)
                        if self.game_over:
                            return
            if not self.game_over:
                self._check_win()

    def _reveal(self, r: int, c: int):
        """Iterative BFS flood-fill — avoids RecursionError on large boards."""
        from collections import deque

        start = self.cells[r][c]
        if start.is_revealed or start.is_flagged:
            return

        queue: deque[tuple[int, int]] = deque()
        queue.append((r, c))
        hit_mine = False

        while queue:
            cr, cc = queue.popleft()
            cell = self.cells[cr][cc]
            if cell.is_revealed or cell.is_flagged:
                continue

            cell.is_revealed = True
            cell.update_visual()
            self.revealed_count += 1

            if cell.is_mine:
                hit_mine = True
                break

            if cell.neighbor_count == 0:
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < self.rows and 0 <= nc < self.cols
                                and not self.cells[nr][nc].is_revealed
                                and not self.cells[nr][nc].is_flagged):
                            queue.append((nr, nc))

        if hit_mine:
            self._game_over()

    def _check_win(self):
        safe_cells = self.rows * self.cols - self.total_mines
        if self.revealed_count >= safe_cells:
            self._win()

    def _win(self):
        self.game_over = True
        self.timer.stop()
        self.face_btn.setText("😎")

        # Auto-flag remaining mines
        for r, c in self.mine_positions:
            cell = self.cells[r][c]
            if not cell.is_flagged:
                cell.is_flagged = True
                self.flag_count += 1
                cell.update_visual()
        self._update_mine_counter()

        dlg = ResultDialog(True, self.elapsed, self.total_mines, self.flag_count, self)
        result = dlg.exec()
        if result == 1:
            self._new_game()

    def _game_over(self):
        self.game_over = True
        self.timer.stop()
        self.face_btn.setText("😵")

        # Reveal all mines
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                if cell.is_mine:
                    cell.is_revealed = True
                    cell.update_visual()
                elif cell.is_flagged and not cell.is_mine:
                    # Wrong flag
                    cell.setText("❌")
                    cell.setFont(QFont("Segoe UI Emoji", max(10, int(self.cell_size * 0.5))))
                    cell.setStyleSheet(f"""
                        QPushButton {{
                            background: #3a1010;
                            border: 1px solid {COLORS['danger']};
                            border-radius: 4px;
                        }}
                    """)

        dlg = ResultDialog(False, self.elapsed, self.total_mines, self.flag_count, self)
        result = dlg.exec()
        if result == 1:
            self._new_game()

    # ── Event handlers ─────────────────────────────────────────────────────
    def _on_difficulty_changed(self, name: str):
        if name == "Custom":
            dlg = CustomDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                r, c, m = dlg.get_values()
                DIFFICULTY_PRESETS["Custom"] = {"rows": r, "cols": c, "mines": m}
            else:
                # Revert combo
                prev = self.difficulty
                self.diff_combo.blockSignals(True)
                self.diff_combo.setCurrentText(prev)
                self.diff_combo.blockSignals(False)
                return

        preset = DIFFICULTY_PRESETS[name]
        self.difficulty = name
        self.rows = preset["rows"]
        self.cols = preset["cols"]
        self.total_mines = preset["mines"]
        self._new_game()

    def _on_zoom_changed(self, value: int):
        self.cell_size = value
        self.zoom_label.setText(f"{value}px")
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c].resize_cell(value)

        board_w = self.cols * (value + 2) + 24
        board_h = self.rows * (value + 2) + 24
        self.board_frame.setMinimumSize(board_w, board_h)

    def _tick(self):
        self.elapsed += 1
        self._update_timer()

    def _update_mine_counter(self):
        remaining = self.total_mines - self.flag_count
        self.mine_lcd.setText(f"💣  {remaining:03d}")

    def _update_timer(self):
        mins, secs = divmod(self.elapsed, 60)
        if mins > 0:
            self.timer_lcd.setText(f"⏱  {mins:02d}:{secs:02d}")
        else:
            self.timer_lcd.setText(f"⏱  {self.elapsed:03d}")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS["bg_dark"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS["bg_panel"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS["bg_card"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS["text_primary"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = MinesweeperWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
