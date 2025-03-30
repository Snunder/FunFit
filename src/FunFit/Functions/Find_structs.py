"""Built-in modules"""
import math

"""External modules"""
import numpy as np
from matplotlib.path import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QMessageBox, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QRegion, QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF, QTransform, QBrush, QLinearGradient, QPainterPath, QCursor

"""Internal modules"""
try:
    from FunFit.Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file
except ImportError:
    from Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file

"""Constants"""
RH_SIZE = 50
CORNER_HANDLE_SIZE = 20
CORNER_HANDLE_COLOR = "#9A7ADB"
SELECTION_BORDER_WIDTH = 5
SELECTION_BORDER_COLOR_START = QColor(128, 83, 255)
SELECTION_BORDER_COLOR_END = QColor(194, 59, 255)
OPACITY_ANIMATION_DURATION = 200

class OverlayWidget(QWidget): # Visualize selections
    """Overlay widget for showing an area of interest."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.selection_polygon = QPolygonF()
        self._current_opacity = 0.0
        self.animation = QPropertyAnimation(self, b"current_opacity")
        self.animation.setDuration(OPACITY_ANIMATION_DURATION)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

    """Define Qt property"""
    def get_current_opacity(self): # Get the current opacity
        return self._current_opacity
    def set_current_opacity(self, value): # Set the current opacity
        self._current_opacity = value
        self.update()
    current_opacity = pyqtProperty(float, get_current_opacity, set_current_opacity)

    """Set the selection polygon and animate the overlay"""
    def set_selection_polygon(self, polygon): # Show selection polygon and animate overlay
        # Check if state changed between empty/non-empty
        was_empty = self.selection_polygon.isEmpty()
        now_empty = polygon.isEmpty()
        
        self.selection_polygon = polygon
        
        if was_empty != now_empty:  # Only animate on state changes
            target_opacity = 1.0 if not now_empty else 0.0
            if self.animation.state() == QPropertyAnimation.State.Running:
                self.animation.stop()
            self.animation.setStartValue(self.current_opacity)
            self.animation.setEndValue(target_opacity)
            self.animation.start()
        else:  # Update the polygon without opacity change
            self.update()

    def paintEvent(self, event): # This event handles the drawing of the overlay
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        alpha = int(self._current_opacity * 140)  # Convert 0-1 range to 0-140 alpha
        
        if not self.selection_polygon.isEmpty():
            # Draw dark overlay with animated opacity
            painter.fillRect(self.rect(), QColor(0, 0, 0, alpha))
            
            # Draw selection border (existing code)
            gradient = QLinearGradient(self.selection_polygon.boundingRect().topLeft(),
                                      self.selection_polygon.boundingRect().bottomRight())
            gradient.setColorAt(0, SELECTION_BORDER_COLOR_START)
            gradient.setColorAt(1, SELECTION_BORDER_COLOR_END)
            painter.setPen(QPen(QBrush(gradient), SELECTION_BORDER_WIDTH))
            painter.drawPolygon(self.selection_polygon)

            # Update mask
            mask = QRegion(self.rect())
            mask -= QRegion(self.selection_polygon.toPolygon())
            self.setMask(mask)
        painter.end()

class RotatableHandle(QLabel): # Enables rotation handle movement
    """Rotatable handle for rotating the selection polygon."""
    def __init__(self, parent, update_callback):
        super().__init__(parent)
        self.parent = parent
        self.update_callback = update_callback
        self.drag_offset = None
        self.angle_rad = 0
        self.handle_pixmap = QPixmap(self.parent.parent.current_dir + "/GUI/rotationhandle.png")
        self.setFixedSize(RH_SIZE, RH_SIZE)
        self.setPixmap(self.handle_pixmap.scaled(int(RH_SIZE / np.sqrt(2)), int(RH_SIZE / np.sqrt(2)), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cursor_pixmap = QPixmap(self.parent.parent.current_dir + "/GUI/rotation_cursor.png")
        self.cursor_icon = QIcon(self.cursor_pixmap)
        cursor = QCursor(self.cursor_icon.pixmap(QSize(25, 25)), 0, 0)
        self.setCursor(cursor)

    """Mouse events"""
    def mousePressEvent(self, event): # This event handles mouse clicks for rotation
        # Check if the mouse is within the image area
        if self.pixmap().size().width() > 0:
            self.drag_offset = event.pos() + QPoint(self.parent.overlay_offset,0)
        else:
            self.drag_offset = None

    def mouseMoveEvent(self, event): # This event handles rotation handle movement
        if self.drag_offset:
            self.move(self.pos() + event.pos() - self.drag_offset)
            self.update_callback(self)

    def mouseReleaseEvent(self, _): # This event handles the release of the rotation handle
        self.drag_offset = None

    """Rotation handling"""
    def set_rotation(self, angle_rad): # Set rotation of the handle
        self.angle_rad = angle_rad
        transform = QTransform().rotate(math.degrees(angle_rad))
        rotated_pixmap = self.handle_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(rotated_pixmap.scaled(self.size() / np.sqrt(2) * (abs(1 * np.sin(angle_rad)) + abs(1 * np.cos(angle_rad))), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class CornerHandle(QLabel): # Cornerhandle 𝘩𝘢𝘯𝘥𝘭𝘪𝘯𝘨 (☞ ͡° ͜ʖ ͡°)☞
    """Corner handle for resizing the selection polygon."""
    def __init__(self, parent, update_callback, corner_index):
        super().__init__(parent)
        self.update_callback = update_callback
        self.drag_offset = None
        self.corner_index = corner_index
        self.setFixedSize(CORNER_HANDLE_SIZE, CORNER_HANDLE_SIZE)
        self.setStyleSheet("background-color: transparent; border-radius: 0px;")
        self.angle_rad = 0
        self.angle_pixmap = self.create_angle_pixmap()
        self.setPixmap(self.angle_pixmap.scaled(int(CORNER_HANDLE_SIZE / np.sqrt(2)), int(CORNER_HANDLE_SIZE / np.sqrt(2)), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_corner_cursor()
        self.parent = parent

    """Create corner handle pixmap"""
    def create_angle_pixmap(self): # Create a 90-degree angle pixmap
        angle_pixmap = QPixmap(CORNER_HANDLE_SIZE, CORNER_HANDLE_SIZE)
        angle_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(angle_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(CORNER_HANDLE_COLOR), 8)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(0, CORNER_HANDLE_SIZE)
        path.lineTo(0, 0)
        path.lineTo(CORNER_HANDLE_SIZE, 0)
        painter.drawPath(path)
        painter.end()
        return angle_pixmap

    """Mouse events"""
    def set_corner_cursor(self): # Cornerhandle cursor activities
        angle = self.parent().angle if hasattr(self.parent(), 'angle') else 0
        index = self.corner_index
        if abs(angle) <= np.pi / 8 or abs(angle) >= 7 * np.pi / 8:
            cursor = Qt.CursorShape.SizeFDiagCursor if index in [0, 2] else Qt.CursorShape.SizeBDiagCursor
        elif np.pi / 8 < angle < 3 * np.pi / 8 or -7 * np.pi / 8 < angle < -5 * np.pi / 8:
            cursor = Qt.CursorShape.SizeVerCursor if index in [0, 2] else Qt.CursorShape.SizeHorCursor
        elif 3 * np.pi / 8 < abs(angle) < 5 * np.pi / 8:
            cursor = Qt.CursorShape.SizeBDiagCursor if index in [0, 2] else Qt.CursorShape.SizeFDiagCursor
        else:
            cursor = Qt.CursorShape.SizeHorCursor if index in [0, 2] else Qt.CursorShape.SizeVerCursor
        self.setCursor(cursor)

    def mousePressEvent(self, event): # This event handles mouse clicks for corner handle movement
        # Check if the mouse is within the image area
        if self.pixmap().size().width() > 0:
            self.drag_offset = event.pos() + QPoint(self.parent.overlay_offset,0)
        else:
            self.drag_offset = None

    def mouseMoveEvent(self, event): # This event handles corner handle movement
        if self.drag_offset:
            new_pos = self.pos() + event.pos() - self.drag_offset
            self.move(new_pos)
            self.update_callback(self)

    def mouseReleaseEvent(self, _): # This event handles the release of the corner handle
        self.drag_offset = None
    
    """Rotation handling"""
    def set_rotation(self, angle_rad): # Set rotation of the corner handle
        self.angle_rad = angle_rad + self.corner_index * np.pi / 2
        transform = QTransform().rotate(math.degrees(angle_rad))
        rotated_pixmap = self.angle_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(rotated_pixmap.scaled(self.size() / np.sqrt(2) * (abs(1 * np.sin(angle_rad)) + abs(1 * np.cos(angle_rad))), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

class FindStructWindow(QMainWindow): 
    """Window to select an area of interest for data analysis."""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.Raw_Z = parent.corrected_data if hasattr(parent, 'corrected_data') else parent.Raw_Z
        self.original_Raw_Z = parent.Raw_Z
        self.x_scale, self.y_scale = parent.x_scale, parent.y_scale
        self.angle = 0
        self.selection_polygon = QPolygonF()
        setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")
        self.init_ui(parent)

    def init_ui(self, parent): # Set up the FindStructWindow UI
        # Set window properties
        self.setWindowTitle("Find structured area")
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), 0, 0)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Add a main layout for storing widgets
        main_widget = QWidget(self)
        main_widget.setCursor(Qt.CursorShape.ArrowCursor)
        layout = QGridLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # Add a title bar to the window
        title_bar = create_title_bar(self, "Select area", "child")
        layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)
        self.title_bar_height = title_bar.height()-2 # Subtract 2 to account for the border size

        # Add the image to the window and initialize the overlay
        self.image_label = display_data(self)
        self.centralWidget().layout().addWidget(self.image_label, 1, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        self.overlay = OverlayWidget(self)
        self.overlay.setGeometry(0, self.title_bar_height, self.parent.img_scale_x, self.parent.img_scale_y)
        self.overlay.show()

        # Add selection information
        self.selection_size = QLabel(self)
        self.selection_size.setText("Selection size: {:.2f} x {:.2f} µm²".format(self.parent.x_scale, self.parent.y_scale))
        self.selection_size.setObjectName("info_text")
        layout.addWidget(self.selection_size, 2, 0, 1, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        # Add reset and apply buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.reset_button = QPushButton("", self)
        self.reset_button.clicked.connect(self.reset_selection)
        self.reset_button.setObjectName("reset_button")
        self.reset_button.setIcon(QIcon(self.parent.current_dir + "/GUI/reset.png"))
        self.reset_button.setIconSize(QSize(25, 25))
        button_layout.addWidget(self.reset_button)

        self.apply_button = QPushButton("Apply", self)
        self.apply_button.clicked.connect(self.apply_selection)
        self.apply_button.setObjectName("main_button")
        button_layout.addWidget(self.apply_button)

        layout.addLayout(button_layout, 2, 1, 1, 2, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        # Enable mouse tracking for the window and overlay
        self.setMouseTracking(True)
        self.show()
        self.overlay_offset = int((self.geometry().width() - self.parent.img_scale_x) / 2)
        self.overlay.move(self.overlay_offset, self.title_bar_height)

        # Add overlay on top of overlay to get mouse events on masked overlays
        self.overwidget = QWidget(self)
        self.overwidget.show()
        self.overwidget.setGeometry(self.overlay_offset, self.title_bar_height, self.parent.img_scale_x, self.parent.img_scale_y)
        self.overwidget.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        self.overwidget.setMouseTracking(True)

    """Mouse events"""
    def mousePressEvent(self, event): # This event handles mouse clicks for polygon creation and dragging
        x, y = event.pos().x(), event.pos().y()
        # Check if the mouse is within the image area
        if self.is_within_image_area(x, y):
            self.outside_click = False
            adjusted_x = x - self.overlay_offset
            adjusted_y = y - self.title_bar_height
            adjusted_pos = QPointF(adjusted_x, adjusted_y)
            
            # Check if the mouse is within the selection polygon
            if not self.selection_polygon.isEmpty() and self.selection_polygon.containsPoint(adjusted_pos, Qt.FillRule.WindingFill):
                self.drag_offset = adjusted_pos - self.selection_polygon.boundingRect().topLeft()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                self.remove_existing_handles()
                self.initialize_new_polygon(adjusted_pos)
                self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.outside_click = True            

    def is_within_image_area(self, x, y): # Check if the mouse is within the image area
        return (
            x > self.overlay_offset and 
            x < self.parent.img_scale_x + self.overlay_offset and 
            y > self.title_bar_height and
            y < self.parent.img_scale_y + self.title_bar_height
        )

    def remove_existing_handles(self): # Remove existing handles properly
        if hasattr(self, 'corner_handles'):
            for handle in self.corner_handles:
                handle.deleteLater()
            del self.corner_handles
        if hasattr(self, 'rotation_handle'):
            self.rotation_handle.deleteLater()
            del self.rotation_handle

    def initialize_new_polygon(self, adjusted_pos): # Initialize new polygon with a tiny non-empty shape
        self.angle = 0
        self.selection_start = adjusted_pos
        self.corners = [adjusted_pos, adjusted_pos + QPointF(0.1, 0), adjusted_pos + QPointF(0.1, 0.1), adjusted_pos + QPointF(0, 0.1)]
        self.selection_polygon = QPolygonF(self.corners)
        self.overlay.set_selection_polygon(self.selection_polygon)

    def mouseMoveEvent(self, event): # This event handles polygon size and dragging (either inside or outside the polygon)
        adjusted_pos = QPointF(event.pos() - QPoint(self.overlay_offset, self.title_bar_height))
        if event.buttons() == Qt.MouseButton.LeftButton and self.outside_click == False:
            if hasattr(self, 'drag_offset') and self.drag_offset:
                self.translate_polygon(adjusted_pos)
            else:
                self.resize_polygon(adjusted_pos)
            self.update()
        else:
            if not self.selection_polygon.isEmpty() and self.selection_polygon.containsPoint(adjusted_pos, Qt.FillRule.WindingFill):
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def translate_polygon(self, adjusted_pos): # Translates the polygon if it is dragged
        delta = adjusted_pos - self.selection_polygon.boundingRect().topLeft() - self.drag_offset
        self.selection_polygon.translate(delta)
        self.corners = [corner + delta for corner in self.corners]
        self.overlay.set_selection_polygon(self.selection_polygon)
        self.translate_rotation_handle()
        self.translate_corner_handles()

    def resize_polygon(self, adjusted_pos): # Resize the polygon while dragging new polygon
        self.selection_end = adjusted_pos
        self.corners = [
            self.selection_start,
            QPointF(self.selection_end.x(), self.selection_start.y()),
            self.selection_end,
            QPointF(self.selection_start.x(), self.selection_end.y())
        ]
        self.selection_polygon = QPolygonF(self.corners)
        self.overlay.set_selection_polygon(self.selection_polygon)
        width, height = abs(self.selection_end.x() - self.selection_start.x()), abs(self.selection_end.y() - self.selection_start.y())
        self.selection_size.setText("Selection size: {:.2f} x {:.2f} µm²".format(width/self.parent.img_scale_x*self.parent.x_scale, height/self.parent.img_scale_x*self.parent.y_scale))

    def mouseReleaseEvent(self, event): # This is the event that triggers the cropping of the data
        if self.outside_click == False:
            end_y = max(0, min(event.pos().y() - self.title_bar_height, self.parent.img_scale_y))
            end_x = max(0, min(event.pos().x() - self.overlay_offset, self.parent.img_scale_x))

            if hasattr(self, 'drag_offset') and self.drag_offset:
                self.drag_offset = None
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.finalize_polygon(QPointF(end_x, end_y))
            self.update()
    
    def finalize_polygon(self, end_pos): # Finalize the polygon and crop data
        self.selection_end = end_pos
        self.corners = [
            self.selection_start,
            QPointF(self.selection_end.x(), self.selection_start.y()),
            self.selection_end,
            QPointF(self.selection_start.x(), self.selection_end.y())
        ]
        min_corner_index = min(range(len(self.corners)), key=lambda i: (self.corners[i].x(), self.corners[i].y()))
        self.corners = [self.corners[(i + min_corner_index) % 4] for i in range(4)]
        if self.corners[1].y() > self.corners[3].y(): self.corners[1], self.corners[3] = self.corners[3], self.corners[1]
        self.selection_polygon = QPolygonF(self.corners)
        self.overlay.set_selection_polygon(self.selection_polygon)
        self.add_rotation_handle()
        self.add_corner_handles()  # Add draggable points after polygon is created

    """Rotation handle"""
    def add_rotation_handle(self): # Add rotation handle to the polygon
        self.rotation_handle = RotatableHandle(self, self.update_rotation_handle)
        handle_pos = self.calculate_rot_handle_position(self.corners[0])
        self.rotation_handle.setGeometry(int(handle_pos.x()), int(handle_pos.y()), int(RH_SIZE/np.sqrt(2)), int(RH_SIZE/np.sqrt(2)))
        self.rotation_handle.show()

    def update_rotation_handle(self, handle): # Updates the rotation handle when dragged
        if hasattr(self, 'corner_handles'): # Remove draggable points when rotating
            for point in self.corner_handles: point.deleteLater()
        center = self.selection_polygon.boundingRect().center() + QPointF(0, self.title_bar_height)
        handle_pos = QPointF(handle.pos()) + QPointF(RH_SIZE/2, RH_SIZE/2)  # Adjust for handle size
        angle_rad = math.atan2(-handle_pos.y() + center.y(), -handle_pos.x() + center.x())  # Calculate angle in radians
        lengths = [math.hypot(p2.x() - p1.x(), p2.y() - p1.y()) for p1, p2 in zip(self.corners, self.corners[1:] + [self.corners[0]])]
        self.angle_offset = math.atan2(lengths[1], lengths[0])
        self.angle = ((angle_rad - self.angle_offset + np.pi) % (2 * np.pi)) - np.pi  # Normalize angle to be between -π and +π
        self.set_polygon_rotation()
        handle.set_rotation(angle_rad - self.angle_offset)  # Rotate the handle image
        new_handle_pos = self.calculate_rot_handle_position(self.corners[0])
        handle.move(int(new_handle_pos.x()), int(new_handle_pos.y()))
        self.add_corner_handles()  # Re-add draggable points after rotation

    def calculate_rot_handle_position(self, corner: QPointF) -> QPointF: # Calculate rotation handle position
        handle_pos = corner + QPointF(-RH_SIZE/2-RH_SIZE/np.sqrt(8)*math.cos(self.angle+np.pi/4),
                                      -RH_SIZE/2-RH_SIZE/np.sqrt(8)*math.sin(self.angle+np.pi/4))
        return QPointF(handle_pos.x() + self.overlay_offset, handle_pos.y() + self.title_bar_height)

    def set_polygon_rotation(self): # Rotates the polygon based on rotation handle position
        center = self.selection_polygon.boundingRect().center()
        adjusted_points = [point - center for point in self.corners]
        angle_diff_rad = self.angle - math.atan2(adjusted_points[1].y() - adjusted_points[0].y(), adjusted_points[1].x() - adjusted_points[0].x())
        self.corners = [QPointF(p.x() * math.cos(angle_diff_rad) - p.y() * math.sin(angle_diff_rad) + center.x(),
                                p.x() * math.sin(angle_diff_rad) + p.y() * math.cos(angle_diff_rad) + center.y()) 
                        for p in adjusted_points]
        self.selection_polygon = QPolygonF(self.corners)
        self.update_overlay()

    def translate_rotation_handle(self): # Moves the rotation handle when associated corner is translated
        if hasattr(self, 'rotation_handle'):
            handle_pos = self.calculate_rot_handle_position(self.corners[0])
            self.rotation_handle.move(int(handle_pos.x()), int(handle_pos.y()))

    """Corner handles"""
    def add_corner_handles(self): # Add draggable points to the corners of the polygon
        self.corner_handles = []
        for i, corner in enumerate(self.corners):
            point = CornerHandle(self, self.update_corner_handle, i)
            corner_pos = self.calculate_corner_handle_position(i, corner)
            point.move(int(corner_pos.x()), int(corner_pos.y()))
            point.show()
            point.set_rotation(self.angle + i * np.pi / 2)
            self.corner_handles.append(point)
            x, y = point.pos().x()+CORNER_HANDLE_SIZE/2, point.pos().y()+CORNER_HANDLE_SIZE/2
            if not self.is_within_image_area(x, y):
                point.setPixmap(QPixmap())
                if i == 0:
                    self.rotation_handle.setPixmap(QPixmap())
            else:
                point.set_rotation(self.angle + i * np.pi / 2)

    def update_corner_handle(self, point): # Update the given corner handle when moved
        index = self.corner_handles.index(point) # Get the index of the dragged point
        
        # Calculate the new position of the dragged point and offset
        new_pos = QPointF(point.pos()) + QPointF(CORNER_HANDLE_SIZE/2, CORNER_HANDLE_SIZE/2 - self.title_bar_height)
        c, x, y = self.corners, self.corners[index].x(), self.corners[index].y()
        diff = new_pos - QPointF(x, y)

        opposite_index, adjacent_indices = (index + 2) % 4, [(index + 1) % 4, (index + 3) % 4] # Calculate the opposite and adjacent corners
        opposite_corner = self.corners[opposite_index]
        adjusted_angle = self.angle + [0, np.pi / 2, np.pi, -np.pi / 2][index] # Adjust the angle based on the index of the dragged point

        # Dot product of diagonal vector and rotated unit vectors
        CW_dot_prod = (new_pos.x() - opposite_corner.x()) * math.cos(adjusted_angle) + (new_pos.y() - opposite_corner.y()) * math.sin(adjusted_angle)
        CCW_dot_prod = (new_pos.x() - opposite_corner.x()) * math.sin(-adjusted_angle) + (new_pos.y() - opposite_corner.y()) * math.cos(adjusted_angle)        
        # Update the positions of the corners while keeping the relative angle between points
        if CW_dot_prod <= 0 and CCW_dot_prod <= 0: # No corner overlap
            c[index] = new_pos
            c[adjacent_indices[1]] = opposite_corner + QPointF(
                CW_dot_prod * math.cos(adjusted_angle),
                CW_dot_prod * math.sin(adjusted_angle)
            )
            c[adjacent_indices[0]] = opposite_corner + QPointF(
                - CCW_dot_prod * math.sin(adjusted_angle),
                CCW_dot_prod * math.cos(adjusted_angle)
            )
        elif CW_dot_prod < 0 and CCW_dot_prod >= 0: # Overlap with counterclockwise adjacent corner
            c[index] = new_pos
            c[adjacent_indices[1]] = new_pos
            c[opposite_index] = opposite_corner + diff
            c[adjacent_indices[0]] = opposite_corner + diff
        elif CW_dot_prod >= 0 and CCW_dot_prod < 0: # Overlap with clockwise adjacent corner
            c[index] = new_pos
            c[adjacent_indices[0]] = new_pos
            c[opposite_index] = opposite_corner + diff
            c[adjacent_indices[1]] = opposite_corner + diff
        else: # All corners overlap
            c[index] = new_pos
            for i in range(4):
                if i == index: continue
                c[i] = opposite_corner + diff

        lengths = [math.hypot(p2.x() - p1.x(), p2.y() - p1.y()) for p1, p2 in zip(self.corners, self.corners[1:] + [self.corners[0]])]
        height, width = abs(lengths[1]), abs(lengths[0])
        self.selection_size.setText("Selection size: {:.2f} x {:.2f} µm²".format(width/self.parent.img_scale_x*self.parent.x_scale, height/self.parent.img_scale_x*self.parent.y_scale))

        # Update the selection polygon with the new corner positions
        self.selection_polygon = QPolygonF(self.corners)
        self.overlay.set_selection_polygon(self.selection_polygon)
        self.update()
        self.translate_corner_handles()
        self.translate_rotation_handle()
    
    def calculate_corner_handle_position(self, i, corner: QPointF) -> QPointF: # Calculate rotation handle position
        handle_pos = corner + QPointF(-CORNER_HANDLE_SIZE/2 + 2*math.cos(-self.angle+3*np.pi/4-i*np.pi/2), 
                                      -CORNER_HANDLE_SIZE/2 - 2*math.sin(-self.angle+3*np.pi/4-i*np.pi/2))
        return QPointF(handle_pos.x() + self.overlay_offset, handle_pos.y() + self.title_bar_height)

    def translate_corner_handles(self): # When translating polygon, update corner handles
        if hasattr(self, 'corner_handles'):
            for i, corner in enumerate(self.corners):
                corner_pos = self.calculate_corner_handle_position(i, corner)
                self.corner_handles[i].move(int(corner_pos.x()), int(corner_pos.y()))
                x, y = self.corner_handles[i].pos().x()+CORNER_HANDLE_SIZE/2, self.corner_handles[i].pos().y()+CORNER_HANDLE_SIZE/2
                if not self.is_within_image_area(x, y):
                    self.corner_handles[i].setPixmap(QPixmap())
                    if i == 0:
                        self.rotation_handle.setPixmap(QPixmap())
                else:
                    self.corner_handles[i].set_rotation(self.angle + i * np.pi / 2)
                    if i == 0:
                        self.rotation_handle.set_rotation(self.angle)

    def remove_corner_handles(self): # Remove corner handles
        if hasattr(self, 'corner_handles'):
            for point in self.corner_handles:
                point.deleteLater()
            del self.corner_handles

    """Overlay update"""
    def update_overlay(self): # Update the overlay with the selection polygon
        if not self.selection_polygon.isEmpty():
            mask = QRegion(self.image_label.rect()) - QRegion(self.selection_polygon.toPolygon())
            self.overlay.setMask(mask)
            self.overlay.set_selection_polygon(self.selection_polygon)
            self.overlay.update()
        else:
            self.overlay.clearMask()
            self.overlay.set_selection_polygon(QPolygonF())
            self.overlay.update()
        self.translate_corner_handles()  # Update draggable points when overlay is updated

    def apply_selection(self): # Apply the selection whent the apply button is clicked
        if self.selection_polygon.isEmpty():
            self.corners = [QPointF(0, 0), QPointF(self.parent.img_scale_x, 0), QPointF(self.parent.img_scale_x, self.parent.img_scale_y), QPointF(0, self.parent.img_scale_y)]
            if hasattr(self.parent, 'overlay'): 
                try: self.parent.overlay.deleteLater() 
                except: pass
            self.close()
            for attr in ['inside_data', 'outside_data', 'inside_image', 'outside_image']:
                if hasattr(self.parent, attr):
                    delattr(self.parent, attr)
            return

        if hasattr(self, 'widget'):
            self.widget.deleteLater()
            del self.widget

        # Snap the current polygon to integer values
        self.overlay.set_selection_polygon(self.selection_polygon)
        self.corners = [QPointF(int(round(p.x())), int(round(p.y()))) for p in self.corners]
        self.selection_polygon = QPolygonF(self.corners)
        self.translate_corner_handles()  # Update draggable points when polygon is snapped to integer values
        # Set all points back to float
        self.corners = [QPointF(p) for p in self.corners]
        self.selection_polygon = QPolygonF(self.corners)
        self.update_overlay()
        
        if hasattr(self.parent, 'overlay'): 
            try: self.parent.overlay.deleteLater() 
            except: pass
        self.parent.overlay = OverlayWidget(self.parent.image)
        self.parent.overlay.setGeometry(self.image_label.geometry())
        self.parent.overlay.set_selection_polygon(self.selection_polygon)
        self.parent.overlay.move(QPoint(0,int(self.parent.image.height()/2-self.parent.img_scale_y/2)))
        self.parent.overlay.show()
        self.parent.overlay.stackUnder(self.parent.export_button)
        
        self.parent.selection_polygon = self.selection_polygon

        # Create a mask for the selection polygon
        mask = np.zeros(self.Raw_Z.shape, dtype=bool)
        x_coords, y_coords = np.meshgrid(np.arange(self.Raw_Z.shape[1]), np.arange(self.Raw_Z.shape[0]))
        points = np.vstack((x_coords.flatten(), y_coords.flatten())).T
        # Create a Path object from the selection polygon
        polygon_path = Path([(point.x() * self.Raw_Z.shape[1] / self.parent.img_scale_x, point.y() * self.Raw_Z.shape[0] / self.parent.img_scale_y) for point in self.selection_polygon])

        # Create a mask for the selection polygon
        x_coords, y_coords = np.meshgrid(np.arange(self.Raw_Z.shape[1]), np.arange(self.Raw_Z.shape[0]))
        points = np.vstack((x_coords.flatten(), y_coords.flatten())).T
        mask = polygon_path.contains_points(points).reshape(self.Raw_Z.shape)

        # Create images with NaNs for outside points
        self.parent.inside_image = np.where(mask, self.original_Raw_Z, np.nan)
        self.parent.outside_image = np.where(~mask, self.original_Raw_Z, np.nan)

        self.close()
        
    def reset_selection(self): # Reset the selection when the reset button is clicked
        if not hasattr(self, 'selection_polygon') or self.selection_polygon.isEmpty():
            return
        self.selection_polygon = QPolygonF()
        self.overlay.set_selection_polygon(self.selection_polygon)
        self.update_overlay()
        self.remove_corner_handles()
        self.rotation_handle.deleteLater()
        del self.rotation_handle
        self.update()

"""Function called from main window."""
def crop_data(self=None):
    try: 
        self.w = FindStructWindow(self)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()