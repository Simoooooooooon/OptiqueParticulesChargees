import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QThread
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import io
from PyQt6.QtCore import pyqtSignal
from . import Image_to_Signals
from . import Write_Signals

# Load the UI file created with QT Designer
Ui_MainWindow, _ = uic.loadUiType("WriteWindow.ui")


class WriteWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # Define a custom signal
    request_data_signal = pyqtSignal()

    def __init__(self):

        super().__init__()

        self.setupUi(self)
        self.setWindowTitle("Write an image to the sample")

        self.pushButton_Hide.clicked.connect(self.hide_window)
        self.pushButton_Reset.clicked.connect(self.Reset)
        self.pushButton_Load_image.clicked.connect(self.loadImage)
        self.pushButton_Triangles.clicked.connect(self.Compute_Triangles)
        self.pushButton_Path.clicked.connect(self.Compute_Path)
        self.pushButton_Signals.clicked.connect(self.Compute_Signals)
        self.pushButton_Go.clicked.connect(self.request_data)

        self.voltageRange = 20

        self.filePath = None
        self.Objects = None
        self.Path = None
        self.LR_signal = None
        self.UD_signal = None
        self.iterations = None
        self.run_Thread = None

    def request_data(self):
        self.request_data_signal.emit()

    def displayImage(self, image):
        try:
            pixmap = QPixmap()

            if isinstance(image, io.BytesIO):
                # Image is a BytesIO object from matplotlib
                qimage = QImage()
                qimage.loadFromData(image.getvalue())
                pixmap = QPixmap.fromImage(qimage)
            elif isinstance(image, str):
                # Image is a file path
                pixmap.load(image)

            # Proceed to scale and display the pixmap as before
            self.QPixmap_ui.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            scaled_pixmap = pixmap.scaled(self.QPixmap_ui.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.QPixmap_ui.setPixmap(scaled_pixmap)

        except Exception as e:
            self.Reset()
            print(f"Failed to display image: {e}")

    def loadImage(self):
        try:
            # Open file dialog to select an image
            self.filePath, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "PNG Files (*.png);;All Files (*)")
            if self.filePath:
                # Once an image is selected, display it
                self.displayImage(self.filePath)

                # Switch button states
                self.pushButton_Load_image.setEnabled(False)
                self.pushButton_Triangles.setEnabled(True)
        except Exception as e:
            self.Reset()
            print(e)

    def Compute_Triangles(self):
        try:
            if self.filePath:
                self.Objects = Image_to_Signals.Image_to_Objects(self.filePath, self.voltageRange)
                self.pushButton_Path.setEnabled(True)
                self.pushButton_Triangles.setEnabled(False)

                # Load the image to get its dimensions for plot scaling
                image = QImage(self.filePath)
                img_width = image.width()
                img_height = image.height()

                # Calculate figure size
                dpi = 100  # Example DPI, adjust as necessary
                figsize_width = img_width / dpi
                figsize_height = img_height / dpi

                # Plotting all objects part
                fig, ax = plt.subplots(figsize=(figsize_width, figsize_height), dpi=dpi)
                colors = cm.rainbow(np.linspace(0, 1, len(self.Objects)))  # Generating colors

                for obj_idx, sorted_voltage_pairs in enumerate(self.Objects):
                    voltage_pairs_x, voltage_pairs_y = zip(*sorted_voltage_pairs)
                    ax.scatter(voltage_pairs_x, voltage_pairs_y, s=1, color=colors[obj_idx])

                ax.grid(True)
                ax.set_aspect('equal', adjustable='box')

                # Save the plot to a BytesIO object and use displayImage to show it
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
                buf.seek(0)
                plt.close(fig)  # Close the figure to free memory

                # Convert the BytesIO object to QPixmap and display it using displayImage
                self.displayImage(buf)

        except Exception as e:
            # Switch button states
            self.Reset()
            print(e)

    def Compute_Path(self):
        try:
            if self.Objects:
                self.Path = Image_to_Signals.Objects_path(self.Objects)
                self.pushButton_Signals.setEnabled(True)
                self.pushButton_Path.setEnabled(False)

                # Load the image to get its dimensions for plot scaling
                image = QImage(self.filePath)
                img_width = image.width()
                img_height = image.height()

                # Calculate figure size
                dpi = 100  # Example DPI, adjust as necessary
                figsize_width = img_width / dpi
                figsize_height = img_height / dpi

                # Plotting path
                all_points = [point for object_path in self.Path for point in object_path]
                all_x_coords, all_y_coords = zip(*all_points)

                fig, ax = plt.subplots(figsize=(figsize_width, figsize_height), dpi=dpi)
                fig.patch.set_alpha(0.0)  # Set the figure background to transparent
                ax.patch.set_alpha(0.0)  # Set the axis background to transparent
                ax.plot(all_x_coords, all_y_coords, '-o', markersize=1, linewidth=0.5, color='blue')
                ax.grid(True)
                ax.set_aspect('equal', adjustable='box')

                # Save the plot to a BytesIO object with a transparent background
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
                buf.seek(0)
                plt.close(fig)  # Close the figure to free memory

                # Convert the BytesIO object to QPixmap and display it using displayImage
                self.displayImage(buf)

        except Exception as e:
            # Switch button states
            self.Reset()
            print(e)

    def Compute_Signals(self):
        try:
            if self.Path:
                self.LR_signal, self.UD_signal = Image_to_Signals.Path_To_Signal(self.Path)
                self.pushButton_Go.setEnabled(True)
                self.pushButton_Signals.setEnabled(False)

                # Load the image to get its dimensions for plot scaling
                image = QImage(self.filePath)
                img_width = image.width()
                img_height = image.height()

                # Calculate figure size
                dpi = 100  # Example DPI, adjust as necessary
                figsize_width = img_width / dpi
                figsize_height = (img_height / dpi) * 2  # Since we have 2 subplots, divide height by 2

                # Plotting signals part
                fig, ax = plt.subplots(2, 1, figsize=(figsize_width, figsize_height), dpi=dpi)
                fig.patch.set_alpha(0.0)  # Set the figure background to transparent

                # Configuration and plotting for the first subplot (LR Signal)
                ax[0].plot(self.LR_signal)

                # Configuration and plotting for the second subplot (UD Signal)
                ax[1].plot(self.UD_signal)

                plt.tight_layout()

                # Save the plot to a BytesIO object with a transparent background
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
                buf.seek(0)
                plt.close(fig)  # Close the figure to free memory

                # Convert the BytesIO object to QPixmap and display it using displayImage
                self.displayImage(buf)

        except Exception as e:
            # Switch button states
            self.Reset()
            print(e)

    def Write_Signals(self, data):
        try:
            if (self.LR_signal is not None) and (self.UD_signal is not None):
                channel_lr, channel_ud = data[0], data[1]
                sampling_frequency = data[2]
                self.iterations = self.spinBox_iterations.value()
                timeout = len(self.LR_signal) / sampling_frequency + 1
                required_time = (timeout - 1) * self.iterations
                self.displayImage(self.filePath)

                # Displaying required time
                if required_time < 60:  # Less than 60 seconds
                    result_str = f"{int(required_time)} seconds"
                else:  # 60 seconds or more
                    minutes = int(required_time) // 60
                    remaining_seconds = int(required_time) % 60
                    result_str = f"{minutes}mn {remaining_seconds}s"

                self.label_time.setText(result_str)  # Write the required time on the UI

                self.run_Thread = Send(channel_lr, channel_ud, self.LR_signal, self.UD_signal,
                                       sampling_frequency, self.iterations, timeout, required_time)
                self.run_Thread.start()

        except Exception as e:
            # Switch button states
            self.Reset()
            print(e)

    def Reset(self):
        self.filePath = None
        self.Objects = None
        self.Path = None
        self.LR_signal = None
        self.UD_signal = None

        # Switch button states
        self.pushButton_Load_image.setEnabled(True)
        self.pushButton_Triangles.setEnabled(False)
        self.pushButton_Path.setEnabled(False)
        self.pushButton_Signals.setEnabled(False)

        self.label_time.setText("")
        self.QPixmap_ui.clear()

    def hide_window(self):
        """
        Hides the main window, providing a way to minimize the application without stopping any ongoing operations.
        """
        try:
            super().hide()

        except Exception as e:
            self.message('Error', f"Couldn't hide the window : {e}")

    # Function to prevent the user from killing the window object
    def closeEvent(self, event):
        """
        Overrides the default close event to prevent the window from being closed and potentially stopping the
        program incorrectly. Instead, it hides the window.
        """

        try:
            event.ignore()  # Ignores the closing event to not kill the window object
            self.hide_window()  # Hides the window

        except Exception as e:
            self.message('Error', f"The closing event failed : {e}")


class Send(QThread):
    def __init__(self, channel_lr, channel_ud, LR_signal, UD_signal, sampling_frequency, iterations, timeout,
                 required_time, parent=None):
        super(Send, self).__init__(parent)
        self.channel_lr = channel_lr
        self.channel_ud = channel_ud
        self.LR_signal = LR_signal
        self.UD_signal = UD_signal
        self.sampling_frequency = sampling_frequency
        self.iterations = iterations
        self.timeout = timeout
        self.required_time = required_time

    def run(self):
        try:
            Write_Signals.write_signals_to_NI(self.channel_lr, self.channel_ud, self.LR_signal, self.UD_signal,
                                              self.sampling_frequency, self.iterations, self.timeout,
                                              self.required_time)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = WriteWindow()
    window.show()
    sys.exit(app.exec())
