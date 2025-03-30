"""External modules"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout, QGridLayout, QPushButton

"""Internal modules"""
try:
    from FunFit.Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file
except:
    from Functions.helpers import display_data, create_title_bar, setStyleSheet_from_file

"""Constants"""
POINT_COLOR = '#3B2070'
PLANE_COLOR = '#686868'
DATA_INTERVAL = 80

class PlaneLevelingWindow(QMainWindow):
    """Window to fit a plane and subtract it to level data."""
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        if hasattr(parent, "outside_image"):
            self.outside_image = np.copy(parent.outside_image)
            if hasattr(parent, "corrected_data"):
                idx = np.where(np.isfinite(self.outside_image))
                self.outside_image[idx] = parent.corrected_data[idx]
        if hasattr(parent, "corrected_data"):
            self.Raw_Z = np.copy(parent.corrected_data)
        else:
            self.Raw_Z = np.copy(parent.Raw_Z)
        self.original_Raw_Z = np.copy(parent.Raw_Z)  # Preserve the original raw data
        self.x_scale, self.y_scale = parent.x_scale, parent.y_scale
        setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")
        self.init_ui(parent)

    def init_ui(self, parent): # Set up the PlaneLevelingWindow UI
        # Set window properties
        self.setWindowTitle("Line Correction")
        self.setGeometry(parent.geometry().x(), parent.geometry().y(), parent.img_scale, parent.img_scale)  # Adjust the window dimensions
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Create the main layout
        main_widget = QWidget(self)
        layout = QGridLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(main_widget)

        # Add title bar at the top
        title_bar = create_title_bar(self, f'Plane leveling (1/{DATA_INTERVAL} data points shown)', "child")
        layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)

        # Populate the window with the fit plane and the apply button
        image_widget = self.display_fit_plane()
        layout.addWidget(image_widget, 1, 1, 1, 1, Qt.AlignmentFlag.AlignCenter)
        apply_button_widget = self.add_apply_button(layout)
        layout.addWidget(apply_button_widget, 2, 1, 1, 1, Qt.AlignmentFlag.AlignCenter)

        self.show()

    def add_apply_button(self, layout): # Add the apply button to the window
        apply_button_widget = QWidget()
        apply_button_layout = QVBoxLayout(apply_button_widget)
        apply_button_layout.setContentsMargins(0, 0, 0, 0)
        apply_button_layout.setSpacing(15)

        apply_button = QPushButton("Apply Correction")
        apply_button.setObjectName("main_button")
        apply_button.clicked.connect(self.apply_correction)
        apply_button_layout.addWidget(apply_button, 0, Qt.AlignmentFlag.AlignCenter)

        return apply_button_widget

    def apply_correction(self): # Apply the correction to the data in the main window
        self.parent.corrected_data = self.parent.leveled_data
        self.Raw_Z = self.parent.leveled_data
        image = display_data(self)
        self.parent.image.setPixmap(image.pixmap())
        self.close()

    def display_fit_plane(self): # Display the fit plane on the image
        if hasattr(self, 'outside_image'):
            Z = self.outside_image
        else:
            Z = self.Raw_Z
        # Use scaled coordinates for the x and y axes
        X_vals, Y_vals = np.linspace(0, self.x_scale, Z.shape[1]), np.linspace(0, self.y_scale, Z.shape[0])
        X, Y = np.meshgrid(X_vals, Y_vals)

        # Fit a plane to the data
        XX, YY, ZZ = X[np.isfinite(Z)], Y[np.isfinite(Z)], Z[np.isfinite(Z)]
        A = np.c_[XX.ravel(), YY.ravel(), np.ones(XX.size)]
        C, _, _, _ = np.linalg.lstsq(A, ZZ.ravel(), rcond=None)
        plane = (C[0] * X + C[1] * Y + C[2]).reshape(Z.shape)

        # Subtract the plane from the original data
        self.parent.leveled_data = self.Raw_Z - plane
        data = np.vstack((X[0::1].flatten(), Y[0::1].flatten(), Z[0::1].flatten())).T
        X_data = np.vstack([X[0::1].flatten(), Y[0::1].flatten()]).T

        plt.rcParams.update({
                            'font.size': 14,
                            'figure.facecolor': 'white',
                            'figure.edgecolor': 'black',
                            'axes.facecolor': 'white',
                            'axes.edgecolor': 'black',
                            'axes.labelcolor': 'black',
                            'xtick.color': 'black',
                            'ytick.color': 'black',
                            'text.color': 'black',
                            'axes.titlesize': 16,
                            'xtick.labelsize': 14,
                            'ytick.labelsize': 14,
                            })

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot a subset of original data points
        ax.scatter(data[0::DATA_INTERVAL, 0], data[0::DATA_INTERVAL, 1], data[0::DATA_INTERVAL, 2], color=POINT_COLOR, label='Data Points')

        # Create a coarser grid for plotting the plane
        x_range = np.linspace(X_data[:, 0].flatten().min(), X_data[:, 0].flatten().max(), 10)
        y_range = np.linspace(X_data[:, 1].flatten().min(), X_data[:, 1].flatten().max(), 10)
        x_grid, y_grid = np.meshgrid(x_range, y_range)
        z_grid = C[0] * x_grid + C[1] * y_grid + C[2]

        # Plot the fitted plane
        ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.5, color=PLANE_COLOR, label='Fitted Plane')

        ax.set_xlabel('X (µm)')
        ax.set_ylabel('Y (µm)')
        ax.set_zlabel('Z (nm)')
        ax.legend()

        # Create a canvas to display the figure
        canvas = FigureCanvas(fig)
        canvas.draw()

        # Create a widget to hold the canvas
        self.image = QWidget()
        layout = QVBoxLayout(self.image)
        layout.addWidget(canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Display the corrected data
        return self.image

"""Function called from main window."""
def fit_and_subtract_plane(self=None):
    try: 
        self.w = PlaneLevelingWindow(self)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()