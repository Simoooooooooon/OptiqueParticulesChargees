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
import time

# Load the UI file created with QT Designer
Ui_MainWindow, _ = uic.loadUiType("WriteWindow.ui")


class WriteWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Main class for the Writing interface.
    Allows the user to write an image into the sample
    Inherits from the main window
    """

    request_data_signal = pyqtSignal()  # Signal to request data to the main window

    def __init__(self):
        """
        Initialize the interface and set up UI components and connections.
        """

        super().__init__()  # Initialize the parent class

        self.setupUi(self)  # Load the UI
        self.setWindowTitle("Write an image to the sample")  # Set window title

        # Connect buttons to their respective functions
        self.pushButton_Hide.clicked.connect(self.hide_window)
        self.pushButton_Reset.clicked.connect(self.Reset)
        self.pushButton_Load_image.clicked.connect(self.loadImage)
        self.pushButton_VoltageMap.clicked.connect(self.Compute_Voltage_Map)
        self.pushButton_Signals.clicked.connect(self.Compute_Signals)
        self.pushButton_Go.clicked.connect(self.Write_Signals)
        self.pushButton_Stop.clicked.connect(self.Stop_Signals)

        # Ensure required time recalculation after modification
        self.spinBox_iterations.valueChanged.connect(self.calculate_required_time)

        # Initialize instance variables
        self.voltageRange = 20
        self.bits_number = 16
        self.label_time.setText("")
        self.filePath = None
        self.Objects = None
        self.LR_signal = None
        self.UD_signal = None
        self.iterations = None
        self.data = None
        self.required_time = None
        self.remaining_time_thread = None
        self.run_Thread = None

    def request_data(self):
        """
        Emit a signal to request data.

        This method emits a signal captured by the main window. The main window sends the data to the function below
        """

        try:
            self.request_data_signal.emit()

        except Exception as e:
            self.message('Error', f"An error occurred while requesting data : {e}")

    def receive_data(self, data):
        """
        Receive data and store it.

        Parameters:
        data (list): The data received from the main window.

        This method assigns the received data to an internal attribute for further processing or usage.
        """

        try:
            self.data = data

        except Exception as e:
            self.message('Error', f"An error occurred while receiving data : {e}")

    def displayImage(self, image):
        """
        Displays an image within the application's UI.

        This function handles the visual rendering of images in the main window. It supports displaying images
        from both file paths and in-memory byte streams (from operations like generating plots with matplotlib).
        The image is scaled to fit the designated UI element while maintaining aspect ratio.

        Parameters:
        - image (str or io.BytesIO): The image to display, provided either as a file path or as a BytesIO object.

        The function uses QPixmap to handle image operations and QLabel for display. Errors during the process
        are handled gracefully through user notifications and resetting the application state.
        """

        try:
            pixmap = QPixmap()

            if isinstance(image, io.BytesIO):
                qimage = QImage()  # Image is a BytesIO object from matplotlib
                qimage.loadFromData(image.getvalue())
                pixmap = QPixmap.fromImage(qimage)

            elif isinstance(image, str):
                pixmap.load(image)  # Image is a file path

            # Proceed to scale and display the pixmap
            self.QPixmap_ui.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            scaled_pixmap = pixmap.scaled(self.QPixmap_ui.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.QPixmap_ui.setPixmap(scaled_pixmap)

        except Exception as e:
            self.message('Error', f"Failed to display the image : {e}")
            self.Reset()

    def loadImage(self):
        """
        Opens a file dialog for the user to select an image and displays the selected image in the UI.

        This function triggers a file dialog that allows the user to select an image file from their file system.
        Supported formats can be specified in the file dialog filter (currently PNG and all other file types are supported).
        Once an image is selected, it is displayed in the main application window using the `displayImage` function.
        Additionally, this function manages the enabling and disabling of UI buttons based on the state of the image loading process.

        Errors during the loading or display process are managed by displaying an error message and resetting the application to a known state.
        """

        try:
            # Open file dialog to select an image
            self.filePath, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "PNG Files (*.png);;All Files (*)")
            if self.filePath:
                # Once an image is selected, display it
                self.displayImage(self.filePath)

                # Switch button states
                self.pushButton_Load_image.setEnabled(False)
                self.pushButton_VoltageMap.setEnabled(True)

        except Exception as e:
            self.message('Error', f"Failed to load the image : {e}")
            self.Reset()

    def Compute_Voltage_Map(self):
        """
        Computes the voltage map from an image file and displays a visual representation.

        This function processes a loaded image file to generate a voltage map, which is a set of voltage
        pairs derived from the image's pixel data. It uses the `Image_to_voltage_pairs` function from the
        `Image_to_Signals` module, calculating sensitivity based on the configured voltage range and bit depth.
        The resulting coordinates are then plotted and displayed within the application.

        The function updates the UI to reflect the new state by enabling and disabling buttons as necessary.
        It also triggers a recalculation of the required time for subsequent operations based on the newly
        generated data.

        Exceptions are handled by displaying error messages and resetting the application state if needed.
        """

        try:
            if self.filePath:
                # Compute the voltage map
                sensitivity = self.voltageRange / (2 ** self.bits_number)
                self.Objects = Image_to_Signals.Image_to_voltage_pairs(self.filePath, self.voltageRange, sensitivity)

                # Update button states
                self.pushButton_Signals.setEnabled(True)
                self.pushButton_VoltageMap.setEnabled(False)

                # Load the image to get its dimensions for plot scaling
                image = QImage(self.filePath)
                img_width = image.width()
                img_height = image.height()

                # Calculate figure size
                dpi = 100  # Example DPI, adjust as necessary
                figsize_width = img_width / dpi
                figsize_height = img_height / dpi

                # Plotting
                fig, ax = plt.subplots(figsize=(figsize_width, figsize_height), dpi=dpi)
                colors = cm.rainbow(np.linspace(0, 1, len(self.Objects)))  # Generating colors

                # Unzip the list of coordinates
                x_vals, y_vals = zip(*self.Objects)
                ax.scatter(x_vals, y_vals, s=1)  # s=1 sets the size of each point

                ax.grid(True)
                ax.set_aspect('equal', adjustable='box')

                # Save the plot to a BytesIO object and use displayImage to show it
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
                buf.seek(0)
                plt.close(fig)  # Close the figure to free memory

                # Convert the BytesIO object to QPixmap and display it using displayImage
                self.displayImage(buf)

                self.calculate_required_time()

        except Exception as e:
            self.message('Error', f"Failed to compute volage map : {e}")
            self.Reset()

    def Compute_Signals(self):
        """
        Computes the Left-Right and Up-Down signals from the voltage map and displays their plots.

        After generating a voltage map with `Compute_Voltage_Map`, this function further processes the data
        to produce Left-Right (LR) and Up-Down (UD) signals using the `pairs_to_signal` method from the
        `Image_to_Signals` module. The signals are plotted in two separate subplots and displayed in the UI.

        This function handles the activation and deactivation of UI buttons based on the process state and
        ensures that visual representations of the signals are updated in the main window. It also considers
        the number of iterations specified by the user to adjust the signal computation accordingly.

        Errors during computation or plotting are managed by notifying the user through a message and resetting
        the application state to ensure stability and reliability.
        """

        try:
            if self.Objects:
                if self.iterations:
                    # Compute signals
                    self.LR_signal, self.UD_signal = Image_to_Signals.pairs_to_signal(self.Objects, self.iterations)

                    # Update buttons state
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

                    # Plotting
                    fig, ax = plt.subplots(2, 1, figsize=(figsize_width, figsize_height), dpi=dpi)
                    fig.patch.set_alpha(0.0)  # Set the figure background to transparent
                    ax[0].plot(self.LR_signal)
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
            self.message('Error', f"Failed to compute signals : {e}")
            self.Reset()

    def Write_Signals(self):
        """
        Initiates the process of writing the computed signals to the NI Card using multi-threading.

        This function checks that the Left-Right (LR) and Up-Down (UD) signals are computed and available.
        It then retrieves necessary channel and frequency settings from the application's data. The signals
        are sent to the card channels using multithreading to manage signal transmission and
        to update UI elements like progress bars and timers concurrently without freezing the GUI.

        The function sets up and starts two threads: one for managing the remaining time and updating the UI,
        and another for the actual signal transmission. It ensures that the application responds to errors during
        the process by displaying messages and resetting the state if needed.

        Errors during setup or execution are handled by notifying the user and resetting the environment to a stable state.
        """

        try:
            if (self.LR_signal is not None) and (self.UD_signal is not None):
                # Getting data from the main window
                self.request_data()
                data = self.data
                channel_lr, channel_ud = data[0], data[1]
                sampling_frequency = data[2]

                # Show the original image back to the user
                self.displayImage(self.filePath)

                # Update buttons states
                self.pushButton_Go.setEnabled(False)
                self.pushButton_Stop.setEnabled(True)

                # Setting up the remaining time thread
                self.remaining_time_thread = Remaining_Time(self.required_time)
                self.remaining_time_thread.update_progress.connect(self.progressBar.setValue)
                self.remaining_time_thread.update_time.connect(self.label_time.setText)
                self.remaining_time_thread.progress_done.connect(self.progress_done)
                self.remaining_time_thread.errorOccurred.connect(self.handle_thread_errors)

                # Setting up the writing thread
                self.run_Thread = Send(channel_lr, channel_ud, self.LR_signal, self.UD_signal,
                                       sampling_frequency, self.required_time)
                self.run_Thread.errorOccurred.connect(self.handle_thread_errors)

                # Starting the threads
                self.remaining_time_thread.start()
                self.run_Thread.start()

        except Exception as e:
            self.message('Error', f"Failed to write signals : {e}")
            self.Reset()

    def calculate_required_time(self):
        """
        Calculates the time required to complete the signal transmission based on the number of iterations and sampling frequency.

        This function retrieves the current sampling frequency and the number of iterations set by the user to compute
        the total time needed to transmit all signals. The computation considers the length of the object list, which represents
        the number of voltage points generated from the image. The result is formatted and displayed in the UI to inform
        the user about the duration of the operation.

        The time is calculated to help in setting expectations and for use in configuring the progress and time tracking threads
        during the signal writing process. Errors in fetching data or performing calculations result in a notification to the user
        and a reset of the application to ensure consistency and reliability.
        """

        try:
            if self.Objects:
                # Getting data from the main window
                self.request_data()
                data = self.data
                if data:
                    sampling_frequency = data[2]

                    # Getting data from the actual window
                    self.iterations = self.spinBox_iterations.value()

                    # Calculating the required time
                    self.required_time = len(self.Objects) / sampling_frequency * self.iterations

                    # Converting the required time
                    if self.required_time < 60:  # Less than 60 seconds
                        result_str = f"{int(self.required_time) + 1} seconds"
                    else:  # 60 seconds or more
                        minutes = int(self.required_time) // 60
                        remaining_seconds = int(self.required_time) % 60 + 1
                        result_str = f"{minutes}mn {remaining_seconds}s"

                    # Displaying the required time
                    self.label_time.setText(f"Required time :\n{result_str}")  # Write the required time on the UI

        except Exception as e:
            self.message('Error', f"Failed to write calculate the required time : {e}")
            self.Reset()

    def progress_done(self):
        """
        Reacts to the completion of the progress, typically signal transmission.

        This method is designed to be called when signal transmission is completed. It enables the 'Go'
        button, allowing the user to start another transmission. This can be connected to a signal indicating
        that the transmission task has finished.

        If an error occurs, an error message is displayed to the user.
        """

        try:
            # Update buttons state
            self.pushButton_Go.setEnabled(True)
            self.pushButton_Stop.setEnabled(False)

        except Exception as e:
            self.message('Error', f"Failed to emit 'done' signal : {e}")

    def Stop_Signals(self):
        """
        Stops the signal transmission process.

        This method attempts to stop any ongoing signal transmission by terminating the threads
        responsible for sending the signals and updating the UI with the remaining time. It resets
        the progress bar to 0 and recalculates the required time for transmission, effectively
        resetting the UI to allow for a new operation to be started.

        If the threads cannot be terminated or if any other error occurs during the process,
        an error message is displayed and the UI is reset to ensure the application remains in a usable state.
        """

        try:
            port = self.data[0][:-4]  # Remove "\aoX" to only get "DevX"
            Write_Signals.reset(port)  # Reset the NI Card

            # Update buttons state
            self.pushButton_Go.setEnabled(True)
            self.pushButton_Stop.setEnabled(False)

            try:
                self.remaining_time_thread.terminate()  # Force kill the thread
            except Exception:
                pass

            try:
                self.run_Thread.terminate()  # Force kill the thread
            except Exception:
                pass

            self.progressBar.setValue(0)  # Progress bar back to 0%
            self.calculate_required_time()  # Show the required time

        except Exception as e:
            self.message('Error', f"Couldn't stop the signals : {e}")

    def Reset(self):
        """
        Resets the application to its initial state.

        This method is designed to reset the application, stopping any ongoing signal transmission
        processes and clearing any data or paths that have been computed or loaded. It attempts to
        terminate any running threads related to signal transmission or time calculation, and resets
        the UI elements to their default states. This includes enabling the 'Load Image' button while
        disabling all others, clearing any displayed images, and resetting all internal variables used
        to store the application's state.

        The method ensures the application is ready to start a new signal transmission process from scratch,
        without needing to restart the application itself. It's a failsafe to return the application to a known
        good state in case of errors or at the user's request.

        If an error occurs during the reset process, an error message is displayed to inform the user.
        """

        try:
            try:
                self.remaining_time_thread.terminate()  # Force kill the thread
            except Exception:
                pass

            try:
                self.run_Thread.terminate()  # Force kill the thread
            except Exception:
                pass

            # Stop the signals
            if self.data is not None:
                self.Stop_Signals()

            # Reset objects
            self.filePath = None
            self.Objects = None
            self.Path = None
            self.LR_signal = None
            self.UD_signal = None
            self.data = None
            self.remaining_time_thread = None
            self.run_Thread = None
            self.required_time = None
            self.label_time.setText("")
            self.QPixmap_ui.clear()

            # Switch button states
            self.pushButton_Load_image.setEnabled(True)
            self.pushButton_VoltageMap.setEnabled(False)
            self.pushButton_Signals.setEnabled(False)
            self.pushButton_Go.setEnabled(False)
            self.pushButton_Stop.setEnabled(False)

        except Exception as e:
            self.message('Error', f"Couldn't reset the device : {e}")

    def message(self, title, message):
        """
        Displays a message to the user in a non-modal message box.

        This method is used throughout the MyWindow class to show various types of messages
        (such as errors, information, etc.) without freezing the interface. It creates a
        non-modal message box that does not block the rest of the UI while open.

        Parameters:
            title (str): The title of the message box.
            message (str): The message to be displayed in the message box.
        """

        # Create a non-modal message box
        msg_box = QtWidgets.QMessageBox(self)  # Message box
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)  # Icon
        msg_box.setText(message)  # Main message
        msg_box.setWindowTitle(title)  # Title of the window
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)  # Ok button
        msg_box.setModal(False)  # Make it non-modal
        msg_box.show()  # Show the message box

    def handle_thread_errors(self, error_message):
        """
        Displays an error message if an error occurs during the sweep process.

        This method is connected to the `errorOccurred` signals. It is triggered
        when the threads encounter an error, and it displays the error message using the
        custom Message method of the MyWindow class.

        Parameters:
            error_message (str): The error message received from the threads.
        """

        self.message('Error', error_message)

    # Function to hide the window
    def hide_window(self):
        """
        Minimizes the main window of the application without terminating ongoing processes.

        This function provides functionality to hide the application's main window, thus minimizing it
        without stopping any operations that may be running in the background. It's a user-friendly feature
        that allows the application to continue operating in a less obtrusive mode.
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
    """
    A thread for sending Left-Right and Up-Down signals to a device using specified channels.

    This thread aims to facilitate the transmission of signal data to a hardware device, handling
    Left-Right (LR) and Up-Down (UD) signals through separate channels. It is designed to operate with
    parameters such as signal arrays, sampling frequency, the number of iterations for the transmission,
    and the overall required time for completion. Errors during initialization or execution are communicated
    back through a custom signal.

    Attributes:
    - errorOccurred (pyqtSignal): Custom signal emitted when an error occurs, carrying an error message.
    """

    errorOccurred = pyqtSignal(str)  # Signal to handle possible errors

    def __init__(self, channel_lr, channel_ud, LR_signal, UD_signal, sampling_frequency, required_time, parent=None):
        """
        Initialize the thread

        Parameters:
        - channel_lr (str): Channel identifier for the LR signal.
        - channel_ud (str): Channel identifier for the UD signal.
        - LR_signal (numpy.ndarray): Array representing the LR signal.
        - UD_signal (numpy.ndarray): Array representing the UD signal.
        - sampling_frequency (int): Sampling frequency for the signals.
        - iterations (int): Number of times the signals should be sent.
        - timeout (float): Timeout for the operation, in seconds.
        - required_time (float): Total required time for the operation, intended for UI updates.
        - parent (QObject, optional): Parent QObject for this thread. Defaults to None.

        Upon encountering an initialization error, this method emits an `errorOccurred` signal with
        a descriptive message of the issue.
        """

        try:
            super(Send, self).__init__(parent)
            self.channel_lr = channel_lr
            self.channel_ud = channel_ud
            self.LR_signal = LR_signal
            self.UD_signal = UD_signal
            self.sampling_frequency = sampling_frequency
            self.required_time = required_time

        except Exception as e:
            self.errorOccurred.emit(f"An error occurred while initializing the write thread : {str(e)}")

    def run(self):
        """
        Send signals and write them to the NI card.

        If an error occurs during the execution of this method, an `errorOccurred` signal is emitted
        with details of the error, allowing for error handling by connected slots or signals.
        """

        try:
            Write_Signals.write_signals_to_NI(self.channel_lr, self.channel_ud, self.LR_signal, self.UD_signal,
                                              self.sampling_frequency, self.required_time + 1)

        except Exception as e:
            self.errorOccurred.emit(f"An error occurred while running the write thread : {str(e)}")


