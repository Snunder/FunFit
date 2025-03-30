"""Built-in modules"""
import sys
import os

"""External modules"""
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QGridLayout, QLabel
from PyQt6.QtGui import QIcon, QPixmap

"""Internal modules"""
try:
    from FunFit.Functions import Fit_selection, Load, Find_structs, Roughness_analysis, Step_line_correction, Plane_leveling, helpers, Bitmap_generator, Plot_lines
except:
    from Functions import Fit_selection, Load, Find_structs, Roughness_analysis, Step_line_correction, Plane_leveling, helpers, Bitmap_generator, Plot_lines

"""Set QT_QPA_PLATFORM to xcb if running on Wayland"""
if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ["QT_QPA_PLATFORM"] = "xcb"

"""Window position"""
window_pos_x, window_pos_y = 100, 100

BUTTONS = [
    ("Load files", Load.load_data),
    ("Find structured area", Find_structs.crop_data),
    ("Step line correction", Step_line_correction.line_correction),
    ("Plane levelling", Plane_leveling.fit_and_subtract_plane),
    ("Plot line cuts", Plot_lines.crop_data),
    ("Fit functions", Fit_selection.init_interface),
    ("Roughness of flat area", Roughness_analysis.extract_roughness),
    ("Bitmap generator", Bitmap_generator.bmp_generator)
]

class MainWindow(QMainWindow):
    """Main window class for the FunFit GUI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_dir = os.path.dirname(os.path.abspath(__file__)) # Get the current directory
        if self.current_dir.endswith('Functions'): # If the current directory ends with 'Functions'
            self.current_dir = os.path.dirname(self.current_dir) # Set the current directory to the parent directory
        self.setWindowIcon(QIcon(os.path.join(self.current_dir, "GUI", "icon.ico"))) # Set the window icon

        self.setup_ui()
        self.setAcceptDrops(True)  # Enable drag-and-drop
        self.corner_decorations = []  # Store corner decorations

        self.default_layout = None  # Placeholder to store the default button layout
        self.drop_label = QLabel("Drop files here", self)  # QLabel for drag-and-drop indication
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setStyleSheet("""
            font-size: 28px;
            color: lightgray;
            background-color: transparent;
        """)
        self.drop_label.hide()  # Hide the label initially
    
    """Set up the main window UI"""
    def setup_ui(self):
        # Main window setup
        with open(self.current_dir + "/GUI/stylesheet.qss", "r") as f:
            self.setStyleSheet(f.read())
        self.setWindowTitle("Main Window")
        self.setGeometry(window_pos_x, window_pos_y, 0, 0)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QGridLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        # Add titlebar without title from helpers.py
        title_bar = helpers.create_title_bar(self, "", "main")
        title_bar.setMaximumHeight(80)
        self.main_layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)
        self.add_function_buttons(self.main_layout)  # Add function buttons to the main layout
        self.default_layout = self.main_layout  # Store the default layout
        self.center() # Center the window after it is shown

    def center(self):
        self.adjustSize()
        screen = self.screen().availableGeometry()
        
        # Calculate center position
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        
        # Move the window to the center
        self.move(x, y)

    """Function buttons"""
    def add_function_buttons(self, layout):
        # Add buttons, connect to their function and set icon (if there is one)
        for i, (button_name, function) in enumerate(BUTTONS):
            button = QPushButton(button_name)
            button.setObjectName("main_button")
            button.clicked.connect(lambda _, func=function: func(self))
            icon_name = f"icon_{button_name.lower().replace(' ', '_')}"
            button.setIcon(QIcon(QPixmap(os.path.join(self.current_dir, "GUI", icon_name + ".png"))))
            button.setIconSize(QSize(32, 32))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            if i == 0:  # Add margin to top and bottom
                button.setStyleSheet("margin-top: 10px;")
            elif i == len(BUTTONS) - 1:
                button.setStyleSheet("margin-bottom: 10px;")
            layout.addWidget(button, i + 1, 0, Qt.AlignmentFlag.AlignTop)

    """Drag and drop handling"""
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.show_drag_indicator()
            self.show_corner_decorations()
            if hasattr(self, 'overlay') and self.overlay:
                try: self.overlay.hide()
                except: pass
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.hide_drag_indicator()
        self.hide_corner_decorations()
        if hasattr(self, 'overlay') and self.overlay:
            try: self.overlay.show()
            except: pass

    def dropEvent(self, event):
        self.hide_corner_decorations()
        self.hide_drag_indicator()
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.handle_file_drop(file_path)

    def handle_file_drop(self, file_path):
        try:
            # Load data from the dropped file
            Load.load_data(self, file_path)
        except:
            pass

    def show_drag_indicator(self):
        # Replace buttons with QLabel indicating drag-and-drop
        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            if widget:
                widget.hide()
        self.main_layout.addWidget(self.drop_label, 1, 0, -1, -1)
        self.drop_label.show()

    def hide_drag_indicator(self):
        # Restore buttons and hide QLabel
        self.drop_label.hide()
        self.drop_label.setParent(None)
        for i in reversed(range(self.main_layout.count())):
            widget = self.main_layout.itemAt(i).widget()
            if widget and widget is not self.drop_label:
                widget.show()
    
    """Corner decorations for drag-and-drop event"""
    def create_corner_decoration(self, position):
        # Create corner decorations with smooth pulsating animation.
        base_size, margin = 20, 10  # Base size and offset from corners
        corner = QLabel(self)
        corner.setFixedSize(base_size, base_size)
        styles = {
            "top-left": "border-top: 2px solid lightgray; border-left: 2px solid lightgray;",
            "top-right": "border-top: 2px solid lightgray; border-right: 2px solid lightgray;",
            "bottom-left": "border-bottom: 2px solid lightgray; border-left: 2px solid lightgray;",
            "bottom-right": "border-bottom: 2px solid lightgray; border-right: 2px solid lightgray;",
        }
        corner.setStyleSheet(f"border: none; {styles[position]}")
        positions = {
            "top-left": (margin, margin),
            "top-right": (self.width() - base_size - margin, margin),
            "bottom-left": (margin, self.height() - base_size - margin),
            "bottom-right": (self.width() - base_size - margin, self.height() - base_size - margin),
        }
        corner.setGeometry(*positions[position], base_size, base_size)
        corner.show()
        return corner

    def show_corner_decorations(self):
        # Create and show corner decorations for drag-and-drop event.
        positions = ["top-left", "top-right", "bottom-left", "bottom-right"]
        self.corner_decorations = [self.create_corner_decoration(pos) for pos in positions]

    def hide_corner_decorations(self):
        # Hide and delete all corner decorations.
        for decoration in self.corner_decorations:
            decoration.hide()
            decoration.deleteLater()
        self.corner_decorations.clear()

    def resizeEvent(self, event):
        # Reposition decorations when the window is resized.
        if self.corner_decorations:
            self.hide_corner_decorations()
            self.show_corner_decorations()  # Recreate decorations on resize
        super().resizeEvent(event)

"""Main function to run the application"""   
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()