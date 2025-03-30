"""External modules"""
import numpy as np

# NANOFRAZOR TOP OUTPUT
def nanofrazorTOP(filename):
    with open(filename,'r', errors="ignore") as file:
        header = []
        for line in file:
            header.append(line.strip())
            if '[Header end]' in line:
                break
    headersize, columnsize, rowsize, x_scale, y_scale = 0, 0, 0, 0, 0
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
        Z = Z.reshape((rowsize, columnsize))
        Z = np.flipud(Z)
    return x, y, Z, x_scale, y_scale

# NANOSCOPE SPM NATIVE OUTPUT
def nanoscopeSPM(filename):
    with open(filename, 'r', errors="ignore") as file:
        header = []
        for line in file:
            header.append(line.strip())
            if '*File list end' in line:
                break
    headersize, columnsize, rowsize, x_scale, y_scale = 0, 0, 0, 0, 0
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
        elif 'Aspect Ratio:' in line:
            aspect_ratio = line.split(' ')[2]
            try: ratio = float(aspect_ratio.split(':')[0])/float(aspect_ratio.split(':')[1])
            except: ratio = 1
        elif 'Scan Size:' in line:
            try: x_scale, y_scale = float(line.split(' ')[2]), float(line.split(' ')[3])
            except: pass
        elif '\\@2:Z offset:' in line:
            break
    x = np.linspace(0, y_scale/ratio, rowsize)
    y = np.linspace(0, x_scale, columnsize)
    with open(filename, 'rb') as file:
        file.seek(headersize)
        Z = np.fromfile(file, dtype='<i4', count=columnsize*rowsize)
        Z = Z.reshape((columnsize,rowsize))
        Z = np.flipud(Z)
        Z = Z*zscale_nmV*zscale_VLSB/pow(2, 32)
    return x, y, Z, x_scale, y_scale/ratio

# GWYDDION SPM OUTPUT
def gwyddionSPM(filename):
    with open(filename, 'rb') as file:
        header = []
        while True:
            line = file.readline().decode('ascii', errors='ignore').strip()
            header.append(line)
            if 'end of header' in line:
                break
        data = []
        while True:
            line = file.readline().decode('ascii', errors='ignore').strip()
            if 'end of experiment' in line:
                break
            data.append(line)

    for i, line in enumerate(header):
        if 'top to bottom' in line and i + 2 < len(header):
            columnsize = int(header[i + 1])
            rowsize = int(header[i + 2])
            x_scale = float(header[i + 5])*1e6
            y_scale = float(header[i + 6])*1e6

    x = np.linspace(0, x_scale, columnsize)
    y = np.linspace(0, y_scale, rowsize)

    # Use numpy to speed up the data processing
    Z = np.zeros(columnsize*rowsize)
    data = np.array(data)
    data = np.char.replace(data, 'e-', 'e-')
    Z = data.astype(np.float64)
    Z = Z.reshape((rowsize, columnsize))
    return x, y, Z, x_scale, y_scale

# FUNFIT OUTPUT
def funfitTXT(filename):
    with open(filename, 'r') as file:
        data = file.readlines()
    header = [line for line in data if line.startswith('#')]
    for i, line in enumerate(header):
        if 'Width:' in line:
            x_scale = float(line.split(' ')[2])
        elif 'Height:' in line:
            y_scale = float(line.split(' ')[2])
    data = data[len(header):]
    Z = np.zeros(shape=(len(data),len(data[0].split())))
    for i, line in enumerate(data):
        Z[i] = np.array(line.split())
    x = np.linspace(0, x_scale, Z.shape[1])
    y = np.linspace(0, y_scale, Z.shape[0])
    return x, y, Z*1e9, x_scale, y_scale