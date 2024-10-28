import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from PyQt6 import QtWidgets
import pickle
import copy

class StructureFinder(QMainWindow):
    def __init__(self, image_path):
        super().__init__()

        # Set up the image label
        self.image = QPixmap(image_path)
        self.label = QLabel()
        self.label.setPixmap(self.image)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.button = QPushButton("Apply")
        self.button.clicked.connect(self.execute)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 5, 5)  # Add margin under the apply button
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Set up the mouse events for square selection
        self.label.mousePressEvent = self.get_mouse_coords

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Load and apply the stylesheet
        with open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r') as f:
            self.setStyleSheet(f.read())
        # Set frameless window and create title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = QWidget(self)
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setStyleSheet("background-color: #19172D;")
        self.title_bar.setFixedHeight(30)
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("Click to box in the outer edges of pattern", self.title_bar)
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
        self.title_bar_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(widget)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # Track variables for dragging
        self.dragging = False
        self.drag_position = None

        # Connect the title bar's mouse events for dragging
        self.title_bar.mousePressEvent = self.start_drag
        self.title_bar.mouseMoveEvent = self.drag_window
        self.title_bar.mouseReleaseEvent = self.stop_drag

        self.show()

    def start_drag(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def drag_window(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def stop_drag(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    def get_mouse_coords(self, event):
        # Square selection logic
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
        self.setGeometry(min(parent.x1, parent.x2), min(parent.y1, parent.y2)+35, width, height+5)

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
    tmp_dat_file.x1_index = int( min(idx_ulx, idx_drx) * len(X[0, :]) / len(X[0, :]) )
    tmp_dat_file.x2_index = int( max(idx_ulx, idx_drx) * len(X[0, :]) / len(X[0, :]) )
    tmp_dat_file.y1_index = int( min(idx_uly, idx_dry) * len(X[:, 0]) / len(X[:, 0]) )
    tmp_dat_file.y2_index = int( max(idx_uly, idx_dry) * len(X[:, 0]) / len(X[:, 0]) )

    x1_index = min(idx_ulx, idx_drx)
    x2_index = max(idx_ulx, idx_drx)
    y1_index = min(idx_uly, idx_dry)
    y2_index = max(idx_uly, idx_dry)

    tmp_dat_file.data = tmp_dat_file.Z[y1_index:y2_index, x1_index:x2_index]
    tmp_dat_file.dataX = X[y1_index:y2_index, x1_index:x2_index]
    tmp_dat_file.dataY = Y[y1_index:y2_index, x1_index:x2_index]

    # Crop the data
    tmp_dat_file.mask = copy.deepcopy(tmp_dat_file.Z)
    tmp_dat_file.mask[y1_index:y2_index, x1_index:x2_index] = np.nan

    # Save the tmp_dat_file object to a file
    with open('tmp_dat_file.pkl', 'wb') as f:
        pickle.dump(tmp_dat_file, f)

# Main function
def main():
    # Load the tmp_dat_file object from the file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)

    plt.imsave(tmp_dat_file.file_path_name, tmp_dat_file.Z, cmap='gray')
    img = cv2.resize(cv2.imread(tmp_dat_file.file_path_name), (tmp_dat_file.img_scale, tmp_dat_file.img_scale))
    cv2.imwrite(tmp_dat_file.file_path_name, img)

    # Open window for finding structured area
    app = QApplication([])
    window = StructureFinder(tmp_dat_file.file_path_name)
    app.exec()

    QApplication.closeAllWindows()

if __name__ == "__main__":
    main()