# FunFit

FunFit is a standalone software package designed to analyse SPM topography data of analytical functions in 3D. 

## COMPATIBILITY
This software was written and tested on Windows 10 (Version 22H2 OS build 19045.5011), Windows 11 (Version 23H2 OS build 22631.4317), macOS Sequoia (Version 15.3.2) and Ubuntu (Version 24.04.2).

The current version of the software can read the following file types:

| Origin:       | File type:    | Version:          |
| ------------- | ------------- | ----------------- |
| NanoFrazor    | .top          | 1.0               |
| NanoScope     | .spm          | 0x09400202        |
| Gwyddion      | .spm          | ISO/TC 201 SPM    |
| Gwyddion      | .txt          | ASCII data matrix |
| FunFit        | .txt          | 0.1.0             |

Additionally, FunFit supports export of data in *.txt* compatible with e.g. Gwyddion. Data can also be exported as graphics (*.png*, *.pdf*, *.svg*). Bitmaps (often used as masks for nanofabrication) created using FunFit will be saved as *.bmp* files.

**NB!** Rotated data from FunFit cannot be read by other softwares.

## Installation

For normal usage this package includes a guide for installing an executable version of the software (FunFit) which simply starts the software.\
This file, in addition to demo data, takes up (~200MB) and should take less than 5 minutes to install on standard hardware and internet.

The entire code is open-source in accordance with the [license](LICENSE) and runs on Python with the external libraries.

The software package has been written using Python 3.12.4 or newer.

The libraries necessary for running the software is as follows:
| Package:      | Version:      |
| ------------- | ------------- |
| numpy         | 2.1.1         |
| matplotlib    | 3.9.2         |
| PyQt6         | 6.8.0.2       |
| scipy         | 1.14.1        |
| sklearn       | 1.5.2         |

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install relevant packages.

#### Additional macOS requirements

| Package:      | Version:      |
| ------------- | ------------- |
| pyobjc        | 11.0          |

### Install FunFit as a python module with desktop shortcut
```bash
pip install git+https://github.com/Snunder/FunFit.git
```
This command installs FunFit as any other module installed using pip. A desktop shortcut is created if possible.

### Clone repository and install dependencies
```bash
git clone https://github.com/Snunder/FunFit.git
cd FunFit
pip install -r requirements.txt
pip install -e . # Editable install
# or
python setup.py install # Install FunFit and Desktop shortcut
```

Running the script FunFit.py should start the software exactly as if run from terminal, once dependencies are downloaded.

### Create desktop shortcut manually
If the standard installation fail to create a desktop shortcut, try this command.

```bash
python -m pip install --force-reinstall --no-deps "git+https://github.com/Snunder/FunFit.git"
# or
python3 -m pip install --force-reinstall --no-deps "git+https://github.com/Snunder/FunFit.git"
```

## Usage

If running from terminal, use following command in the environment, FunFit is installed:

```bash
funfit
```

If compiling a standalone app using pyinstaller, use the executable file instead.

## DEMO
As the GUI is inherently simple with few options, the software should be self explanatory. However, here is a complete description on how to properly use FunFit.

When running the script either from executable or directly from terminal a Graphics User Interface (GUI) will open.

[<img src="../main/UI_images/main_window.png" height="500">](../main/UI_images/main_window.png)

### LOAD:
Most functions require a subject dataset to run, which is loaded by clicking the **Load Files** button, which opens File Explorer such that the user can select an appropriate dataset. Here we have provided demo data which is available in the folder [tests](../main/tests) for the user to try the functions.\
Once the data is loaded, there are options of common data correction functions for SPM topography data, none of which are mandatory to run for the software to work.\
If the user interrupts the process in the loading process, nothing changes.

The loading function also supports "drag and drop" events for loading data. Note that only supported file types will trigger the load event.

[<img src="../main/UI_images/main_window.png" height="500">](../main/UI_images/main_window.png)
[<img src="../main/UI_images/drop_event.png" height="500">](../main/UI_images/drop_event.png)

After loading the data, the loaded data will be shown in the main window.

[<img src="../main/UI_images/main_window_loaded.png" height="500">](../main/UI_images/main_window_loaded.png)

