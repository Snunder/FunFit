"""Built-in modules"""
from io import BytesIO

"""External modules"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")
import matplotlib.colors
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QTextDocument, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QStyledItemDelegate, QGridLayout, QPushButton
)

"""Internal modules"""
try:
    from FunFit.Functions import helpers, Fit_config
except:
    from Functions import helpers, Fit_config

FIT_EQUATIONS = Fit_config.FIT_EQUATIONS
LINE_CUT_FACE_COLOR = "#FFFFFF"
PLOT_TEXT_COLOR = "#000000"

class ResultsWindow(QMainWindow):
    """Window to display fitting results."""
    def __init__(self, parent, popt, perr, func_name, param_names, plot_window=None):
        super().__init__(parent)
        self.parent = parent
        self.popt, self.perr = popt, perr
        self.func_name, self.param_names = func_name, param_names
        self.plot_window = plot_window
        helpers.setStyleSheet_from_file(self, self.parent.parent.current_dir + "/GUI/stylesheet.qss")
        self.init_ui()

    def init_ui(self): # Set up the ResultsWindow UI
        # Set window properties
        self.setGeometry(self.parent.geometry().x(), self.parent.geometry().y(), 650, 450)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        # Create the main layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central_widget)
        
        # Add title bar
        title_bar = helpers.create_title_bar(self, "Fitting Results", "child")
        layout.addWidget(title_bar, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Main content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        # Parameter table with units
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value", "Uncertainty"])
        self.populate_table()
        self.table.setObjectName("results_table")
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setItemDelegate(HTMLDelegate())

        # Equation display
        equation_label = QLabel("Fitted Equation:")
        equation_label.setStyleSheet("color: white; font-size: 20px;")
        equation_pixmap = self.get_equation_image()
        equation_display = QLabel()
        equation_display.setPixmap(equation_pixmap)
        equation_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        equation_display.setFixedHeight(50)
        
        # Add widgets to the layout
        content_layout.addWidget(self.table, 4)
        content_layout.addWidget(equation_label)
        content_layout.addWidget(equation_display)
        layout.addWidget(content_widget)
    
    def populate_table(self): # Populate the parameter table with the fitting results
        # Map parameter names to units
        unit_map = {
            'µ_x': 'µm', 'µ_y': 'µm', 'A': 'nm', 'λ': 'µm', 'φ': '', 'θ': '°',
            'x0': 'µm', 'y0': 'µm', 'c': 'nm', 'σ': 'µm',
            'µ': 'µm', 'b': 'µm⁻¹', 'N': ''
        }
        
        # Filter out subscripts from parameter names
        filtered_params = [
            (name, val, err, name.split('<sub>')[0])
            for name, val, err in zip(self.param_names, self.popt, self.perr)
        ]

        # Populate the table
        self.table.setRowCount(len(filtered_params)+1)
        for i, (name, val, err, base) in enumerate(filtered_params):
            unit = unit_map.get(base, '')
            val_text = f"{val:.3f} {unit}" if unit else f"{val:.3f}"
            err_text = f"{err:.1e} {unit}" if unit and not np.isnan(err) else "N/A" if np.isnan(err) else f"{err:.1e}"
            
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(val_text))
            self.table.setItem(i, 2, QTableWidgetItem(err_text))
            self.table.setRowHeight(i, 40)
        # Add the RMSE to the table
        self.table.setItem(i+1, 0, QTableWidgetItem('RMSE'))
        self.table.setItem(i+1, 1, QTableWidgetItem(f"{self.plot_window.rmse:.4f} nm"))
        self.table.setItem(i+1, 2, QTableWidgetItem(''))
        self.table.setRowHeight(i+1, 40)

        self.table.setItemDelegate(HTMLDelegate())
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.resizeColumnsToContents()

    def get_equation_image(self): # Get a pixmap of the fitted equation
        # Use the imported FIT_EQUATIONS instead of a local dictionary
        eq_str = FIT_EQUATIONS.get(self.func_name, "")
        
        # Smaller figure size for compact display
        fig = Figure(figsize=(6, 1))  # Reduced height from 2 to 1
        canvas = FigureCanvasQTAgg(fig)
        fig.patch.set_alpha(0.0)
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.text(0.5, 0.5, eq_str, 
                ha='center', va='center', fontsize=14, color='white', usetex=False)
        
        buf = BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight')
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        return pixmap
    
class HTMLDelegate(QStyledItemDelegate):
    """Delegate to display HTML text in a QTableWidget."""
    def paint(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole)
        document = QTextDocument()
        document.setHtml(f'<span style="color: white; font-size: 20px;">{text}</span>')
        painter.save()
        painter.translate(option.rect.topLeft())
        document.drawContents(painter)
        painter.restore()

class PlotWindow(QMainWindow):
    """Window to display the fitted results as plots."""
    def __init__(self, parent, x, y, Z_data, Z_fit, popt, perr, func_name, param_names):
        super().__init__(parent)
        self.parent = parent
        self.x, self.y, self.Z_data, self.Z_fit = x, y, Z_data, Z_fit
        self.Z_residual = Z_data - Z_fit
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

    def init_ui(self): # Set up the PlotWindow UI
        # Set window properties
        self.setGeometry(self.parent.geometry().x(), self.parent.geometry().y(), 1600, 800)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)

        # Create the main layout
        central_widget = QWidget()
        main_layout = QGridLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setCentralWidget(central_widget)

        # Add title bar
        title_bar = helpers.create_title_bar(self, "Fit Preview", "child")
        main_layout.addWidget(title_bar, 0, 0, 1, -1, Qt.AlignmentFlag.AlignTop)

        # Create figure and canvas
        figure_container = QWidget()
        figure_layout = QVBoxLayout(figure_container)
        figure_layout.setContentsMargins(0, 0, 0, 0)
        figure_layout.setSpacing(0)
        
        self.figure = Figure(figsize=(14, 7))
        self.canvas = FigureCanvasQTAgg(self.figure)
        figure_layout.addWidget(self.canvas)
        main_layout.addWidget(figure_container, 1, 0)
        main_layout.setRowStretch(1, 1)
        
        self.plot_results()

    def plot_results(self): # Plot the fitting results
        matplotlib.rcParams.update({
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

        # Create subplots
        self.ax1 = self.figure.add_subplot(231)
        self.ax2 = self.figure.add_subplot(232)
        self.ax3 = self.figure.add_subplot(233)
        self.ax4 = self.figure.add_subplot(234)
        self.ax5 = self.figure.add_subplot(235)
        self.ax6 = self.figure.add_subplot(236)
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
            ax.set_box_aspect(1)

        self.data_processing()

        self.plot_fit()
        self.plot_data()
        self.plot_residual()
        
        self.data_processing_FFT()
        
        self.plot_fit_FFT()
        self.plot_data_FFT()
        self.plot_residual_FFT()

        for ax in [self.ax1, self.ax2, self.ax3]:
            ax.set_xlabel('x (µm)', fontsize=12)
            ax.set_ylabel('y (µm)', fontsize=12)

        # B O X   A S P E C T   R A T I O
        for ax in [self.ax4, self.ax5, self.ax6]:
            ax.set_xlabel('Frequency (1/µm)', fontsize=12)
            ax.set_ylabel('Frequency (1/µm)', fontsize=12)
            ax.set_xlim(-self.smallestaxis, self.smallestaxis)
            ax.set_ylim(-self.smallestaxis, self.smallestaxis)
            ax.set_box_aspect(1)

        try:
            self.add_export_buttons()
            # Update button positions when the canvas is drawn
            self.canvas.mpl_connect('draw_event', self.update_button_positions)
        except: pass

        self.figure.tight_layout(pad=0.0)
        self.canvas.draw()

    def data_processing(self): # Process the data for plotting
        self.mask1 = ~np.isnan(self.Z_data)
        self.x_masked = self.x[self.mask1.any(axis=0)]
        self.y_masked = self.y[self.mask1.any(axis=1)]
        self.Z_data_masked = self.Z_data[np.ix_(self.mask1.any(axis=1), self.mask1.any(axis=0))]
        self.Z_fit_cropped = self.Z_fit[np.ix_(self.mask1.any(axis=1), self.mask1.any(axis=0))]
        self.Z_fit_masked = np.ma.masked_where(np.isnan(self.Z_fit_cropped), self.Z_fit_cropped)
        self.Z_data_masked = np.ma.masked_where(np.isnan(self.Z_data_masked), self.Z_data_masked)
        self.Z_residual_masked = self.Z_residual[np.ix_(self.mask1.any(axis=1), self.mask1.any(axis=0))]

        # Save data for export
        self.Z_fit_export = np.nan_to_num(self.Z_fit_masked, nan=np.nan)
        self.Z_data_export = np.nan_to_num(self.Z_data_masked, nan=np.nan)
        self.Z_residual_export = np.nan_to_num(self.Z_residual_masked, nan=np.nan)

    def data_processing_FFT(self): # Process the data for FFT plotting
        # Crop data to mask for FFT (has to be square). Elaborate for angled polygons, fast for rectangles.
        self.Z_fit_cropped = self.crop_to_valid_box(self.Z_fit)
        self.Z_data_cropped = self.crop_to_valid_box(self.Z_data)
        self.Z_residual_cropped = self.crop_to_valid_box(self.Z_residual)

        # Calculate FFT of cropped data, remove DC component, and normalize
        fft_fit_norm = np.abs(np.fft.fftshift(np.fft.fft2(self.Z_fit_cropped - np.mean(self.Z_fit_cropped)))) / np.max(np.abs(np.fft.fftshift(np.fft.fft2(self.Z_fit_cropped - np.mean(self.Z_fit_cropped)))))
        fft_data_norm = np.abs(np.fft.fftshift(np.fft.fft2(self.Z_data_cropped - np.mean(self.Z_data_cropped)))) / np.max(np.abs(np.fft.fftshift(np.fft.fft2(self.Z_data_cropped - np.mean(self.Z_data_cropped)))))
        fft_residual_norm = np.abs(np.fft.fftshift(np.fft.fft2(self.Z_residual_cropped - np.mean(self.Z_residual_cropped)))) / np.max(np.abs(np.fft.fftshift(np.fft.fft2(self.Z_residual_cropped - np.mean(self.Z_residual_cropped)))))
        
        # Assign FFT arrays to instance attributes for export use
        self.fft_fit_norm = fft_fit_norm
        self.fft_data_norm = fft_data_norm
        self.fft_residual_norm = fft_residual_norm
        
        # Define a custom colormap with multiple colors
        colors = [(0/256, 0/256, 0/256), (197/256, 114/256, 255/256), (219/256, 1, 255/256), (1, 1, 1)]  # Black to purple to magenta
        n_bins = 100
        cmap_name = 'FFT_colormap'
        self.fft_cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)

        # Calculate frequency axes (1/µm)
        self.freq_x = 2*np.pi*np.fft.fftshift(np.fft.fftfreq(self.Z_data.shape[1], d=(self.x[1] - self.x[0])))
        self.freq_y = 2*np.pi*np.fft.fftshift(np.fft.fftfreq(self.Z_data.shape[0], d=(self.y[1] - self.y[0])))
        self.smallestaxis = min(self.freq_x[-1], self.freq_y[-1])

    def plot_fit(self): # Plot the fit and its FFT
        Z_fit_masked = np.ma.masked_where(np.isnan(self.Z_fit_cropped), self.Z_fit_cropped)
        c1 = self.ax1.imshow(Z_fit_masked, extent=[self.x_masked[0], self.x_masked[-1], self.y_masked[0], self.y_masked[-1]],
                origin='lower', cmap='Purples_r', aspect='auto')
        self.cbar1 = self.figure.colorbar(c1, ax=self.ax1, fraction=0.05, pad=0.05)
        self.cbar1.set_label('Height, $Z$ (nm)', labelpad=14, rotation=270, fontsize=12)
        self.ax1.set_title('Fit')

    def plot_fit_FFT(self):
        c4 = self.ax4.imshow(self.fft_fit_norm, cmap=self.fft_cmap, extent=[self.freq_x[0], self.freq_x[-1], self.freq_y[0], self.freq_y[-1]], aspect='auto')
        self.cbar4 = self.figure.colorbar(c4, ax=self.ax4, fraction=0.05, pad=0.05)
        self.ax4.set_title('FFT of Fit')

    def plot_data(self): # Plot the data and its FFT
        Z_data_masked = np.ma.masked_where(np.isnan(self.Z_data_masked), self.Z_data_masked)
        c2 = self.ax2.imshow(Z_data_masked, extent=[self.x_masked[0], self.x_masked[-1], self.y_masked[0], self.y_masked[-1]],
            origin='lower', cmap='Purples_r', aspect='auto')
        self.cbar2 = self.figure.colorbar(c2, ax=self.ax2, fraction=0.05, pad=0.05)
        self.cbar2.set_label('Height, $Z$ (nm)', labelpad=14, rotation=270, fontsize=12)
        self.ax2.set_title('Data')

    def plot_data_FFT(self):
        c5 = self.ax5.imshow(self.fft_data_norm, cmap=self.fft_cmap, extent=[self.freq_x[0], self.freq_x[-1], self.freq_y[0], self.freq_y[-1]], aspect='auto')
        self.cbar5 = self.figure.colorbar(c5, ax=self.ax5, fraction=0.05, pad=0.05)
        self.ax5.set_title('FFT of Data')

    def plot_residual(self): # Plot the residual data from the fit and its FFT
        Z_residual_masked = self.Z_residual[np.ix_(self.mask1.any(axis=1), self.mask1.any(axis=0))]
        Z_residual_masked = np.ma.masked_where(np.isnan(Z_residual_masked), Z_residual_masked)
        max_abs = max(abs(np.nanmax(Z_residual_masked)), abs(np.nanmin(Z_residual_masked)))
        c3 = self.ax3.imshow(Z_residual_masked, extent=[self.x_masked[0], self.x_masked[-1], self.y_masked[0], self.y_masked[-1]],
            origin='lower', cmap='RdBu_r', vmin=-max_abs, vmax=max_abs, aspect='auto')
        self.cbar3 = self.figure.colorbar(c3, ax=self.ax3, fraction=0.05, pad=0.05)
        self.cbar3.set_label('Residual, $ΔZ$ (nm)', labelpad=14, rotation=270, fontsize=12)
        rmse = np.sqrt(np.nanmean(Z_residual_masked**2))
        self.rmse = rmse
        self.ax3.set_title(f'Residual [RMSE: {rmse:.4f} nm]')

    def plot_residual_FFT(self):
        c6 = self.ax6.imshow(self.fft_residual_norm, cmap=self.fft_cmap, extent=[self.freq_x[0], self.freq_x[-1], self.freq_y[0], self.freq_y[-1]], aspect='auto')
        self.cbar6 = self.figure.colorbar(c6, ax=self.ax6, fraction=0.05, pad=0.05)
        self.ax6.set_title('FFT of Residual')

    def add_export_buttons(self): # Plot the FFT of the fit, data, and residual
        # Export buttons
        self.export_buttons = []
        for i in range(6):
            btn = QPushButton(self.canvas)
            btn.setFixedSize(30, 30)
            btn.setIcon(QIcon(self.parent.parent.current_dir + "/GUI/icon_export.png"))
            btn.setObjectName("export_button")
            btn.clicked.connect(lambda _, idx=i: helpers.export_plot(self, idx))
            self.export_buttons.append(btn)
            btn.hide()
        
    def crop_to_valid_box(self, data): # Crop the data to a valid box for FFT
        self.mask1 = ~np.isnan(data)
        if not np.any(self.mask1):
            return data
        rows, cols = self.mask1.shape
        max_area, max_coords = 0, (0, 0, 0, 0)
        heights = np.zeros(cols, dtype=int)
        for i in range(rows):
            heights = np.where(self.mask1[i], heights + 1, 0)
            stack = []
            for j in range(cols + 1):
                current_h = heights[j] if j < cols else 0
                while stack and heights[stack[-1]] > current_h:
                    h = heights[stack.pop()]
                    w = j if not stack else j - stack[-1] - 1
                    area = h * w
                    if area > max_area:
                        left_idx = stack[-1] + 1 if stack else 0
                        max_area, max_coords = area, (i - h + 1, left_idx, i, j - 1)
                stack.append(j)
            top, left, bottom, right = max_coords
        return data[max(0, top):min(rows, bottom + 1), max(0, left):min(cols, right + 1)] if max_area else data

    def update_button_positions(self, event=None): # Update the position of the export buttons
        for i, ax in enumerate([self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]):
            pos = ax.get_position()
            canvas_width = self.canvas.width()
            canvas_height = self.canvas.height()
            btn_x = int(pos.x1 * canvas_width) - 35  # 60px width + 5px padding
            btn_y = int((1 - pos.y1) * canvas_height) + 5
            self.export_buttons[i].move(btn_x, btn_y)
            self.export_buttons[i].show()