"""Built-in modules"""
import os

"""External modules"""
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

"""Internal modules"""
try:
    from FunFit.Functions.Fit_selection import FunctionSelectionWindow
    import FunFit.Functions.Fit_handling as Fit_handling
    from FunFit.Functions.Fit_handling import model_function_builder
except:
    from Functions.Fit_selection import FunctionSelectionWindow
    import Functions.Fit_handling as Fit_handling
    from Functions.Fit_handling import model_function_builder

BUTTONS = [
    ("Polynomials", Fit_handling.Polynomials, "polynomial"),
    ("Exponential", Fit_handling.Exponential, "exponential"),
    ("Fourier series", Fit_handling.FourierSeries, "fourierseries"),
    ("Quasicrystal", Fit_handling.Quasicrystal, "quasicrystal"),
    ("Gaussian", Fit_handling.Gaussian, "gaussian"),
    ("Custom function", Fit_handling.Custom, "custom")
]

class InputDialog_BMP(QWidget):
    """Window to input parameters for the bitmap generator."""
    def __init__(self, parent, function):
        super().__init__()
        self.function = function
        self.parent = parent
        self.on_submit()
        
    def on_submit(self): # When the user submits open ParameterSelectionWindow with the parameters for the bitmap generator
        x_size = 1
        y_size = 1
        nm_px = 10*1e-3
        no_x = int(np.ceil(x_size/nm_px))
        no_y = int(np.ceil(y_size/nm_px))
        self.parent.Raw_x = np.linspace(-x_size/2, x_size/2, no_x)
        self.parent.Raw_y = np.linspace(-y_size/2, y_size/2, no_y)
        self.parent.Raw_Z = np.zeros((no_x, no_y))
        Fit_handling.ParameterSelectionWindow.add_parameter_widgets = add_parameter_widgets
        self.function(self.parent)
        self.close()

"""Bitmap_generator.add_parameter_widgets - Used when generating a bitmap"""
def add_parameter_widgets(self):
    # Add equation label at the top
    equation_pixmap = self.get_equation_image()
    equation_label = QLabel()
    equation_label.setPixmap(equation_pixmap)
    equation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    equation_label.setFixedHeight(50)
    self.scroll_layout.addWidget(equation_label, 0, 0, 1, 2)
    self.equation_label = equation_label
    
    # Existing parameter widgets
    skip_params = ["x0", "y0"]
    for i, param in enumerate([p for p in self.parameters if p not in skip_params]):
        label, line_edit = Fit_handling.create_param_widget(param, self)
        self.param_edits[param] = line_edit
        self.scroll_layout.addWidget(label, i + 1, 0)
        self.scroll_layout.addWidget(line_edit, i + 1, 1)
        self.scroll_layout.setRowMinimumHeight(i + 1, 30)
        self.scroll_layout.setRowStretch(i + 1, 0)

    # Adjust apply button position
    apply_button = QPushButton("Export bitmap")
    apply_button.clicked.connect(self.on_apply)
    apply_button.setObjectName("main_button")
    main_layout = self.centralWidget().layout()
    main_layout.addWidget(apply_button, 2, 1)

    # Add bitmap specific parameters
    self.bmp_info_layout = QGridLayout()
    self.bmp_info_layout.setContentsMargins(0, 0, 0, 10)
    self.bmp_info_layout.setSpacing(0)
    names = ["x dimension [µm]:", 
             "y dimension [µm]:", 
             "Resolution [nm/px]:"]
    for i, param in enumerate(["x_scale", "y_scale", "nm_px"]):
        label, line_edit = Fit_handling.create_param_widget(param, self)
        self.param_edits[param] = line_edit
        line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        line_edit.textChanged.connect(lambda: self.update_bitmap())
        
        line_edit.setPlaceholderText("1" if "scale" in param else "10")
        label.setText(names[i])
        self.bmp_info_layout.addWidget(label, i + 1, 0)
        self.bmp_info_layout.addWidget(line_edit, i + 1, 1)
        self.bmp_info_layout.setRowMinimumHeight(i + 1, 30)
    main_layout.addLayout(self.bmp_info_layout, 2, 0, 1, 1)

