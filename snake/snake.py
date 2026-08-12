import sys, random, os
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QKeyEvent, QIcon
from PyQt6.QtCore import QTimer, Qt

CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ICONS_DIR = os.path.join(_BASE_DIR)

def _icon(name: str) -> QIcon:
    """İkon klasöründen QIcon döndürür."""
    return QIcon(os.path.join(_ICONS_DIR, name))

class SnakeGame(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snake Game")
        self.resize(CELL_SIZE * GRID_WIDTH, CELL_SIZE * GRID_HEIGHT)
        self.setWindowIcon(_icon("snake.png"))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.timer.start(150)

        self.reset_game()

    def reset_game(self):
        self.snake = [(5, 5), (4, 5), (3, 5)]
        self.direction = (1, 0)
        self.food = self.random_food()
        self.game_over = False

    def random_food(self):
        while True:
            pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if pos not in self.snake:
                return pos

    def update_game(self):
        if self.game_over:
            return
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # Çarpışma kontrolü
        if (new_head in self.snake or
            new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self.game_over = True
            self.update()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.food = self.random_food()
        else:
            self.snake.pop()

        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up and self.direction != (0, 1):
            self.direction = (0, -1)
        elif event.key() == Qt.Key.Key_Down and self.direction != (0, -1):
            self.direction = (0, 1)
        elif event.key() == Qt.Key.Key_Left and self.direction != (1, 0):
            self.direction = (-1, 0)
        elif event.key() == Qt.Key.Key_Right and self.direction != (-1, 0):
            self.direction = (1, 0)
        elif event.key() == Qt.Key.Key_Space and self.game_over:
            self.reset_game()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # Daha koyu night blue arka plan
        painter.fillRect(self.rect(), QColor(15, 15, 70))

        # Yılan (border yok)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 255, 0))
        for x, y in self.snake:
            painter.drawRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

        # Yem (border yok)
        painter.setBrush(QColor(255, 0, 0))
        fx, fy = self.food
        painter.drawRect(fx * CELL_SIZE, fy * CELL_SIZE, CELL_SIZE, CELL_SIZE)

        # Game Over + Press Space
        if self.game_over:
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "GAME OVER\nPress Space")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = SnakeGame()
    game.show()
    sys.exit(app.exec())
