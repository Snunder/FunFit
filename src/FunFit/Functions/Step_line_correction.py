"""Built-in modules"""
import warnings
import copy

"""External modules"""
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QMessageBox, QPushButton, QVBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt
import numpy as np

"""Internal modules"""
try:
    from FunFit.Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file
except:
    from Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file

BUTTONS = [
    ("Median Alignment", 0),
    ("Median Difference", 1),
    ("Polynomial", 2),
    ("Raw", 3)
]

class LineCorrectionWindow(QMainWindow):
    """Window for performing step line corrections."""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        if hasattr(parent, 'inside_image') and hasattr(parent, 'outside_image'):
            self.inside_image = parent.inside_image
            self.outside_image = parent.outside_image
        self.Raw_Z = parent.corrected_data if hasattr(parent, "corrected_data") else parent.Raw_Z
        self.original_Raw_Z = np.copy(parent.Raw_Z) # Preserve the original raw data
        self.x_scale, self.y_scale = parent.x_scale, parent.y_scale
        setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")
        self.init_ui(parent)

    def init_ui(self, parent): # Set up the LineCorrectionWindow UI
        # Set window properties
        self.setWindowTitle("Line Correction")
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), 0, 0)  # Adjust the window dimensions
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Add a main layout for storing widgets
        main_widget = QWidget(self)
        layout = QGridLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # Add title bar at the top
        title_bar = create_title_bar(self, "Step line correction", "child")
        layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)

        # Populate layout with buttons and image
        buttons_widget = self.add_function_buttons()
        layout.addWidget(buttons_widget, 1, 0, 1, 1, Qt.AlignmentFlag.AlignTop) # Add buttons to the left
        image_widget = display_data(self)
        layout.addWidget(image_widget, 1, 1, 1, 1, Qt.AlignmentFlag.AlignCenter) # Add image to the right
        self.add_apply_button(layout) # Add the apply button below the image
        self.show()

    def add_function_buttons(self): # Add buttons to the left of the displayed data
        buttons_widget = QWidget()  # Container for buttons
        buttons_layout = QVBoxLayout(buttons_widget)  # Vertical layout for stacking buttons
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(15)

        # Create buttons based on the button number and add them to the layout
        for i, (button_name, idx) in enumerate(BUTTONS):
            button = QPushButton(button_name)
            button.setObjectName(f"main_button")
            if i == 0:  # Add margin to top and bottom
                button.setStyleSheet("margin-top: 10px;")
            elif i == len(BUTTONS) - 1:
                button.setStyleSheet("margin-bottom: 10px;")
            button.clicked.connect(lambda _, func=self.handle_button_click, idx=i: func(idx))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            buttons_layout.addWidget(button)
            if button_name == "Polynomial":
                button.setToolTip("Select the degree of the polynomial fit")
                self.degree_slider = QSlider(Qt.Orientation.Horizontal)
                self.degree_slider.setMinimum(0)
                self.degree_slider.setMaximum(9)
                self.degree_slider.setValue(2)
                self.degree = 2
                self.degree_slider.valueChanged.connect(self.update_degree_display)
                self.degree_display = QLabel("Polynomial degree: 2")
                self.degree_display.setStyleSheet("color: white; font-size: 16px; font-family: Verdana;")

                buttons_layout.addWidget(self.degree_display, 0, Qt.AlignmentFlag.AlignCenter)
                buttons_layout.addWidget(self.degree_slider, 0, Qt.AlignmentFlag.AlignCenter)
                
        return buttons_widget

    def update_degree_display(self, value): # Update the polynomial degree display
        self.degree_display.setText("Polynomial degree: " + str(value))
        self.degree = value

    def add_apply_button(self, layout): # Add the apply button below the image
        apply_button_widget = QWidget()  # Container for the bottom button
        apply_button_layout = QVBoxLayout(apply_button_widget)
        apply_button_layout.setContentsMargins(0, 0, 0, 0)
        apply_button_layout.setSpacing(15)

        apply_button = QPushButton("Apply Correction")
        apply_button.setObjectName("main_button")
        apply_button.clicked.connect(self.apply_correction)
        apply_button_layout.addWidget(apply_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Add the bottom button layout to the grid layout below the image
        layout.addWidget(apply_button_widget, 2, 1, 1, 1, Qt.AlignmentFlag.AlignCenter)

    """Button click handlers"""
    def handle_button_click(self, button_index): # Handle button click
        raw_data = self.original_Raw_Z
        corrected_data = None

        match button_index:
            case 0:
                corrected_data = self.median_alignment(raw_data)
            case 1:
                corrected_data = self.median_difference(raw_data)
            case 2:
                corrected_data = self.polynomial_fit(raw_data, self.degree)
            case 3:
                corrected_data = raw_data

        if corrected_data is not None:
            self.corrected_data = corrected_data
            self.update_display(corrected_data)

    def median_alignment(self, data): # Perform median alignment
        # Use the outside of the highlighted rectangle for median alignment
        if hasattr(self.parent, 'inside_image') and hasattr(self.parent, 'outside_image'):
            outside_data = self.outside_image
            warnings.filterwarnings('ignore')
            median_values = np.nanmedian(outside_data, axis=1)
            warnings.filterwarnings('default')
            median_values[np.isnan(median_values)] = 0
            return data - median_values[:, np.newaxis]
        else:
            # Fallback to median alignment on the entire dataset if no rectangle is defined
            return data - np.median(data, axis=1)[:, np.newaxis]

    def median_difference(self, data): # Perform median difference alignment
        diff_data = copy.deepcopy(data)
        # Use the outside of the highlighted rectangle for median diff
        if hasattr(self.parent, 'inside_image') and hasattr(self.parent, 'outside_image'):
            outside_data = copy.deepcopy(self.outside_image)
            diff_data = outside_data
            median_diff = np.zeros(len(diff_data))
            for i in range(len(diff_data)-1):
                differences = diff_data[i] - diff_data[i+1]
                warnings.filterwarnings('ignore')
                median_diff[i+1] = np.median(differences[np.where(~np.isnan(differences))])
                warnings.filterwarnings('default')
                median_diff[np.isnan(median_diff)] = 0
                diff_data[i+1, :] = diff_data[i+1, :] + median_diff[i+1]
            return data + median_diff[:, np.newaxis] - np.nanmedian(diff_data[0])
        else:
            # Fallback to median diff alignment on the entire dataset if no rectangle is defined
            median_diff = np.zeros(len(diff_data))
            for i in range(len(diff_data)-1):
                differences = diff_data[i] - diff_data[i+1]
                median_diff[i+1] = np.median(differences[np.where(~np.isnan(differences))])
                diff_data[i+1, :] = diff_data[i+1, :] + median_diff[i+1]
            return data + median_diff[:, np.newaxis] - np.median(diff_data[0])

    def polynomial_fit(self, data, degree): # Perform polynomial fit alignment
        if degree == 0:
            return self.median_alignment(data)
        poly_data = copy.deepcopy(data)
        # Use the outside of the highlighted rectangle for polynomial fit
        if hasattr(self.parent, 'inside_image') and hasattr(self.parent, 'outside_image'):
            outside_data = self.outside_image
            x = np.arange(len(outside_data[0]))
            for i in range(len(outside_data)):
                y = outside_data[i]
                idx = np.isfinite(y)
                if len(x[idx]) < 2:
                    continue
                p = np.polyfit(x[idx], y[idx], degree)
                poly_data[i] = poly_data[i] - np.polyval(p, x)
            return poly_data
        else:
            # Fallback to polynomial fit on the entire dataset if no rectangle is defined
            x = np.arange(len(data))
            for i in range(len(data)):
                y = data[i]
                idx = np.isfinite(y)
                p = np.polyfit(x[idx], y[idx], degree)
                poly_data[i] = poly_data[i] - np.polyval(p, x)
            return poly_data

    """Update the displayed data"""
    def update_display(self, data): # Update the displayed data
        self.Raw_Z = data
        image_widget = display_data(self)
        layout = self.centralWidget().layout()
        layout.itemAtPosition(1, 1).widget().deleteLater()  # Remove the existing widget
        layout.addWidget(image_widget, 1, 1, 1, 1, Qt.AlignmentFlag.AlignCenter)  # Add the new widget

    """Apply the correction"""
    def apply_correction(self): # Apply the correction to the data
        if not hasattr(self, "corrected_data"):
            self.parent.corrected_data = self.original_Raw_Z
        else:    
            self.parent.corrected_data = self.corrected_data
        self.Raw_Z = self.parent.corrected_data
        image = display_data(self)
        self.parent.image.setPixmap(image.pixmap())
        self.close()

"""Function called from main window."""
def line_correction(self=None):
    try: 
        self.w = LineCorrectionWindow(self)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()