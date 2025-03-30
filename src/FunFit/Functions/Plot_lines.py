"""Built-in modules"""
import math

"""External modules"""
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QMessageBox, QPushButton, QLabel, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt, QPoint, QPointF, QSize, QLineF, QRectF
from PyQt6.QtGui import QRegion, QIcon, QPixmap, QPainter, QPen, QColor, QTransform, QBrush, QLinearGradient

"""Internal modules"""
try:
    from FunFit.Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file
except:
    from Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file

"""Constants"""
CORNER_HANDLE_SIZE = 30
CORNER_HANDLE_COLOR = "#9A7ADB"
SELECTION_BORDER_WIDTH = 5
SELECTION_BORDER_COLOR_START = QColor(128, 83, 255)
SELECTION_BORDER_COLOR_END = QColor(194, 59, 255)
LINE_CUT_COLOR = "#EB7194"
LINE_CUT_FACE_COLOR = "#232036"
PLOT_TEXT_COLOR = "#706E85"

class OverlayWidget(QWidget):
    """Overlay widget for showing an area of interest."""
    def __init__(self, parent):
        super().__init__(parent)
        self.selection_line = QLineF()
        
    def set_selection_line(self, line): # Set the selection line
        self.selection_line = line

    def paintEvent(self, event): # Paint the selection line
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.selection_line.isNull():            
            # Draw selection line with gradient
            gradient = QLinearGradient(self.selection_line.p1(),
                                      self.selection_line.p2())
            gradient.setColorAt(0, SELECTION_BORDER_COLOR_START)
            gradient.setColorAt(1, SELECTION_BORDER_COLOR_END)
            painter.setPen(QPen(QBrush(gradient), SELECTION_BORDER_WIDTH))
            painter.drawLine(self.selection_line)            
        painter.end()

