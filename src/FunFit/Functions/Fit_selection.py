"""External modules"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QPushButton, QMessageBox, QLabel
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor

"""Internal modules"""
try:
    from FunFit.Functions import Fit_handling, helpers
except:
    from Functions import Fit_handling, helpers

BUTTONS = [
    ("Polynomials", Fit_handling.Polynomials, "polynomial"),
    ("Exponential", Fit_handling.Exponential, "exponential"),
    ("Fourier series", Fit_handling.FourierSeries, "fourierseries"),
    ("Quasicrystal", Fit_handling.Quasicrystal, "quasicrystal"),
    ("Gaussian", Fit_handling.Gaussian, "gaussian"),
    ("Custom function", Fit_handling.Custom, "custom")
]

class HoverButton(QPushButton):
    """Button that displays a bitmap when hovered."""
    hovered = pyqtSignal(QPoint, QPixmap)
    unhovered = pyqtSignal()
    def __init__(self, text, equation_type): # Set up the button
        super().__init__(text)
        self.bitmap_pixmap = helpers.generate_bitmap_from_equation(equation_type) if equation_type not in ["auto"] else None
        self.setMouseTracking(True)

    def enterEvent(self, event): # Show the bitmap when the mouse enters the button
        if self.bitmap_pixmap:
            self.hovered.emit(event.globalPosition().toPoint(), self.bitmap_pixmap)
        super().enterEvent(event)

    def leaveEvent(self, event): # Hide the bitmap when the mouse leaves the button
        if self.bitmap_pixmap:
            self.unhovered.emit()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event): # Update the bitmap position when the mouse moves
        if self.bitmap_pixmap:
            self.hovered.emit(event.globalPosition().toPoint(), self.bitmap_pixmap)
        super().mouseMoveEvent(event)

class ToolTipWindow(QLabel):
    """Window to display a tooltip."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background: white; border: 1px solid black;")

    def show_bitmap(self, pos, pixmap): # Show the tooltip with a bitmap
        if not pixmap.isNull():
            self.setPixmap(pixmap)
            self.adjustSize()
            self.move(pos + QPoint(0, 0))
            self.show()

class FunctionSelectionWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_dir = parent.current_dir
        self.main_window = parent
        self.tooltip = ToolTipWindow()
        self.setWindowTitle("Function Selection")
        self.setGeometry(0, 0, 0, 0)
        self.setup_ui(parent)
        
    def setup_ui(self, parent): # Set up the FunctionSelectionWindow UI
        # Set window properties
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), 0, 0)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        helpers.setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")

        # Create the main layout
        main_widget = QWidget(self)
        layout = QGridLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # Add title bar at the top
        title_bar = helpers.create_title_bar(self, "Select fit preset", "child")
        layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)

        # Add buttons to the window with tooltips
        for i, (name, function, equation_type) in enumerate(BUTTONS):
            button = HoverButton(name, equation_type)
            button.setObjectName("main_button")
            button.clicked.connect(self.create_button_handler(function))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.hovered.connect(self.show_tooltip)
            button.unhovered.connect(self.hide_tooltip)
            layout.addWidget(button, i+1, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        self.show()

    def create_button_handler(self, function): # Create a button handler for the function
        # Placeholder function populated when calling FunctionSelectionWindow
        return
    
    def show_tooltip(self, pos, pixmap): # Show the tooltip with a bitmap
        fixed_offset = QPoint(20, 0)
        cursor_pos = QCursor.pos()
        self.tooltip.show_bitmap(cursor_pos + fixed_offset, pixmap)

    def hide_tooltip(self): # Hide the tooltip
        self.tooltip.hide()

"""Function called from main window."""
def init_interface(self=None):
    try:
        Fit_handling.ParameterSelectionWindow.on_apply = Fit_handling.on_apply
        Fit_handling.ParameterSelectionWindow.add_parameter_widgets = Fit_handling.add_parameter_widgets
        FunctionSelectionWindow.create_button_handler = create_button_handler
        self.w = FunctionSelectionWindow(self)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()

"""Button handler for FunctionSelectionWindow."""
def create_button_handler(self, function):
    def handler():
        function(self.main_window)
        self.tooltip.hide()
        self.close()
    return handler