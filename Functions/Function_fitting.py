import numpy as np
import matplotlib.pyplot as plt
import pickle
from scipy.optimize import curve_fit
import Functions.Function_presets as fitmodel
from matplotlib.colors import LinearSegmentedColormap
from PyQt6.QtWidgets import QMessageBox

def Function_fit(functiontype = "quasicrystal", fitting_model = None, IC = None, Bounds = None):
    
    """
    Main function for fitting a quasicrystal function to the data.
    """
    if fitting_model is None:
        if functiontype == "quasicrystal":
            [fitting_model, IC, Bounds] = fitmodel.quasicrystal()
        elif functiontype == "custom":
            [fitting_model, IC, Bounds] = fitmodel.custom()

    user_clicked = False  # Initialize the flag for user input
    # Open the temporary object from pickle
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)
    # Define raw data
    z = tmp_dat_file.data
    tmpX = tmp_dat_file.dataX
    tmpY = tmp_dat_file.dataY

    # Flatten the data for curve fitting
    X = np.column_stack((tmpX.flatten(), tmpY.flatten()))
    Z = z.flatten()

    # Set inf/nan to 0 (edge values from rotation)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)
    z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)

    # Fit the model
    try:
        popt, _ = curve_fit(fitting_model, X.T, Z, p0=IC, bounds=Bounds)
    except RuntimeError as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(f"Error: {e}")
        msg.setWindowTitle("Error")
        msg.exec()
        return e
    # Predict using the fitted model
    Z_fit_vector = fitting_model(X.T, *popt)
    # Reshape the predicted data back to the original shape
    Z_fit = Z_fit_vector.reshape(z.shape)

    # Plot the original data, the fitted model and the residuals
    fig, axs = plt.subplots(2, 3, figsize=(18, 12))
    
    # Define a custom colormap with multiple colors
    colors = [(0/256, 0/256, 0/256), (197/256, 114/256, 255/256), (219/256, 1, 255/256), (1, 1, 1)]  # Black to purple to magenta
    n_bins = 100  # Number of bins in the colormap
    cmap_name = 'custom_colormap'
    fft_cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins) # Create the colormap for fft plots
    
    ## JUST PLOTTING FROM HERE (except RMSE) ##
    # Raw data
    c1 = axs[0, 0].imshow(z, cmap='Purples_r', aspect='auto', extent=[np.min(tmpX), np.max(tmpX), np.min(tmpY), np.max(tmpY)]) # plot
    cbar1 = fig.colorbar(c1, ax=axs[0, 0], shrink=0.7) # colorbar
    axs[0, 0].set_title('Original data', fontsize=16) # title
    axs[0, 0].set_ylabel('y (µm)', fontsize=14) # y-axis label
    cbar1.set_label('z (nm)', fontsize=14) # colorbar label
    vmin1 = np.min(z) # min value for colorbar
    vmax1 = np.max(z) # max value for colorbar
    # Make the plot square
    axs[0, 0].set_box_aspect(1) 
    # Set colorbar ticks
    cbar1ticks = np.linspace(vmin1, vmax1, num=7)
    cbar1.set_ticks(cbar1ticks)
    cbar1.set_ticklabels(['{:.1f}'.format(tick) for tick in cbar1ticks]) # Place 7 ticks with 1 decimal
    
    # Fourier transform of original data
    z_fft = np.fft.fftshift(np.fft.fft2(z-np.mean(z)))
    z_fft_magnitude = np.abs(z_fft)/np.max(np.abs(z_fft)) # Normalize to the max value
    
    # Calculate angular frequency axes (1/µm), will be used for all plots
    freq_x = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(z.shape[1], d=(tmpX[0, 1] - tmpX[0, 0])))
    freq_y = 2 * np.pi * np.fft.fftshift(np.fft.fftfreq(z.shape[0], d=(tmpY[1, 0] - tmpY[0, 0])))
    
    # Plot the Fourier transform of the original data
    c4 = axs[1, 0].imshow(z_fft_magnitude, cmap=fft_cmap, aspect='auto', extent=[freq_x[0], freq_x[-1], freq_y[0], freq_y[-1]]) # plot
    cbar4 = fig.colorbar(c4, ax=axs[1, 0], shrink=0.7) # colorbar with shrink to match plot height
    axs[1, 0].set_title('Fourier Transform of Original Data', fontsize=16) # title
    cbar4.set_label('Magnitude', fontsize=14) # colorbar label

    # Make the plot S Q U A R E
    axs[1, 0].set_box_aspect(1)
    axs[1, 0].set_ylabel('Frequency (1/µm)', fontsize=14) # y-axis label
    # Limit axes
    smallestaxis = min(freq_x[-1], freq_y[-1]) # Makes plot square based on smallest axis
    axs[1, 0].set_xlim(-smallestaxis, smallestaxis) # limit x-axis
    axs[1, 0].set_ylim(-smallestaxis, smallestaxis) # limit y-axis

    # Rewrite popt into scientific notation with fixed decimals for title
    popt = ['{:.2e}'.format(i) for i in popt]
    # Exclude the first two parameters
    popt = popt[2:]

    # Insert a newline after every third parameter
    popt_with_newlines = []
    for index, param in enumerate(popt):
        popt_with_newlines.append(param)
        # Add a newline character after every third parameter
        if (index + 1) % 3 == 0:
            popt_with_newlines.append('\n')

    # Join the parameters into a single string with comma separation
    popt = ', '.join(popt_with_newlines)
    # Add "fitted parameters \n"
    popt = 'Fitted parameters: \n' + popt

    # Fitted model
    c2 = axs[0, 1].imshow(Z_fit, cmap='Purples_r', aspect='auto', extent=[np.min(tmpX), np.max(tmpX), np.min(tmpY), np.max(tmpY)])
    cbar2 = fig.colorbar(c2, ax=axs[0, 1], shrink=0.7) # colorbar with shrink to match plot height
    axs[0, 1].set_title(popt, fontsize=16) # title
    axs[0, 1].set_xlabel('x (µm)', fontsize=14) # x-axis label
    cbar2.set_label('z (nm)', fontsize=14) # colorbar label
    # Set colorbar limits to the min and max values of the original data
    vmin2 = np.min(Z_fit)
    vmax2 = np.max(Z_fit)
    # Set colorbar ticks
    cbar2ticks = np.linspace(vmin2, vmax2, num=7)
    cbar2.set_ticks(cbar2ticks)
    cbar2.set_ticklabels(['{:.1f}'.format(tick) for tick in cbar2ticks])
    # Make the plot square (might stretch the plot)
    axs[0, 1].set_box_aspect(1) 

    # Fourier transform of fitted model
    Z_fit_fft = np.fft.fftshift(np.fft.fft2(Z_fit-np.mean(Z_fit)))
    Z_fit_fft_magnitude = np.abs(Z_fit_fft)/np.max(np.abs(Z_fit_fft)) # Normalize to the max value

    # Plot the Fourier transform of the fitted model
    c5 = axs[1, 1].imshow(Z_fit_fft_magnitude, cmap=fft_cmap, aspect='auto', extent=[freq_x[0], freq_x[-1], freq_y[0], freq_y[-1]]) # plot
    cbar5 = fig.colorbar(c5, ax=axs[1, 1], shrink=0.7) # Colorbar
    axs[1, 1].set_title('Fourier Transform of Fitted Model', fontsize=16) # title
    cbar5.set_label('Magnitude', fontsize=14) # colorbar label
    axs[1, 1].set_box_aspect(1) # Make the plot square
    # Limit axes
    axs[1, 1].set_xlim(-smallestaxis, smallestaxis)
    axs[1, 1].set_ylim(-smallestaxis, smallestaxis)
    axs[1, 1].set_xlabel('Frequency (1/µm)', fontsize=14) # x-axis label
    # RMSE map
    residuals = z - Z_fit # residuals
    rmse = np.sqrt(np.mean((residuals**2).flatten(), axis=0)) # RMSE sqrt(mean(residuals^2))

    # Center the colorbar around 0 (will be changed later, only makes the plot symmetric)
    vmin3 = np.min(residuals)
    vmax3 = np.max(residuals)
    if abs(vmin3) > abs(vmax3):
        # Set a corner pixel of residuals to the opposite of the max value
        zlim3 = [vmin3, abs(vmin3)]
        residuals[-1, -1] = abs(vmin3) # This is illegal
    else:
        # Set a corner pixel of residuals to the max value
        zlim3 = [-abs(vmax3), vmax3]
        residuals[-1, -1] = -abs(vmax3) # This is also illegal
    # Plot the residuals
    c3 = axs[0,2].imshow(residuals, cmap='RdBu_r', aspect='auto', extent=[np.min(tmpX), np.max(tmpX), np.min(tmpY), np.max(tmpY)]) # plot
    cbar3 = fig.colorbar(c3, ax=axs[0, 2], shrink=0.7)  # Colorbar
    axs[0, 2].set_title('Residual plot\nRMSE: {:.1f} nm'.format(rmse), fontsize=16)  # title
    cbar3.set_label('Residual (nm)', fontsize=14) # colorbar label
    axs[0, 2].set_box_aspect(1)  # Make the plot square
    # Set colorbar ticks to display the two extreme values
    cbar3ticks = np.linspace(zlim3[0], zlim3[1], num=7)
    cbar3.set_ticks(cbar3ticks)
    cbar3.set_ticklabels(['{:.1f}'.format(tick) for tick in cbar3ticks])

    # Fourier transform of residuals
    residuals_fft = np.fft.fftshift(np.fft.fft2(residuals-np.mean(residuals)))
    residuals_fft_magnitude = np.abs(residuals_fft)/np.max(np.abs(residuals_fft)) # Normalize to the max value
    # Plot the Fourier transform of the residuals (if that's interesting?)
    c6 = axs[1, 2].imshow(residuals_fft_magnitude, cmap=fft_cmap, aspect='auto', extent=[freq_x[0], freq_x[-1], freq_y[0], freq_y[-1]]) # plot
    cbar6 = fig.colorbar(c6, ax=axs[1, 2], shrink=0.7) # Colorbar
    axs[1, 2].set_title('Fourier Transform of Residuals', fontsize=16) # title
    cbar6.set_label('Magnitude', fontsize=14) # colorbar label
    axs[1, 2].set_box_aspect(1)  # Make the plot square
    # Limit axes
    axs[1, 2].set_xlim(-smallestaxis, smallestaxis)
    axs[1, 2].set_ylim(-smallestaxis, smallestaxis)

    plt.tight_layout()
    plt.show()

def main():
    global IC, crosshair, ax, background, extent, user_clicked
    [fitting_model, IC, Bounds] = fitmodel.quasicrystal()

    Function_fit(functiontype = "quasicrystal", fitting_model = fitting_model, IC = IC, Bounds = Bounds)
    # Function_fit(functiontype = "custom")

if __name__ == "__main__":
    main()