### FIND STRUCTURED AREA:
For more accurate data analysis, the **Find structured area** button opens a prompt for the user to drag a rectangle.

This should enclose the patterned region, such that step-line correction and plane leveling algorithms are only performed on the flat plane surrounding the patterned region.
Additionally, the later **Plot Line Cuts** and **Fit Functions** features will only be performed on the area inside the marked rectangle.

[<img src="../main/UI_images/find_structs.png" height="450">](../main/UI_images/find_structs.png)
[<img src="../main/UI_images/find_structs_chosen.png" height="450">](../main/UI_images/find_structs_chosen.png)

The window shows the size of selection area and allows for dragging corners and rotating the area. Selection can be either reset or applied with the buttons at the bottom.
Once a selection is applied, the main window updates with an overlay to display chosen area.

[<img src="../main/UI_images/main_window_cropped.png" height="500">](../main/UI_images/main_window_cropped.png)

### STEP LINE CORRECTION:
Standard of AFM pictures are step line artefacts, where this software includes several algorithms for correcting these artefacts.\
Clicking the **Step line correction** button opens a window where the user can choose between the two correction methods. The user is provided with a preview of the corrected data before applying the step line correction.

[<img src="../main/UI_images/step_line_correction.png" height="400">](../main/UI_images/step_line_correction.png)
[<img src="../main/UI_images/median_aligned_data.png" height="400">](../main/UI_images/median_aligned_data.png)

Correction algorithms in the current version of the software are as follows:

| Algorithm:        | What it does:      |
| ----------------- | ------------- |
| Median alignment  | Align data to median of unmasked data in ligns |
| Median difference | Calculate difference between neighboring unmasked pixels. Align data to median of calculated difference for each line |
| Polynomial        | Fit a 1d polynomial of chosen degree and subtract from each line |
| Raw               | Displays raw, unaligned data |

This function inherits the overlay from the main window imlicitly. Therefore corrections are calculated based on the excluded region.

[<img src="../main/UI_images/main_window_corrected.png" height="500">](../main/UI_images/main_window_corrected.png)

After application the data shown in the main GUI window is updated.

### PLANE LEVELING:
Another standard "artefact" is a tilted sample when the image was taken. This is corrected by plane leveling.
Clicking the **Plane leveling** button fits the data outside the box marked in **Find structured area** (if existing. Otherwise all data) to a linear plane. The resulting plane and an ensamble of data points (sample rate i shown at the top of the window). 

[<img src="../main/UI_images/plane_fit.png" height="350">](../main/UI_images/plane_fit.png)

Pressing the **Apply Correction** button subtracts this plane from all the data, such that the average flat plane is set to 0 and the image no longer tilts.

### PLOT LINE CUTS:

This function opens a window for displaying slices of data. The left half of the window displays a top-down view of the data (as seen in the main window). The line shown dictates what data is plotted.\
The right half of the window shows the profile of the data along the chosen line.

This function is merely meant for illustrating the actual data, and thus does not manipulate height data.\
Instead the plot depicts the pixelvalues closest to the line. The sampling is based on the dimension (x,y) of the line with highest sampling rate.

[<img src="../main/UI_images/plot_lines.png" height="450">](../main/UI_images/plot_lines.png)
[<img src="../main/UI_images/plot_lines_selection.png" height="450">](../main/UI_images/plot_lines_selection.png)

### FIT FUNCTIONS:

Unique to this software is the option to fit 3D functions to topography data. It is recommended to crop the data again so fitting is only done on relevant parts of the data. This increases efficiency and accuracy.

By clicking the **Fit functions** button, the user is prompted with a list of function presets. These are as follows:

| Function type:    | Description:  |
| ----------------- | ------------- |
| Polynomials       | Polynomial function of degree N with only variation in x-direction |
| Exponential       | Exponential function |
| Fourier series    | A sum of N cosine waves in one direction (with angular correction) |
| Quasicrystal      | An N-fold rotationally symmetric quasicrystal, defined with N sinusoids |
| Gaussian          | 2D Gaussian function |
| Custom function   | Create a custom function that represents the data |

For both *Fourier series* and *Quasicrystal*, the algorithm calculates initial guess of wavelengths based on the Fourier transform of the data.

