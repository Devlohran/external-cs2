import sys
import win32gui
import win32api
import win32con
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QCheckBox, QVBoxLayout, QDesktopWidget
from PyQt5.QtCore import QTimer, QPoint, Qt
from overlay import Overlay

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.overlay = Overlay()
        self.initUI()

        # Para movimentação da janela
        self.old_pos = None

    def initUI(self):
        self.setGeometry(100, 100, 200, 200)  # Ajuste a altura para acomodar as checkboxes
        self.setStyleSheet("background-color: black;")
        
        # Centralize the window
        self.center()

        # Set window flags and attributes
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Checkbox to toggle bounding boxes
        self.checkbox_bounding_boxes = QCheckBox("Show Bounding Boxes")
        self.checkbox_bounding_boxes.setChecked(True)
        self.checkbox_bounding_boxes.stateChanged.connect(self.toggleBoundingBoxes)
        self.checkbox_bounding_boxes.setStyleSheet("color: white;")

        # Checkbox to toggle text overlays
        self.checkbox_text_overlays = QCheckBox("Show Text Overlays")
        self.checkbox_text_overlays.setChecked(True)
        self.checkbox_text_overlays.stateChanged.connect(self.toggleTextOverlays)
        self.checkbox_text_overlays.setStyleSheet("color: white;")

        # Checkbox to toggle skeletons
        self.checkbox_skeletons = QCheckBox("Show Skeletons")
        self.checkbox_skeletons.setChecked(True)
        self.checkbox_skeletons.stateChanged.connect(self.toggleSkeletons)
        self.checkbox_skeletons.setStyleSheet("color: white;")

        # Checkbox to toggle team check
        self.checkbox_team_check = QCheckBox("Enable Team Check")
        self.checkbox_team_check.setChecked(True)
        self.checkbox_team_check.stateChanged.connect(self.toggleTeamCheck)
        self.checkbox_team_check.setStyleSheet("color: white;")

        layout = QVBoxLayout()  # Usando QVBoxLayout para disposição vertical
        layout.addWidget(self.checkbox_bounding_boxes)
        layout.addWidget(self.checkbox_text_overlays)
        layout.addWidget(self.checkbox_skeletons)
        layout.addWidget(self.checkbox_team_check)

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

    def toggleBoundingBoxes(self, state):
        self.overlay.setShowBoundingBoxes(state == Qt.Checked)

    def toggleTextOverlays(self, state):
        self.overlay.setShowTextOverlays(state == Qt.Checked)

    def toggleSkeletons(self, state):
        self.overlay.setShowSkeletons(state == Qt.Checked)

    def toggleTeamCheck(self, state):
        self.overlay.setTeamCheck(state == Qt.Checked)

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
