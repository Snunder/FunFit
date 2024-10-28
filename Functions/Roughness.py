import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets
import pickle
from sklearn import linear_model

from Functions.helpers import plotopts

# Define a class that inherits from QMainWindow
class StructureFinder(QMainWindow):
    def __init__(self, image_path):
        # Call the __init__ method of the QMainWindow class to initialize the basic functionality of the main window
        super().__init__()

        # Load the image from the given image path
        self.image = QPixmap(image_path)

        # Create a QLabel to display the image
        self.label = QLabel()
        self.label.setPixmap(self.image)
        # Set the alignment of the label to center
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.button = QPushButton("Apply")
        self.button.clicked.connect(self.execute)

        # Create a QVBoxLayout to hold the QLabel and QPushButton
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Add margin under the apply button
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        # Remove window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setStyleSheet("background-color: #19172D;")
        self.title_bar.setFixedHeight(30)
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("Box in the outer edges of pattern", self.title_bar)
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

        # Add line under the title bar
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        line.setLineWidth(1)
        line.setStyleSheet("color: #937CC2;")
        layout.addWidget(line)

        layout.addWidget(self.label)
        layout.addWidget(self.button)

        # Allow to choose structured area by pressing two opposite corners and draw a rectangle
        self.label.mousePressEvent = self.get_mouse_coords
        
        # Create a QWidget to hold the QVBoxLayout
        widget = QWidget()
        widget.setLayout(layout)
        # Set the QWidget as the central widget of the QMainWindow
        self.setCentralWidget(widget)
        self.setStyleSheet("QMainWindow {background-color: #19172D;}")
        with(open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r')) as f:
            self.setStyleSheet(f.read())
        
        # Enable dragging the window using the titlebar
        self.title_bar.mousePressEvent = self.start_drag
        self.title_bar.mouseMoveEvent = self.do_drag

        # Show the QMainWindow
        self.show()

    def start_drag(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def do_drag(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def get_mouse_coords(self, event):
        if not hasattr(self, 'x1'):
            self.x1 = event.pos().x()
            self.y1 = event.pos().y()
        elif not hasattr(self, 'x2'):
            self.x2 = event.pos().x()
            self.y2 = event.pos().y()
            global ulx, drx, uly, dry
            ulx, drx, uly, dry = self.x1, self.x2, self.y1, self.y2

            # Draw a rectangle
            self.top = Rectangle(self, abs(self.x2 - self.x1), abs(self.y2 - self.y1))
            self.top.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.top.show()
        else:
            self.x1 = event.pos().x()
            self.y1 = event.pos().y()
            del self.x2
            del self.y2
            self.top.close()
            self.top = None

    def execute(self):
        if hasattr(self, 'x2'):
            self.close()
            analyze_data()
        else:
            pass

# Add a grid to the plot
class Rectangle(QtWidgets.QFrame):
    def __init__(self, parent, width, height):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        
        self.setStyleSheet("QFrame {border: 5px dashed #937CC2;background-color: none;}")
        self.setFrameStyle(QtWidgets.QFrame.Shape.Box | QtWidgets.QFrame.Shadow.Plain)
        self.setLineWidth(2)
        self.setGeometry(min(parent.x1, parent.x2), min(parent.y1, parent.y2)+35, width, height)

def analyze_data():
    # Load the tmp_dat_file object from the file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)

    os.remove(tmp_dat_file.file_path_name)

    X, Y = np.meshgrid(tmp_dat_file.x, tmp_dat_file.y)

    idx_ulx = int(ulx * len(X[0, :]) / tmp_dat_file.img_scale)
    idx_drx = int(drx * len(X[0, :]) / tmp_dat_file.img_scale)
    idx_uly = int(uly * len(X[:, 0]) / tmp_dat_file.img_scale)
    idx_dry = int(dry * len(X[:, 0]) / tmp_dat_file.img_scale)

    # Rotate indices based on the angle    
    x1_index = min(idx_ulx, idx_drx)
    x2_index = max(idx_ulx, idx_drx)
    y1_index = min(idx_uly, idx_dry)
    y2_index = max(idx_uly, idx_dry)

    # Crop the data
    tmp_dat_file.mask = tmp_dat_file.Z[y1_index:y2_index, x1_index:x2_index]

    x = tmp_dat_file.x[x1_index:x2_index]
    y = tmp_dat_file.y[y1_index:y2_index]

    X, Y = np.meshgrid(x, y)
    XX = X[np.where(~np.isnan(tmp_dat_file.mask))].flatten()
    YY = Y[np.where(~np.isnan(tmp_dat_file.mask))].flatten()
    Z = tmp_dat_file.mask[np.where(~np.isnan(tmp_dat_file.mask))].flatten()

    x1, y1, z1 = XX.flatten(), YY.flatten(), Z.flatten()

    X_data = np.vstack([x1, y1]).T
    Y_data = z1

    reg = linear_model.LinearRegression().fit(X_data, Y_data)


    # Subtract fitted plane from tmp_dat_file.Z and tmp_dat_file.mask
    X, Y = np.meshgrid(x, y)
    residuals = tmp_dat_file.mask - (reg.coef_[0]*X + reg.coef_[1]*Y + reg.intercept_)
    rmse = np.sqrt(np.mean((residuals**2).flatten(), axis=0)) # RMSE sqrt(mean(residuals^2))

    plt.figure()
    plt.imshow(residuals, cmap='viridis',extent=[min(x), max(x), min(y), max(y)], aspect=len(x)/len(y))
    plt.title('Roughness analysis\nRMSE: {:.1f} nm'.format(rmse), fontsize=16)  # title
    plotopts(x, y, residuals)
    plt.gcf().set_size_inches(8, 8)
    plt.show()