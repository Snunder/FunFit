import numpy as np
import matplotlib.pyplot as plt
import pickle
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QPen, QIcon
from PyQt6.QtCore import Qt, QPoint
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib as mpl
from PyQt6 import QtGui
import os

# Define a class that inherits from QMainWindow
class OffsetFinder(QMainWindow):
    def __init__(self):
        # Call the __init__ method of the QMainWindow class to initialize the basic functionality of the main window
        super().__init__()
        # Load the image from the given image path
        self.image = QPixmap(plot_to_QPixmap())

        # Create a QLabel to display the image
        self.label = QLabel()
        self.label.setPixmap(self.image)
        # Set the alignment of the label to center
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button = QPushButton("Apply")
        self.button.clicked.connect(self.execute)
        with open(os.getcwd()+'/GUI/main_stylesheet.qss', 'r') as f:
            self.button.setStyleSheet(f.read())
        # Create a QVBoxLayout to hold the QLabel and QPushButton
        layout = QVBoxLayout()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add titlebar
        titlebar = QWidget(self)
        titlebar.setObjectName('titlebar')
        titlebar.setFixedHeight(30)
        titlebar_layout = QHBoxLayout(titlebar)  # Change to QHBoxLayout for horizontal alignment
        titlebar_layout.setContentsMargins(0, 0, 0, 0)
        titlebar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.title_label = QLabel("Select center point for initial guess (x0, y0)")
        self.title_label.setStyleSheet("color: white; font-size: 16px; font-family: Verdana;")
        
        self.close_button = QPushButton()
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
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
        self.close_button.setIcon(QIcon("GUI/icon_close.png"))
        self.close_button.clicked.connect(lambda checked: self.close())
        
        titlebar_layout.addWidget(self.title_label)
        titlebar_layout.addStretch()
        titlebar_layout.addWidget(self.close_button)
        
        titlebar.setStyleSheet("background-color: #19172D;")
        layout.addWidget(titlebar)
        # Add line under titlebar
        separator = QWidget(self)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #4B4587; border: none; margin: 0px; padding: 0px;")
        layout.addWidget(separator)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        
        # Allow to choose center point by clicking on the image
        self.label.mousePressEvent = self.get_mouse_coords
        self.crosshair = QLabel(self)
        self.crosshair.setStyleSheet("color: red; font-size: 20px;")
        self.crosshair.setFixedSize(self.label.pixmap().size())
        self.crosshair.paintEvent = self.paint_crosshair
        self.crosshair.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.crosshair.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.crosshair.hide()
        self.label.mousePressEvent = self.get_mouse_coords
        
        # Create a QWidget to hold the QVBoxLayout
        widget = QWidget()
        widget.setLayout(layout)
        widget.setStyleSheet("background-color: #2B2942;")
        # Set the QWidget as the central widget of the QMainWindow
        self.setCentralWidget(widget)

        # Enable dragging the window using the titlebar
        titlebar.mousePressEvent = self.start_drag
        titlebar.mouseMoveEvent = self.do_drag

        # Show the QMainWindow
        self.show()

    def start_drag(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def do_drag(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def paint_crosshair(self, event):
        painter = QPainter(self.crosshair)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        crosshair_size = 40
        painter.drawLine(QPoint(int(crosshair_size/2), -crosshair_size), QPoint(int(crosshair_size/2), crosshair_size))
        painter.drawLine(QPoint(-crosshair_size, int(crosshair_size/2)), QPoint(crosshair_size, int(crosshair_size/2)))
        painter.end()

    def get_mouse_coords(self, event):
        self.x0 = event.pos().x()
        self.y0 = event.pos().y()
        # Translate the coordinates to the coordinates of the plot
        x_ratio = event.pos().x() / self.label.pixmap().width()
        y_ratio = event.pos().y() / self.label.pixmap().height()

        self.x0_plot = extent[0] + x_ratio * (extent[1] - extent[0])
        self.y0_plot = extent[3] - y_ratio * (extent[3] - extent[2])
        
        # Adjust for the titlebar height
        self.crosshair.move(self.x0 - 20, self.y0 - 20 + self.label.y())
        self.crosshair.show()
        self.crosshair.raise_()

    def execute(self):
        self.close()
        plt.close('all')

def plot_to_QPixmap():

    #---- set up a mpl figure instance ----

    fig = mpl.figure.Figure()
    fig.patch.set_facecolor('none')
    fig.set_canvas(FigureCanvasAgg(fig))
    renderer = fig.canvas.get_renderer()

    #---- plot the mathTex expression ----

    # Load the tmp_dat_file from pickle file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)
    # Define raw data
    z = tmp_dat_file.data
    tmpX = tmp_dat_file.dataX
    tmpY = tmp_dat_file.dataY
    offset = np.nanmean(z)
    

    # Plot the raw data and wait for user input
    fig, ax = plt.subplots()
    global extent
    extent = [tmpX.min(), tmpX.max(), tmpY.min(), tmpY.max()] # Define the extent of the plot
    ax.imshow(z, extent=extent, origin='lower', cmap='Purples_r', aspect='auto') # Display the raw data

    fig.subplots_adjust(
        top=1,
        bottom=0,
        left=0,
        right=1,
        hspace=0,
        wspace=0
    )

    #---- convert mpl figure to QPixmap ----

    buf, size = fig.canvas.print_to_buffer()
    qimage = QtGui.QImage.rgbSwapped(QtGui.QImage(buf, size[0], size[1],
                                                  QtGui.QImage.Format.Format_ARGB32))
    qpixmap = QtGui.QPixmap(qimage)

    return qpixmap

class ClickHandler:
    def __init__(self):
        self.x0 = None
        self.y0 = None
        self.user_clicked = False

    def onclick(self, event):
        """
        Event handler for mouse click to select the initial guess for the fit.

        Parameters:
        event (MouseEvent): The mouse event containing the click coordinates.
        """
        self.x0 = float(event.xdata)
        self.y0 = float(event.ydata)
        self.user_clicked = True
        plt.close()

    def onmove(self, event):
        """
        Event handler for mouse movement to update the crosshair position.

        Parameters:
        event (MouseEvent): The mouse event containing the cursor coordinates.
        """
        if event.inaxes:
            if event.xdata is not None and event.ydata is not None:
                if (extent[0] <= event.xdata <= extent[1]) and (extent[2] <= event.ydata <= extent[3]): # Check if the cursor is within the plot boundaries
                    crosshair.set_xdata([event.xdata]) 
                    crosshair.set_ydata([event.ydata])      # Update the crosshair position
                    event.canvas.restore_region(background) # Restore the background
                    ax.draw_artist(crosshair)               # Redraw the crosshair
                    event.canvas.blit(ax.bbox)              # Blit the updated plot
                else:
                    event.canvas.restore_region(background) # Restore the background
                    crosshair.set_xdata([])                 
                    crosshair.set_ydata([])                 # Hide the crosshair
                    ax.draw_artist(crosshair)               # Redraw the crosshair
                    event.canvas.blit(ax.bbox)              # Blit the (non)updated plot

    def onclose(self, event):
        """
        Event handler for closing the plot window, to stop the code instead of running on lost input.

        Parameters:
        event (CloseEvent): The close event.
        """
        if not self.user_clicked:
            exit()

def main(handler=None):
    global crosshair, ax, background, extent
    if handler is None:
        handler = ClickHandler() # Create an instance of the ClickHandler class
    
    # Load the tmp_dat_file from pickle file
    with open('tmp_dat_file.pkl', 'rb') as f:
        tmp_dat_file = pickle.load(f)
    # Define raw data
    z = tmp_dat_file.data
    tmpX = tmp_dat_file.dataX
    tmpY = tmp_dat_file.dataY
    offset = np.nanmean(z)
    

    # Plot the raw data and wait for user input
    fig, ax = plt.subplots()
    extent = [tmpX.min(), tmpX.max(), tmpY.min(), tmpY.max()] # Define the extent of the plot
    ax.imshow(z, extent=extent, origin='lower', cmap='viridis', aspect='auto') # Display the raw data
    plt.title('Select center point for initial guess (x0, y0)', fontsize=16)   # Set the title

    # Draw the canvas once and cache the background
    fig.canvas.draw()
    background = fig.canvas.copy_from_bbox(ax.bbox)

    # Add a crosshair that starts at the center of the plot
    crosshair, = ax.plot([(tmpX.min() + tmpX.max()) / 2], [(tmpY.min() + tmpY.max()) / 2], 'r+', markersize=15)

    # Connect the event handlers to the plot
    cid_move = fig.canvas.mpl_connect('motion_notify_event', handler.onmove)
    cid_close = fig.canvas.mpl_connect('close_event', handler.onclose)
    cid_click = fig.canvas.mpl_connect('button_press_event', handler.onclick)

    # Display the plot
    plt.show()

    # Disconnect the event listeners
    fig.canvas.mpl_disconnect(cid_click)
    fig.canvas.mpl_disconnect(cid_move)
    fig.canvas.mpl_disconnect(cid_close)

    # Clean up temporary variables
    del cid_click, cid_move, cid_close, crosshair, ax, background, extent

    # Return the clicked coordinates
    return handler.x0, handler.y0, offset

if __name__ == "__main__":
    # x0, y0, offset = main()
    app = QApplication([])
    window = OffsetFinder()
    app.exec()