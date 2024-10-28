import numpy as np
import matplotlib.pyplot as plt
import pickle
from sklearn import linear_model

def main():
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)

    X, Y = np.meshgrid(tmp_dat_file.x, tmp_dat_file.y)
    XX = X[np.where(~np.isnan(tmp_dat_file.mask))].flatten()
    YY = Y[np.where(~np.isnan(tmp_dat_file.mask))].flatten()
    Z = tmp_dat_file.mask[np.where(~np.isnan(tmp_dat_file.mask))].flatten()

    x1, y1, z1 = XX.flatten(), YY.flatten(), Z.flatten()

    X_data = np.vstack([x1, y1]).T
    Y_data = z1

    data = np.vstack((XX[0::1], YY[0::1], Z[0::1])).T

    reg = linear_model.LinearRegression().fit(X_data, Y_data)

    # Subtract fitted plane from tmp_dat_file.Z
    tmp_dat_file.Z = tmp_dat_file.Z - (reg.coef_[0]*X + reg.coef_[1]*Y + reg.intercept_)

    x1_index = min(tmp_dat_file.x1_index, tmp_dat_file.x2_index)
    x2_index = max(tmp_dat_file.x1_index, tmp_dat_file.x2_index)
    y1_index = min(tmp_dat_file.y1_index, tmp_dat_file.y2_index)
    y2_index = max(tmp_dat_file.y1_index, tmp_dat_file.y2_index)

    X, Y = np.meshgrid(tmp_dat_file.x, tmp_dat_file.y)

    tmp_dat_file.data = tmp_dat_file.Z[y1_index:y2_index, x1_index:x2_index]
    tmp_dat_file.dataX = X[y1_index:y2_index, x1_index:x2_index]
    tmp_dat_file.dataY = Y[y1_index:y2_index, x1_index:x2_index]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot a subset of original data points
    ax.scatter(data[0::80, 0], data[0::80, 1], data[0::80, 2], color='#3B2070', label='Data Points')

    # Create a coarser grid for plotting the plane
    x_range = np.linspace(X_data[:, 0].min(), X_data[:, 0].max(), 10)
    y_range = np.linspace(X_data[:, 1].min(), X_data[:, 1].max(), 10)
    x_grid, y_grid = np.meshgrid(x_range, y_range)
    z_grid = reg.coef_[0] * x_grid + reg.coef_[1] * y_grid + reg.intercept_

    # Plot the fitted plane
    ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.5, color='#686868', label='Fitted Plane')

    ax.set_xlabel('X (µm)')
    ax.set_ylabel('Y (µm)')
    ax.set_zlabel('Z (nm)')
    ax.legend()
    plt.show()
    return

if __name__ == "__main__":
    main()
