import sys
import ctypes
import win32gui
from entities import get_entities_info, get_offsets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QCheckBox, QHBoxLayout, QDesktopWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer, QPoint
import win32api
import win32con

class Drawable:
    def __init__(self, color=QColor(0, 255, 0), thickness=2):
        self.color = color
        self.thickness = thickness
        self.pen = QPen(self.color, self.thickness)
    
    def draw(self, painter):
        raise NotImplementedError("Draw method must be implemented by subclasses")

class BoundingBox(Drawable):
    def __init__(self, x, y, width, height, color=QColor(255, 0, 0), thickness=2):
        super().__init__(color, thickness)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def draw(self, painter):
        painter.setPen(self.pen)
        painter.drawRect(self.x, self.y, self.width, self.height)

class Line(Drawable):
    def __init__(self, x1, y1, x2, y2, color=QColor(0, 255, 0), thickness=2):
        super().__init__(color, thickness)
        self.x1 = int(x1)
        self.y1 = int(y1)
        self.x2 = int(x2)
        self.y2 = int(y2)

    def draw(self, painter):
        painter.setPen(self.pen)
        painter.drawLine(self.x1, self.y1, self.x2, self.y2)

class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawables = []
        self.offsets = get_offsets()
        self.show_drawings = True
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        hwnd = self.winId().__int__()
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, ctypes.windll.user32.GetWindowLongW(hwnd, -20) | 0x00000020)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateOverlay)
        self.timer.start(1000 // 60)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.show_drawings:
            for drawable in self.drawables:
                drawable.draw(painter)

    def updateOverlay(self):
        entities = get_entities_info(self.offsets, team_check=True)

        self.drawables = []
        for entity in entities:
            if entity.OnScreen:
                self.drawables.append(BoundingBox(entity.Rect.Left, entity.Rect.Top,
                                                    entity.Rect.Right - entity.Rect.Left,
                                                    entity.Rect.Bottom - entity.Rect.Top))

        self.update()

    def setShowDrawings(self, show):
        self.show_drawings = show
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.overlay = Overlay()
        self.initUI()

        # Para movimentação da janela
        self.old_pos = None

    def initUI(self):
        self.setGeometry(100, 100, 100, 100)
        self.setStyleSheet("background-color: black;")
        
        # Centralize the window
        self.center()

        # Set window flags and attributes
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.checkbox = QCheckBox("Show Drawings")
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.toggleDrawings)

        # Set the checkbox text color to white
        self.checkbox.setStyleSheet("color: white;")

        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Timer to check for the active window
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkActiveWindow)
        self.timer.start(1000)  # Check every second

        # Timer to check for the Insert key press
        self.key_timer = QTimer(self)
        self.key_timer.timeout.connect(self.checkInsertKey)
        self.key_timer.start(100)  

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def toggleDrawings(self, state):
        self.overlay.setShowDrawings(state == Qt.Checked)

    def checkActiveWindow(self):
        hwnd = win32gui.GetForegroundWindow()
    
        if hwnd == self.winId().__int__():
            return 

        window_title = win32gui.GetWindowText(hwnd)
    
        if "Counter-Strike 2" in window_title:
            self.overlay.showFullScreen()
        else:
            self.overlay.hide()
            self.hide()


    def checkInsertKey(self):
        if win32api.GetAsyncKeyState(win32con.VK_INSERT) & 0x8000:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    # Implementação da movimentação da janela
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())