[<img src="../main/UI_images/main_window_cropped_to_fit.png" height="400">](../main/UI_images/main_window_cropped_to_fit.png)
[<img src="../main/UI_images/hover_fitting_function.png" height="400">](../main/UI_images/hover_fitting_function.png)

Selecting a preset function opens a new window with the fitting equation shown, input fields for initial guesses of parameters and a bitmap corresponding to the chosen parameter values.\
The parameters will in most cases be known to some extent by the user as the topography is a consequence of chosen parameters.

Selecting the **Custom function** option instead of a preset function, opens another window. In the input field, the custom function is input. The script automatically compiles a visualization of the function and detects parameters in the input function.

Using the "Equation Preview" and the "Detected Parameters", the user should verify, that the function is recognized properly. If not, naming of parameters and syntax error might be the cause.

When pressing **Apply**, a new window for inputting initial guesses of parameters is opened.

[<img src="../main/UI_images/custom_function_generator_empty.png" height="400">](../main/UI_images/custom_function_generator_empty.png)
[<img src="../main/UI_images/custom_function_generator_entered.png" height="400">](../main/UI_images/custom_function_generator_entered.png)

Pressing the **Apply** button in the parameter selection window starts the fitting algorithm. The parameter window will be overlayed with a status message of the plot.

[<img src="../main/UI_images/parameter_selection.png" height="400">](../main/UI_images/parameter_selection.png)
[<img src="../main/UI_images/parameter_selection_load.png" height="400">](../main/UI_images/parameter_selection_load.png)

After choosing fitting parameters, the software will try to make a fit based on the initial guesses. The underlying method is not perfect, so the better the guess, the more likely a good fit will be applied. 

When the software is done fitting, two windows will open. One showing the fitted parameters and an uncertainty in the form of a table. 
The other window depicts a plot with 2 rows of plot data. The top row is the real space data, while the bottom row is the Fourier transform of the data. First column is fitted data, the second column is raw data of chosen area and the third column is residual plots. A *RMSE* value is shown in the title description of the real-space residual plot.

[<img src="../main/UI_images/fitted_parameters.png" height="300">](../main/UI_images/fitted_parameters.png)
[<img src="../main/UI_images/fitted_plots.png" height="400">](../main/UI_images/fitted_plots.png)

### Roughness of flat area

In addition to fitting the data to a specific function, the user can also calculate roughness of flat surfaces. This function opens a window like the **Find structured area** function. Here a flat representative area is chosen instead.

[<img src="../main/UI_images/roughness_analysis_chosen.png" height="450">](../main/UI_images/roughness_analysis_chosen.png)

When applying, a linear plane will be fitted to the selected data. The *RMSE* value of this plot is directly linked to the surface roughness of the sample given the initial chosen area is flat. The function opens a window showing the residual from subtracting the plane and a *RMSE* value.

[<img src="../main/UI_images/roughness_analysis_result.png" height="450">](../main/UI_images/roughness_analysis_result.png)

### Bitmap generator

The **Bitmap generator** has options for creating bitmaps corresponding to the fitting function.\
When a function type for the bitmap has been chosen, the user will be prompted for values associated with the function. This includes all the parameters but also the desired size in the x-, and y-direction as well as the size of each pixel.

[<img src="../main/UI_images/bitmap_function.png" height="400">](../main/UI_images/bitmap_function.png)
[<img src="../main/UI_images/hover_bitmap_function.png" height="400">](../main/UI_images/hover_bitmap_function.png)
[<img src="../main/UI_images/bitmap_parameter_selection.png" height="400">](../main/UI_images/bitmap_parameter_selection.png)

When pressing **Export bitmap**, the user isbe prompted for a directory for saving the bitmap file. The bitmap is saved as '*bitmap.bmp*'. Note that this overwrites any file in the chosen directory with the same name.

Since this software is meant to be used for topography data, bitmaps can be used as a mask in i.e. NanoFrazor software. This function generates the initial bitmap to be used. 

## Troubleshooting

If you encounter any issues while using FunFit, please refer to the [GitHub Issues](https://github.com/Snunder/FunFit/issues) page to report bugs or request help from the community.

## License

[GNU General Public License](https://web.archive.org/web/20160316065455/https://opensource.org/licenses/gpl-3.0)
