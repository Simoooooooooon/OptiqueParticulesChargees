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
        self.pushButton_Triangles.clicked.connect(self.Compute_Triangles)
        self.pushButton_Path.clicked.connect(self.Compute_Path)
        self.pushButton_Signals.clicked.connect(self.Compute_Signals)
        self.pushButton_Go.clicked.connect(self.Write_Signals)
        self.pushButton_Stop.clicked.connect(self.Stop_Signals)

        # Ensure required time recalculation after modification
        self.spinBox_iterations.valueChanged.connect(self.calculate_required_time)

        # Initialize instance variables
        self.voltageRange = 20
        self.label_time.setText("")
        self.filePath = None
        self.Objects = None
        self.Path = None
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
        Display an image in the UI.

        This method supports displaying images either from a file path or directly from a BytesIO object
        containing image data, typically generated by matplotlib or similar libraries.

        Parameters:
        image (str | io.BytesIO): The source of the image to be displayed. If it is a string, it is treated
                                  as a file path to the image. If it is an instance of io.BytesIO, it is
                                  assumed to contain the binary data of the image.

        This method attempts to load the image, scale it appropriately for the UI, and display it. If the
        process fails, it resets the UI to a safe state and shows an error message.
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
        Open a file dialog for the user to select an image, then display the selected image in the UI.

        This method opens a dialog allowing the user to select an image file. Once an image is selected,
        it calls `displayImage` to show the image in the application's UI. If an image is successfully
        loaded and displayed, it disables the button to load an image and enables the button to
        compute triangles. If the process fails, it resets the UI to a safe state and shows an error message.
        """

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
            self.message('Error', f"Failed to load the image : {e}")
            self.Reset()

    def Compute_Triangles(self):
        """
        Compute and plot triangles from the selected image.

        This method uses the `Image_to_Signals.Image_to_Objects` function to compute objects (triangles)
        from the currently selected image file. These objects are then plotted with matplotlib,
        and the plot is displayed in the application's UI. This method assumes that an image has already been
        selected and `self.filePath` is set.

        The process involves:
        - Computing objects from the image.
        - Plotting these objects with different colors for visualization.
        - Saving the plot to a BytesIO object.
        - Displaying the BytesIO object in the UI using `displayImage`.

        If an error occurs during this process, the UI is reset to a safe state and an error message is shown.
        Upon successful completion, it enables the button to show the path of triangles and disables
        the button to compute triangles, indicating that the process is complete.
        """

        try:
            if self.filePath:
                # Compute the triangles
                self.Objects = Image_to_Signals.Image_to_Objects(self.filePath, self.voltageRange)

                # Update button states
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

                # Plotting
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
            self.message('Error', f"Failed to compute triangles : {e}")
            self.Reset()

    def Compute_Path(self):
        """
        Computes the optimal path through the detected objects in the image.

        After detecting objects within the image using `Compute_Triangles`, this method calculates
        the optimal path that connects these objects. The path is then plotted and displayed in the UI.
        This function enables the button to send signals (based on the computed path) and disables
        the button to compute the path again, indicating the process is complete.

        The computed path is stored in `self.Path`, and the visualization includes transparent backgrounds
        for both the figure and axes, with the path plotted in blue.

        If an error occurs, a message is displayed and the UI is reset to a safe state.
        """

        try:
            if self.Objects:
                # Compute the optimal path
                self.Path = Image_to_Signals.Objects_path(self.Objects)

                # Update button states
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

                # Plotting
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
            self.message('Error', f"Failed to compute path : {e}")
            self.Reset()

    def Compute_Signals(self):
        """
        Converts the computed path into Left-Right (LR) and Up-Down (UD) signals.

        After computing the path through `Compute_Path`, this method transforms that path into two signals:
        one representing left-right movement (LR signal) and the other representing up-down movement (UD signal).
        These signals are plotted and displayed in the UI. This enables the button to start the signal
        transmission process and disables the button to compute the signals again.

        Additionally, this function calls `calculate_required_time` to estimate the time needed for signal
        transmission based on the computed signals.

        If an error occurs during the signal computation, a message is displayed, and the UI is reset.
        """

        try:
            if self.Path:
                # Compute signals
                self.LR_signal, self.UD_signal = Image_to_Signals.Path_To_Signal(self.Path)

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

                self.calculate_required_time()

        except Exception as e:
            self.message('Error', f"Failed to compute signals : {e}")
            self.Reset()

    def Write_Signals(self):
        """
        Initiates the process of sending the computed LR and UD signals to a specified device.

        This method sends the Left-Right (LR) and Up-Down (UD) signals, computed in `Compute_Signals`, to a NI device
        using the channel information and sampling frequency retrieved through `request_data`. It also calculates
        the timeout based on the signal length and sampling frequency, and displays the image associated with
        the signals in the UI.

        The method manages the UI state, disabling the start button and enabling the stop button, indicating that
        the signal transmission is in progress. It also starts threads for managing the signal transmission and
        updating the UI with the remaining time until completion.

        If any errors occur during the setup or transmission process, an error message is displayed, and the UI
        is reset to a safe state.
        """

        try:
            if (self.LR_signal is not None) and (self.UD_signal is not None):
                # Getting data from the main window
                self.request_data()
                data = self.data
                channel_lr, channel_ud = data[0], data[1]
                sampling_frequency = data[2]

                # Show the original image back to the suer
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
        Calculates the time required to send the entire set of signals.

        This method calculates the required time based on the length of the Left-Right (LR) signal,
        the sampling frequency, and the number of iterations specified by the user. It updates the UI
        to display this calculated time. If the calculated time is less than 60 seconds, it displays
        the result in seconds; otherwise, it displays the result in minutes and seconds.

        This method is intended to give the user an estimate of how long the signal transmission will take.

        If an error occurs during calculation, an error message is displayed and the UI is reset to a safe state.
        """

        try:
            if (self.LR_signal is not None) and (self.UD_signal is not None):
                # Getting data from the main window
                self.request_data()
                data = self.data
                sampling_frequency = data[2]

                # Getting data from the actual window
                self.iterations = self.spinBox_iterations.value()

                # Calculating the required time
                self.required_time = len(self.LR_signal) / sampling_frequency * self.iterations

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
            self.pushButton_Triangles.setEnabled(False)
            self.pushButton_Path.setEnabled(False)
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
                                              self.sampling_frequency, self.required_time)

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
