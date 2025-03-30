"""Built-in modules"""
import ast
import re
from io import BytesIO

"""External modules"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton

"""Internal modules"""
try:
    from FunFit.Functions import helpers
except:
    from Functions import helpers

class CustomFunctionWindow(QMainWindow):
    """Window for defining a custom function."""
    accepted = pyqtSignal(object, list, str, str) # Emits (model_func, parameters, func_str)
    
    # Library of math functions
    math_functions_mapping = {
        'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
        'arcsin': np.arcsin, 'arccos': np.arccos, 'arctan': np.arctan,
        'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
        'exp': np.exp, 'log': np.log, 'log10': np.log10, 'sqrt': np.sqrt,
        'abs': np.abs, 'floor': np.floor, 'ceil': np.ceil, 'trunc': np.trunc,
        'degrees': np.degrees, 'radians': np.radians, 'deg2rad': np.deg2rad,
        'rad2deg': np.rad2deg, 'mod': np.mod, 'power': np.power, 'arctan2': np.arctan2,
        'expm1': np.expm1, 'log1p': np.log1p, 'log2': np.log2, 'sinc': np.sinc,
        'pi': np.pi, 'e': np.e
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        with open(self.parent.current_dir + "/GUI/stylesheet.qss", "r") as f:
            style = f.read()
        style += """* { color: white; } """
        self.setStyleSheet(style)
        self.init_ui()

    def init_ui(self): # Set up the UI
        # Set window properties
        self.setWindowTitle("Custom Function")
        self.setGeometry(self.parent.geometry().x(), self.parent.geometry().y(), 500, 400)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        # Create the main layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setContentsMargins(0, 0, 0, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        title_bar = helpers.create_title_bar(self, "Custom Function", "child")
        layout.addWidget(title_bar)
        
        # Function input box
        self.function_edit = QTextEdit()
        self.function_edit.setStyleSheet("border: 2px solid purple; margin: 10px; background-color: #242424;")
        self.function_edit.setPlaceholderText("Example: A*x^2 + B*sin(2*pi/\lambda*y*x + \phi) + C")
        self.function_edit.textChanged.connect(self.update_parameters_display)
        label1 = QLabel("Enter your function (use x and y variables):")
        label1.setStyleSheet("margin-left: 10px;")
        layout.addWidget(label1)
        layout.addWidget(self.function_edit)

        # Equation preview
        self.equation_preview = QLabel()
        self.equation_preview.setFixedHeight(50)
        label2 = QLabel("Equation Preview:")
        label2.setStyleSheet("margin-left: 10px;")
        layout.addWidget(label2)
        layout.addWidget(self.equation_preview)

        # Parameters display
        self.params_label = QLabel("Detected Parameters: None")
        self.params_label.setStyleSheet("margin-left: 10px;")
        layout.addWidget(self.params_label)
        
        # Error display
        self.equation_error = QLabel()
        layout.addWidget(self.equation_error)
        
        # Buttons
        button_box = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setObjectName("main_button")
        self.apply_btn.clicked.connect(self.validate_and_apply)
        self.apply_btn.setEnabled(False)
        button_box.addWidget(self.apply_btn)
        button_box.setContentsMargins(0, 0, 0, 10)        
        
        layout.addLayout(button_box)
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Timer for input delay
        self.input_timer = QTimer(self)
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(self.delayed_update_parameters_display)

    def replace_greek_letters(self, expr: str) -> str: # Replace Greek letters with their Unicode equivalent
        # First convert LaTeX-like sequences (\phi, \theta, etc.) to normal text
        latex_map = {
            r'\\alpha': 'α',
            r'\\beta': 'β',
            r'\\gamma': 'γ',
            r'\\delta': 'δ',
            r'\\theta': 'θ',
            r'\\phi': 'φ',
            r'\\mu': 'µ',
            r'\\sigma': 'σ',
            r'\\omega': 'ω',
            r'\\lambda': 'λ'
        }
        for pattern, replacement in latex_map.items():
            expr = re.sub(pattern, replacement, expr, flags=re.IGNORECASE)
        return expr

    def update_parameters_display(self): # Update the parameters display
        expr = self.function_edit.toPlainText().strip()
        self.equation_error.clear()
        self.equation_preview.clear()

        # Immediately update LaTeX preview
        self.update_latex_preview(expr=expr)

        # Delayed update of parameters display
        self.input_timer.stop()
        try:
            if re.search(r'[+\-*/^]$', expr):
                raise ValueError("Expression cannot end with an operator")
            if re.search(r'^[+\-*/^]', expr):
                raise ValueError("Expression cannot start with an operator")
            if expr.count('(') != expr.count(')'):
                raise ValueError("Unmatched parentheses")
            if re.search(r'\blambda\b', expr) and not re.search(r'\\lambda\b', expr):
                raise ValueError("'lambda' is a reserved keyword in Python, use '\\lambda' instead.")
            if not re.match(r'^[a-zA-Z0-9_+\-*/^()., \\\[\]α-ωΑ-Ωµ]*$', expr):
                raise ValueError("Expression contains invalid characters or unsupported operators")

            expr = self.replace_greek_letters(expr)
            self.expr_with_greek = expr
            expr_ast = expr.replace('^', '**')
            tree = ast.parse(expr_ast, mode='eval')
            allowed_names = {'x','y','np'}.union(self.math_functions_mapping.keys())
            parameters = sorted({
                node.id for node in ast.walk(tree)
                if isinstance(node, ast.Name) and node.id not in allowed_names
            })
            valid = re.compile(r'^[a-zA-Z_α-ωΑ-Ωµ]+\w*$')
            for p in parameters:
                if p == "lambda":
                    raise ValueError("Cannot use 'lambda' as a parameter name, it is a Python reserved keyword.")
                if not valid.match(p):
                    raise ValueError(f"Invalid parameter name: '{p}'")
            self.parameters = parameters
            params_text = ', '.join(parameters) if parameters else 'None'
            self.params_label.setText(f"Detected Parameters: {params_text}")
            self.apply_btn.setEnabled(bool(parameters))
            self._last_error = None
        except Exception as e:
            self._last_error = str(e)
            self.params_label.setText("Detected Parameters: None")
            self.apply_btn.setEnabled(False)
            self.input_timer.start(800)

    def delayed_update_parameters_display(self): # Display an error message
        if getattr(self, '_last_error', None):
            self.params_label.setText(f"<span style='color:red'>Invalid input: {self._last_error}</span>")
            self._last_error = None

    def convert_to_latex(self, expr):  # Convert the expression to LaTeX
        # Replace exponentiation operators with ^
        expr = re.sub(r'\*\*|\^', '^', expr)
        # Replace * with space
        expr = expr.replace('*', ' ')
        # Replace functions with their LaTeX equivalents
        funcs = list(self.math_functions_mapping.keys())
        funcs.remove('pi')
        funcs.remove('e')
        for func in funcs:
            # Don't replace if already .np
            expr = re.sub(rf'(?<!np\.)\b{func}\s*(?=\()', rf'\\{func}', expr)
        # Replace constants
        expr = re.sub(r'\bpi\b', r'\\pi', expr)
        expr = re.sub(r'\be\b', r'e', expr)
        # Clean up extra spaces
        expr = re.sub(r'\s+', ' ', expr).strip()

        # Define valid terms with support for 1-level nested parentheses in function arguments
        valid_term = r'''(?:[0-9.]*\\(?:[a-zA-Z_α-ωΑ-Ωµ]+)\([^()]*(?:\([^()]*\)[^()]*)*\)''' + \
                    r'''|[0-9.]*\\?[a-zA-Z_α-ωΑ-Ωµ]+''' + \
                    r'''|[0-9.]+)'''

        # Parenthesized denominator: Match "valid_term / (...)" with nested parentheses
        pattern_paren_denom = re.compile(
            rf'({valid_term})\s*/\s*\(((?:[^()]|\([^()]*\))*)\)'
        )
        while True:
            new_expr = pattern_paren_denom.sub(r'\\frac{\1}{\2}', expr, 1)
            if new_expr == expr:
                break
            expr = new_expr

        # Parenthesized numerator: Match "(...) / valid_term" with nested parentheses
        pattern_paren = re.compile(
            rf'\(((?:[^()]|\([^()]*\))*)\)\s*/\s*({valid_term})'
        )
        while True:
            new_expr = pattern_paren.sub(r'\\frac{\1}{\2}', expr, 1)
            if new_expr == expr:
                break
            expr = new_expr

        # Non-parenthesized fractions: Match "valid_term / valid_term"
        pattern = re.compile(rf'({valid_term})\s*/\s*({valid_term})')
        while True:
            new_expr = pattern.sub(r'\\frac{\1}{\2}', expr, 1)
            if new_expr == expr:
                break
            expr = new_expr

        return f'${expr}$' if expr else '$ $'

    def update_latex_preview(self, expr=None): # Update the LaTeX preview
        self.equation_error.clear()
        if expr is None:
            expr = self.function_edit.toPlainText().strip()
        expr = self.replace_greek_letters(expr)
        if not expr:
            self.equation_preview.clear()
            return

        try:
            latex_str = self.convert_to_latex(expr)
            fig = Figure(figsize=(4, 1.5), facecolor='none')
            fig.set_alpha(0.0)
            canvas = FigureCanvasQTAgg(fig)
            ax = fig.add_subplot(111)
            ax.axis('off')
            ax.text(0.05, 0.5, latex_str, ha='left', va='center', fontsize=14, color='white', usetex=False)

            buf = BytesIO()
            fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.equation_preview.setPixmap(pixmap)
        except Exception as e:
            self.equation_preview.clear()
            self.equation_error.setText(f"Equation error: {str(e)}")

    def validate_and_apply(self): # Validate the function and apply it
        try:
            if not hasattr(self, 'expr_with_greek'):
                raise ValueError("Function cannot be empty")

            # Use the expression with Greek letters already replaced
            func_str = self.expr_with_greek
            if not func_str:
                raise ValueError("Function cannot be empty")

            raw_expr = func_str
            latex_str = self.convert_to_latex(raw_expr)
            func_str = func_str.replace('^', '**')

            def model_func(X, *args):
                x, y = X
                local_params = dict(zip(self.parameters, args))
                local_namespace = {'x': x, 'y': y, 'np': np}
                local_namespace.update(self.math_functions_mapping)
                local_namespace.update(local_params)
                return eval(func_str, local_namespace)

            # Test evaluation
            x = y = 1.0
            namespace = {'np': np, 'x': x, 'y': y}
            namespace.update(self.math_functions_mapping)
            test_params = {p: 1.0 for p in self.parameters}
            result = eval(func_str, namespace, test_params)
            if not isinstance(result, (int, float, np.ndarray, np.generic)):
                raise ValueError("Function must return numeric value")

            self.accepted.emit(model_func, self.parameters, raw_expr, latex_str)
            self.close()
        except Exception as e:
            self.equation_error.setText(f"Error: {str(e)}")
            self.params_label.setText("Detected Parameters: None")
            self.apply_btn.setEnabled(False)