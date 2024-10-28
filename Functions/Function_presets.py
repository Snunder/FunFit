import numpy as np
import matplotlib as mpl
import math
import re
import Functions.functionoffset_input as foi
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
import os

def mathTex_to_QPixmap(mathTex, fs):

    mathTex = mathTex.replace('^', '\\text{\\^}')
    mathTex = mathTex.replace('*', '\\cdot{}')

    #---- set up a mpl figure instance ----

    fig = mpl.figure.Figure()
    fig.patch.set_facecolor('none')
    fig.set_canvas(FigureCanvasAgg(fig))
    renderer = fig.canvas.get_renderer()

    #---- plot the mathTex expression ----

    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.patch.set_facecolor('none')
    t = ax.text(0, 0, mathTex, ha='left', va='bottom', fontsize=fs, color='white')

    #---- fit figure size to text artist ----

    fwidth, fheight = fig.get_size_inches()
    fig_bbox = fig.get_window_extent(renderer)

    text_bbox = t.get_window_extent(renderer)

    tight_fwidth = text_bbox.width * fwidth / fig_bbox.width
    tight_fheight = text_bbox.height * fheight / fig_bbox.height

    fig.set_size_inches(tight_fwidth, tight_fheight)

    #---- convert mpl figure to QPixmap ----

    buf, size = fig.canvas.print_to_buffer()
    qimage = QtGui.QImage.rgbSwapped(QtGui.QImage(buf, size[0], size[1],
                                                  QtGui.QImage.Format.Format_ARGB32))
    qpixmap = QtGui.QPixmap(qimage)

    return qpixmap

