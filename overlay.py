import ctypes
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer
from entities import get_entities_info, get_offsets

class Drawable:
    def __init__(self, color=QColor(0, 255, 0), thickness=1):
        self.color = color
        self.thickness = thickness
        self.pen = QPen(self.color, self.thickness)
    
    def draw(self, painter):
        raise NotImplementedError("Draw method must be implemented by subclasses")

class BoundingBox(Drawable):
    def __init__(self, x, y, width, height, color=QColor(255, 0, 0), thickness=1):
        super().__init__(color, thickness)
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)

    def draw(self, painter):
        painter.setPen(self.pen)
        painter.drawRect(self.x, self.y, self.width, self.height)

class TextOverlay(Drawable):
    def __init__(self, x, y, text, color=QColor(255, 255, 255), font_size=12):
        super().__init__(color, thickness=1)
        self.x = int(x)
        self.y = int(y)
        self.text = text
        self.font = QFont()
        self.font.setPixelSize(font_size)

    def draw(self, painter):
        painter.setPen(self.pen)
        painter.setFont(self.font)

        # Medir o tamanho do texto
        text_rect = painter.fontMetrics().boundingRect(self.text)
        text_width = text_rect.width()
        text_height = text_rect.height()

        # Calcular a posição para centralizar o texto
        x = int(self.x - text_width / 2)
        y = int(self.y + text_height / 2)

        painter.drawText(x, y, self.text)

class Skeleton(Drawable):
    def __init__(self, bones, color=QColor(0, 255, 0), thickness=1):
        super().__init__(color, thickness)
        self.bones = [(start, end) for start, end in bones if start and end]

    def draw(self, painter):
        painter.setPen(self.pen)
        for start_bone, end_bone in self.bones:
            x1, y1 = int(start_bone.x), int(start_bone.y)
            x2, y2 = int(end_bone.x), int(end_bone.y)
            painter.drawLine(x1, y1, x2, y2)

class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawables = []
        self.offsets = get_offsets()
        self.show_bounding_boxes = True
        self.show_text_overlays = True
        self.show_skeletons = True
        self.team_check = False  
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
        for drawable in self.drawables:
            drawable.draw(painter)

    def updateOverlay(self):
        entities = get_entities_info(self.offsets, team_check=self.team_check)  # Use a configuração team_check

        self.drawables = []
        for entity in entities:
                if self.show_bounding_boxes:
                    self.drawables.append(BoundingBox(entity.Rect.Left, entity.Rect.Top,
                                                        entity.Rect.Right - entity.Rect.Left,
                                                        entity.Rect.Bottom - entity.Rect.Top))
                if self.show_text_overlays:
                    text_x = entity.Rect.Left + (entity.Rect.Right - entity.Rect.Left) / 2
                    text_y = entity.Rect.Top - 10
                    self.drawables.append(TextOverlay(text_x, text_y, entity.Name))
                
                if self.show_skeletons:
                    bones_to_draw = [
                        (entity.Bones.get("head"), entity.Bones.get("neck_0")),
                        (entity.Bones.get("neck_0"), entity.Bones.get("spine_1")),
                        (entity.Bones.get("spine_1"), entity.Bones.get("spine_2")),
                        (entity.Bones.get("spine_2"), entity.Bones.get("pelvis")),
                        (entity.Bones.get("spine_2"), entity.Bones.get("arm_upper_L")),
                        (entity.Bones.get("arm_upper_L"), entity.Bones.get("arm_lower_L")),
                        (entity.Bones.get("arm_lower_L"), entity.Bones.get("hand_L")),
                        (entity.Bones.get("spine_2"), entity.Bones.get("arm_upper_R")),
                        (entity.Bones.get("arm_upper_R"), entity.Bones.get("arm_lower_R")),
                        (entity.Bones.get("arm_lower_R"), entity.Bones.get("hand_R")),
                        (entity.Bones.get("pelvis"), entity.Bones.get("leg_upper_L")),
                        (entity.Bones.get("leg_upper_L"), entity.Bones.get("leg_lower_L")),
                        (entity.Bones.get("leg_lower_L"), entity.Bones.get("ankle_L")),
                        (entity.Bones.get("pelvis"), entity.Bones.get("leg_upper_R")),
                        (entity.Bones.get("leg_upper_R"), entity.Bones.get("leg_lower_R")),
                        (entity.Bones.get("leg_lower_R"), entity.Bones.get("ankle_R")),
                    ]
                    self.drawables.append(Skeleton(bones_to_draw))

        self.update()

    def setShowBoundingBoxes(self, show):
        self.show_bounding_boxes = show
        self.update()

    def setShowTextOverlays(self, show):
        self.show_text_overlays = show
        self.update()

    def setShowSkeletons(self, show):
        self.show_skeletons = show
        self.update()

    def setTeamCheck(self, check):
        self.team_check = check
        self.update()
