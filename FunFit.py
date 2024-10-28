# Libraries: PyQt6, matplotlib, numpy, math, cv2, os, pickle, re, copy, sys
import os
import matplotlib.pyplot as plt
import pickle
import cv2
import numpy as np
import math
import re
import copy


# Set path for helper function scripts
functions_path = os.getcwd() + "\\Functions\\"

# Import specific functions
from Functions.helpers import plotopts
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QDialog, QHBoxLayout, QFrame
from PyQt6.QtGui import QPixmap, QIcon, QScreen
import sys
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt, QProcess, QCoreApplication, QSize 
from random import randint

# Import the functions
import Functions.Load as Load
import Functions.Find_structs as Find_structs
import Functions.Level_median as Level_median
import Functions.Fit_plane as Fit_Plane
import Functions.Cross_sections as Cross_sections
import Functions.Function_fitting as Function_fitting
import Functions.Function_presets as Function_presets
import Functions.Roughness as Roughness
import Functions.functionoffset_input as foi
import Functions.Bitmap_generator as Bitmap_generator

global loaded 
loaded = False

# Function caller main window
class FunctionCaller(QMainWindow):
    def __init__(self, parent):
        super().__init__()

        self.setWindowTitle("")
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Load external stylesheet
        with open(os.getcwd() + '/GUI/main_stylesheet.qss', 'r') as f:
            self.setStyleSheet(f.read())
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Ensure no spacing between title bar and separator

        # Custom title bar
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 0)
        title_bar.setLayout(title_bar_layout)
        title_bar.setStyleSheet("background-color: #19172D")  # Set background color

        # Title text
        title_text = QLabel("Select function")
        title_text.setStyleSheet("color: white; font-size: 16px; padding-left: 10px; font-family: 'Verdana';")
        title_bar_layout.addWidget(title_text)

        # Spacer to push close button to the right
        title_bar_layout.addStretch()

        # Close button with style
        close_button = QPushButton()
        close_button.setFixedSize(40, 30)
        close_button.setStyleSheet("""
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
                qproperty-iconSize: 20px;
            }
            QPushButton:hover {
                background-color: #FF3B3B;
            }
            QPushButton:pressed {
                background-color: #FF1C1C;
            }
        """)
        close_button.setIcon(QIcon(QPixmap(os.getcwd()+"/GUI/icon_close.png")))
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)

        # Add title bar to main layout
        main_layout.addWidget(title_bar)

        # Separator
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #4B4587;")
        main_layout.addWidget(separator)

        # Buttons for each function
        self.qc_button = QPushButton("Quasicrystal")
        self.qc_button.clicked.connect(lambda checked: parent.fit_type_identifier(0))
        self.qc_button.setStyleSheet("margin-top: 5px; font-family: 'Verdana';")
        main_layout.addWidget(self.qc_button)
        

        fs_button = QPushButton("Fourier series")
        fs_button.clicked.connect(lambda checked: parent.fit_type_identifier(1))
        # main_layout.addWidget(fs_button)

        custom_button = QPushButton("Custom function")
        custom_button.clicked.connect(lambda checked: parent.fit_type_identifier(2))
        custom_button.setStyleSheet("margin-bottom: 10px; font-family: 'Verdana';")
        main_layout.addWidget(custom_button)

        # Set main widget as central widget
        self.setCentralWidget(main_widget)
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Function Caller")
        self.setGeometry(100, 100, 300, 200)
        l3 = QVBoxLayout()
        l2 = QHBoxLayout()

        l = QVBoxLayout()
        l.setContentsMargins(0, 0, 0, 0)  # Remove margins
        l.setSpacing(0)  # Remove spacing between elements
        l3.setContentsMargins(0, 0, 0, 0)  # Remove margins
        l3.setSpacing(0)  # Remove spacing between elements

        # Remove window frame for a custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Custom title bar
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(10, 10, 10, 10)  # Customize margins as needed
        title_bar.setLayout(title_bar_layout)
        title_bar.setStyleSheet("background-color: #19172D;")  # Set background color

        # Title icon
        title_icon = QLabel()
        title_icon.setPixmap(QPixmap(os.getcwd()+"/GUI/icon.png").scaled(100, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title_bar_layout.addWidget(title_icon)
        
        # Add a spacer to push the close button to the right
        title_bar_layout.addStretch()

        # Add mouse events to the title bar for dragging
        title_bar.mousePressEvent = self.mousePressEvent
        title_bar.mouseMoveEvent = self.mouseMoveEvent

        # Close button
        close_button = QPushButton()
        close_button.setFixedSize(40, 30)
        close_button.setStyleSheet("""
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
        close_button.setIcon(QIcon(QPixmap(os.getcwd()+"/GUI/icon_close.png")))
        close_button.clicked.connect(self.close)
        title_bar_layout.addWidget(close_button)

        # Add title bar to the layout
        l3.addWidget(title_bar)

        # Exact border separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(2)
        l3.addWidget(separator)

        # Add buttons for each function
        buttons = [
            ("  Load files", os.getcwd()+"/GUI/icon_load.png", self.load_function),
            ("  Find structured area", os.getcwd()+"/GUI/icon_findarea.png", self.find_struct),
            ("  Step line correction", os.getcwd()+"/GUI/icon_linecorrection.png", self.level_data),
            ("  Plane levelling", os.getcwd()+"/GUI/icon_planelevel.png", self.fit_plane),
            ("  Plot line cuts", os.getcwd()+"/GUI/icon_linecut.png", self.cross_section),
            ("  Fit functions", os.getcwd()+"/GUI/icon_functionfit.png", self.fit_functions),
            ("  Roughness of flat area", os.getcwd()+"/GUI/icon_surfaceroughness.png", self.roughness_fit),
            ("  Bitmap generator", os.getcwd()+"/GUI/icon_bitmap.png", self.bitmap_generator)
        ]
        for text, icon_path, func in buttons:
            button = QPushButton(text)
            if icon_path:
                icon = QIcon(QPixmap(icon_path))
                button.setIcon(icon)
                button.setIconSize(QSize(32, 32))
            button.clicked.connect(lambda checked, f=func: f())
            l.addWidget(button)
            # Increase margin above the first button
            if text == "  Load files":
                button.setStyleSheet("margin-top: 10px;")
            # Increase margin for last button
            if text == "  Bitmap generator":
                button.setStyleSheet("margin-bottom: 10px;")
            #button.setStyleSheet("background-color: #3A3668;")
        l2.addLayout(l)
        global widget_num
        widget_num = len(l2)

        w = QWidget()
        w.setLayout(l2)
        q = QWidget()
        q.setLayout(l3)
        self.setMenuWidget(q)
        self.setCentralWidget(w)

        with open(os.getcwd() + '/GUI/main_stylesheet.qss', 'r') as f:
            self.setStyleSheet(f.read())
        separator.setStyleSheet("background-color: #4B4587; border: none; margin: 0px; padding: 0px;")
        separator.update()
        separator.repaint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def load_function(self):
        try:
            Load.main(self)
        except:
            self.not_loaded()
            return

        global loaded
        loaded = True
        self.create_bitmap = False

        # Load the tmp_dat_file object from the file
        with open('tmp_dat_file.pkl', 'rb') as f:
            tmp_dat_file = pickle.load(f)
        
        plt.imsave(tmp_dat_file.file_path_name, tmp_dat_file.Z, cmap='gray')
        img = cv2.resize(cv2.imread(tmp_dat_file.file_path_name), (tmp_dat_file.img_scale, tmp_dat_file.img_scale))
        cv2.imwrite(tmp_dat_file.file_path_name, img)

        self.image = QLabel()
        self.image.setPixmap(QPixmap(tmp_dat_file.file_path_name))
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        x = self.centralWidget().layout()
        if x.count() > widget_num:
            x.itemAt(x.count() - 1).widget().deleteLater()
        x.addWidget(self.image)

    def find_struct(self):
        if loaded:
            # Load the tmp_dat_file object from the file
            with open('tmp_dat_file.pkl', 'rb') as f:
                tmp_dat_file = pickle.load(f)
            
            plt.imsave(tmp_dat_file.file_path_name, tmp_dat_file.Z, cmap='gray')
            img = cv2.resize(cv2.imread(tmp_dat_file.file_path_name), (tmp_dat_file.img_scale, tmp_dat_file.img_scale))
            cv2.imwrite(tmp_dat_file.file_path_name, img)

            self.w = Find_structs.StructureFinder(tmp_dat_file.file_path_name)

            self.w.button.clicked.connect(self.on_find_struct_window_closed)

            # Save the tmp_dat_file object to a file
            with open('tmp_dat_file.pkl', 'wb') as f:
                pickle.dump(tmp_dat_file, f)

        else:
            self.not_loaded()
        self.update()

    def on_find_struct_window_closed(self):
        if not hasattr(self.w, 'x2'):
            self.not_struct_chosen()
        else:
            print("Implement rectangle drawing on figure in main window")

    def level_data(self):
        if loaded:
            # Open data file
            with open('tmp_dat_file.pkl', 'rb') as f:
                tmp_dat_file = pickle.load(f)
            self.w = Level_median.LevelTypePicker(tmp_dat_file.file_path_name)

            self.w.button_exec.clicked.connect(self.on_level_data_window_closed)

        else:
            self.not_loaded()
        self.update()

    def on_level_data_window_closed(self):
        # Load the tmp_dat_file object from the file
        with open('tmp_dat_file.pkl', 'rb') as f:
            tmp_dat_file = pickle.load(f)
        
        plt.imsave(tmp_dat_file.file_path_name, tmp_dat_file.Z, cmap='gray')
        img = cv2.resize(cv2.imread(tmp_dat_file.file_path_name), (tmp_dat_file.img_scale, tmp_dat_file.img_scale))
        cv2.imwrite(tmp_dat_file.file_path_name, img)


        self.image = QLabel()
        self.image.setPixmap(QPixmap(tmp_dat_file.file_path_name))
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        x = self.centralWidget().layout()
        if x.count() > widget_num:
            x.itemAt(x.count() - 1).widget().deleteLater()
        x.addWidget(self.image)

    def fit_plane(self):
        if loaded:
            Fit_Plane.main()

        else:
            self.not_loaded()
        self.update()

    def cross_section(self):
        if loaded:
            Cross_sections.main()

        else:
            self.not_loaded()
        self.update()

    def fit_functions(self):
        if loaded:
            self.w = FunctionCaller(self)
        else:
            self.not_loaded()

    def fit_type_identifier(self, functiontype):
        types = ["quasicrystal", "fourier_series", "custom"]
        self.w.close()

        if types[functiontype] == "quasicrystal":
            self.w = Function_presets.InputDialog_QC()
            if self.create_bitmap:
                self.w.button.clicked.connect(
                    lambda checked: self.bitmap(functiontype)
                    )
                self.create_bitmap = False
            else:
                self.w.button.clicked.connect(
                    lambda checked: self.on_input_window_closed(functiontype)
                    )
            self.w.show()
        elif types[functiontype] == "custom":
            self.w = Function_presets.InputDialog_Custom()
            if self.create_bitmap:
                self.w.button.clicked.connect(
                    lambda checked: self.bitmap(functiontype)
                    )
                self.create_bitmap = False
            else:
                self.w.button.clicked.connect(
                    lambda checked: self.on_input_window_closed(functiontype)
                    )
            
            self.w.show()

    def on_input_window_closed(self, functiontype):
        # Remove when fourier series is implemented
        if functiontype == 1:
            functiontype = 2

        types = ["quasicrystal", "fourier_series", "custom"]

        global IC, crosshair, ax, background, extent, user_clicked

        if types[functiontype] == "quasicrystal":
            param_names = ['x0', 'y0', 'amplitude', 'wavelength', 'phase_shift', 'angle', 'offset']
            N_terms = int(self.w.N_terms.text())
            IC = [0]*len(param_names)
            if N_terms >= 4:
                self.ch = foi.OffsetFinder()
                self.ch.button.clicked.connect(
                    lambda checked: self.fit_functions_qc(N_terms, param_names)
                )
            else:
                IC[0] = 0
                IC[1] = 0
                IC[2:6] = [self.w.A.text(), self.w.lbd.text(), self.w.phi.text(), self.w.theta.text()]
                for i, param in enumerate(IC[2:6], start=2):
                    try:
                        IC[i] = eval(IC[i], {"np": np, "math": math})
                    except Exception as e:
                        # print(f"Invalid input for parameter '{param}': {e}")
                        IC[i] = 0  # Default to 0 if the input is invalid

                [fitting_model, IC, Bounds] = Function_presets.quasicrystal(N_terms, param_names, IC)
                Function_fitting.Function_fit("quasicrystal", fitting_model, IC, Bounds)

        elif types[functiontype] == "fourier_series":
            [fitting_model, IC, Bounds] = Function_presets.fourier_series()

        elif types[functiontype] == "custom":
            ## Open window for custom function input
            pass
            func_str = self.w.text_input.text()

            user_input_IC = self.w.user_input_IC

            param_names = Function_presets.extract_parameters(func_str)
            # Create the fitting function
            fitting_model = Function_presets.create_fitting_function(func_str, param_names)

            IC = [0]*len(param_names)

            IC = user_input_IC
            for i, param in enumerate(IC[2:len(param_names)], start=2):
                try:
                    IC[i] = eval(IC[i], {"np": np, "math": math})
                except Exception as e:
                    # print(f"Invalid input for parameter '{param}': {e}")
                    IC[i] = 0  # Default to 0 if the input is invalid
            Bounds = ([-np.inf] * len(param_names), [np.inf] * len(param_names))

            # Split the function string into terms and check if all terms are non-periodic
            periodic = Function_presets.is_periodic_function(func_str)

            # If the function is periodic, the offset can be produced by a phase shift
            if periodic:
                Function_fitting.Function_fit("custom", fitting_model, IC, Bounds)
            else:
                self.ch = foi.OffsetFinder()
                self.ch.button.clicked.connect(
                    lambda checked: self.fit_functions_custom(fitting_model, IC, Bounds)
                )

    def fit_functions_qc(self, N_terms, param_names):
        IC = [0]*len(param_names)
        [x0,y0] = [self.ch.x0_plot, self.ch.y0_plot]
        IC[0] = x0
        IC[1] = y0
        IC[2:6] = [self.w.A.text(), self.w.lbd.text(), self.w.phi.text(), self.w.theta.text()]
        for i, param in enumerate(IC[2:6], start=2):
            try:
                IC[i] = eval(IC[i], {"np": np, "math": math})
            except Exception as e:
                # print(f"Invalid input for parameter '{param}': {e}")
                IC[i] = 0  # Default to 0 if the input is invalid

        [fitting_model, IC, Bounds] = Function_presets.quasicrystal(N_terms, param_names, IC)
        Function_fitting.Function_fit("quasicrystal", fitting_model, IC, Bounds)

    def fit_functions_custom(self, fitting_model, IC, Bounds):
        [x0,y0] = [self.ch.x0_plot, self.ch.y0_plot]
        IC[0] = x0
        IC[1] = y0
        Function_fitting.Function_fit("custom", fitting_model, IC, Bounds)

    def roughness_fit(self):
        if loaded:
            # Load the tmp_dat_file object from the file
            with open('tmp_dat_file.pkl', 'rb') as f:
                tmp_dat_file = pickle.load(f)
            
            plt.imsave(tmp_dat_file.file_path_name, tmp_dat_file.Z, cmap='gray')
            img = cv2.resize(cv2.imread(tmp_dat_file.file_path_name), (tmp_dat_file.img_scale, tmp_dat_file.img_scale))
            cv2.imwrite(tmp_dat_file.file_path_name, img)

            self.w = Roughness.StructureFinder(tmp_dat_file.file_path_name)

            self.w.button.clicked.connect(self.on_find_flat_window_closed)

            # Save the tmp_dat_file object to a file
            with open('tmp_dat_file.pkl', 'wb') as f:
                pickle.dump(tmp_dat_file, f)
        else:
            self.not_loaded()

    def bitmap_generator(self):
        self.create_bitmap = True
        self.w = FunctionCaller(self)

    def bitmap(self, functiontype):
        # Remove when fourier series is implemented
        if functiontype == 1:
            functiontype = 2

        types = ["quasicrystal", "fourier_series", "custom"]

        global IC, crosshair, ax, background, extent, user_clicked

        if types[functiontype] == "quasicrystal":
            param_names = ['x0', 'y0', 'amplitude', 'wavelength', 'phase_shift', 'angle', 'offset']
            N_terms = int(self.w.N_terms.text())
            IC = [0]*len(param_names)
            IC[0] = 0
            IC[1] = 0
            IC[2:6] = [self.w.A.text(), self.w.lbd.text(), self.w.phi.text(), self.w.theta.text()]
            for i, param in enumerate(IC[2:6], start=2):
                try:
                    IC[i] = eval(IC[i], {"np": np, "math": math})
                except Exception as e:
                    # print(f"Invalid input for parameter '{param}': {e}")
                    IC[i] = 0  # Default to 0 if the input is invalid

            [fitting_model, IC, Bounds] = Function_presets.quasicrystal(N_terms, param_names, IC)
            self.w = Bitmap_generator.InputDialog_BMP(self)
            self.w.button.clicked.connect(
                lambda checked, f=fitting_model, IC=IC: Bitmap_generator.Function_fit(self, f, IC, float(self.w.xsize.text()), float(self.w.ysize.text()), float(self.w.nm_px.text()))
            )

        elif types[functiontype] == "fourier_series":
            [fitting_model, IC, Bounds] = Function_presets.fourier_series()

        elif types[functiontype] == "custom":
            ## Open window for custom function input
            pass
            func_str = self.w.text_input.text()

            user_input_IC = self.w.user_input_IC

            param_names = Function_presets.extract_parameters(func_str)
            # Create the fitting function
            fitting_model = Function_presets.create_fitting_function(func_str, param_names)

            IC = [0]*len(param_names)

            IC = user_input_IC
            for i, param in enumerate(IC[2:len(param_names)], start=2):
                try:
                    IC[i] = eval(IC[i], {"np": np, "math": math})
                except Exception as e:
                    # print(f"Invalid input for parameter '{param}': {e}")
                    IC[i] = 0  # Default to 0 if the input is invalid
            Bounds = ([-np.inf] * len(param_names), [np.inf] * len(param_names))

            # If the function is periodic, the offset can be produced by a phase shift
            self.w = Bitmap_generator.InputDialog_BMP(self)
            self.w.button.clicked.connect(
                lambda checked, f=fitting_model, IC=IC: Bitmap_generator.Function_fit(self, f, IC, float(self.w.xsize.text()), float(self.w.ysize.text()), float(self.w.nm_px.text()))
            )


    def on_find_flat_window_closed(self):
        if not hasattr(self.w, 'x2'):
            self.not_struct_chosen()

    def not_loaded(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Data not loaded")
        msg.setWindowTitle("Error")
        msg.exec()

    def not_struct_chosen(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Structured area not chosen")
        msg.setWindowTitle("Error")
        msg.exec()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

    try:
        os.remove('tmp_dat_file.pkl')
    except:
        pass

    try:
        os.remove('tmp_img.png')
    except:
        pass

    loaded = False

    sys.exit()

if __name__ == "__main__":
    main()