class InputDialog_QC(QWidget):
    def __init__(self, text=''):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setContentsMargins(0, 0, 0, 0)

        with open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r') as f:
            self.setStyleSheet(f.read())

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # Custom title bar
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setStyleSheet("background-color: #19172D;")
        self.title_bar.setFixedHeight(30)
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("Select initial guess parameters", self.title_bar)
        self.title_label.setStyleSheet("margin-left: 10px; color: white; font-size: 16px; font-family: Verdana;")
        self.title_bar_layout.addWidget(self.title_label)
        self.title_bar_layout.addStretch()

        self.close_button = QPushButton("", self.title_bar)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
            background-color: #19172D; 
            color: white; 
            border-radius: 0px;
            border: none;
            font-weight: normal;
            font-size: 30px; 
            margin: -10px;
            padding: 0px; 
            text-align: center;
            qproperty-iconSize: 20px;}
            QPushButton:hover {
            background-color: #FF3B3B;}
            QPushButton:pressed {
            background-color: #FF1C1C;}
        """)
        self.close_button.setIcon(QIcon("GUI/icon_close.png"))
        self.close_button.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.close_button)

        layout.addWidget(self.title_bar)
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #4B4587;")
        layout.addWidget(separator)

        # Main content
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
        self.content.setLayout(self.content_layout)
        layout.addWidget(self.content)

        self.label = QLabel()
        pixmap = QPixmap(os.getcwd()+'/GUI/quasicrystaleq.png').scaled(550, 400, Qt.AspectRatioMode.KeepAspectRatio)
        self.label.setPixmap(pixmap)
        self.content_layout.addWidget(self.label)

        verticalbox = QHBoxLayout()
        self.label = QLabel()
        self.label.setPixmap(mathTex_to_QPixmap(r'  Enter number of sines ($N$):', 16))
        verticalbox.addWidget(self.label)
        self.N_terms = QLineEdit(self)
        self.N_terms.setFixedSize(200, 40)
        self.N_terms.setPlaceholderText('1')
        self.N_terms.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.N_terms)
        layout.addLayout(verticalbox)
        
        verticalbox = QHBoxLayout()
        self.label = QLabel()
        self.label.setPixmap(mathTex_to_QPixmap(r'  Enter amplitude ($A$) [nm]:', 16))
        verticalbox.addWidget(self.label)
        self.A = QLineEdit(self)
        self.A.setFixedSize(200, 40)
        self.A.setPlaceholderText('10')
        self.A.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.A)
        layout.addLayout(verticalbox)
        
        verticalbox = QHBoxLayout()
        self.label = QLabel()
        self.label.setPixmap(mathTex_to_QPixmap(r'  Enter wavelength ($\lambda$) [µm]:', 16))
        verticalbox.addWidget(self.label)
        self.lbd = QLineEdit(self)
        self.lbd.setFixedSize(200, 40)
        self.lbd.setPlaceholderText('1')
        self.lbd.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.lbd)
        layout.addLayout(verticalbox)
        
        verticalbox = QHBoxLayout()
        self.label = QLabel()
        self.label.setPixmap(mathTex_to_QPixmap(r'  Enter phaseshift ($\varphi$):', 16))
        verticalbox.addWidget(self.label)
        self.phi = QLineEdit(self)
        self.phi.setFixedSize(200, 40)
        self.phi.setPlaceholderText('0')
        self.phi.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.phi)
        layout.addLayout(verticalbox)
        
        verticalbox = QHBoxLayout()
        self.label = QLabel()
        self.label.setPixmap(mathTex_to_QPixmap(r'  Enter angle ($\delta\theta$) [deg]:', 16))
        verticalbox.addWidget(self.label)
        self.theta = QLineEdit(self)
        self.theta.setFixedSize(200, 40)
        self.theta.setPlaceholderText('0')
        self.theta.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.theta)
        layout.addLayout(verticalbox)
        
        self.button = QPushButton('Submit', self)
        self.button.clicked.connect(self.on_submit)
        layout.addWidget(self.button)
        self.button.setStyleSheet('margin-bottom: 10px;')

        self.setLayout(layout)

                # Enable dragging the window on the titlebar
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.dragPos = event.globalPosition().toPoint()
        
        def mouseMoveEvent(event):
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
                self.dragPos = event.globalPosition().toPoint()
                event.accept()
        
        self.title_bar.mousePressEvent = mousePressEvent
        self.title_bar.mouseMoveEvent = mouseMoveEvent

    def on_submit(self):
        # user_input = self.text_input.text()
        self.close()

class InputDialog_Custom(QWidget):
    def __init__(self, text=''):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle('Input Dialog')
        with(open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r')) as f:
            self.setStyleSheet(f.read())
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        #self.setStyleSheet("background-color: #302D58;")
        layout.setSpacing(0)
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setStyleSheet("background-color: #19172D;")
        self.title_bar.setFixedHeight(30)
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("Input Dialog", self.title_bar)
        self.title_label.setStyleSheet("margin-left: 10px; color: white; font-size: 16px; font-family: Verdana;")
        self.title_bar_layout.addWidget(self.title_label)
        self.title_bar_layout.addStretch()
        self.close_button = QPushButton("", self.title_bar)
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
            background-color: #19172D; 
            color: white; 
            border-radius: 0px;
            border: none;
            font-weight: normal;
            font-size: 30px; 
            margin: -10px;
            padding: 0px; 
            text-align: center;
            qproperty-iconSize: 20px;}
            QPushButton:hover {
            background-color: #FF3B3B;}
            QPushButton:pressed {
            background-color: #FF1C1C;}
        """)
        self.close_button.setIcon(QIcon("GUI/icon_close.png"))
        self.close_button.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.close_button)
        layout.addWidget(self.title_bar)
        self.separator = QWidget()
        self.separator.setFixedHeight(2)
        self.separator.setStyleSheet("background-color: #4B4587;")
        layout.addWidget(self.separator)
        self.label = QLabel()
        self.label.setPixmap(mathTex_to_QPixmap(r'$  f\,(x, y) = $', 16))
        layout.addWidget(self.label)
        self.text_input = QLineEdit(self)
        self.text_input.setFixedSize(200, 40)
        self.text_input.setPlaceholderText('Enter function here')
        self.text_input.textEdited.connect(self.on_text_edited)
        self.text_input.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px;')
        layout.addWidget(self.text_input)

        self.button = QPushButton('Submit', self)
        self.button.clicked.connect(self.on_submit)
        layout.addWidget(self.button)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.title_bar.underMouse():
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
        
            

        

    def on_text_edited(self):
        tex_str = self.text_input.text()
        tex_str = tex_str.replace('\\', '')
        # If a number is entered without a parenthesis, *, +, -, or /, on the left side, add a multiplication sign on the left side if the number is not at the beginning of the string
        tex_str = re.sub(r'(?<![\(\+\-\*\^/\d])\d+', r'*\g<0>', tex_str)
        # If a number is entered without a parenthesis, *, +, -, or /, add a multiplication sign on the right side if the number is not at the end of the string
        tex_str = re.sub(r'\d+(?![\)\+\-\*\^/\d])', r'\g<0>*', tex_str)
        # If * is at the beginning or end of the string, remove it
        tex_str = re.sub(r'^\*', '', tex_str)
        tex_str = re.sub(r'\*$', '', tex_str)

        self.label.setPixmap(mathTex_to_QPixmap(fr'$f(x, y) = {tex_str}$', 12))
        param_names = extract_parameters(tex_str)

        try:
            missing_params = [param for param in self.old_param_names if param not in param_names]
            idx = np.where(np.array(self.old_param_names) == missing_params[0])[0][0]
            self.user_input_IC.pop(idx)
        except:
            pass

        try:
            self.user_input_IC[0] = 0
        except:
            self.user_input_IC = [0] * len(param_names)

        self.old_param_names = param_names

        if len(self.user_input_IC) > len(param_names):
            # self.user_input_IC = self.user_input_IC[:len(param_names)]
            pass
        else:
            self.user_input_IC += [0] * (len(param_names) - len(self.user_input_IC))

        if self.layout().count() > 5:
            for i in range(5, self.layout().count()):
                self.layout().itemAt(i).widget().deleteLater()

        for i, param in enumerate(param_names[2:], start=2):
            self.param = QLabel(f"{param}:")
            self.param.setStyleSheet("font-size: 16px; color: white;")
            self.layout().addWidget(self.param)
            self.i = QLineEdit(self)
            self.i.setFixedSize(200, 40)
            self.i.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px;')
            self.i.setText(str(self.user_input_IC[i]))
            self.i.textEdited.connect(
            lambda text, i=i: self.update_IC(text, i)
            )
            self.layout().addWidget(self.i)

    def update_IC(self, text, i):
        self.user_input_IC[i] = text

    def on_submit(self):
        # user_input = self.text_input.text()
        self.close()

