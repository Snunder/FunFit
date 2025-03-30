"""Built-in modules"""
from io import BytesIO
import copy

"""External modules"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from scipy.optimize import curve_fit
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt, QTimer, QRect
from PyQt6.QtGui import QIntValidator, QPixmap, QPainter, QPen, QColor
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QMessageBox, QLabel, QLineEdit, QScrollArea, QPushButton


"""Internal modules"""
try:
    from FunFit.Functions import helpers
    from FunFit.Functions.Fit_plotting import PlotWindow, ResultsWindow
    from FunFit.Functions.Custom_fit_handling import CustomFunctionWindow
    from FunFit.Functions.Fit_config import FIT_PRESETS, FIT_EQUATIONS
except:
    from Functions import helpers
    from Functions.Fit_plotting import PlotWindow, ResultsWindow
    from Functions.Custom_fit_handling import CustomFunctionWindow
    from Functions.Fit_config import FIT_PRESETS, FIT_EQUATIONS

"""Set fitting parameters for chosen function"""
def set_fitting_params(parent, func_name, parameters=None):
    global FITTINGPARAMETERS
    if func_name == "Custom" and parameters is not None: # Custom function with parameters
        FITTINGPARAMETERS = parameters
    else: # Hard coded functions
        FITTINGPARAMETERS = FIT_PRESETS[func_name]
    init_interface(parent, parameters=FITTINGPARAMETERS, function_name=func_name) # Initialize parameter selection window

"""Create fitting function based on selected model and parameters"""
def model_function_builder(func_name, param_edits):
    def polynomial_model(X, *params):
        x, y = X
        N = int(param_edits["N"].text().strip() or 1)
        coeffs, c = params[:N], params[-1] if len(params) > N else 0.0
        try:
            c = float(c.text().strip())
        except:
            pass
        return c + np.sum([coeffs[i] * (x ** (i + 1)) for i in range(N)], axis=0)
    def exponential_model(X, *params):
        x, y = X
        A, b, c = params
        return A * np.exp(b * x) + c
    def gaussian_model(X, *params):
        x, y = X
        A, mu_x, mu_y, sigma_x, sigma_y, c = params
        return A * np.exp(-((x - mu_x)**2 / (2 * sigma_x**2) + (y - mu_y)**2 / (2 * sigma_y**2))) + c
    def quasicrystal_model(X, *params):
        x, y = X
        N = int(param_edits["N"].text().strip() or 1)
        if len(params) < 3*N + 4:
            theta, x0, y0, c = params[3*N] * np.pi / 180, 0.0, 0.0, params[3*N + 1]
        else:
            theta, x0, y0, c = params[3*N] * np.pi / 180, params[3*N + 1], params[3*N + 2], params[3*N + 3]
        result = sum(params[i*3] * np.cos(2 * np.pi / params[i*3 + 1] * ((x - x0) * np.cos((theta + i * 180 / N) * np.pi / 180) + (y - y0) * np.sin((theta + i * 180 / N) * np.pi / 180)) + params[i*3 + 2]) for i in range(N))
        return result + c
    def fourier_model(X, *params):
        x, y = X
        N = int(param_edits["N"].text().strip() or 1)
        theta, c = params[3*N] * np.pi / 180, params[3*N + 1]
        result = sum(params[i*3] * np.cos(2 * np.pi / params[i*3 + 1] * (x * np.cos(theta) + y * np.sin(theta)) + params[i*3 + 2]) for i in range(N))
        return result + c
    models = {
        "Polynomials": polynomial_model,
        "Exponential": exponential_model,
        "Gaussian": gaussian_model,
        "Quasicrystal": quasicrystal_model,
        "Fourier series": fourier_model,
        "Custom": CUSTOM_MODEL
    }
    return models.get(func_name)

CUSTOM_MODEL = None

"""Called from Function_selection_window.py"""
def Auto(parent): # Auto - pending
    print("Auto")
def Polynomials(parent): # Polynomials
    set_fitting_params(parent, "Polynomials")
def Exponential(parent): # Exponential
    set_fitting_params(parent, "Exponential")
def Quasicrystal(parent): # Quasicrystal
    set_fitting_params(parent, "Quasicrystal")
def FourierSeries(parent): # Fourier series
    set_fitting_params(parent, "Fourier series")
def Gaussian(parent): # Gaussian function
    set_fitting_params(parent, "Gaussian")
def Custom(parent): # Custom function
    def handle_custom_accepted(model_func, parameters, func_str, latex_str):
        global CUSTOM_MODEL, FIT_EQUATIONS
        CUSTOM_MODEL = model_func
        FIT_PRESETS["Custom"] = parameters
        FIT_EQUATIONS["Custom"] = latex_str  # Store custom equation
        set_fitting_params(parent, "Custom", parameters=parameters)
        
    window = CustomFunctionWindow(parent) # Open custom function window
    window.accepted.connect(handle_custom_accepted)
    window.show()

"""Convert text to float, replace pi with numpy.pi"""
def parse_input(text):
    text = text.strip().replace("pi", str(np.pi))
    try:
        return float(eval(text))
    except:
        return 0.0

class FitWorker(QObject):
    """Worker class for fitting process."""
    finished = pyqtSignal(object, object, object) # (popt, perr, Z_fit)
    error = pyqtSignal(Exception)

    def __init__(self, parent, inside_image, params):
        super().__init__()
        self.parent = parent
        self.params = params
        self.inside_image = inside_image

    def run(self): # Run the fitting process
        try:
            # Load and prepare data
            Z_data = self.parent.corrected_data if hasattr(self.parent, 'corrected_data') else self.parent.Raw_Z
            initial_guesses = {}
            for param in self.params['FITTINGPARAMETERS']:
                if param not in ['x0', 'y0']:
                    text_val = self.params['param_edits'][param].text().strip() or "0.0"
                    initial_guesses[param] = parse_input(text_val)
            if self.inside_image is not None:
                if self.inside_image.shape == Z_data.shape:
                    mask = ~np.isnan(self.inside_image)
                else:
                    # Log mismatch and ignore the mask
                    print("Mask shape does not match data shape. Ignoring mask.")
                    mask = np.ones_like(Z_data, dtype=bool)
            else:
                mask = np.ones_like(Z_data, dtype=bool)

            x_flat, y_flat = np.meshgrid(self.parent.Raw_x, self.parent.Raw_y)
            x_flat, y_flat, Z = x_flat.flatten(), y_flat.flatten(), Z_data.flatten()
            x_flat, y_flat, Z = x_flat[mask.flatten()], y_flat[mask.flatten()], Z[mask.flatten()]

            # Determine initial guesses based on function type
            func_name = self.params['function_name']
            if func_name == "Gaussian":
                # Find max in MASKED data
                if len(Z) > 0:
                    max_idx = np.nanargmax(Z)
                    initial_guesses['µ_x'] = x_flat[max_idx]
                    initial_guesses['µ_y'] = y_flat[max_idx]
                else:  # Fallback if no data
                    initial_guesses['µ_x'] = 0.0
                    initial_guesses['µ_y'] = 0.0
                # Safeguard sigma values
                initial_guesses['σ_x'] = max(1.0, 1e-6)
                initial_guesses['σ_y'] = max(1.0, 1e-6)
                
            elif func_name in ["Quasicrystal", "Fourier series"]:
                # FFT-based translation detection with multiple peaks
                Z_data_2d = np.nan_to_num(Z_data) if np.isnan(Z_data).any() else Z_data
                fft_shift = np.fft.fftshift(np.fft.fft2(Z_data_2d - np.mean(Z_data_2d)))
                phase = np.angle(fft_shift)
                magnitude = np.abs(fft_shift)
                crow, ccol = magnitude.shape[0]//2, magnitude.shape[1]//2
                magnitude_work = magnitude.copy()
                magnitude_work[crow-10:crow+11, ccol-10:ccol+11] = 0  # Mask DC component

                n_components = int(self.params['param_edits']["N"].text().strip() or 1)
                peaks_info = []
                auto_lambdas = []  # Store detected wavelengths
                
                # Calculate pixel sizes
                dx = self.parent.Raw_x[1] - self.parent.Raw_x[0] if len(self.parent.Raw_x) > 1 else 1.0
                dy = self.parent.Raw_y[1] - self.parent.Raw_y[0] if len(self.parent.Raw_y) > 1 else 1.0

                for _ in range(n_components):
                    peak_idx = np.argmax(magnitude_work)
                    if magnitude_work.flat[peak_idx] == 0:
                        break
                    prow, pcol = np.unravel_index(peak_idx, magnitude_work.shape)
                    
                    # Calculate frequency components
                    freq_x = (pcol - ccol)/(magnitude_work.shape[1]*dx)
                    freq_y = (prow - crow)/(magnitude_work.shape[0]*dy)
                    
                    freq_magnitude = np.sqrt(freq_x**2 + freq_y**2)
                    wavelength = 1.0/freq_magnitude if freq_magnitude != 0 else 0.0
                    auto_lambdas.append(max(wavelength, 1e-6))  # Prevent zero wavelengths
                    phi = phase[prow, pcol]
                    peaks_info.append((freq_x, freq_y, phi))
    
                    # Mask detected peak
                    magnitude_work[max(0,prow-10):prow+11, max(0,pcol-10):pcol+11] = 0

                # Assign detected wavelengths to parameters
                lambda_params = [p for p in FITTINGPARAMETERS if p.startswith("λ<sub>")]
                for i, param in enumerate(lambda_params):
                    if i < len(auto_lambdas):
                        initial_guesses[param] = auto_lambdas[i]
                    else:
                        initial_guesses[param] = 1e-6  # Default safe value

                # Solve linear system for x0, y0 using all detected peaks
                if len(peaks_info) > 0:
                    A = []
                    b = []
                    for fx, fy, ph in peaks_info:
                        A.append([fx, fy])
                        b.append(-ph/(2*np.pi))
                    A = np.array(A)
                    b = np.array(b)
                    try:
                        x0_initial, y0_initial = np.linalg.lstsq(A, b, rcond=None)[0]
                    except np.linalg.LinAlgError:
                        # Fallback to strongest peak if matrix is singular
                        fx, fy, ph = peaks_info[0]
                        x0_initial = -ph/(2*np.pi*fx) if fx !=0 else 0
                        y0_initial = -ph/(2*np.pi*fy) if fy !=0 else 0
                    initial_guesses.update({'x0': x0_initial, 'y0': y0_initial})

            # Rest of the fitting process remains the same
            if "c" in FITTINGPARAMETERS:
                initial_guesses["c"] = np.mean(Z)
            p0 = [initial_guesses[p] for p in FITTINGPARAMETERS if p != "N"]
            model_func = model_function_builder(self.params['function_name'], self.params['param_edits'])

            if x_flat.size > 1e5:
                sample_idx = np.random.choice(x_flat.size, size=int(1e5), replace=False)
                x_flat = np.ascontiguousarray(x_flat[sample_idx])
                y_flat = np.ascontiguousarray(y_flat[sample_idx])
                Z = np.ascontiguousarray(Z[sample_idx])

            popt, pcov = curve_fit(model_func, (x_flat, y_flat), Z, p0=p0)
            x_full, y_full = np.meshgrid(self.parent.Raw_x, self.parent.Raw_y)
            Z_fit = model_func((x_full.flatten(), y_full.flatten()), *popt).reshape(len(self.parent.Raw_y), len(self.parent.Raw_x))
            perr = np.sqrt(np.diag(pcov)) if pcov is not None else np.full_like(popt, np.nan)
            self.finished.emit(popt, perr, Z_fit)
        except Exception as e:
            self.error.emit(e)
            
class ParameterSelectionWindow(QMainWindow):
    """Parameter selection window for fitting functions."""
    def __init__(self, parent, parameters, function_name):
        super().__init__()
        self.parent = parent
        if hasattr(parent, 'corrected_data'): self.Raw_Z = parent.corrected_data # Use corrected data if available
        else: self.Raw_Z = parent.Raw_Z
        self.Raw_x, self.Raw_y = parent.Raw_x, parent.Raw_y
        self.parameters, self.function_name = parameters, function_name
        self.dynamic_bases, self.static_params, self.param_edits = [], [], {}
        seen = set()

        # Extract dynamic and static parameters
        for param in parameters[1:]:
            if "<sub>" in param:
                base = param.split("<sub>")[0]
                if base not in seen:
                    seen.add(base)
                    self.dynamic_bases.append(base)
            else:
                if param not in self.static_params:
                    self.static_params.append(param)

        self.fit_thread, self.fit_worker = None, None
        helpers.setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")
        self.init_ui(parent)

    def init_ui(self, parent): # Initialize the ParameterSelectionWindow UI
        # Set window properties
        self.setWindowTitle(self.function_name)
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), 600, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Create the main layout
        main_layout = QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(central_widget)

        # Add title bar at the top
        title_bar = helpers.create_title_bar(self, self.function_name, "child")
        main_layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)

        # Add scroll area for parameter widgets
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.objectName = "scroll_content"
        self.scroll_layout = QGridLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)
        self.scroll_area.setWidget(scroll_content)
        main_layout.addWidget(self.scroll_area, 1, 0)

        # Add preview label for dynamic bitmap
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("background-color: transparent;")
        main_layout.addWidget(self.preview_label, 1, 1)

        self.add_parameter_widgets()
        self.initial_bitmap()
        self.update_bitmap()
        
    def initial_bitmap(self): # Set an initial bitmap for the preview label
        if hasattr(self.parent, 'x_scale') and hasattr(self.parent, 'y_scale'):
            self.ratio = self.parent.x_scale / self.parent.y_scale
        else:
            self.ratio = self.parent.Raw_x[-1] / self.parent.Raw_y[-1]
        self.img_scale = 300
        self.figure = Figure(facecolor='none', edgecolor='none', frameon=False, figsize=(5/self.ratio, 5), dpi=int(self.img_scale/5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.preview_label.setFixedSize(self.img_scale, self.img_scale)
        self.ax = self.figure.add_axes([0, 0, 1, 1], frameon=False)
        self.ax.set_xticks([]), self.ax.set_yticks([])
        x_full, y_full = np.meshgrid(self.parent.Raw_x, self.parent.Raw_y)
        scan_ratio = len(self.parent.Raw_x) / len(self.parent.Raw_y)
        Z_fit = np.zeros_like(x_full)
        
        self.ax.imshow(Z_fit, cmap='gray', origin='upper', aspect=1)
        self.canvas.draw()
        self.preview_label.setPixmap(QPixmap(self.canvas.grab()).scaled(int(self.preview_label.size().width() / np.sqrt(2)), int(self.preview_label.size().height() / np.sqrt(2)), 
                                                                           Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def get_equation_image(self): # Get the equation image for the preview label
        eq_str = FIT_EQUATIONS.get(self.function_name, "")
        fig = Figure(figsize=(6, 1))
        canvas = FigureCanvasQTAgg(fig)
        fig.patch.set_alpha(0.0)
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.text(0.05, 0.5, eq_str, ha='left', va='center', fontsize=14, color='white', usetex=False)

        buf = BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight')
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        return pixmap

    def add_parameter_widgets(self): # Add parameter widgets to the scroll area
        # Placeholder for adding parameter widgets
        return

    def modify_fitting_parameters(self, text): # Update FITTINGPARAMETERS array based on N input
        try:
            n = int(text)
            global FITTINGPARAMETERS
            FITTINGPARAMETERS = ["N"]
            for i in range(1, n + 1):
                for base in self.dynamic_bases:
                    FITTINGPARAMETERS.append(f"{base}<sub>{i}</sub>")
            FITTINGPARAMETERS.extend(self.static_params)
            if n > 0:
                self.update_ui(text)
        except ValueError:
            pass

    def update_ui(self, n_value=None): # Update UI when N is changed
        copy_param_edits = copy.copy(self.param_edits)
        self.param_edits.clear()
        n_label = None
        n_line_edit = None
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget == self.equation_label:
                continue
            if isinstance(widget, QLabel) and widget.text().startswith("N ="):
                n_label = widget
            elif isinstance(widget, QLineEdit) and widget.text() == (str(n_value) if n_value else ""):
                n_line_edit = widget
            else:
                if widget:
                    widget.deleteLater()

        for row in range(100):
            self.scroll_layout.setRowMinimumHeight(row, 0)

        if n_label and n_line_edit:
            self.scroll_layout.addWidget(n_label, 1, 0)
            self.scroll_layout.addWidget(n_line_edit, 1, 1)
            self.scroll_layout.setRowMinimumHeight(1, 30)
            self.param_edits["N"] = n_line_edit

        row_index = 2
        for param in [p for p in FITTINGPARAMETERS if p not in ("N", "x0", "y0")]:
            label, line_edit = create_param_widget(param, self)
            self.param_edits[param] = line_edit
            self.scroll_layout.addWidget(label, row_index, 0)
            self.scroll_layout.addWidget(line_edit, row_index, 1)
            self.scroll_layout.setRowMinimumHeight(row_index, 30)
            row_index += 1

        for param in [p for p in copy_param_edits if p in ("x_scale", "y_scale", "nm_px") and p not in FITTINGPARAMETERS]:
            self.param_edits[param] = copy_param_edits[param]
            self.update_bitmap()

        for row in range(100):
            self.scroll_layout.setRowMinimumHeight(row, 0)

        if n_label and n_line_edit:
            self.scroll_layout.addWidget(n_label, 1, 0)
            self.scroll_layout.addWidget(n_line_edit, 1, 1)
            self.scroll_layout.setRowMinimumHeight(1, 30)
            self.param_edits["N"] = n_line_edit
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.on_apply)
        apply_button.setObjectName("main_button")
        helpers.setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")

        self.scroll_layout.addWidget(apply_button, row_index, 0, 1, 2)

    def update_bitmap(self): # Update the dynamic bitmap based on the current parameters
        # Extract parameters and build the equation
        param_values = {param: self.param_edits[param].text().strip() for param in self.param_edits if param != "N"}

        # Skip parameters for scaling if they are present
        skip_params = ["x_scale", "y_scale", "nm_px"]
        x_size, y_size, nm_px = None, None, None
        for param in skip_params:
            if param in param_values:
                if param == "nm_px":
                    try: nm_px = float(param_values["nm_px"])*1e-3 if param_values["nm_px"] != '' else 10*1e-3
                    except ValueError: nm_px = 10*1e-3
                elif param == "x_scale":
                    try: x_size = float(param_values["x_scale"]) if param_values["x_scale"] != '' else 1
                    except ValueError: x_size = 1
                elif param == "y_scale":
                    try: y_size = float(param_values["y_scale"]) if param_values["y_scale"] != '' else 1
                    except ValueError: y_size = 1
        param_values = {param: param_values[param] for param in param_values if param not in skip_params}
        
        # Calculate the number of pixels based on the scale
        try:
            no_x = int(np.ceil(x_size/nm_px))
            no_y = int(np.ceil(y_size/nm_px))
            self.parent.Raw_x = np.linspace(-x_size/2, x_size/2, no_x)
            self.parent.Raw_y = np.linspace(-y_size/2, y_size/2, no_y)
            self.parent.Raw_Z = np.zeros((no_x, no_y))
            self.ratio = x_size / y_size
        except: pass

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
        
        if hasattr(self.parent, 'inside_image') and not nm_px:
            self.mask1 = ~np.isnan(self.parent.inside_image)
            self.x_masked = self.parent.Raw_x[self.mask1.any(axis=0)]
            self.y_masked = self.parent.Raw_y[self.mask1.any(axis=1)]
            self.ratio = self.x_masked[-1] / self.y_masked[-1]
            x_full, y_full = np.meshgrid(self.x_masked-np.mean(self.x_masked), self.y_masked-np.mean(self.y_masked))

        try:
            if hasattr(self, 'x_masked'):
                Z_fit = model_func((x_full.flatten(), y_full.flatten()), *param_values.values()).reshape(len(self.y_masked), len(self.x_masked))
            else:
                Z_fit = model_func((x_full.flatten(), y_full.flatten()), *param_values.values()).reshape(len(self.parent.Raw_y), len(self.parent.Raw_x))
        except:
            return

        # Plot the bitmap
        self.ax.clear()
        self.img_scale = 300
        self.preview_label.setFixedSize(self.img_scale, self.img_scale)
        self.figure = Figure(facecolor='none', edgecolor='none', frameon=False, figsize=(5, 5), dpi=int(self.img_scale/5.5))
        if self.ratio > 1:
            self.figure.set_size_inches(5, 5/self.ratio)
        elif self.ratio < 1:
            self.figure.set_size_inches(5*self.ratio, 5)
        else:
            self.figure.set_size_inches(5, 5)

        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_axes([0, 0, 1, 1], frameon=False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        if hasattr(self, 'x_masked'):
            x_full, y_full = np.meshgrid(self.x_masked, self.y_masked)
        else:
            x_full, y_full = np.meshgrid(self.parent.Raw_x, self.parent.Raw_y)

        x_extent = (x_full[-1, -1] - x_full[0, 0])/2
        y_extent = (y_full[-1, -1] - y_full[0, 0])/2
        self.ax.imshow(Z_fit, cmap='gray', origin='upper', aspect=1, extent=(-x_extent, x_extent, -y_extent, y_extent))
        self.canvas.draw()
        
        # Set the pixmap for the preview label
        pixelmap = QPixmap(self.canvas.grab())
        painter = QPainter(pixelmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#000000"), 8)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        r1 = pixelmap.rect().getCoords()
        painter.drawRect(QRect(r1[0], r1[1], r1[2], r1[3]))
        painter.end()
        self.preview_label.setPixmap(pixelmap)

    def on_apply(self): # Apply the fitting parameters
        if hasattr(self, 'plot_window') and self.plot_window is not None:
            self.plot_window.close()
            self.plot_window = None

        # Disable UI during fitting
        self.scroll_area.setEnabled(False)
        self.show_loading_overlay()

        # Prepare parameters for worker
        inside_image = getattr(self.parent, 'inside_image', None)
        params = {
            'parent': self.parent,
            'param_edits': self.param_edits,
            'FITTINGPARAMETERS': FITTINGPARAMETERS,
            'function_name': self.function_name
        }

        # Setup thread and worker
        self.fit_thread = QThread()
        self.fit_worker = FitWorker(self, inside_image, params)
        self.fit_worker.moveToThread(self.fit_thread)
        
        # Connect signals
        self.fit_thread.started.connect(self.fit_worker.run)
        self.fit_worker.finished.connect(self.on_fit_complete)
        self.fit_worker.error.connect(self.on_fit_error)
        self.fit_worker.finished.connect(self.fit_thread.quit)
        self.fit_worker.error.connect(self.fit_thread.quit)
        
        self.fit_thread.start()

    def show_loading_overlay(self): # Show loading overlay during fitting
        self.loading_label = QLabel("Processing", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("""
            font-size: 24px; 
            color: white; 
            background-color: rgba(0, 0, 0, 150);
        """)
        self.loading_label.setGeometry(0, 0, self.width(), self.height())
        self.loading_label.show()
        
        # Animation setup
        self.dot_count = 0
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.update_loading_dots)
        self.loading_timer.start(400)  # Update every 400ms

    def update_loading_dots(self): # Update loading dots dynamically
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.loading_label.setText(f"Processing{dots}")

    def hide_loading_overlay(self): # Hide loading overlay after fitting is complete
        if hasattr(self, 'loading_timer'):
            self.loading_timer.stop()
            self.loading_timer.deleteLater()
        if hasattr(self, 'loading_label'):
            self.loading_label.hide()
            self.loading_label.deleteLater()

    def on_fit_complete(self, popt, perr, Z_fit): # Process fitting results
        # Process results in main thread
        self.hide_loading_overlay()
        self.scroll_area.setEnabled(True)
        
        if hasattr(self.parent, 'corrected_data'): Raw_Z = self.parent.corrected_data  
        else: Raw_Z = self.parent.Raw_Z
        Z_fit_flipped = np.flip(Z_fit, axis=0) # Use np.flip instead of np.flipud for faster flipping
        
        # Flip the data if inside_image is present
        if hasattr(self.parent, 'inside_image'):
            mask_2d = np.isfinite(self.parent.inside_image)
            Z_data_inside = np.full_like(Raw_Z, np.nan)
            Z_data_inside[mask_2d] = Raw_Z[mask_2d]
            Z_data_flipped = np.flip(Z_data_inside, axis=0)
        else:
            Z_data_flipped = np.flip(Raw_Z, axis=0)

        # Show the plot window and results window
        self.plot_window = PlotWindow(self, self.parent.Raw_x, self.parent.Raw_y, 
                                    Z_data_flipped, Z_fit_flipped,
                                    popt, perr, self.function_name, FITTINGPARAMETERS)
        self.plot_window.show()
        filtered_params = [p for p in FITTINGPARAMETERS if p != "N"]
        
        if self.function_name == "Gaussian": # No idea why, but this is necessary
            popt[FITTINGPARAMETERS.index('µ_y')] = max(self.parent.Raw_y) - popt[FITTINGPARAMETERS.index('µ_y')]
        
        self.results_window = ResultsWindow(self, popt=popt, perr=perr, func_name=self.function_name, param_names=filtered_params)
        self.results_window.show()
        self.close()

    def on_fit_error(self, error): # Handle fitting errors
        self.hide_loading_overlay()
        self.scroll_area.setEnabled(True)
        helpers.error_message(f"Fitting error: {str(error)}")

"""Function called from set_fitting_params function."""
def init_interface(parent=None, parameters=None, function_name="Parameter Selection"):
    try:
        w = ParameterSelectionWindow(parent, parameters, function_name)
        w.show()
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()

"""Fit_handling.create_param_widget - Used when fitting functions"""
def create_param_widget(param, parent=None):
    label = QLabel(f"{param} =")
    label.setObjectName("param_label")
    line_edit = QLineEdit()
    line_edit.setObjectName("param_edit")
    helpers.setStyleSheet_from_file(line_edit, parent.parent.current_dir + "/GUI/stylesheet.qss")
    if "λ" in param: # Wavelengths
        line_edit.setPlaceholderText("0.25")
    elif any(i in param for i in ["A", "σ"]) or param == "b": # Amplitudes, sigmas, b
        line_edit.setPlaceholderText("1.0")
    elif "N" in param: # Number of components
        line_edit.setPlaceholderText("1")
        line_edit.setText("1")
    else: # Default
        line_edit.setPlaceholderText("0")

    if param == "N": # Add signal for N
        def n_changed(text):
            parent.modify_fitting_parameters(text)
            parent.update_bitmap()
        line_edit.setValidator(QIntValidator(1, 1000))
        line_edit.textChanged.connect(n_changed if parent else lambda: None)
    else:
        line_edit.textChanged.connect(parent.update_bitmap if parent else lambda: None)
    return label, line_edit

"""Fit_handling.add_parameter_widgets - Used when fitting functions"""
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
        label, line_edit = create_param_widget(param, self)
        self.param_edits[param] = line_edit
        self.scroll_layout.addWidget(label, i + 1, 0)
        self.scroll_layout.addWidget(line_edit, i + 1, 1)
        self.scroll_layout.setRowMinimumHeight(i + 1, 30)
    
    helpers.setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")
    # Adjust apply button position
    apply_button = QPushButton("Apply")
    apply_button.clicked.connect(self.on_apply)
    apply_button.setObjectName("main_button")
    self.scroll_layout.addWidget(apply_button, len(self.parameters) + 1, 0, 1, 2)

"""Fit_handling.on_apply - Used when fitting functions"""
def on_apply(self):
        if hasattr(self, 'plot_window') and self.plot_window is not None:
            self.plot_window.close()
            self.plot_window = None

        # Disable UI during fitting
        self.scroll_area.setEnabled(False)
        self.show_loading_overlay()

        # Prepare parameters for worker
        inside_image = getattr(self.parent, 'inside_image', None)
        params = {
            'parent': self.parent,
            'param_edits': self.param_edits,
            'FITTINGPARAMETERS': FITTINGPARAMETERS,
            'function_name': self.function_name
        }

        # Setup thread and worker
        self.fit_thread = QThread()
        self.fit_worker = FitWorker(self, inside_image, params)
        self.fit_worker.moveToThread(self.fit_thread)
        
        # Connect signals
        self.fit_thread.started.connect(self.fit_worker.run)
        self.fit_worker.finished.connect(self.on_fit_complete)
        self.fit_worker.error.connect(self.on_fit_error)
        self.fit_worker.finished.connect(self.fit_thread.quit)
        self.fit_worker.error.connect(self.fit_thread.quit)
        
        self.fit_thread.start()