import sys
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt
import warnings
from Modules_FIB import Ni_Dependencies
from Modules_FIB import Visa_Dependencies
from Modules_FIB import Source_Lenses
import numpy as np
from PIL import Image
import json
from math import ceil
from Modules_FIB import Thread
import Draw

# Ignores the ResourceWarnings made by PyVISA library
warnings.simplefilter("ignore", ResourceWarning)

# Load the UI file created with QT Designer
Ui_MainWindow, QtBaseClass = uic.loadUiType("Main_interface.ui")


# Main class for the interface
class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """
    Main class for the Focused Ion Beam (FIB) control interface.
    Inherits from QMainWindow and the Ui_MainWindow generated from Qt Designer.
    """

    send_data_signal = QtCore.pyqtSignal(list)  # Signal to send data to the "write" window
    listChanged = QtCore.pyqtSignal(list)  # Signal to emit acquired data

    # Initialize the interface
    def __init__(self, write_window):
        """
        Initialize the interface and set up UI components and connections.
        """

        try:
            super(MainWindow, self).__init__()  # Initialize the parent class
            self.WriteWindow = write_window   # Create an instance of the "write" window
            self.setupUi(self)  # Load the UI
            self.setWindowTitle("Interface de pilotage du FIB")  # Set window title

            # Listen for the request_data_signal from the "write" window
            self.WriteWindow.request_data_signal.connect(self.provide_data)

            # Connect buttons to their respective functions
            self.pushButton_quit.clicked.connect(self.quit)
            self.pushButton_dev_refresh.clicked.connect(self.populate_dev_combobox)
            self.pushButton_connect_dev.clicked.connect(self.connect_to_card)
            self.pushButton_gpp_4323_refresh.clicked.connect(self.populate_gpp_4323_combobox)
            self.pushButton_connect_gpp_4323.clicked.connect(self.connect_to_gpp_4323)
            self.pushButton_connect_gpp_4323_help.clicked.connect(self.gpp_4323_help)
            self.pushButton_sweep.clicked.connect(self.sweep)
            self.pushButton_save_image.clicked.connect(self.save_image)
            self.pushButton_load_config.clicked.connect(self.load_config)
            self.pushButton_save_config.clicked.connect(self.save_config)
            self.pushButton_connections.clicked.connect(self.show_connections_window)
            self.pushButton_show_write.clicked.connect(self.show_write_window)
            self.pushButton_start_video.clicked.connect(self.start_video)
            self.pushButton_stop_video.clicked.connect(self.stop_video)

            # Connect sliders to their respective functions
            self.brightness_slider.valueChanged.connect(self.gpp_4323_brightness_slider_changed)
            self.brightness_slider.sliderReleased.connect(self.gpp_4323_brightness_slider_released)

            # Ensure required time recalculation after modification
            self.spinBox_time_per_pixel.valueChanged.connect(self.required_time)
            self.spinBox_image_size.valueChanged.connect(self.required_time)
            self.spinBox_sampling_frequency.editingFinished.connect(self.required_time)
            self.comboBox_Scanning_Mode.currentTextChanged.connect(self.required_time)

            # Initialize instance variables
            self.video_resolution = 100
            self.port_dev = None
            self.gpp_power_supply = None
            self.sweep_thread = None
            self.population_thread = None
            self.progressBarThread = None
            self.currentImage = None
            self.video_thread = None

            # Initialize the comboBoxes
            self.populate_dev_combobox()
            self.populate_gpp_4323_combobox()

            # Initialize the acquisition time
            self.required_time()

            # Initialize the image to black
            self.image_display(
                np.zeros(self.spinBox_image_size.value() ** 2, dtype=np.uint8).reshape(self.spinBox_image_size.value(),
                                                                                       self.spinBox_image_size.value()))
            # Initialize the connections window
            self.Source_Lenses = Source_Lenses.Window()

        except Exception as e:
            self.message('Error', f"Failed during the initialisation process : {e}")

    def provide_data(self):
        """
        Gathers and sends configuration data to the write window.

        This method is designed to collect data relevant to the write window configuration,
        specifically the selected channels for Left-Right and Up-Down signals and the desired
        sampling frequency. It checks if the current configuration is valid through `is_config_good`.
        If valid, it compiles this data into a list and emits it using a signal to a receiver.

        Raises:
        - Exception: Captures and handles any exceptions, displaying an error message with the
          details of the exception.
        """

        try:
            # Automatically send data back to SecondWindow when requested
            data = []
            channel_lr = self.comboBox_hs.currentText()
            channel_ud = self.comboBox_vs.currentText()
            sampling_frequency = self.spinBox_sampling_frequency.value()

            if self.is_config_good():
                data.append(channel_lr)
                data.append(channel_ud)
                data.append(sampling_frequency)
                self.send_data_signal.emit(data)

        except Exception as e:
            self.message('Error', f"An error occurred while sending data : {e}")

    # Function to quit the application
    def quit(self):
        """
        Function to quit the application safely.
        Disconnects from the power supply if connected before exiting.
        """

        try:
            if self.gpp_power_supply is not None:
                self.gpp_power_supply.disconnect()
            self.Source_Lenses.stop()
            self.WriteWindow.Stop_Signals()
            QtCore.QCoreApplication.instance().quit()

        except Exception as e:
            self.message('Error', f"An error occurred while quitting the application : {e}")

    # Function to display the Source_Lenses window
    def show_connections_window(self):
        """
        Function to display the "Source_Lenses" window to the user when the button is pressed
        """

        try:
            self.Source_Lenses.show()

        except Exception as e:
            self.message('Error', f"Couldn't show the Source_Lenses window : {e}")

    def show_write_window(self):
        """
        Function to display the "Write" window to the user when the button is pressed
        """

        try:
            self.WriteWindow.show()

        except Exception as e:
            self.message('Error', f"Couldn't show the Write window : {e}")

    #########################################################################################

    # NI connection part

    # Function to display the current available devices
    def populate_dev_combobox(self):
        """
        Populates the combobox with the names of National Instruments (NI) devices currently connected to the system.

        This method queries the local NI system for all connected devices and updates the combobox with their names.
        It is used to provide a selection of available NI devices for user interaction.
        """

        try:
            system = Ni_Dependencies.ni_cards_system()
            items = [device.name for device in system.devices]  # Lists the connected NI devices
            self.comboBox_dev.clear()  # Clear existing items
            self.comboBox_dev.addItems(items)  # Add new items

        except Exception as e:
            self.message('Error', f"Couldn't populate the NI card combo-box : {e}")

    # Connection to the NI Card and verification
    def connect_to_card(self):
        """
        Establishes a connection to the selected NI card and populates the corresponding combo-boxes for analog input
        and output channels.

        This method checks if the selected device from the combobox is currently connected. If so, it retrieves and
        lists the available analog output and input channels of the selected NI device in their respective combo-boxes.
        """

        try:
            self.port_dev = self.comboBox_dev.currentText()
            system = Ni_Dependencies.ni_cards_system()
            if (not self.comboBox_dev.currentText() in system.devices) or (
                    self.comboBox_dev.currentText() == ""):  # Checks if the device is connected
                self.message('Error', 'Wrong port choice')
                self.populate_dev_combobox()
                self.port_dev = None
            else:  # If the device is connected, we do this
                self.port_dev = self.comboBox_dev.currentText()
                device = Ni_Dependencies.ni_cards_device(self.port_dev)
                ao_channels = [chan.name for chan in
                               device.ao_physical_chans]  # Lists the available analog output channels
                ai_channels = [chan.name for chan in
                               device.ai_physical_chans]  # Lists the available analog input channels

                # Sets the maximum sampling frequency
                self.spinBox_sampling_frequency.setMaximum(int(device.ai_max_single_chan_rate))

                self.comboBox_vs.clear()  # Clear existing items
                self.comboBox_hs.clear()  # Clear existing items
                self.comboBox_vs.addItems(ao_channels)  # Add new items
                self.comboBox_hs.addItems(ao_channels)  # Add new items
                self.comboBox_sensor.clear()  # Clear existing items
                self.comboBox_sensor.addItems(ai_channels)  # Add new items

        except Exception as e:
            self.message('Error', f"Couldn't connect to the NI card : {e}")

    #########################################################################################
    # Gpp_4323 connection part

    # Thread to display the current available devices because slow response
    def populate_gpp_4323_combobox(self):
        """
        Initiates a background thread to populate the GPP 4323 combobox with available device names.

        This method starts a separate thread to retrieve the list of connected devices (specifically for GPP 4323) to
        prevent the GUI from freezing during this potentially time-consuming operation. The retrieved device names are
        then listed in the GPP 4323 combobox.
        """

        try:
            self.population_thread = Thread.Population()
            self.population_thread.list.connect(self.send_to_gpp_combobox)
            self.population_thread.errorOccurred.connect(self.handle_thread_errors)
            self.population_thread.finished.connect(self.thread_cleanup)
            self.population_thread.start()
        except Exception as e:
            self.message('Error', f"Couldn't populate GPP4323 combo-box : {e}")

    # Function to display the list to the comboBoxes
    def send_to_gpp_combobox(self, items):
        """
        Displays the list of connected VISA devices in the comboBox.

        Args:
        items (list): List of device names to be displayed in the comboBox.
        """

        self.comboBox_gpp_4323.clear()  # Clear existing items
        self.comboBox_gpp_4323.addItems(items)  # Add new items

    # Connection to the gpp_4323 and verification
    def connect_to_gpp_4323(self):
        """
        Handles the connection to the selected GPP4323 power supply.
        Validates the selection and updates the UI based on the connection status.
        """

        try:
            current_text = self.comboBox_gpp_4323.currentText()
            if current_text == '':
                self.message('Error', f"Please select something")
            else:
                self.gpp_power_supply = Visa_Dependencies.PowerSupply(current_text)

                error_checker = self.gpp_power_supply.connect()  # None if no error and "error message" otherwise
                if error_checker is None:
                    self.brightness_slider.setEnabled(True)  # Enables the brightness slider
                else:
                    self.message('Error', f'Failed to connect to GPP4323 : {error_checker}')
        except Exception as e:
            self.message('Error', f"Couldn't connect to GPP4323 : {e}")

    # Connection help button
    def gpp_4323_help(self):
        """
        Displays a help message regarding the connections for the GPP4323 power supply.
        """

        self.message('Help',
                     'Connect both CH1(-) and CH2(+) together.\n+32V is at CH1(+), 0V is at CH2(+) and -32V is at CH2(-).\nConnect the brown cable to CH4(+) and the blue cable to CH4(-).')

    #########################################################################################
    # Sliders part

    # Updates the label as the user changes the slider
    def gpp_4323_brightness_slider_changed(self):
        """
        Updates the label to display the current brightness tension value based on the slider's position.
        This function is called whenever the slider value changes.
        """

        try:
            tension = self.brightness_slider.value()  # Gets the value of the slider
            self.label_current_brightness.setText(
                f'Brightness tension (V) : {str(tension)}')  # Shows to the user the current tension
        except Exception as e:
            self.message('Error', f'Error in "gpp_4323_brightness_slider_changed": {e}')

    # Updates the value only when the user release the slider
    def gpp_4323_brightness_slider_released(self):
        """
        Updates the brightness tension of the GPP power supply when the slider is released. This function ensures
        that the power supply's tension is updated only when the user finishes adjusting the slider.
        """

        try:
            self.gpp_power_supply.set_tension(
                self.brightness_slider.value())  # Gets the value of the slider and send it to the power supply
        except Exception as e:
            self.message('Error', f'Error in "gpp_4323_brightness_slider_released": {e}')

    #########################################################################################
    # Sweep part

    def sweep(self):
        """
        Function to start the Sweep operation.
        Checks for valid configurations and starts the SweepThread and ProgressBarThread.
        """

        if self.is_config_good():
            try:
                # Gets the values from the comboBoxes
                time_per_pixel = self.spinBox_time_per_pixel.value()
                sampling_frequency = self.spinBox_sampling_frequency.value()
                pixels_number = self.spinBox_image_size.value()
                channel_lr = self.comboBox_hs.currentText()
                channel_ud = self.comboBox_vs.currentText()
                channel_read = self.comboBox_sensor.currentText()
                mode = self.comboBox_Scanning_Mode.currentText()
                # Sweep signal generation in a thread
                self.sweep_thread = Thread.SweepThread(time_per_pixel, sampling_frequency, pixels_number,
                                                       channel_lr,
                                                       channel_ud, channel_read, mode)
                self.sweep_thread.errorOccurred.connect(self.handle_thread_errors)
                self.sweep_thread.image.connect(self.image_display)
                self.sweep_thread.finished.connect(self.thread_cleanup)

                self.progressBarThread = Thread.ProgressBar(time_per_pixel, pixels_number)
                self.progressBarThread.progressUpdated.connect(self.update_progress_bar)
                self.progressBarThread.errorOccurred.connect(self.handle_thread_errors)
                self.progressBarThread.finished.connect(self.thread_cleanup)

                self.sweep_thread.start()
                self.progressBarThread.start()

            except Exception as e:
                self.message('Error', f"An error occurred during the sweep process : {e}")

    # If an error occurred in any thread, we display it to the user
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

    # Update the progression bar
    def update_progress_bar(self, value):
        """
        Updates the progress bar's value during the sweep process.

        This method is connected to the `progressUpdated` signal of the ProgressBar thread. It is
        called periodically to update the progress bar on the UI to reflect the current progress of
        the sweep operation.

        Parameters:
            value (int): The current progress value to set on the progress bar.
        """

        self.progressBar_sweep.setValue(value)

    #########################################################################################
    # Video Scanning part

    # Initialize and start the video
    def start_video(self):
        """
        Initializes and starts the video acquisition process by creating and starting a video thread.
        Before starting, it performs checks to ensure that the NI Card is connected, different channels are
        selected for horizontal and vertical sweeps, and the time per pixel is sufficient based on the sampling
        frequency. If any check fails, an error message is displayed. On successful start, it disables the start
        video button and enables the stop video button, along with disabling other relevant UI components to
        prevent conflicting operations.
        """

        if self.is_config_good():
            try:
                time_per_pixel = 4
                sampling_frequency = 250000
                pixels_number = self.video_resolution
                channel_lr = self.comboBox_hs.currentText()
                channel_ud = self.comboBox_vs.currentText()
                channel_read = self.comboBox_sensor.currentText()

                self.video_thread = Thread.VideoThread(time_per_pixel, sampling_frequency, pixels_number, channel_lr,
                                                       channel_ud, channel_read)
                self.video_thread.image.connect(self.video_display)
                self.video_thread.errorOccurred.connect(self.handle_thread_errors)
                self.video_thread.finished.connect(self.thread_cleanup)
                self.video_thread.start()

                # Change buttons states
                self.pushButton_start_video.setEnabled(False)
                self.pushButton_stop_video.setEnabled(True)
                self.pushButton_sweep.setEnabled(False)
                self.pushButton_save_image.setEnabled(False)

            except Exception as e:
                self.message('Error', f"Couldn't start the video : {e}")

    # Stops the video
    def stop_video(self):
        """
        Stops the video acquisition process by signaling the video thread to stop.
        It tries to safely terminate the video thread and then resets the UI components to their initial state,
        enabling the start video button and disabling the stop video button, along with re-enabling other UI
        components for further operations. If stopping the video thread fails, an error message is displayed.
        """

        try:
            self.video_thread.stop()  # Stops the acquisition

            # Change buttons states
            self.pushButton_start_video.setEnabled(True)
            self.pushButton_stop_video.setEnabled(False)
            self.pushButton_sweep.setEnabled(True)
            self.pushButton_save_image.setEnabled(True)
        except Exception as e:
            self.message('Error', f"Couldn't stop the video : {e}")

    #########################################################################################
    # Image part

    # Display the image
    def image_display(self, np_image):
        """
        Function to display the image in the interface.
        Normalizes the values and updates the QPixmap with the new image.

        Args:
        image (numpy.ndarray): List of pixel values to be displayed.
        """

        try:
            pixels_number = self.spinBox_image_size.value()

            self.currentImage = np_image  # Useful to save the image
            stride = pixels_number  # Number of bytes per line for a grayscale image
            q_image = QImage(np_image.data, pixels_number, pixels_number, stride, QImage.Format.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_image)
            pixmap = pixmap.scaled(self.QPixmap_ui.width(), self.QPixmap_ui.height(),
                                   Qt.AspectRatioMode.KeepAspectRatio)
            self.QPixmap_ui.setPixmap(pixmap)
            self.repaint()

        except Exception as e:
            self.message('Error', f" Couldn't display the image : {e}")

    def video_display(self, np_image):
        """
        Function to display the image in the interface in case of video scanning.
        Normalizes the values and updates the QPixmap with the new image.

        Args:
        image (numpy.ndarray): List of pixel values to be displayed.
        """

        try:
            pixels_number = self.video_resolution

            stride = pixels_number  # Number of bytes per line for a grayscale image
            q_image = QImage(np_image.data, pixels_number, pixels_number, stride, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            pixmap = pixmap.scaled(self.QPixmap_ui.width(), self.QPixmap_ui.height(),
                                   Qt.AspectRatioMode.KeepAspectRatio)
            self.QPixmap_ui.setPixmap(pixmap)
            self.repaint()

        except Exception as e:
            self.message('Error', f" Couldn't display the image : {e}")

    # Save the image
    def save_image(self):
        """
        Function to save the current image displayed in the interface.
        Opens a dialog to choose the file location and format.
        """

        try:
            # Get the save name
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Image", "",
                                                                "PNG Files (*.png);;JPEG Files (*.jpeg);;BMP Files ("
                                                                "*.bmp);;TIFF Files (*.tiff);;All Files (*)")
            if filename:
                # Save the image currently displayed on the QPixmap
                img = Image.fromarray(self.currentImage)
                img.save(filename)
        except Exception as e:
            self.message('Error', f"Failed to save image : {e}")

    #########################################################################################
    # Config part

    def is_config_good(self):
        """Checks if the current configuration is valid.

        Returns:
            bool: True if the configuration is valid, False otherwise.
        """

        try:
            # Check if NI Card is connected
            if self.port_dev is None:
                self.message('Error', "Please connect to the NI Card first.")
                return False

            # Check if different channels are selected for horizontal and vertical sweep
            if self.comboBox_hs.currentText() == self.comboBox_vs.currentText():
                self.message('Error', "Please choose different channels for horizontal and vertical sweep.")
                return False

            # Check if the time per pixel is sufficient given the sampling frequency
            min_time_per_pixel = ceil(1000000 / self.spinBox_sampling_frequency.value())
            if self.spinBox_time_per_pixel.value() < min_time_per_pixel:
                self.message('Error', f"You must have at least {min_time_per_pixel} µs per pixel.")
                return False

            # Check if GPP power supply is connected
            #            if self.gpp_power_supply is None:
            #                self.message('Error', "Please connect to GPP power supply first.")
            #                return False

            # If all checks pass
            return True
        except Exception as e:
            self.message('Error', f"An error occurred during configuration validation: {str(e)}")

    def save_config(self):
        """
        Function to save the current configuration to a JSON file.
        Extracts values from UI elements and writes them to 'config.json'.
        """

        try:
            # Gets the values from the UI
            config = {
                "time_per_pixel": self.spinBox_time_per_pixel.value(),
                "sampling_frequency": self.spinBox_sampling_frequency.value(),
                "pixels_number": self.spinBox_image_size.value(),
                "channel_lr": self.comboBox_hs.currentText(),
                "channel_ud": self.comboBox_vs.currentText(),
                "channel_read": self.comboBox_sensor.currentText(),
                "port_dev": self.comboBox_dev.currentText(),
                "gpp_power_supply": self.comboBox_gpp_4323.currentText()
            }

            # Saves into a json file
            with open('config.json', 'w') as config_file:
                json.dump(config, config_file)
            self.message('Success', "Config saved successfully")

        except Exception as e:
            self.message('Error', f"Couldn't save config : {e}")

    def load_config(self):
        """
        Function to load configuration from a JSON file.
        Reads 'config.json' and updates the UI elements with stored values.
        """

        try:
            # Loads the json config file
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)

            # Updates the UI
            self.spinBox_time_per_pixel.setValue(config.get("time_per_pixel", 0))
            self.spinBox_sampling_frequency.setValue(config.get("sampling_frequency", 0))
            self.spinBox_image_size.setValue(config.get("pixels_number", 0))
            self.comboBox_dev.setCurrentText(config.get("port_dev", ""))
            self.connect_to_card()
            self.comboBox_hs.setCurrentText(config.get("channel_lr", ""))
            self.comboBox_vs.setCurrentText(config.get("channel_ud", ""))
            self.comboBox_sensor.setCurrentText(config.get("channel_read", ""))
            self.comboBox_gpp_4323.setCurrentText(config.get("gpp_power_supply", ""))
            self.connect_to_gpp_4323()

        # Handles errors
        except FileNotFoundError:
            self.message('Error', "Configuration file not found.")
        except json.JSONDecodeError:
            self.message('Error', "Error reading the configuration file.")
        except Exception as e:
            self.message('Error', f"Failed to load the config : {e}")

    #########################################################################################
    # Others part

    # Error message that doesn't freeze the interface
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

    # Clean up the used thread resources
    def thread_cleanup(self):
        """
        Cleans up the resources used by finished threads.

        This method is typically connected to the 'finished' signal of QThread objects. It ensures
        that thread objects are deleted safely after their execution is complete, helping to free up
        resources and prevent memory leaks.
        """

        try:
            sender = self.sender()  # Retrieves the object that emitted the signal (in this case, the finished thread)
            if sender:
                sender.deleteLater()  # Safely deletes the thread object to free up resources

        except Exception as e:
            self.message('Error', f"An error occurred while cleaning up a thread : {e}")

    # Calculation of the required time
    def required_time(self):
        """
        Calculates and displays the required time for the sweep operation.

        This method calculates the total time required for the sweep operation based on the
        time per pixel and the total number of pixels. It updates the UI to display this
        information in a user-friendly format.
        """

        try:
            pixels_number = self.spinBox_image_size.value()
            if self.comboBox_Scanning_Mode.currentText() == 'Normal':
                pixels_number += 2
            sampling_frequency = self.spinBox_sampling_frequency.value()

            # Changes the step "time_per_pixel" can take
            min_time_per_pixel = int(1000000 / sampling_frequency)
            self.spinBox_time_per_pixel.setSingleStep(min_time_per_pixel)
            self.spinBox_time_per_pixel.setMinimum(min_time_per_pixel)
            self.spinBox_time_per_pixel.setMaximum(min_time_per_pixel * 100)

            # Calculate and display the number of time we average
            time_per_pixel = self.spinBox_time_per_pixel.value()
            time_per_pixel = time_per_pixel / 1000000  # s to µs
            average = int(time_per_pixel * sampling_frequency)

            # Setting average measure text
            if average == 1:
                self.label_average.setText(f"Taking 1 measure")
            else:
                self.label_average.setText(f"Taking {str(average)} measures")

            # Calculating acquisition time
            total_seconds = time_per_pixel * pixels_number ** 2

            # Displaying acquisition time
            if total_seconds < 0.001:  # Less than 1 millisecond
                microseconds = int(total_seconds * 1000000)  # Convert to microseconds
                result_str = f"{microseconds} µs"
            elif total_seconds < 1:  # Less than 1 second, but more than 1 millisecond
                milliseconds = int(total_seconds * 1000)  # Convert to milliseconds
                result_str = f"{milliseconds} ms"
            elif total_seconds < 60:  # Less than 60 seconds
                result_str = f"{int(total_seconds)} seconds"
            else:  # 60 seconds or more
                minutes = int(total_seconds) // 60
                remaining_seconds = int(total_seconds) % 60
                result_str = f"{minutes}mn {remaining_seconds}s"

            self.label_time.setText(f"Acquisition time : {result_str}")

        except Exception as e:
            self.message('Error', f"Failed during the calculation of the required acquisition time : {e}")


#########################################################################################

# Main function
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)  # Create a Qt application

    writeWindow = Draw.Write_Interface.WriteWindow()    # Create an instance of WriteWindow
    mainWindow = MainWindow(writeWindow)  # Create an instance of MainWindow

    mainWindow.send_data_signal.connect(writeWindow.receive_data)   # Send data to the WriteWindow

    mainWindow.show()  # Show the window
    sys.exit(app.exec())  # Start the application event loop