def get_user_input(text=''):
    app = QApplication([])
    dialog = InputDialog_QC(text)
    dialog.show()
    app.exec()
    return dialog.text_input.text()

# Functions for handling custom fitting
def preprocess_function_string(func_str):
    """
    Preprocess the function string to replace common mathematical functions with their NumPy equivalents
    and replace ^ with ** for exponentiation.

    Parameters:
    func_str (str): String representation of the mathematical function.

    Returns:
    str: Preprocessed function string.
    """
    replacements = {
        'cos': 'np.cos',
        'sin': 'np.sin',
        'tan': 'np.tan',
        'exp': 'np.exp',
        'log': 'np.log',
        'sqrt': 'np.sqrt',
        'abs': 'np.abs',
        'pi': 'np.pi',
        '^': '**',
    }
    for old, new in replacements.items():
        # Only replace if the function name is not already prefixed with 'np.'
        func_str = func_str.replace(old, new) if f'np.{old}' not in func_str else func_str
    # Remove all spaces
    func_str = func_str.replace(" ", '')
    # Replace x and y with (x-x0) and (y-y0) to allow for translation
    func_str = re.sub(r'(?<!\w)x(?!\w)', "(x-x0)", func_str)
    func_str = re.sub(r'(?<!\w)y(?!\w)', "(y-y0)", func_str)
    # Remove any incompatible sign at the beginning of the expression
    while func_str and func_str[0] in '*/^':
        func_str = func_str[1:]
    return func_str

