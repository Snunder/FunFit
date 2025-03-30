"""Built-in modules"""
import os

"""External modules"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QApplication
from PyQt6.QtGui import QIcon

"""Internal modules"""
try:
    from FunFit.Functions.helpers import display_data, error_message, add_export_button
    import FunFit.Functions.Load_dataformats as read
except:
    from Functions.helpers import display_data, error_message, add_export_button
    import Functions.Load_dataformats as read

def load_data(self=None, file_path=None):
    # Open a file dialog to select the file to plot
    if not file_path:
        Dialog_window = QFileDialog()
        Dialog_window.setWindowTitle("Select the file to plot")
        Dialog_window.setFileMode(QFileDialog.FileMode.ExistingFile)
        Dialog_window.setNameFilter("All Files (*);;NanoFrazor Files (*.top);;NanoScope Files (*.spm)")
        Dialog_window.setOption(QFileDialog.Option.DontUseNativeDialog)
        Dialog_window.setWindowIcon(QIcon(os.path.join(self.current_dir, "GUI", "icon_window.png")))
        Dialog_window.setDirectory(os.path.dirname(self.current_dir) + "/tests")
        if Dialog_window.exec() == QFileDialog.DialogCode.Accepted:
            FileName = Dialog_window.selectedFiles()[0]
    else: 
        FileName = file_path
    try:
        with open(FileName, 'r') as file:
            first_lines = [file.readline().strip() for _ in range(20)]  # Read the first 20 lines and remove newline characters
    except: return
    
    # Delete all attributes related to the previous data
    for attr in ['Raw_x', 'Raw_y', 'Raw_Z', 'corrected_data', 'inside_image', 'outside_image', 'selection_polygon', 'overlay', 'image']:
        if hasattr(self, attr):
            try: getattr(self, attr).deleteLater() if attr in ['overlay', 'image'] else delattr(self, attr)
            except: pass

    # Checks for both SxM Image file and NanoFrazor in the first lines of the file (for nanofrazor .top files)
    if any('SxM Image file' in line for line in first_lines) and any('NanoFrazor' in line for line in first_lines) and any('Version: 1.0' in line for line in first_lines):
        FileType = 'NanoFrazor.top'
    # Checks for the version of the file (for NanoScope .spm files)
    elif '\\Version: 0x09400202' in first_lines:
        FileType = 'NanoScope.spm'
    elif 'ISO/TC 201 SPM data transfer format' in first_lines:
        FileType = 'Gwyddion.spm'
    elif '# Channel: ZSensor' in first_lines:
        FileType = 'FunFit.txt'
    else:
        error_message("Unknown file type")
        return
    # check if the file is a .top file or a .spm file
    if FileType == 'NanoFrazor.top':
        self.Raw_x, self.Raw_y, self.Raw_Z, self.x_scale, self.y_scale = read.nanofrazorTOP(FileName)
    elif FileType == 'NanoScope.spm':
        self.Raw_x, self.Raw_y, self.Raw_Z, self.x_scale, self.y_scale = read.nanoscopeSPM(FileName)
    elif FileType == 'Gwyddion.spm':
        self.Raw_x, self.Raw_y, self.Raw_Z, self.x_scale, self.y_scale = read.gwyddionSPM(FileName)
    elif FileType == 'FunFit.txt':
        self.Raw_x, self.Raw_y, self.Raw_Z, self.x_scale, self.y_scale = read.funfitTXT(FileName)

    # Display the data in main window
    self.image.deleteLater() if hasattr(self, 'image') else None
    self.image = display_data(self)
    self.centralWidget().layout().addWidget(self.image, 1, 1, -1, Qt.AlignmentFlag.AlignTop)
    add_export_button(self) # Add export button to main window
    
    # Wayland update delays
    QApplication.processEvents()  # Ensure UI updates immediately
    # self.resize(self.image.pixmap().size())  # Explicitly resize to the image size

    try: del self.corrected_data
    except AttributeError: pass
    return