class Remaining_Time(QThread):
    """
    A thread to manage and update the remaining time and progress for a long-running operation.

    This thread calculates and updates the remaining time for an operation based on the `required_time`
    provided during initialization. It emits signals to update a progress bar and a time label in the UI
    with the current progress and remaining time, respectively. When the operation completes, or the
    remaining time runs out, it signals the completion of the progress.

    Attributes:
    - errorOccurred (pyqtSignal): Emitted when an exception is caught, with a message detailing the error.
    - update_progress (pyqtSignal): Emitted to update the progress bar, carrying the current progress percentage.
    - update_time (pyqtSignal): Emitted to update the remaining time label, carrying the formatted time string.
    - progress_done (pyqtSignal): Emitted when the operation is complete or the time has fully elapsed.
    """

    errorOccurred = pyqtSignal(str)  # Signal to handle possible errors
    update_progress = pyqtSignal(int)  # Pour la mise à jour de la barre de progression
    update_time = pyqtSignal(str)  # Pour la mise à jour du label de temps restant
    progress_done = pyqtSignal()

    def __init__(self, required_time, parent=None):
        """
        Initialize the progress bar thread.

        Parameters:
        - required_time(float): The total time required for the operation, in seconds.
        - parent(QObject, optional): The parent QObject for this thread.Defaults to None.

        Upon encountering an initialization error, this method emits an `errorOccurred` signal with
        a descriptive message of the issue.
        """

        try:
            super(Remaining_Time, self).__init__(parent)
            self.required_time = required_time

        except Exception as e:
            self.errorOccurred.emit(f"An error occurred while initializing the time thread : {str(e)}")

    def run(self):
        """
        Executes the remaining time tracking logic of the thread.

        Once started, this method calculates the elapsed and remaining time at frequent intervals,
        emitting signals to update the UI with the current progress and the formatted remaining time.
        Upon completion of the operation or when the remaining time runs out, it emits a `progress_done`
        signal to indicate that the operation has finished.

        If an error occurs during the execution of this method, an `errorOccurred` signal is emitted
        with details of the error, allowing for error handling by connected slots or signals.
        """

        try:
            start_time = time.time()  # Start timing for operation duration

            while True:
                elapsed_time = time.time() - start_time  # Calculate elapsed time
                remaining_time = self.required_time - elapsed_time + 1  # Compute remaining time

                if remaining_time <= 1:  # Check if operation is complete
                    self.update_progress.emit(100)  # Update progress bar to full
                    self.update_time.emit("Done")  # Update label to show completion
                    self.progress_done.emit()  # Signal that progress is done
                    break  # Exit loop

                progress = int((elapsed_time / self.required_time) * 100)  # Calculate progress percentage
                self.update_progress.emit(progress)  # Emit progress update

                # Decide format for displaying remaining time
                if remaining_time < 60:  # For less than a minute
                    time_str = f"Remaining time :\n{int(remaining_time)} seconds"
                else:  # For a minute or more
                    minutes = int(remaining_time) // 60
                    remaining_seconds = int(remaining_time) % 60
                    time_str = f"Remaining time :\n{minutes}mn {remaining_seconds}s"

                self.update_time.emit(time_str)  # Emit remaining time update

                time.sleep(0.001)

        except Exception as e:
            self.errorOccurred.emit(f"An error occurred while running the time thread : {str(e)}")
