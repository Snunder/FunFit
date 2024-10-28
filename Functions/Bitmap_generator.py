import numpy as np
import matplotlib.pyplot as plt
import Functions.Function_presets as fitmodel
from matplotlib.colors import LinearSegmentedColormap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets
from PyQt6.QtGui import QIcon
import os

class InputDialog_BMP(QWidget):
    def __init__(self, text=''):
        super().__init__()

        self.setWindowTitle('Input Dialog')

        layout = QVBoxLayout()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet('background-color: #19172D;')
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        with(open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r')) as f:
            self.setStyleSheet(f.read())

        # Titlebar
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName('titleBar')
        self.title_bar.setStyleSheet('background-color: #19172D;')
        self.title_bar.setFixedHeight(30)
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel('Bitmap Generator', self.title_bar)
        self.title_label.setStyleSheet('margin-left: 10px; color: white; font-size: 16px; font-family: Verdana;')
        self.title_bar_layout.addWidget(self.title_label)
        self.title_bar_layout.addStretch()
        self.close_button = QPushButton('', self.title_bar)
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
        self.close_button.setIcon(QIcon(os.getcwd()+'GUI/icon_close.png'))
        self.close_button.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.close_button)
        layout.addWidget(self.title_bar)

        # Add line under the title bar
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        line.setLineWidth(1)
        line.setStyleSheet('color: #4B4587;')
        layout.addWidget(line)

        verticalbox = QHBoxLayout()
        self.label = QLabel('  Enter x size in µm: ')
        self.label.setStyleSheet('font-size: 16px; color: white; font-family: Verdana;')
        verticalbox.addWidget(self.label)
        self.xsize = QLineEdit(self)
        self.xsize.setFixedSize(200, 40)
        self.xsize.setPlaceholderText('1')
        self.xsize.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.xsize)
        layout.addLayout(verticalbox)

        verticalbox = QHBoxLayout()
        self.label = QLabel('  Enter y size in µm: ')
        self.label.setStyleSheet('font-size: 16px; color: white; font-family: Verdana;')
        verticalbox.addWidget(self.label)
        self.ysize = QLineEdit(self)
        self.ysize.setFixedSize(200, 40)
        self.ysize.setPlaceholderText('1')
        self.ysize.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.ysize)
        layout.addLayout(verticalbox)
        
        verticalbox = QHBoxLayout()
        self.label = QLabel('  Enter nm/pixel: ')
        self.label.setStyleSheet('font-size: 16px; color: white; font-family: Verdana;')
        verticalbox.addWidget(self.label)
        self.nm_px = QLineEdit(self)
        self.nm_px.setFixedSize(200, 40)
        self.nm_px.setPlaceholderText('10')
        self.nm_px.setStyleSheet(
            'font-size: 16px; color: white; background-color: #333333; padding: 1px; border: 2px solid #4B4587; margin: 5px; border-radius: 5px; margin-right: 10px;')
        verticalbox.addWidget(self.nm_px)
        layout.addLayout(verticalbox)
                
        self.button = QPushButton('Submit', self)
        self.button.clicked.connect(self.on_submit)
        with open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r') as f:
            self.button.setStyleSheet(f.read())
        self.button.setStyleSheet('margin-bottom: 10px;')
        layout.addWidget(self.button)
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
        
        self.setLayout(layout)
        self.show()

    def on_submit(self):
        self.close()

def Function_fit(self=None, fitting_model = None, IC = None, x_size = 1, y_size = 1, nm_px = 10):
    
    nm_px = nm_px * 1e-3 # Convert nm to µm

    x = np.linspace(-x_size/2, x_size/2, max(1,int(x_size/nm_px)))
    y = np.linspace(-y_size/2, y_size/2, max(1,int(y_size/nm_px)))

    X, Y = np.meshgrid(x, y)
    tmpX = X
    tmpY = Y

    # Flatten the data for curve fitting
    X = np.column_stack((tmpX.flatten(), tmpY.flatten()))

    # Set inf/nan to 0 (edge values from rotation)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    # Predict using the fitted model
    Z_fit_vector = fitting_model(X.T, *IC)
    # Reshape the predicted data back to the original shape
    try:
        Z_fit = Z_fit_vector.reshape(Y.shape)
    except:
        Z_fit = Z_fit_vector

    # Plot the original data, the fitted model and the residuals
    plt.figure()
    
    # Define a custom colormap with multiple colors
    colors = [(0/256, 0/256, 0/256), (197/256, 114/256, 255/256), (219/256, 1, 255/256), (1, 1, 1)]  # Black to purple to magenta
    n_bins = 100  # Number of bins in the colormap
    cmap_name = 'custom_colormap'
    fft_cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins) # Create the colormap for fft plots
    
    # Fitted model
    plt.imshow(Z_fit, cmap='Purples_r', aspect='equal', extent=[np.min(tmpX), np.max(tmpX), np.min(tmpY), np.max(tmpY)])
    plt.tight_layout()
    plt.show()

    FileName = QFileDialog.getExistingDirectory(
        parent=self,
        caption="Select the directory to save the bitmap",
        options=QFileDialog.Option.DontUseNativeDialog,
    )

    if FileName == '':
        return
    filepath_name = FileName + "\\bitmap.bmp"
    plt.imsave(filepath_name, Z_fit, cmap='gray')

def main():
    global IC, crosshair, ax, background, extent, user_clicked
    [fitting_model, IC, Bounds] = fitmodel.custom()

    Function_fit(fitting_model = fitting_model, IC = IC)
    # Function_fit(functiontype = "custom")

if __name__ == "__main__":
    main()