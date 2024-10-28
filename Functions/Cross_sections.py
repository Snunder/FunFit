import numpy as np
import matplotlib.pyplot as plt
import pickle
from matplotlib.colors import LinearSegmentedColormap

def main():
    # Load the tmp_dat_file object from a file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)
    # Divide the figure into 3 plots
    fig, axs = plt.subplots(1, 3, figsize=(20, 5))
    # Define custom color map
    colors = [(204/256, 175/256, 255/256), (87/256, 0, 146/256)] 
    n_bins = 100  # Number of bins in the colormap
    cmap_name = 'custom_colormap'
    cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins) # Create the colormap for fft plots

    # Plot N_linecuts
    N_linecuts = 15
    step = max(1, len(tmp_dat_file.data) // N_linecuts)  # Calculate step to ensure only 30 plots
    for i in range(0, len(tmp_dat_file.data), step):
        axs[0].plot(tmp_dat_file.dataX[i], tmp_dat_file.data[i], color=cmap(i/len(tmp_dat_file.data)), alpha=0.8)
    axs[0].set_title('Line cuts', fontsize=14)
    axs[0].set_xlabel('X (µm)', fontsize=12)  # Set the x-axis label
    axs[0].set_ylabel('Z (nm)', fontsize=12)  # Set the y-axis label

    # Contour plot with horizontal flip
    flipped_data = np.fliplr(tmp_dat_file.data)
    im = axs[1].imshow(flipped_data, extent=[tmp_dat_file.dataX.min(), tmp_dat_file.dataX.max(), tmp_dat_file.dataY.min(), tmp_dat_file.dataY.max()], origin='lower', cmap='Purples_r', aspect='auto')
    cbar = fig.colorbar(im, ax=axs[1])
    axs[1].set_title('Data', fontsize=14)
    axs[1].set_xlabel('X (µm)', fontsize=12)  # Set the x-axis label
    axs[1].set_ylabel('Y (µm)', fontsize=12)  # Set the y-axis label
    cbar.set_label('Z (nm)', fontsize=12)  # Set the colorbar label

    # Mean plot with shaded region for standard deviation
    mean_line_cut = np.nanmean(tmp_dat_file.data, axis=0)
    std_line_cut = np.nanstd(tmp_dat_file.data, axis=0)
    
    axs[2].plot(tmp_dat_file.dataX[0], mean_line_cut, color='#3B2070')
    axs[2].fill_between(tmp_dat_file.dataX[0], mean_line_cut - std_line_cut, mean_line_cut + std_line_cut, color='#3B2070', alpha=0.2)
    
    axs[2].set_xlabel('X (µm)', fontsize=12)  # Set the x-axis label
    axs[2].set_ylabel('Mean Z (nm)', fontsize=12)  # Set the y-axis label
    axs[2].set_title('Mean Line Cut with Standard Deviation', fontsize=14)

    plt.tight_layout()
    plt.show()

    # Save the tmp_dat_file object to a file
    with open('tmp_dat_file.pkl', 'wb') as f:
        pickle.dump(tmp_dat_file, f)
    return

if __name__ == "__main__":
    main()