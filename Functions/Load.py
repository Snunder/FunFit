import os
import numpy as np
# import matplotlib as mpl
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QFileDialog
from scipy.ndimage import rotate
# import sys
import cv2
import pickle
# from screeninfo import get_monitors
import ctypes
import platform
import subprocess

# Load data from the NanoFrazor or the AFM
def load_data(self=None):

    FileName = QFileDialog.getOpenFileName(
        caption="Select the file to plot",
        options=QFileDialog.Option.DontUseNativeDialog,
        filter="All Files (*);;NanoFrazor Files (*.top);;NanoScope Files (*.spm)"
    )[0]

    with open(FileName, 'r', errors="ignore") as file:
        first_lines = [file.readline().replace('\n', '') for _ in range(20)]  # Read the first 20 lines and remove newline characters

    # Checks for both SxM Image file and NanoFrazor in the first lines of the file (for nanofrazor .top files)
    if any('SxM Image file' in line for line in first_lines) and any('NanoFrazor' in line for line in first_lines) and any('Version: 1.0' in line for line in first_lines):
        FileType = 'NanoFrazor.top'
   
    # Checks for the version of the file (for NanoScope .spm files)
    elif '\\Version: 0x09400202' in first_lines:
        FileType = 'NanoScope.spm'
    else:
        raise ValueError("Unknown file type")
    # check if the file is a .top file or a .spm file
    if FileType == 'NanoFrazor.top':
        x, y, Z, x_scale, y_scale = headerdata_top(FileName)
    elif FileType == 'NanoScope.spm':
        x, y, Z, x_scale, y_scale = headerdata_spm(FileName)

    return x, y, Z, x_scale, y_scale

# Load .top files from the NanoFrazor
def headerdata_top(filename):
    with open(filename,'r', errors="ignore") as file:
        header = []
        for line in file:
            header.append(line.strip())
            if '[Header end]' in line:
                break

    headersize = 0
    columnsize = 0
    rowsize = 0
    x_scale = 0
    y_scale = 0

    for line in header:
        if 'Image header size:' in line:
            headersize = int(line.split(': ')[1])
        elif 'Number of columns:' in line:
            columnsize = int(line.split(': ')[1])
        elif 'Number of rows:' in line:
            rowsize = int(line.split(': ')[1])
        elif 'X Amplitude:' in line:
            x_scale = float(line.split(' ')[2]) * 1e-3 # In µm
        elif 'Y Amplitude:' in line:
            y_scale = float(line.split(' ')[2]) * 1e-3 # In µm

    x = np.linspace(0, x_scale, columnsize)
    y = np.linspace(0, y_scale, rowsize)

    with open(filename, 'rb') as file:
        file.seek(headersize)
        Z = np.fromfile(file, dtype=np.double)
        Z = Z.reshape((rowsize, columnsize)).transpose()
        Z = np.rot90(Z, 1)
        # Z = np.fliplr(Z.T)

    return x, y, Z, x_scale, y_scale

# Load .spm files from the AFM
def headerdata_spm(filename):
    with open(filename, 'r', errors="ignore") as file:
        header = []
        for line in file:
            header.append(line.strip())
            if '*File list end' in line:
                break

    headersize = 0
    columnsize = 0
    rowsize = 0
    x_scale = 0
    y_scale = 0

    for line in header:
        if 'Data offset:' in line:
            headersize = int(line.split(': ')[1])
        elif 'Samps/line:' in line:
            rowsize = int(line.split(': ')[1])
        elif 'Number of lines:' in line:
            columnsize = int(line.split(': ')[1])
        elif '\\@Sens. ZsensSens:' in line:
            zscale_nmV = float(line.split(' ')[3])
        elif '\\@2:Z scale:' in line:
            zscale_VLSB = float(line.split(' ')[7])
        elif 'Scan Size:' in line:
            try:
                x_scale = float(line.split(' ')[2])
                y_scale = float(line.split(' ')[3])
            except:
                pass
        elif '\\@2:Z offset:' in line:
            break

    x = np.linspace(0, y_scale, rowsize)
    y = np.linspace(0, x_scale, columnsize)

    with open(filename, 'rb') as file:
        file.seek(headersize)
        Z = np.fromfile(file, dtype='<i4', count=columnsize*rowsize)
        Z = Z.reshape((columnsize,rowsize)).transpose()
        Z = np.rot90(Z, 1)
        Z = Z*zscale_nmV*zscale_VLSB/pow(2, 32)

    return x, y, Z, x_scale, y_scale

# Define a class for loading, leveling and rotating data
class data_for_plot():
    def __init__(self):
        self.x1, self.x2, self.y1, self.y2 = 0, 0, 0, 0
        self.x, self.y, self.Z, self.x_scale, self.y_scale = load_data()
        # self.Z_level = line_by_line_leveling_median_diff(self.Z)
        self.mask = self.Z
        self.Z_raw = self.Z
        self.indexes = None
        self.data = self.Z
        X, Y = np.meshgrid(self.x, self.y)
        
        self.x1_index = 0
        self.x2_index = len(self.x)
        self.y1_index = 0
        self.y2_index = len(self.y)

        self.dataX = X
        self.dataY = Y
        self.Z_rot_data = None
        self.Z_rot_data_img = None

        # Set the scale of the image to width of the main display monitor
        if platform.system() == "Windows":
            user32 = ctypes.windll.user32
            screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        elif platform.system() == "Darwin":
            screensize = subprocess.check_output(["system_profiler", "SPDisplaysDataType"]).decode("utf-8")
            screensize = screensize.split('\n')
            for line in screensize:
                if 'Resolution' in line:
                    screensize = line.split(': ')[1].split('x')
            screensize = [int(''.join(filter(str.isdigit, screensize))) for screensize in screensize]

        self.img_scale = min(screensize) // 3

        self.temp_filename = 'tmp_img.png'
        self.file_path_name = os.path.join(os.getcwd(), self.temp_filename)

        plt.imsave(self.file_path_name, self.Z, cmap='gray')
        img = cv2.resize(cv2.imread(self.file_path_name), (self.img_scale, self.img_scale))
        cv2.imwrite(self.file_path_name, img)

        angle_input = 360
        self.Z_rot_data = rotate(self.Z, angle=-angle_input, reshape=True, order=0, mode='constant', cval=np.inf)
        self.Z_rot_data_img = rotate(self.Z, angle=-angle_input, reshape=True, order=0, mode='constant', cval=max(self.Z.flatten())*2)


        self.angle = 360#None#angle_input

# Main function
def main(parent=None):
    # Load pre etching data
    global self
    self = parent
    tmp_dat_file = data_for_plot()

    # Save the tmp_dat_file object to a file
    with open('tmp_dat_file.pkl', 'wb') as f:
        pickle.dump(tmp_dat_file, f)

    return

if __name__ == "__main__":
    main()