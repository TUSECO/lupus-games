import sys, random, os
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox, QMenuBar, QVBoxLayout
from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtCore import Qt

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICONS_DIR = os.path.join(_BASE_DIR)

def _icon(name: str) -> QIcon:
    """İkon klasöründen QIcon döndürür."""
    return QIcon(os.path.join(_ICONS_DIR, name))

class TicTacToe(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TicTacToe")
        self.setFixedSize(600, 600)
        self.setWindowIcon(_icon("favicon.png"))

        # Arka plan rengi (nightblue'un koyu hali)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(10, 10, 40))
        self.setPalette(palette)

        self.current_player = "×"
        self.buttons = []
        self.mode = "Medium"  # varsayılan zorluk

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # Menü bar
        menubar = QMenuBar(self)
        mode_menu = menubar.addMenu("Mode")
        easy_action = mode_menu.addAction("Easy")
        medium_action = mode_menu.addAction("Medium")
        hard_action = mode_menu.addAction("Hard")

        easy_action.triggered.connect(lambda: self.setMode("Easy"))
        medium_action.triggered.connect(lambda: self.setMode("Medium"))
        hard_action.triggered.connect(lambda: self.setMode("Hard"))

        main_layout.setMenuBar(menubar)

        # Oyun grid
        grid = QGridLayout()
        for row in range(3):
            row_buttons = []
            for col in range(3):
                btn = QPushButton("")
                btn.setFixedSize(180, 180)
                btn.setStyleSheet("font-size: 48px; color: white; background-color: #0a0a28;")
                btn.clicked.connect(lambda _, r=row, c=col: self.handleMove(r, c))
                grid.addWidget(btn, row, col)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        main_layout.addLayout(grid)
        self.setLayout(main_layout)

    def setMode(self, mode):
        self.mode = mode
        self.resetBoard()

    def handleMove(self, row, col):
        btn = self.buttons[row][col]
        if btn.text() == "" and self.current_player == "×":
            btn.setText("×")
            if self.checkWin("×"):
                self.showMessage("YOU WIN!")
                return
            elif self.isDraw():
                self.showMessage("DRAW!")
                return
            self.current_player = "○"
            self.computerMove()

    def computerMove(self):
        if self.mode == "Easy":
            empty = [(r, c) for r in range(3) for c in range(3) if self.buttons[r][c].text() == ""]
            if empty:
                r, c = random.choice(empty)
                self.buttons[r][c].setText("○")

        elif self.mode == "Medium":
            moves = []
            best_score = -999
            for r in range(3):
                for c in range(3):
                    if self.buttons[r][c].text() == "":
                        self.buttons[r][c].setText("○")
                        score = self.minimax(False, max_depth=2)  # sınırlı zekâ
                        self.buttons[r][c].setText("")
                        if score > best_score:
                            best_score = score
                            moves = [(r, c)]
                        elif score == best_score:
                            moves.append((r, c))
            if moves:
                r, c = random.choice(moves)
                self.buttons[r][c].setText("○")

        elif self.mode == "Hard":
            moves = []
            best_score = -999
            for r in range(3):
                for c in range(3):
                    if self.buttons[r][c].text() == "":
                        self.buttons[r][c].setText("○")
                        score = self.minimax(False, max_depth=9)  # tam zekâ
                        self.buttons[r][c].setText("")
                        if score > best_score:
                            best_score = score
                            moves = [(r, c)]
                        elif score == best_score:
                            moves.append((r, c))
            if moves:
                r, c = random.choice(moves)
                self.buttons[r][c].setText("○")

        if self.checkWin("○"):
            self.showMessage("COMPUTER WINS!")
            return
        elif self.isDraw():
            self.showMessage("DRAW!")
            return
        self.current_player = "×"

    def minimax(self, is_maximizing, depth=0, max_depth=2):
        if self.checkWin("○"):
            return 1
        if self.checkWin("×"):
            return -1
        if self.isDraw():
            return 0
        if depth >= max_depth:
            return 0

        if is_maximizing:
            best_score = -999
            for r in range(3):
                for c in range(3):
                    if self.buttons[r][c].text() == "":
                        self.buttons[r][c].setText("○")
                        score = self.minimax(False, depth+1, max_depth)
                        self.buttons[r][c].setText("")
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = 999
            for r in range(3):
                for c in range(3):
                    if self.buttons[r][c].text() == "":
                        self.buttons[r][c].setText("×")
                        score = self.minimax(True, depth+1, max_depth)
                        self.buttons[r][c].setText("")
                        best_score = min(score, best_score)
            return best_score

    def checkWin(self, player):
        for i in range(3):
            if all(self.buttons[i][j].text() == player for j in range(3)):
                return True
            if all(self.buttons[j][i].text() == player for j in range(3)):
                return True
        if all(self.buttons[i][i].text() == player for i in range(3)):
            return True
        if all(self.buttons[i][2 - i].text() == player for i in range(3)):
            return True
        return False

    def isDraw(self):
        return all(self.buttons[r][c].text() != "" for r in range(3) for c in range(3))

    def resetBoard(self):
        self.current_player = "×"
        for row in self.buttons:
            for btn in row:
                btn.setText("")
                btn.setEnabled(True)

    def showMessage(self, text):
        msg = QMessageBox(self)
        msg.setWindowTitle("TicTacToe Result")
        msg.setText(text)
        reset_button = msg.addButton("Reset", QMessageBox.ButtonRole.AcceptRole)
        msg.setFixedSize(600, 400)
        msg.setStyleSheet("QMessageBox {background-color: darkblue; font-size: 22px; color: white; text-align: center;} QPushButton {font-size: 18px;}")
        msg.exec()
        if msg.clickedButton() == reset_button:
            self.resetBoard()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.resetBoard()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TicTacToe()
    window.show()
    sys.exit(app.exec())
