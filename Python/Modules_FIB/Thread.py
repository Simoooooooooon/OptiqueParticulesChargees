from PyQt6 import QtCore
from PyQt6.QtCore import QThread, pyqtSignal
from Modules_FIB import Scanning
from Modules_FIB import Visa_Dependencies
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
        try:
            super(SweepThread, self).__init__(parent)  # Initialize the QThread parent class
            self.time_per_pixel = time_per_pixel
            self.sampling_frequency = sampling_frequency
            self.pixels_number = pixels_number
            self.channel_lr = channel_lr
            self.channel_ud = channel_ud
            self.channel_read = channel_read
            self.mode = mode

        except Exception as e:
            self.errorOccurred.emit(f"__init__ in SweepThread returned : {str(e)}")

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
            self.errorOccurred.emit(f"SweepThread returned : {str(e)}")


# Thread class for close in time acquisition (video scanning)
class VideoThread(QThread):
    """
    A specialized QThread for handling video acquisition and processing. This thread is responsible for initiating,
    capturing, and stopping video data based on given parameters. It communicates with NI hardware for video data
    acquisition, utilizing specified channels for control and data capture,
    and operates continuously until explicitly stopped.

    Attributes:
        write_task: Task handle for writing to the hardware, used to control the scanning process.
        read_task: Task handle for reading from the hardware, used to acquire the video data.
        timeout: The maximum time in seconds to wait for a read operation to complete.
        total_samples_to_read: The total number of samples to read in each acquisition cycle.
        running: A flag indicating whether the video acquisition should continue running.

    Signals:
        image: Emitted with the captured image data for each frame.
        errorOccurred: Emitted with an error message if an exception occurs during acquisition.
    """

    errorOccurred = QtCore.pyqtSignal(str)
    image = QtCore.pyqtSignal(np.ndarray)

    # Configures the card for the video acquisition
    def __init__(self, time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read,
                 parent=None):
        """
        Initializes the video thread with parameters for video acquisition and sets up the necessary tasks
        for reading and writing to the hardware.

        Parameters:
            time_per_pixel (int): Time in microseconds allocated for each pixel.
            sampling_frequency (int): The frequency at which samples are acquired.
            pixels_number (int): The total number of pixels in the video frame.
            channel_lr (str): The channel used for horizontal (left-right) scanning.
            channel_ud (str): The channel used for vertical (up-down) scanning.
            channel_read (str): The channel used for reading sensor data.
            parent (QObject, optional): The parent object for this thread. Defaults to None.
        """

        try:
            super(VideoThread, self).__init__(parent)

            # Initialization of the tasks RW for continuous acquisitions
            init = Scanning.video_init(time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud,
                                       channel_read)
            self.pixels_number = pixels_number
            self.write_task = init[0]
            self.read_task = init[1]
            self.timeout = init[2]
            self.total_samples_to_read = init[3]
            self.running = True

        except Exception as e:
            self.errorOccurred.emit(f"__init__ in VideoThread returned : {str(e)}")

    # Continuously running
    def run(self):
        """
        The main loop of the thread, responsible for continuously acquiring video data until stopped. Captured
        data is emitted through the `image` signal. If an error occurs during acquisition, the error is emitted
        through the `errorOccurred` signal.
        """
        try:
            while self.running:  # While the user didn't ask to stop

                # Get a new image
                data = Scanning.video_instance(self.write_task, self.read_task,
                                               self.timeout, self.pixels_number, self.total_samples_to_read)
                self.image.emit(data)

        except Exception as e:
            self.errorOccurred.emit(f"VideoThread returned : {str(e)}")

    # Used to stop the video flux and erase the NI tasks
    def stop(self):
        """
        Stops the video acquisition process by setting the running flag to False, which ends the loop in the
        `run` method. It also safely stops and cleans up the hardware tasks for reading and writing.
        """

        try:
            self.running = False
            time.sleep(.1)  # Timeout to prevent errors from showing up
            Scanning.video_stop(self.write_task, self.read_task)  # Stops the RW tasks

        except Exception as e:
            self.errorOccurred.emit(f"Stop function in VideoThread returned : {str(e)}")


# Thread class for GPP ComboBox population
class Population(QThread):
    """
    This thread is responsible for asynchronously fetching the list of connected VISA devices to populate UI components,
    such as ComboBoxes, without blocking the main application UI. It enhances the responsiveness of the application
    by performing potentially time-consuming operations in a separate thread.

    Signals:
        errorOccurred (str): Emitted when an error occurs during the fetching process.
        list (list): Emitted with the fetched list of VISA devices.
    """

    errorOccurred = QtCore.pyqtSignal(str)
    list = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        """
        Initializes the thread for populating connected VISA devices.

        Parameters:
            parent (QObject, optional): The parent object for this thread, if any. Defaults to None.
        """
        try:
            super(Population, self).__init__(parent)  # Initialize the QThread parent class

        except Exception as e:
            self.errorOccurred.emit(f"__init__ in Population thread returned : {str(e)}")

    # Get the list of connected devices and send it back
    def run(self):
        """
        The main execution method of the thread, which attempts to fetch the list of connected VISA devices.
        Upon successful retrieval, it emits the list through the 'list' signal. If an error occurs, the error
        is emitted through the 'errorOccurred' signal.
        """

        try:
            items = Visa_Dependencies.resources_list()
            self.list.emit(items)

        except Exception as e:
            self.errorOccurred.emit(f"Population thread returned : {str(e)}")


# Thread class for the progress bar
class ProgressBar(QThread):
    """
    Manages a progress bar's updates in a separate thread to maintain UI responsiveness during operations
    that require progress tracking, such as long-running processes. It calculates and emits the progress
    percentage based on the time elapsed relative to the total expected time of the operation.

    Signals:
        progressUpdated (int): Emitted with the current progress percentage (0-100).
        errorOccurred (str): Emitted if an error occurs during the progress update process.
    """

    progressUpdated = QtCore.pyqtSignal(int)  # Signal to update the progression
    errorOccurred = QtCore.pyqtSignal(str)

    def __init__(self, time_per_pixel, pixels_number, parent=None):
        """
        Initializes the ProgressBar thread with the parameters needed to calculate the progress over time.

        Parameters:
            time_per_pixel (int): Time in microseconds allocated for each pixel.
            pixels_number (int): The total number of pixels in the operation, used to calculate total time.
            parent (QObject, optional): The parent object for this thread, if any. Defaults to None.
        """
        try:
            super(ProgressBar, self).__init__(parent)
            time_per_pixel = time_per_pixel / 1000000
            self.total_time = time_per_pixel * (pixels_number + 2) ** 2
            self.interval = time_per_pixel  # Update interval

        except Exception as e:
            self.errorOccurred.emit(f"__init__ in ProgressBar thread returned : {str(e)}")

    # Calculates the percentage progress and send it back
    def run(self):
        """
        The main execution method of the thread, calculating and emitting the progress of an operation
        based on the elapsed time. The progress is updated at intervals specified by `self.interval`
        and continues until the total time of the operation has passed. It ensures progress updates are
        smooth and consistent, aiming for minimal disruption to the user experience.
        """

        try:
            start_time = time.time()
            while time.time() - start_time < self.total_time:
                elapsed_time = time.time() - start_time
                progress = int((elapsed_time / self.total_time) * 100)
                self.progressUpdated.emit(progress)
                time.sleep(self.interval)  # Wait for the next update
            self.progressUpdated.emit(100)

        except Exception as e:
            self.errorOccurred.emit(f"ProgressBar thread returned : {str(e)}")