"""Bitmap_generator.create_button_handler - Used when generating a bitmap"""
def create_button_handler(self, function):
    def handler():
        self.w2 = InputDialog_BMP(self, function) # Open the input dialog for the bitmap generator
        self.tooltip.hide()
        self.close()
    return handler

"""Bitmap_generator.on_apply - Used when generating a bitmap"""
def on_apply(self):
    # Extract parameters and build the equation
    param_values = {param: self.param_edits[param].text().strip() for param in self.param_edits if param != "N"}
    
    # Skip parameters for scaling if they are present
    skip_params = ["x_scale", "y_scale", "nm_px"]
    x_size, y_size, nm_px = None, None, None
    for param in skip_params:
        if param in param_values:
            if param == "nm_px":
                nm_px = float(param_values["nm_px"])*1e-3 if param_values["nm_px"] != '' else 10*1e-3
            elif param == "x_scale":
                x_size = float(param_values["x_scale"]) if param_values["x_scale"] != '' else 1
            elif param == "y_scale":
                y_size = float(param_values["y_scale"]) if param_values["y_scale"] != '' else 1
    param_values = {param: param_values[param] for param in param_values if param not in skip_params}
    
    # Calculate the number of pixels based on the scale
    try:
        no_x = int(np.ceil(x_size/nm_px))
        no_y = int(np.ceil(y_size/nm_px))
        self.parent.Raw_x = np.linspace(-x_size/2, x_size/2, no_x)
        self.parent.Raw_y = np.linspace(-y_size/2, y_size/2, no_y)
        self.parent.Raw_Z = np.zeros((no_x, no_y))
        self.ratio = x_size / y_size
    except Exception as e: print(e); pass

    # Get values for the parameters
    try:
        param_values["N"] = self.param_edits["N"]
        if param_values["N"] == "":
            param_values["N"] = 1
    except: pass

    # Convert parameters to float
    for param in param_values:
        if param_values[param] == "":
            param_values[param] = float(self.param_edits[param].placeholderText().strip())
        else:
            try:
                param_values[param] = float(param_values[param])
            except:
                param_values[param]
    
    # Build the model function
    model_func = model_function_builder(self.function_name, param_values)
    x_full, y_full = np.meshgrid(self.parent.Raw_x-np.mean(self.parent.Raw_x), self.parent.Raw_y-np.mean(self.parent.Raw_y))
    try:
        Z_fit = model_func((x_full.flatten(), y_full.flatten()), *param_values.values()).reshape(len(self.parent.Raw_y), len(self.parent.Raw_x))
    except:
        return
    
    # Open a file dialog to select the directory to save the bitmap
    Dialog_window = QFileDialog()
    Dialog_window.setWindowTitle(f"Export bitmap")
    Dialog_window.setFileMode(QFileDialog.FileMode.Directory)
    Dialog_window.setOption(QFileDialog.Option.DontUseNativeDialog)
    Dialog_window.setWindowIcon(QIcon(os.path.join(self.parent.parent.current_dir, "GUI", "icon_window.png")))
    Dialog_window.setDirectory(os.path.dirname(self.parent.parent.current_dir) + "/tests")
    if Dialog_window.exec() == QFileDialog.DialogCode.Accepted:
        file_path = Dialog_window.selectedFiles()[0]
    else:
        return

    # Save Z_fit as a bitmap file
    if file_path == '':
        return
    filepath_name = os.path.join(file_path, "bitmap.bmp")
    plt.imsave(filepath_name, Z_fit, cmap='gray')

    self.close()

"""Function called from main window."""
def bmp_generator(self=None):
    self.current_dir = os.path.dirname(os.path.realpath(__file__))
    if self.current_dir.endswith('Functions'):
        self.current_dir = os.path.dirname(self.current_dir)
    try:
        FunctionSelectionWindow.create_button_handler = create_button_handler
        Fit_handling.ParameterSelectionWindow.on_apply = on_apply
        self.w = FunctionSelectionWindow(self)
        buttons = self.w.findChildren(QPushButton)
        for button in buttons:
            if button.text() == "Auto (pending)":
                button.deleteLater()
        self.w.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
        labels = self.w.findChildren(QLabel)
        for label in labels:
            if label.text() == "Select fit preset":
                label.setText("Select .bmp preset")
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()
