# FunFit

FunFit is a standalone software package designed to analyse AFM topography data of analytical functions in 3D. 

## COMPATIBILITY
This software was written and tested on Windows 10 (Version 22H2 OS build 19045.5011), Windows 11 (Version 23H2 OS build 22631.4317) and macOS Sequoia (Version 15.0.1).
It is **NOT** compatible with Linux.

The current version of the software can only read NanoFrazor .top (Version: 1.0) and NanoScope .spm files (Version: 0x09400202) currently, but will be expanded in the future.
It is currently not capable of exporting data in other formats than pythons standard plot-saving options (as images).

## Installation

The software can be downloaded by cloning
```bash
git clone https://github.com/Snunder/FunFit
```

For normal usage there is included a fuide for installing an executable version of the software (FunFit.exe) which simply starts the software. 

This file, in addition to demo data, takes up (~200MB) and should take less than 5 minutes to install on standard hardware and internet.

The entire code is open-source in accordance with the license and runs on Python with the external libraries.

The software package has been written using Python 3.12.4 or newer.

The libraries necessary for running the software is as follows:
| Package:      | Version:      |
| ------------- | ------------- |
| matplotlib    | 3.9.2         |
| cv2           | 4.10.0.84     |
| PyQt6         | (6.7.1)       |
| scipy         | (1.14.1)      |
| tkinter       | (0.1.0)       |
| sklearn       | (1.5.2)       |
| pyinstaller   | (6.10.0)      |

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install relevant packages.

```bash
pip install matplotlib
pip install opencv-python
pip install PyQt6
pip install scipy
pip install tk
pip install scikit-learn
pip install pyinstaller
git clone https://github.com/Snunder/FunFit.git
cd FunFit
```

```bash
pyinstaller --onefile -w < YOUR PATH >//FunFit.py
```

Running the script FunFit.py should start the software exactly as the executable file, once dependencies are downloaded.

## Usage

If running from terminal:

```bash
python "FunFit.py"
```

If compiling a standalone app using pyinstaller, use the executable file instead.

## DEMO
As the GUI is inherently simple with few options, the software should be self explanatory. However, here is a complete description on how to use properly use FunFit.

When running the script either from executable or directly from terminal a Graphics User Interface (GUI) will open.

![FunFit GUI](../main/Demo_data/Demo_imgs/main_window.png)

### LOAD:
Most functions require a subject dataset to run, which is loaded by clicking the "Load Files" button, which opens File Explorer such that the user can select an appropriate dataset. Here we have provided demo data which is available in the folder ![Demo_data](../main/Demo_data) for the user to try the functions.
Once the data is loaded, there are options of common data correction functions for AFM data, none of which are mandatory to run for the software to work.
If the user interrupts the process in the loading process, a pop-up will appear warning the user.

After loading the data, the loaded data will be shown in the main window

![FunFit GUI](../main/Demo_data/Demo_imgs/main_window_loaded.png)

### FIND STRUCTURED AREA:

For more accurate data analysis, the "Find structured area" button opens a prompt for the user to click twice which draws a rectangle.

![FunFit GUI](../main/Demo_data/Demo_imgs/find_structs.png)

This should enclose the patterned region, such that step-line correction and plane leveling algorithms are only performed on the flat plane surrounding the patterned region.
Additionally, the later "Plot Line Cuts" and "Fit Functions" features will only be performed on the area inside the marked rectangle.

### STEP LINE CORRECTION:
Standard of AFM pictures are step line artefacts, where this software includes the Median and Difference of Median algorithms for correcting these artefacts.
Clicking the "Step line correction" button opens a window where the user can choose between the two correction methods. The user is provided with a preview of the corrected data before applying the step line correction

![FunFit GUI](../main/Demo_data/Demo_imgs/find_structs.png)

After application the data shown in the main GUI window is updated.

### PLANE LEVELING:
Another standard "artefact" is a tilted sample when the image was taken. This is corrected by plane leveling.
Clicking the "Plane leveling" button fits the data outside the box marked in "Find structured area" (if existing) to a plane and subtracts this plane from all the data, such that the average flat plane is set to 0 and the image no longer tilts.

The function opens a figure window showing a sample of the data points and the fitted plane.

![FunFit GUI](../main/Demo_data/Demo_imgs/plane_fit.png)

### PLOT LINE CUTS:
This feature, as the name implies, plots line cuts of the current data. This opens 1 plot with 3 subfigures, the first of which is 20 evenly spaced y-axis line cuts. The second is the chosen area of corrected data. The third plot is an average across the y-axis along with standard deviation.

![FunFit GUI](../main/Demo_data/Demo_imgs/line_cuts.png)

### FIT FUNCTIONS:
Unique to this software is the option to fit 3D functions to topography data. By clicking the "fit functions" button, the user is prompted with two (soon to be expanded) different functions types: Quasi crystals and custom.

![FunFit GUI](../main/Demo_data/Demo_imgs/function_fit_opts.png)

Selecting the Quasi crystal option opens a new window with the fitting equation shown at the top as well as input fields for initial guesses of fitting parameters. These will in most cases be known by the user as the topography is a consequence of chosen parameters.

![FunFit GUI](../main/Demo_data/Demo_imgs/function_fit_QC.png)

Selecting the Custom function option instead opens another window with the fitting equation shown at the top with a input field for writing the custom equation to be used for fitting. The equation shown at the top will be updated while the user types to provide an idea of what will happen when applying the fit. When adding fitting parameter all necessary input fields for initial guesses will be created when necessary.

![FunFit GUI](../main/Demo_data/Demo_imgs/function_fit_custom.png)

After choosing fitting parameters, the software will try to make a fit based on the initial guesses. The underlying method is not perfect, so the better the guess, the more likely a good fit will be applied. When the software is done fitting, a plot will be shown with 2 rows of plot data. The top row is the real space data, while the bottom row is the Fourier transform of the data. First column is raw data of chosen area, the second column is fitted data and the third column is residual plots. A RMSE value is shown in the title description of the real-space residual plot.

![FunFit GUI](../main/Demo_data/Demo_imgs/function_fit_results.png)

### Roughness of flat area

In addition to fitting the data to a specific function, the user can also calculate roughness of flat surfaces. This function opens a window like the **Find structured area** function. Here a flat area is chosen instead.

![FunFit GUI](../main/Demo_data/Demo_imgs/roughness_area.png)

When applying, a plane will be fitted to the data, and the RMSE value of this plot is directly linked to the surface roughness of the sample given the initial chosen area is flat. The function opens a plot showing the error and a RMSE value.

![FunFit GUI](../main/Demo_data/Demo_imgs/roughness_fit.png)

### Bitmap generator

Since this software is meant to be used for topography data, an initial bitmap mask for use in i.e. NanoFrazor software can be generated. The bitmap generator has options for creating bitmaps corresponding to the fitting function. When a function and parameters for the bitmap has been chosen, the user will be prompted for desired size in the x-, and y-direction as well as the size of each pixel. 

![FunFit GUI](../main/Demo_data/Demo_imgs/bitmap_generator_size.png)

The user will then be prompted for a directory for saving the bitmap file, and a plot of the created bitmap will be shown.

![FunFit GUI](../main/Demo_data/Demo_imgs/bitmap_generator_dir.png)

## Troubleshooting

If you encounter any issues while using FunFit, please refer to the [GitHub Issues](https://github.com/Snunder/FunFit/issues) page to report bugs or request help from the community.


## License

[GNU General Public License](https://web.archive.org/web/20160316065455/https://opensource.org/licenses/gpl-3.0)

