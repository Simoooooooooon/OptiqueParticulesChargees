from PyQt6 import QtCore
from PyQt6.QtCore import QThread, pyqtSignal
from Modules_FIB import Scanning  # Module for Scanning & acquisition, use the Ni_Dependencies module
from Modules_FIB import Visa_Dependencies  # Module for Visa Dependencies (unfinished)
import time
import numpy as np


#########################################################################################
# Classes

# Thread class for sweep
class SweepThread(QThread):
    """
    A QThread subclass for handling the sweep signal generation in a separate thread.

    This thread class is responsible for running the sweep signal generation process in the background,
    thereby keeping the main UI responsive. It communicates the results and errors through signals.

    Attributes:
        errorOccurred (pyqtSignal): Signal emitted when an error occurs in the thread.
        image (pyqtSignal): Signal emitted with the image data once the sweep process is complete.
    """
    errorOccurred = QtCore.pyqtSignal(str)  # Signal to handle possible errors
    image = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read, mode,
                 parent=None):
        """
        Initializes the SweepThread with necessary parameters for the sweep process.

        Parameters:
            time_per_pixel (float): Time spent per pixel in the scan.
            sampling_frequency (int): The sampling frequency for the scan.
            pixels_number (int): Number of pixels in each dimension of the scan.
            channel_lr (str): The channel used for left-right movement.
            channel_ud (str): The channel used for up-down movement.
            channel_read (str): The channel used for reading the data.
            parent (QObject): The parent object for this thread, if any.
        """
        super(SweepThread, self).__init__(parent)  # Initialize the QThread parent class
        self.time_per_pixel = time_per_pixel
        self.sampling_frequency = sampling_frequency
        self.pixels_number = pixels_number
        self.channel_lr = channel_lr
        self.channel_ud = channel_ud
        self.channel_read = channel_read
        self.mode = mode

    # Get the list of pixels and send it back
    def run(self):
        """
        Executes the sweep operation in a separate thread.

        This method is automatically called when the thread starts. It runs the sweep process and emits
        the resulting image data or any errors encountered.
        """
        try:
            # Scanning signal generation from "Scanning.py"
            if self.mode == "Triangle":
                data = Scanning.triangle_scanning(self.time_per_pixel, self.sampling_frequency, self.pixels_number,
                                                  self.channel_lr,
                                                  self.channel_ud, self.channel_read)
            else:
                data = Scanning.rise_scanning(self.time_per_pixel, self.sampling_frequency, self.pixels_number,
                                              self.channel_lr,
                                              self.channel_ud, self.channel_read)
            self.image.emit(data)
        except Exception as e:
            self.errorOccurred.emit(str(e))


# Thread class for close in time acquisition (video scanning)
class VideoThread(QThread):
    """
    A QThread subclass for handling the VideoR_thread signal generation in a separate thread.

    This thread class is responsible for running the continuous acquisition signal generation process in the background,
    thereby keeping the main UI responsive. It communicates the results and errors through signals.

    Attributes:
        errorOccurred (pyqtSignal): Signal emitted when an error occurs in the thread.
        image (pyqtSignal): Signal emitted with the image data once the scanning process is complete.
    """
    errorOccurred = QtCore.pyqtSignal(str)
    image = QtCore.pyqtSignal(np.ndarray)

    # Configures the card for the video acquisition
    def __init__(self, time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read,
                 parent=None):
        super(VideoThread, self).__init__(parent)
        init = Scanning.video_init(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud,
                                   channel_read)
        self.pixels_number = pixels_number
        self.write_task = init[0]
        self.read_task = init[1]
        self.timeout = init[2]
        self.total_samples_to_read = init[3]
        self.running = True

    # Continuously running
    def run(self):
        while self.running:  # While the user didn't ask to stop
            try:
                # Get a new image
                data = Scanning.video_instance(self.write_task, self.read_task,
                                               self.timeout, self.pixels_number, self.total_samples_to_read)
                self.image.emit(data)
            except Exception as e:
                self.errorOccurred.emit(str(e))

    # Used to stop the video flux and erase the NI tasks
    def stop(self):
        self.running = False
        time.sleep(.1)
        Scanning.video_stop(self.write_task, self.read_task)


# Thread class for GPP ComboBox population
class Population(QThread):
    list = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(Population, self).__init__(parent)  # Initialize the QThread parent class

    # Get the list of connected devices and send it back
    def run(self):
        items = Visa_Dependencies.resources_list()
        self.list.emit(items)


# Thread class for the progress bar
class ProgressBar(QThread):
    """
    A QThread subclass for populating the list of connected GPIB devices.

    This thread class is used to asynchronously retrieve and emit the list of connected GPIB devices,
    ensuring that the UI remains responsive during this potentially time-consuming process.

    Attributes:
        list (pyqtSignal): Signal emitted with the list of connected GPIB devices.
    """
    progressUpdated = pyqtSignal(int)  # Signal to update the progression

    def __init__(self, time_per_pixel, pixels_number, parent=None):
        """
        Initializes the Population thread.

        Parameters:
            parent (QObject): The parent object for this thread, if any.
        """
        super(ProgressBar, self).__init__(parent)
        time_per_pixel = time_per_pixel / 1000000
        self.total_time = time_per_pixel * (pixels_number + 2) ** 2
        self.interval = time_per_pixel  # Update interval

    # Calculates the percentage progress and send it back
    def run(self):
        """
        Executes the device population process in a separate thread.

        This method is automatically called when the thread starts. It retrieves the list of connected
        GPIB devices and emits it through the 'list' signal.
        """
        start_time = time.time()
        while time.time() - start_time < self.total_time:
            elapsed_time = time.time() - start_time
            progress = int((elapsed_time / self.total_time) * 100)
            self.progressUpdated.emit(progress)
            time.sleep(self.interval)  # Wait for the next update
        self.progressUpdated.emit(100)