def create_fitting_function(func_str, param_names):
    """
    Create a fitting function from a string representation of a mathematical function.

    Parameters:
    func_str (str): String representation of the mathematical function.
    param_names (list): List of parameter names.

    Returns:
    function: Fitting function.
    """
    # Preprocess the function string
    func_str = preprocess_function_string(func_str)

    def fitting_function(XY, *params):
        x, y = XY
        # Create a dictionary of parameter values
        param_dict = {param_names[i]: params[i] for i in range(len(params))}
        
        # Create a lambda function to evaluate the function string
        func_lambda = eval(f"lambda x, y, {', '.join(param_names)}: {func_str}", {"np": np, "math": math})
        
        # Call the lambda function with the parameters
        return func_lambda(x, y, *params)
    return fitting_function

def extract_parameters(func_str):
    """
    Extract the parameter names from the function string.

    Parameters:
    func_str (str): String representation of the mathematical function.

    Returns:
    list: List of parameter names.
    """
    known_functions = {'x', 'y', 'np', 'math', 'cos', 'sin', 'tan', 'exp', 'log', 'sqrt', 'abs', 'pi'} # Should not be treated as parameters
    all_identifiers = set(re.findall(r'\b[A-Za-z_]\w*\b', func_str))
    all_identifiers.update(['x0', 'y0'])
    param_names = list(all_identifiers - known_functions)

    # Sort param_names based on their first occurrence in func_str
    param_positions = {} # Create a dictionary to store the first position of each parameter
    for param in param_names:
        # Use regex to find the position of the parameter as a whole word
        match = re.search(rf'\b{re.escape(param)}\b', func_str)
        if match:
            param_positions[param] = match.start()
    param_names = sorted(param_names, key=lambda param: param_positions.get(param, float('inf')))
    if 'x0' in param_names:
        param_names.remove('x0')
        param_names.insert(0, 'x0')
    
    if 'y0' in param_names:
        param_names.remove('y0')
        param_names.insert(1, 'y0')

    # Swap the first two values after sorting
    if param_names[0] == 'y0':
        param_names[0], param_names[1] = param_names[1], param_names[0]
    return param_names

def is_periodic_function(func_str): # This code is sensitive to quasicrystals above 3 terms, but we have another function for that
    # Remove spaces from the function string
    func_str = func_str.replace(" ", "")
    
    # Check if x or y is raised to a power other than 1 anywhere in the function string
    if re.search(r'[xy]\*\*\d+', func_str):
        return False
    
    # Check if x or y appears outside sin/cos or within functions like exp, log, etc.
    outside_trig_pattern = r'(?<!sin|cos)\([^\)]*([xy])[^\)]*\)'
    if re.search(outside_trig_pattern, func_str):
        return False
    
    # Look for variables outside parentheses of sin/cos
    linear_term_pattern = r'([+-/*=]\s*[xy](?![^\(]*[)])|\b[xy]\b(?![^\(]*\)))'
    if re.search(linear_term_pattern, func_str):
        return False
    return True