class CornerHandle(QLabel): # Cornerhandle 𝘩𝘢𝘯𝘥𝘭𝘪𝘯𝘨 (☞ ͡° ͜ʖ ͡°)☞
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
        pen = QPen(QColor(f"{CORNER_HANDLE_COLOR}"), 8)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rectangle = QRectF(int(CORNER_HANDLE_SIZE/4), int(CORNER_HANDLE_SIZE/4), int(3*CORNER_HANDLE_SIZE/4), int(3*CORNER_HANDLE_SIZE/4))
        painter.drawRoundedRect(rectangle, int(CORNER_HANDLE_SIZE/2), int(CORNER_HANDLE_SIZE/2))
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
            self.drag_offset = event.pos()
        else:
            self.drag_offset = None

    def mouseMoveEvent(self, event): # This event handles corner handle movement
        if self.drag_offset:
            new_pos = self.pos() + event.pos() - self.drag_offset
            if self.parent.is_within_image_area(new_pos.x()+int(CORNER_HANDLE_SIZE/2), new_pos.y()+int(CORNER_HANDLE_SIZE/2)):
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
        self.x_scale, self.y_scale = parent.x_scale, parent.y_scale
        self.angle = 0
        self.selection_line = QLineF()
        self.init_ui(parent)
        setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")

    def init_ui(self, parent): # Set up the FindStructWindow UI
        # Set window properties
        self.setWindowTitle("Choose line cuts")
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), 0, 0)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        # Add a main layout for storing widgets
        main_widget = QWidget(self)
        layout = QGridLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # Add a title bar to the window
        title_bar = create_title_bar(self, "Select line", "child")
        layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)
        self.title_bar_height = title_bar.height()-2 # Subtract 2 to account for the border size

        # Add the image to the window and initialize the overlay
        self.image_label = display_data(self)
        self.centralWidget().layout().addWidget(self.image, 1, 0, 1, 2, Qt.AlignmentFlag.AlignTop)
        self.overlay = OverlayWidget(self)
        self.overlay.setGeometry(0, self.title_bar_height, self.parent.img_scale_x, self.parent.img_scale_y)
        self.overlay.show()

        # Add selection information
        self.selection_size = QLabel(self)
        self.selection_size.setText("Selection length: {:.2f} µm".format(self.parent.x_scale))
        self.selection_size.setStyleSheet("color: white; padding: 10px; text-align: left; padding-left: 10px; font-size: 16px;margin: 2px 10px; font-family: Verdana;")
        layout.addWidget(self.selection_size, 2, 0, 1, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)

        # Add reset button
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)

        self.reset_button = QPushButton("", self)
        self.reset_button.clicked.connect(self.reset_selection)
        self.reset_button.setObjectName("reset_button")
        reset_icon = QIcon(self.parent.current_dir + "/GUI/reset.png")
        self.reset_button.setIcon(reset_icon)
        self.reset_button.setIconSize(QSize(25, 25))
        button_layout.addWidget(self.reset_button)

        layout.addLayout(button_layout, 2, 1, 1, 2, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

        # Add the line plot widget
        fig_layout = QVBoxLayout()
        fig_layout.setContentsMargins(0, 0, 0, 0)
        fig_layout.setSpacing(0)
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("background-color: transparent;")
        fig_layout.addWidget(self.preview_label)
        layout.addLayout(fig_layout, 1, 3, 1, -1, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignRight)
        
        # Enable mouse tracking for the overlay
        self.overlay.setMouseTracking(True)  # Enable mouse tracking for the overlay
        self.show()
        self.overlay.move(0, self.title_bar_height)
        self.reset_selection() # Initialize the selection polygon

    def reset_selection(self): # Reset the selection polygon
        self.remove_existing_handles()
        self.selection_start = QPointF(0, self.parent.img_scale_y/2)
        self.selection_end = QPointF(self.parent.img_scale_x, self.parent.img_scale_y/2)
        self.corners = [self.selection_start, self.selection_end]
        self.selection_line = QLineF(self.corners[0], self.corners[1])
        self.overlay.set_selection_line(self.selection_line)
        self.add_corner_handles()
        self.update()
        self.plot_renderer()
        self.selection_size.setText("Selection length: {:.2f} µm".format(self.parent.x_scale))

    """Mouse events"""
    def mousePressEvent(self, event): # This event handles mouse clicks for polygon creation and dragging
        x, y = event.pos().x(), event.pos().y()
        # Check if the mouse is within the image area
        if self.is_within_image_area(x, y):
            adjusted_x = x
            adjusted_y = y - self.title_bar_height
            adjusted_pos = QPointF(adjusted_x, adjusted_y)
            
            # Check if the mouse is within the selection polygon
            if not self.selection_line.isNull() and self.distance_point_to_line(adjusted_pos, self.selection_line) < 10:
                self.drag_offset = adjusted_pos - self.selection_line.p1()
            else:
                self.remove_existing_handles()
                self.initialize_new_polygon(adjusted_pos)
        else:
            self.selection_start = None
    
    def is_within_image_area(self, x, y): # Check if the mouse is within the image area
        return (
            x > 0 and 
            x < self.parent.img_scale_x and 
            y > self.title_bar_height and
            y < self.parent.img_scale_y + self.title_bar_height
        )
    
    def initialize_new_polygon(self, adjusted_pos): # Initialize new polygon with a tiny non-empty shape
        # Initialize new polygon with a tiny non-empty shape
        self.angle = 0
        self.selection_start = adjusted_pos
        self.corners = [adjusted_pos,adjusted_pos + QPointF(0.1, 0.1)]
        self.selection_line = QLineF(self.corners[0], self.corners[1])
        self.overlay.set_selection_line(self.selection_line)

    def remove_existing_handles(self): # Remove existing handles properly
        if hasattr(self, 'corner_handles'):
            for handle in self.corner_handles:
                handle.deleteLater()
            del self.corner_handles

    def distance_point_to_line(self, point, line): # Calculate the distance between a point and a line
        dist_to_line = abs((line.p2().y() - line.p1().y()) * point.x() - (line.p2().x() - line.p1().x()) * point.y() + line.p2().x() * line.p1().y() - line.p2().y() * line.p1().x()) / line.length()
        dist_to_p1 = math.sqrt((point.x() - line.p1().x())**2 + (point.y() - line.p1().y())**2)
        dist_to_p2 = math.sqrt((point.x() - line.p2().x())**2 + (point.y() - line.p2().y())**2)
        if dist_to_p1 > line.length()+10 or dist_to_p2 > line.length()+10:
            return math.inf
        return dist_to_line

    def mouseMoveEvent(self, event): # This event handles polygon size and dragging (either inside or outside the polygon)
        adjusted_pos = QPointF(event.pos() - QPoint(0, self.title_bar_height))
        if event.buttons() == Qt.MouseButton.LeftButton and self.selection_start != None:
            if hasattr(self, 'drag_offset') and self.drag_offset:
                self.translate_polygon(adjusted_pos)
            else:
                self.resize_polygon(adjusted_pos)
            self.update()
        self.plot_renderer()

    def translate_polygon(self, adjusted_pos): # Translates the polygon if it is dragged
        p1, p2 = self.selection_line.p1(), self.selection_line.p2()
        delta = adjusted_pos - self.drag_offset - self.selection_line.p1()
        if self.is_within_image_area(p1.x()+delta.x(), p1.y()+delta.y()+self.title_bar_height) and self.is_within_image_area(p2.x()+delta.x(), p2.y()+delta.y()+self.title_bar_height):
            self.selection_line.translate(delta)
            self.corners = [corner + delta for corner in self.corners]
            self.overlay.set_selection_line(self.selection_line)
            self.translate_corner_handles()

    def resize_polygon(self, adjusted_pos): # Resize the polygon while dragging new polygon
        self.selection_end = adjusted_pos
        if self.is_within_image_area(self.selection_end.x(), self.selection_end.y()+self.title_bar_height):
            self.corners = [
                self.selection_start,
                self.selection_end,
            ]
            self.selection_line = QLineF(self.corners[0], self.corners[1])
            self.overlay.set_selection_line(self.selection_line)
            length = abs(self.selection_line.length())
            self.selection_size.setText("Selection length: {:.2f} µm".format(length/self.parent.img_scale_x*self.parent.x_scale))
            self.overlay.move(0, self.title_bar_height)

    def mouseReleaseEvent(self, event): # This is the event listens for mouse release
        if self.selection_start != None:
            end_y = max(0, min(event.pos().y() - self.title_bar_height, self.parent.img_scale_y))
            end_x = max(0, min(event.pos().x() - 0, self.parent.img_scale_x))

            if hasattr(self, 'drag_offset') and self.drag_offset:
                self.drag_offset = None
            else:
                self.finalize_line(QPointF(end_x, end_y))
            self.update()
        self.plot_renderer()

    def finalize_line(self, end_pos): # Finalize the line after dragging
        self.selection_end = end_pos
        self.corners = [self.selection_start, self.selection_end]
        self.selection_line = QLineF(self.corners[0], self.corners[1])
        self.overlay.set_selection_line(self.selection_line)
        self.add_corner_handles()  # Add draggable points after polygon is created

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
            else:
                point.set_rotation(self.angle + i * np.pi / 2)
        self.plot_renderer()

    def update_corner_handle(self, point): # Update the corner handles when dragged
        index = self.corner_handles.index(point)
        self.corners[index] = QPointF(point.pos()) + QPointF(int(CORNER_HANDLE_SIZE/2), int(-self.title_bar_height + CORNER_HANDLE_SIZE/2))  # Adjust for new handle size

        length = abs(self.selection_line.length())
        self.selection_size.setText("Selection length: {:.2f} µm".format(length/self.parent.img_scale_x*self.parent.x_scale))

        # Update the selection polygon with the new corner positions
        self.selection_line = QLineF(self.corners[0], self.corners[1])
        self.overlay.set_selection_line(self.selection_line)
        self.update()
        self.translate_corner_handles()        
        self.plot_renderer()

    def calculate_corner_handle_position(self, i, corner: QPointF) -> QPointF: # Calculate rotation handle position
        handle_pos = corner + QPointF(-CORNER_HANDLE_SIZE/2 + 5*math.cos(-self.angle+3*np.pi/4-i*np.pi/2), 
                                      -CORNER_HANDLE_SIZE/2 - 5*math.sin(-self.angle+3*np.pi/4-i*np.pi/2))
        return QPointF(handle_pos.x(), handle_pos.y() + self.title_bar_height)

    def translate_corner_handles(self): # When translating polygon, update corner handles
        if hasattr(self, 'corner_handles'):
            for i, corner in enumerate(self.corners):
                corner_pos = self.calculate_corner_handle_position(i, corner)
                self.corner_handles[i].move(int(corner_pos.x()), int(corner_pos.y()))
                x, y = self.corner_handles[i].pos().x()+CORNER_HANDLE_SIZE/2, self.corner_handles[i].pos().y()+CORNER_HANDLE_SIZE/2
                if not self.is_within_image_area(x, y):
                    self.corner_handles[i].setPixmap(QPixmap())
                else:
                    self.corner_handles[i].set_rotation(self.angle + i * np.pi / 2)

    """Overlay and plot renderer"""
    def update_overlay(self):
        if not self.selection_line.isNull():
            mask = QRegion(self.image_label.rect())
            self.overlay.setMask(mask)
            self.overlay.set_selection_line(self.selection_line)
            self.overlay.update()
        else:
            self.overlay.clearMask()
            self.overlay.set_selection_line(QLineF())
            self.overlay.update()
        self.translate_corner_handles()  # Update draggable points when overlay is updated

    def plot_renderer(self):
        self.ratio = self.parent.img_scale_x / self.parent.img_scale_y
        p1, p2 = self.selection_line.p1(), self.selection_line.p2()
        p1x, p2x = self.parent.img_scale_x - p1.x(), self.parent.img_scale_x - p2.x()
        p1y, p2y = self.parent.img_scale_y - p1.y(), self.parent.img_scale_y - p2.y()
        #Convert to data coordinates
        x_scaling = self.parent.x_scale/self.parent.img_scale_x
        y_scaling = self.parent.y_scale/self.parent.img_scale_y
        x1, y1 = p1.x() * x_scaling, p1.y() * y_scaling
        x2, y2 = p2.x() * x_scaling, p2.y() * y_scaling
        closest_x1_index = np.abs(self.parent.Raw_x - x1).argmin()
        closest_y1_index = np.abs(self.parent.Raw_y - y1).argmin()
        closest_x2_index = np.abs(self.parent.Raw_x - x2).argmin()
        closest_y2_index = np.abs(self.parent.Raw_y - y2).argmin()
        if closest_x2_index < closest_x1_index:
            closest_x1_index, closest_x2_index = closest_x2_index, closest_x1_index
        if closest_y2_index < closest_y1_index:
            closest_y1_index, closest_y2_index = closest_y2_index, closest_y1_index
        
        if closest_x2_index - closest_x1_index > closest_y2_index - closest_y1_index:
            x_indices = np.arange(closest_x1_index, closest_x2_index)
            y_indices = np.linspace(closest_y1_index, closest_y2_index, len(x_indices))
            y_indices = y_indices.astype(int)
        else:
            y_indices = np.arange(closest_y1_index, closest_y2_index)
            x_indices = np.linspace(closest_x1_index, closest_x2_index, len(y_indices))
            x_indices = x_indices.astype(int)

        if y1 > y2:
            y_indices = np.flip(y_indices)
        plotting_line = self.Raw_Z[y_indices, x_indices]

        self.figure = Figure(facecolor=LINE_CUT_FACE_COLOR, edgecolor=PLOT_TEXT_COLOR, frameon=True, figsize=(5, 5), dpi=int(self.parent.img_scale_x/5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.img_scale = self.parent.img_scale_x
        self.preview_label.setFixedSize(self.img_scale, self.img_scale)        
        self.ax = self.figure.add_subplot(111)
        length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        x_axis = np.linspace(0, length, len(plotting_line))
        self.ax.plot(x_axis,plotting_line, color=LINE_CUT_COLOR, linewidth=2)
        self.ax.set_facecolor(LINE_CUT_FACE_COLOR)
        self.ax.set_xlim(0, length)
        self.ax.set_xlabel("Distance (µm)", color=PLOT_TEXT_COLOR, fontsize=12)
        self.ax.set_ylabel("Height (nm)", color=PLOT_TEXT_COLOR, fontsize=12)
        self.ax.tick_params(axis='x', colors=PLOT_TEXT_COLOR)
        self.ax.tick_params(axis='y', colors=PLOT_TEXT_COLOR)
        self.ax.spines['bottom'].set_color(PLOT_TEXT_COLOR)
        self.ax.spines['top'].set_color(PLOT_TEXT_COLOR)
        self.ax.spines['right'].set_color(PLOT_TEXT_COLOR)
        self.ax.spines['left'].set_color(PLOT_TEXT_COLOR)
        self.figure.tight_layout()
        self.canvas.draw()
        pixelmap = QPixmap(self.canvas.grab())

        self.preview_label.setPixmap(pixelmap)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

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