import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Plotting options
def plotopts(x, y, Z):
    cbar = plt.colorbar(ticks=mticker.AutoLocator())
    cbar.ax.tick_params(labelsize=21)
    cbar.set_label('Depth z (nm)', fontsize=21)
    plt.xlabel('Length x (µm)', fontsize=21)
    plt.ylabel('Length y (µm)', fontsize=21)
    ratio = x[-1] / y[-1]
    plt.gcf().set_size_inches(8, 8 * ratio)
    plt.gca().tick_params(labelsize=21)
    plt.gca().spines['top'].set_linewidth(1.5)
    plt.gca().spines['right'].set_linewidth(1.5)
    plt.gca().spines['bottom'].set_linewidth(1.5)
    plt.gca().spines['left'].set_linewidth(1.5)
    plt.box(True)
    plt.set_cmap('Purples_r')
