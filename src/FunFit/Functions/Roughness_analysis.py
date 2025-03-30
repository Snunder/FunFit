"""External modules"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtGui import QPolygonF, QPixmap

"""Internal modules"""
try:
    from FunFit.Functions.helpers import create_title_bar, setStyleSheet_from_file, add_export_button, export_plot
    from FunFit.Functions.Find_structs import FindStructWindow
    import FunFit.Functions.Fit_plotting as Fit_plotting
except:
    from Functions.helpers import create_title_bar, setStyleSheet_from_file, add_export_button, export_plot
    from Functions.Find_structs import FindStructWindow
    import Functions.Fit_plotting as Fit_plotting

LINE_CUT_FACE_COLOR = "#232036"
PLOT_TEXT_COLOR = "#706E85"

class Roughness_analysis_window(FindStructWindow):
    """Window for selecting a flat area to calculate roughness. Inherits from FindStructWindow."""
    def apply_selection(self): # Apply the selection to the data
        # If no selection, use entire image
        if self.selection_polygon.isEmpty():
            self.corners = [QPointF(0, 0), 
                            QPointF(self.parent.img_scale_x, 0), 
                            QPointF(self.parent.img_scale_x, self.parent.img_scale_y), 
                            QPointF(0, self.parent.img_scale_y)]
            self.selection_polygon = QPolygonF(self.corners)

        # Create a Path object from the selection polygon
        polygon_path = Path([(point.x() * self.Raw_Z.shape[1] / self.parent.img_scale_x, 
                              point.y() * self.Raw_Z.shape[0] / self.parent.img_scale_y) 
                              for point in self.selection_polygon])

        # Create a mask for the selection polygon
        mask = np.zeros(self.Raw_Z.shape, dtype=bool)
        x_coords, y_coords = np.meshgrid(np.arange(self.Raw_Z.shape[1]), np.arange(self.Raw_Z.shape[0]))
        points = np.vstack((x_coords.flatten(), y_coords.flatten())).T
        mask = polygon_path.contains_points(points).reshape(self.Raw_Z.shape)

        # Create images with NaNs for outside points
        self.inside_image = np.where(mask, self.Raw_Z, np.nan)
        self.outside_image = np.where(~mask, self.Raw_Z, np.nan)
        self.calc()

    def calc(self): # Calculate the roughness of the flat area
        if hasattr(self, 'inside_image') and hasattr(self, 'outside_image'):
            Z = self.inside_image
        else:
            Z = self.Raw_Z
        # Fit a plane to the data
        X, Y = np.meshgrid(np.arange(Z.shape[1]), np.arange(Z.shape[0]))
        XX, YY, ZZ = X[np.isfinite(Z)], Y[np.isfinite(Z)], Z[np.isfinite(Z)]
        A = np.c_[XX.ravel(), YY.ravel(), np.ones(XX.size)]
        C, _, _, _ = np.linalg.lstsq(A, ZZ.ravel(), rcond=None)
        plane = (C[0] * X + C[1] * Y + C[2]).reshape(Z.shape)

        # Subtract the plane from the original data
        self.residuals = Z - plane
        
        self.plot_window = PlotWindow(self.parent, self.parent.Raw_x, self.parent.Raw_y, Z, plane)
        self.plot_window.show()

        self.close()

class PlotWindow(QMainWindow):
    """Window for plotting the roughness of a flat area."""
    def __init__(self, parent, x, y, Z_data, Z_fit):
        super().__init__()
        self.parent = parent
        self.x, self.y, self.Z_data, self.Z_fit = x, y, Z_data, Z_fit
        self.residuals = Z_data - Z_fit
        setStyleSheet_from_file(self, self.parent.current_dir + "/GUI/stylesheet.qss")
        plt.rcParams.update({
                            'font.size': 14,
                            'figure.facecolor': LINE_CUT_FACE_COLOR,
                            'figure.edgecolor': PLOT_TEXT_COLOR,
                            'axes.facecolor': LINE_CUT_FACE_COLOR,
                            'axes.edgecolor': PLOT_TEXT_COLOR,
                            'axes.labelcolor': PLOT_TEXT_COLOR,
                            'xtick.color': PLOT_TEXT_COLOR,
                            'ytick.color': PLOT_TEXT_COLOR,
                            'text.color': PLOT_TEXT_COLOR,
                            'axes.titlesize': 16,
                            'xtick.labelsize': 14,
                            'ytick.labelsize': 14,
                            })
        self.init_ui()

    def init_ui(self): # Initialize the PlotWindow UI
        # Set window properties
        self.setWindowTitle("Roughness Preview")
        self.setGeometry(self.parent.geometry().x(), self.parent.geometry().y(), 0, 0)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Add a main layout for storing widgets
        central_widget = QWidget()
        main_layout = QGridLayout(central_widget)
        self.setCentralWidget(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add title bar at the top
        title_bar = create_title_bar(self, "Fit Preview", "child")
        main_layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)

        # Add the roughness plot widget
        fig_layout = QVBoxLayout()
        fig_layout.setContentsMargins(0, 0, 0, 0)
        fig_layout.setSpacing(0)
        self.roughness_plot = QLabel()
        self.roughness_plot.setStyleSheet("background-color: transparent;")
        fig_layout.addWidget(self.roughness_plot)
        fig_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(fig_layout, 1, 0, 1, -1, Qt.AlignmentFlag.AlignCenter)
        self.showRoughness()

        self.image, self.current_dir = self.roughness_plot, self.parent.current_dir
        self.img_scale_x, self.img_scale_y = self.parent.img_scale_x, self.parent.img_scale_y
        add_export_button(self) # Add export button to the main layout
        self.export_button.move(20, 20)
        self.export_button.clicked.disconnect()
        self.export_button.clicked.connect(lambda _, idx=2: self.export_roughness(idx))

    def export_roughness(self, idx): # Export the roughness plot
        # Set the plot window style
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
        self.plot_window = Fit_plotting.PlotWindow(self, self.x, self.y, np.flipud(self.Z_data), np.flipud(self.Z_fit), None, None, None, None)
        self.plot_window.ax6.set_title('')
        export_plot(self.plot_window, idx)

    def calculations(self): # Calculate the roughness
        # Remove NaN values from x, y, and Z_data
        mask = ~np.isnan(self.residuals)
        x_masked, y_masked = self.x[mask.any(axis=0)], self.y[mask.any(axis=1)]

        Z_residual_masked = self.residuals[np.ix_(mask.any(axis=1), mask.any(axis=0))]
        Z_residual_masked = np.ma.masked_where(np.isnan(Z_residual_masked), Z_residual_masked)
        max_abs = max(abs(np.nanmax(Z_residual_masked)), abs(np.nanmin(Z_residual_masked)))
        rmse = np.sqrt(np.nanmean(Z_residual_masked**2))
        return x_masked, y_masked, Z_residual_masked, max_abs, rmse

    def showRoughness(self): # Show the roughness plot
        # Calculate roughness
        x_masked, y_masked, Z_residual_masked, max_abs, rmse = self.calculations()
        
        # Create a figure and canvas
        self.figure = Figure(frameon=True, tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)

        self.ax1 = self.figure.add_subplot(111)
        self.ax1.set_anchor('W')
        ratio = Z_residual_masked.shape[0] / Z_residual_masked.shape[1]
        c1 = self.ax1.imshow(np.flipud(Z_residual_masked), extent=[x_masked[0], x_masked[-1], y_masked[0], y_masked[-1]],
                             origin='lower', cmap='RdBu_r', vmin=-max_abs, vmax=max_abs, aspect=1/ratio)
        cbar1 = self.figure.colorbar(c1, ax=self.ax1, orientation='vertical')
        cbar1.set_label('Height (nm)')
        self.ax1.set_title(f'Residual [RMSE: {rmse:.4f} nm]', color=PLOT_TEXT_COLOR)
        self.ax1.set_xlabel("x (µm)")
        self.ax1.set_ylabel("y (µm)")
        self.canvas.draw()

        pixelmap = QPixmap(self.canvas.grab())
        self.roughness_plot.setPixmap(pixelmap)
        self.roughness_plot.setAlignment(Qt.AlignmentFlag.AlignCenter)

"""Function called from main window."""
def extract_roughness(self=None):
    try: 
        self.w = Roughness_analysis_window(self)
    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Data not loaded.")
        msg.setInformativeText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()