import numpy as np
import matplotlib.pyplot as plt
import pickle
from scipy.ndimage import rotate
import copy
import cv2
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QMessageBox, QHBoxLayout
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt


def level_data(type = 'median'):    
    # Load the tmp_dat_file object from a file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)

    # Set coordinates of structured area to ignore
    tmp = rotate(tmp_dat_file.mask, angle=tmp_dat_file.angle, reshape=True, order=0, mode='constant', cval=np.inf)

    # Find all indexes of tmp which are not inf
    idx2 = np.where(np.isfinite(tmp))
    Z = tmp[min(idx2[0]):max(idx2[0]), min(idx2[1]):max(idx2[1])]

    # Find indexes of nan values in the data corresponding to the structured area
    idx = np.where(np.isnan(Z))
    save_data = copy.deepcopy(tmp_dat_file.Z)
    tmp_dat_file.Z[idx] = np.nan

    if type == 'raw':
        tmp_dat_file.Z = tmp_dat_file.Z_raw

    if type == 'median':
        # Median filter to level the data
        # Calculate the median of each line
        tmp_dat_file.medians = np.zeros(len(tmp_dat_file.Z))
        
        # For each line calculate the median value
        for i in range(len(tmp_dat_file.Z)):
            idx2 = np.where(~np.isnan(tmp_dat_file.Z[i]))
            tmp_dat_file.medians[i] = np.median(tmp_dat_file.Z[i][idx2])

        tmp_dat_file.Z[idx] = save_data[idx]

        # Use a simple median filter to level
        tmp_dat_file.Z = tmp_dat_file.Z - tmp_dat_file.medians[:, np.newaxis]

    elif type == 'median diff':
        # Define array to store median values
        median_diff = np.zeros(len(tmp_dat_file.Z))
        # For each line subtract the median value of difference between vertical neighbor pixels in two rows
        for i in range(len(tmp_dat_file.Z)-1):
            idx2 = np.where(~np.isnan(tmp_dat_file.Z[i]))
            
            # Calculate the differences between vertical neighbor pixels in two rows i and i+1
            differences = tmp_dat_file.Z[i] - tmp_dat_file.Z[i+1]

            # Calculate the median of the differences
            median_diff[i+1] = np.median(differences[np.where(~np.isnan(differences))])
            
            # Subtract the median difference from each element in the row
            tmp_dat_file.Z[i+1, :] = tmp_dat_file.Z[i+1, :] + median_diff[i+1]

        # Subtract the median difference from all rows
        save_data = save_data + median_diff[:, np.newaxis]
        tmp_dat_file.Z = save_data

    tmp_dat_file.mask = copy.deepcopy(tmp_dat_file.Z)
    tmp_dat_file.mask[idx] = np.nan
    tmp_dat_file.indexes = idx
    return tmp_dat_file

# Define a class that inherits from QMainWindow
class LevelTypePicker(QMainWindow):
    def __init__(self, image_path):
        # Call the __init__ method of the QMainWindow class to initialize the basic functionality of the main window
        super().__init__()

        global type_chosen
        type_chosen = False
        
        # Create a QVBoxLayout to hold the QLabel and QPushButton
        layout = QVBoxLayout()
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        titlebar = QWidget(self)
        titlebar.setObjectName('titlebar')
        titlebar.setFixedHeight(30)
        titlebar_layout = QHBoxLayout(titlebar)
        titlebar_layout.setContentsMargins(0, 0, 0, 0)
        titlebar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        titlebar_layout.addStretch()
        self.title_label = QLabel("Choose leveling type")
        self.title_label.setStyleSheet("color: white; font-size: 16px; font-family: Verdana;")
        titlebar_layout.addWidget(self.title_label)
        titlebar_layout.addStretch()
        titlebar.setStyleSheet("background-color: #19172D;")
        self.close_button = QPushButton()
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
        self.close_button.clicked.connect(lambda checked: self.close())
        titlebar_layout.addWidget(self.close_button)
        
        layout.addWidget(titlebar)
        layout.setContentsMargins(0, 0, 0, 5)
        buttons = [
            ("Raw data", "raw"),
            ("Median", 'median'),
            ("Median diff", 'median diff')
        ]
        for text, method in buttons:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, type=method: self.choose_type(type))
            layout.addWidget(button)

        self.button_exec = QPushButton("Apply")
        self.button_exec.clicked.connect(
            lambda checked: self.execute()
        )

        layout.addWidget(self.button_exec)
        # Create a QWidget to hold the QVBoxLayout
        widget = QWidget()
        widget.setLayout(layout)
        # Set the QWidget as the central widget of the QMainWindow
        self.setCentralWidget(widget)

        with(open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r')) as f:
            self.setStyleSheet(f.read())
        
        # Enable dragging the window on the titlebar
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.dragPos = event.globalPosition().toPoint()
        
        def mouseMoveEvent(event):
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
                self.dragPos = event.globalPosition().toPoint()
                event.accept()
        
        titlebar.mousePressEvent = mousePressEvent
        titlebar.mouseMoveEvent = mouseMoveEvent
        
        # Show the QMainWindow
        self.show()


    def choose_type(self, type):
        global type_chosen
        type_chosen = True
        self.data = level_data(type)

        plt.imsave(self.data.file_path_name, self.data.Z, cmap='gray')
        img = cv2.resize(cv2.imread(self.data.file_path_name), (self.data.img_scale, self.data.img_scale))
        cv2.imwrite(self.data.file_path_name, img)

        self.image = QLabel()
        self.image.setPixmap(QPixmap(self.data.file_path_name))
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        x = self.centralWidget().layout()
        if x.count() > 5:
            x.itemAt(x.count() - 2).widget().deleteLater()
        x.insertWidget(4, self.image)

        return 

    def execute(self):
        if type_chosen:
            tmp_dat_file = self.data
            # Save the tmp_dat_file object to a file
            with open('tmp_dat_file.pkl', 'wb') as f:
                pickle.dump(tmp_dat_file, f)
            self.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Leveling type not chosen")
            msg.setWindowTitle("Error")
            msg.exec()
            return


def main():

    # Open data file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)

    app = QApplication([])
    window = LevelTypePicker(tmp_dat_file.file_path_name)
    app.exec()

    return

if __name__ == "__main__":
    main()