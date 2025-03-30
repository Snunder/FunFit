"""Built-in modules"""
import os
import platform
import subprocess
import ctypes

"""External modules"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QMessageBox, QApplication, QFileDialog
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QColor, QImage

"""Internal modules"""
try:
    from FunFit.Functions.Fit_plotting import PlotWindow
except:
    from Functions.Fit_plotting import PlotWindow

"""Get application size from system"""
def image_size():
    # Set the scale of the image to width of the main display monitor
    if platform.system() == "Windows":
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    elif platform.system() == "Darwin":
        from AppKit import NSScreen
        screensize = [int(NSScreen.mainScreen().frame().size.width*3/2), int(NSScreen.mainScreen().frame().size.height*3/2)]
    elif platform.system() == "Linux":
        output = subprocess.check_output("xrandr | grep '*' | awk '{print $1}'", shell=True).decode().strip().split('\n')[0]
        screensize = output.split('x')
        screensize = [int(screensize[0]), int(screensize[1])]

    image_size = min(screensize) // 3
    return image_size

"""Create a title bar for the provided parent window"""
def create_title_bar(parent, title="Window Title", type="category"):
    # Create a container for the title bar
    title_bar_container = QWidget(parent)
    title_bar_container.setObjectName("title_bar_container")
    
    # Create a layout for the title bar
    title_bar_layout = QVBoxLayout(title_bar_container)
    title_bar_layout.setContentsMargins(0, 0, 0, 0)
    title_bar_layout.setSpacing(0)

    # Create a layout for the title bar contents
    title_bar_inner_layout = QHBoxLayout()
    if type != "child":
        title_bar_inner_layout.setContentsMargins(10, 10, 10, 10)
        dir = parent.current_dir
    else:
        title_bar_inner_layout.setContentsMargins(0, 0, 0, 3)
        try:
            dir = parent.parent.current_dir
        except:
            try:
                dir = parent.parent.parent.current_dir
            except:
                dir = parent.current_dir
    title_bar_inner_layout.setSpacing(0)

    # Create the title bar widget
    title_bar = DraggableTitleBar(parent, title, type, dir)
    
    # Add the title bar to the layout
    setStyleSheet_from_file(title_bar_container, os.path.join(dir, "GUI", "stylesheet.qss"))
    title_bar_inner_layout.addWidget(title_bar)
    title_bar_layout.addLayout(title_bar_inner_layout)
    return title_bar_container

"""Class for a draggable title bar"""
class DraggableTitleBar(QWidget):
    def __init__(self, parent, title, type, dir):
        super().__init__(parent)
        self.parent = parent
        self.current_dir = dir
        self.setFixedHeight(30 if type != "child" else 25)
        self.setStyleSheet("background-color: #19172D")
        self.dragging = False
        self.drag_position = QPoint()
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.init_ui(title, type)

    def init_ui(self, title, type): # Initialize the title bar UI
        title_bar_layout_inner = QHBoxLayout()
        title_bar_layout_inner.setContentsMargins(0, 0, 0, 0)
        title_bar_layout_inner.setSpacing(0)
        self.setLayout(title_bar_layout_inner)

        # Add title icon to main window
        if type != "child":
            # Title icon
            self.title_icon = QLabel()
            pixmap = QPixmap(os.path.join(self.current_dir, "GUI", "icon.png"))
            self.title_icon.setPixmap(pixmap.scaled(100, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            title_bar_layout_inner.addWidget(self.title_icon)
        
        # Title text
        title_text = QLabel(title)
        title_text.setStyleSheet("color: white; font-size: 16px; padding-left: 10px; font-family: 'Verdana'; border: none;")
        title_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_bar_layout_inner.addWidget(title_text, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Add info and close buttons to window if relevant
        if type != "child":
            # Info button
            info_button = self.create_info_button()
            title_bar_layout_inner.addWidget(info_button, 0, Qt.AlignmentFlag.AlignRight)
        close_button = self.create_close_button(self.parent, type)  # Add the close button
        title_bar_layout_inner.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

    def create_close_button(self, parent, type): # Create close button widget and return
        close_button = QPushButton()
        close_button.setFixedSize(40, 30 if type != "child" else 25)
        close_button.setIcon(QIcon(QPixmap(os.path.join(self.current_dir, "GUI", "icon_close.png"))))
        close_button.setObjectName("close_button")
        setStyleSheet_from_file(close_button, self.current_dir + "/GUI/stylesheet.qss")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)

        # If mainwindow is closed, close the application
        if type != "child":
            close_button.clicked.connect(QApplication.instance().quit)
        else:
            close_button.clicked.connect(parent.close)
        return close_button

    def create_info_button(self): # Create info button widget and return
        # Info button
        info_button = QPushButton()
        info_button.setFixedSize(30, 30)
        info_button.setIcon(QIcon(self.current_dir + "/GUI/icon_info.png"))
        info_button.setObjectName("info_button")
        setStyleSheet_from_file(info_button, self.current_dir + "/GUI/stylesheet.qss")
        info_button.clicked.connect(self.info_button_action)  # Define the action for the info button
        info_button.setCursor(Qt.CursorShape.PointingHandCursor)
        return info_button

    def info_button_action(self): # Info button for data loaded in FunFit
        if not hasattr(self.parent, "Raw_Z"):
            return
        # Open tab with information about the loaded data
        info = QMessageBox()
        info.setWindowTitle("Data Information")
        info.setText(f"Data dimensions (rows,cols): {self.parent.Raw_Z.shape}\n"
                     f"X scale: {self.parent.x_scale}µm\n"
                     f"Y scale: {self.parent.y_scale}µm")
        if hasattr(self.parent, "Z_fit"):
            info.setInformativeText(f"Fit parameters: {self.parent.Z_fit}")
        info.exec()
        
    """Mouse events"""
    def mousePressEvent(self, event): # This event handles mouse clicks for dragging
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event): # This event handles mouse movement for dragging
        if self.dragging:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event): # This event handles mouse release for dragging
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()

"""Display the data as an image widget"""
def display_data(self=None):
    # Set the image scale
    self.img_scale = image_size()
    ratio = self.x_scale / self.y_scale
    self.img_scale_x, self.img_scale_y = self.img_scale, int(self.img_scale / ratio)
    
    # Create a figure and canvas for the image
    figure = Figure(facecolor=None, edgecolor=None, frameon=False, figsize=(self.img_scale_x/100, self.img_scale_y/100), dpi=100)
    canvas = FigureCanvasQTAgg(figure)
    ax = figure.add_axes([0, 0, 1, 1])
    ax.imshow(self.Raw_Z, cmap='gray', aspect=self.Raw_Z.shape[1]/self.Raw_Z.shape[0]/ratio)
    self.image = QLabel()
    self.image.setPixmap(canvas.grab())
    self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Add column stretch to ensure image column expands
    layout = self.centralWidget().layout()
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)
    try:
        if hasattr(self, 'selection_display') and self.selection_display:
            self.selection_display.deleteLater()
        if hasattr(self, 'border_widget') and self.border_widget:
            self.border_widget.deleteLater()
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.deleteLater()
    except:
        pass
    return self.image

"""Add an export button to the main window"""
def add_export_button(self):
    # Create the export button graphic
    btn = QPushButton(self.image)
    btn.setFixedSize(30, 30)
    btn.setIcon(QIcon(self.current_dir + "/GUI/icon_export.png"))
    btn.setObjectName("export_button")
    setStyleSheet_from_file(btn, self.current_dir + "/GUI/stylesheet.qss")
    btn.clicked.connect(lambda _, idx=1: export_main(self, idx))
    
    # Position the export button
    self.export_button = btn
    pos = self.image.pos()
    btn_x = int(pos.x()) + int(self.img_scale_x) - 35 # Position the button in the top right corner
    vertical_offset = int((self.image.size().height() - self.img_scale_y)/2)
    btn_y = int(pos.y()) + int((self.img_scale_x - self.img_scale_y)/2) + 15 + vertical_offset # Position the button in the top right corner
    self.export_button.move(btn_x, btn_y)
    self.export_button.show()

    def export_main(self, idx):
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
        Z_data = self.corrected_data if hasattr(self, 'corrected_data') else self.Raw_Z
        self.plot_window = PlotWindow(self, self.Raw_x, self.Raw_y, Z_data, self.Raw_Z-1, None, None, None, None)
        self.plot_window.ax5.set_title('')
        export_plot(self.plot_window, idx)

"""Export data to a file"""
def export_plot(self, index):
    data_map = {
        0: (self.Z_fit_export, 'Fit', 'Purples_r'),
        1: (self.Z_data_export, 'Data', 'Purples_r'),
        2: (self.Z_residual_export, 'Residual', 'RdBu_r'),
        3: (self.fft_fit_norm, 'FFT_Fit', self.fft_cmap),
        4: (self.fft_data_norm, 'FFT_Data', self.fft_cmap),
        5: (self.fft_residual_norm, 'FFT_Residual', self.fft_cmap)
    }
    data, title, cmap = data_map.get(index, (None, None, None))
    if data is None:
        return
    
    if self.parent.__class__.__name__ != 'MainWindow':
        data = np.flipud(data)

    # Open a file dialog to select the file to plot
    self.current_dir = os.path.dirname(os.path.realpath(__file__))
    if self.current_dir.endswith('Functions'):
        self.current_dir = os.path.dirname(self.current_dir)
    Dialog_window = QFileDialog()
    Dialog_window.setWindowTitle(f"Export {title}")
    Dialog_window.setFileMode(QFileDialog.FileMode.AnyFile)
    Dialog_window.setNameFilter("Text files (*.txt);;PNG images (*.png);;PDF files (*.pdf);;SVG images (*.svg)")
    Dialog_window.setOption(QFileDialog.Option.DontUseNativeDialog)
    Dialog_window.setWindowIcon(QIcon(os.path.join(self.current_dir, "GUI", "icon_window.png")))
    Dialog_window.setDirectory(os.path.dirname(self.current_dir) + "/tests")
    if Dialog_window.exec() == QFileDialog.DialogCode.Accepted:
        file_path, selected_filter = Dialog_window.selectedFiles()[0], Dialog_window.selectedNameFilter()
    else:
        return
    
    # Handle file extension based on selected filter
    if selected_filter == "Text files (*.txt)": # Write the data to a text file
        if not file_path.endswith('.txt'):
            file_path += '.txt'
        f = open(file_path, 'w', encoding='utf-8')
        # Write the header and data to the file
        if index <= 2:
            f.writelines([
                          f"# Channel: ZSensor\n", 
                          f"# Width: {self.x[-1] - self.x[0]:.3f} µm\n",
                          f"# Height: {self.y[-1] - self.y[0]:.3f} µm\n",
                          "# Value units: m\n"
                          ])
            np.savetxt(f, data*1e-9, fmt='%.4e', delimiter='\t')
            f.close()
        else:
            f.writelines([
                          "# Channel: FFT\n",
                          "# X,Y units: 1/µm\n",
                          "# Value units: relative intensity\n"
                          ])
            np.savetxt(f, data, fmt='%.6e', delimiter='\t')
    else: # Save the plot as an image
        if selected_filter == "PNG images (*.png)" and not file_path.endswith('.png'):
            file_path += '.png'
        elif selected_filter == "PDF files (*.pdf)" and not file_path.endswith('.pdf'):
            file_path += '.pdf'
        elif selected_filter == "SVG images (*.svg)" and not file_path.endswith('.svg'):
            file_path += '.svg'
        
        # Get plot items
        plot = self.figure
        ax, cbar = plot.get_axes()[index], plot.get_axes()[index+6]
        ax.figure.canvas.draw(), cbar.figure.canvas.draw()
        
        # Setup the plot extent
        pad=0.02
        items = ax.get_xticklabels() + ax.get_yticklabels() 
        items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
        items += [cbar, cbar.yaxis.label]
        bbox = Bbox.union([item.get_window_extent() for item in items])
        full_extent = bbox.expanded(1.0 + pad, 1.0 + pad)
        extent = full_extent.transformed(plot.dpi_scale_trans.inverted())
        plot.savefig(file_path, bbox_inches=extent)

"""Generate a bitmap from an equation"""
def generate_bitmap_from_equation(equation_type):
    # Set parameters for the image
    size = 100
    image = QImage(size, size, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))

    # Generate the image based on the equation type
    for x in range(size):
        for y in range(size):
            if equation_type == "fourierseries":
                N = 2
                value = int((100 * np.sin(N * x / size * 2 * np.pi - np.pi/2) + 
                              50 * np.sin(2 * N * x / size * 2 * np.pi + np.pi/2)) + 120)
            elif equation_type == "polynomial":
                value = int(0.0005*(x-size/2)**2 * 2*size + 10)
            elif equation_type == "exponential":
                value = int(np.exp(0.06*x) + 10)
            elif equation_type == "quasicrystal":
                N = 6
                value = int(sum(50*np.cos(2 * np.pi / 7 * ((x - size/2) * np.cos((i * 180 / N) * np.pi / 180) + 
                                                           (y - size/2) * np.sin((i * 180 / N) * np.pi / 180))) + 10 
                                                           for i in range(N)))
            elif equation_type == "gaussian":
                value = int((np.exp(-((x - size / 2) ** 2 + (y - size / 2) ** 2) / (2 * (size / 5) ** 2))) * 255)
            elif equation_type == "custom":
                zx, zy = x * 3.0 / size - 2.0, y * 3.0 / size - 1.5
                c = complex(zx, zy)
                z = complex(0, 0)
                for i in range(256):
                    if abs(z) > 2.0: break
                    z = z * z + c
                value = 240 - int(i * 240 / 256) 
            else:
                value = 128
            
            # Ensure the value is within the range 0-255
            value = max(0, min(255, value))
            color = QColor(value, value, value)
            image.setPixelColor(x, y, color)
    return QPixmap.fromImage(image)

"""Set the stylesheet from a file"""
def setStyleSheet_from_file(self, filepath): # Set the stylesheet from a file
    with open(filepath, "r") as f:
        self.setStyleSheet(f.read())

"""Show an error message"""
def error_message(message):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(message)
    msg.setWindowTitle("Error")
    msg.exec()