# Fitting models start here
def custom():
    """
    Create a custom fitting function based on user input.
    """
    # THIS IS USER INPUT FOR GUI LATER
    # Prompt the user to input the function string
    func_str = input("Enter the function string: ")
    # Extract parameter names
    param_names = extract_parameters(func_str)
    # Create the fitting function
    fitting_model = create_fitting_function(func_str, param_names)

    # Initial guess for the parameters
    IC = [0] * len(param_names)
    Bounds = ([-np.inf] * len(param_names), [np.inf] * len(param_names))
    # THIS IS USER INPUT
    # Initial guess for x0 and y0 (no offset), this will be determined from the user input (clicking on the plot)

    # This function detects if the custom function is non-periodic
    def is_non_periodic(term):
        """
        Determine if a term is non-periodic.

        Parameters:
        term (str): The term to check.

        Returns:
        bool: True if the term is non-periodic, False otherwise.
        """
        # Check if the term contains sine or cosine
        if re.search(r'np\.sin|np\.cos', term):
            # Ensure x and y are only to the power of 1 within sine and cosine
            if re.search(r'np\.(sin|cos)\((x|y)(?![\*\^])', term):
                return False
            else:
                return True
        # Allow all constant terms that are not multiplied with x or y
        elif re.search(r'\b(x|y)\b', term):
            # Check if x or y is part of a polynomial term like x^2 or y^2
            if re.search(r'\b(x\^2|y\^2)\b', term):
                return True
            return False
        else:
            return True

    # Split the function string into terms and check if all terms are non-periodic
    terms = re.split(r'[+\-*/()]', func_str)
    non_periodic = all(is_non_periodic(term) for term in terms if term)
    # If the function is non-periodic, the user should select a fitting offset for the function
    if non_periodic:
        [x0, y0, offset] = foi.main()
    # If the function is periodic, the offset can be produced by a phase shift
    else:
        x0 = 0
        y0 = 0
    # Set ICs
    IC[0] = x0
    IC[1] = y0

    # THIS IS USER INPUT FOR GUI
    # Prompt the user for initial guesses for the parameters, skipping the first two terms (x0 and y0)
    for i, param in enumerate(param_names[2:], start=2):
        user_input = input(f"Enter initial guess for parameter '{param}': ")
        # Replace 'pi' with 'np.pi' if entered by the user, but not if 'np.pi' is already present
        if 'np.pi' not in user_input:
            user_input = user_input.replace('pi', 'np.pi')
        try:
            IC[i] = eval(user_input, {"np": np, "math": math})
        except Exception as e:
            print(f"Invalid input for parameter '{param}': {e}")
            IC[i] = 0  # Default to 0 if the input is invalid
    return fitting_model, IC, Bounds

def quasicrystal(N_terms=None, param_names=None, IC=None):
    """
    Create a quasicrystal fitting function based on user input.
    """
    if N_terms is None:
        N_terms = int(input("Enter the number of terms in the Fourier series: "))
    
    # User input for the quasicrystal function
    if param_names is None:
        param_names = ['x0', 'y0', 'amplitude', 'wavelength', 'phase_shift', 'angle', 'offset']
    
    if IC is None:
        IC = [0] * len(param_names)
        
        for i, param in enumerate(param_names[2:6], start=2):
            user_input = input(f"Enter initial guess for parameter '{param}': ")
            # user_input = get_user_input(f"Enter initial guess for parameter '{param}': ")
            try:
                IC[i] = eval(user_input, {"np": np, "math": math})
            except Exception as e:
                print(f"Invalid input for parameter '{param}': {e}")
                IC[i] = 0  # Default to 0 if the input is invalid
        
        
        if N_terms >= 4:
            print("bug")
            [x0,y0,offset] = foi.main()
            IC[0] = x0
            IC[1] = y0
        else:
            IC[0] = 0
            IC[1] = 0

    # Bounds on x0 and y0, other parameters are free
    Bounds = ([IC[0] - abs(IC[3]/2), IC[1] - abs(IC[3]/2), -np.inf, -np.inf, -np.inf, -np.inf, -np.inf],[IC[0] + abs(IC[3]/2), IC[1] + abs(IC[3]/2), np.inf, np.inf, np.inf, np.inf, np.inf])

    # its 3am and this is what you get, it works ok?
    def fitting_function(XY, *params):
        x, y = XY
        x0, y0, amplitude, wavelength, phase_shift, angle, offset = params
        result = 0
        for i in range(N_terms):
            theta_i = np.deg2rad(angle + i * 360 / (2 * N_terms))
            result += np.cos(2 * np.pi / wavelength * ((x - x0) * np.cos(theta_i) + (y - y0) * np.sin(theta_i)) + phase_shift)
        return amplitude / N_terms * result + offset
    return fitting_function, IC, Bounds