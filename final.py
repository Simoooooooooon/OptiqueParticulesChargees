import nidaqmx
import sys
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, Qt
import pyvisa
import warnings
import Sweep
import time
import numpy as np
from PIL import Image
import json
import math


# Ignores the ResourceWarnings made by PyVISA library
warnings.simplefilter("ignore", ResourceWarning)

# Load the UI file created with QT Designer
Ui_MainWindow, QtBaseClass = uic.loadUiType("final.ui")


# Main class for the interface
class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    listChanged = QtCore.pyqtSignal(list)  # Signal to emit acquired data

    # Initialize the interface
    def __init__(self):
        super(MyWindow, self).__init__()  # Initialize the parent class
        self.setupUi(self)  # Load the UI
        self.setWindowTitle("Interface de pilotage du FIB")  # Set window title

        # Connect buttons to their respective functions
        self.pushButton_quit.clicked.connect(self.quit)
        self.pushButton_dev_refresh.clicked.connect(self.populate_dev_combobox)
        self.pushButton_connect_dev.clicked.connect(self.connect_to_card)
        self.pushButton_gpp_4323_refresh.clicked.connect(self.populate_gpp_4323_combobox)
        self.pushButton_connect_gpp_4323.clicked.connect(self.connect_to_gpp_4323)
        self.pushButton_connect_gpp_4323_help.clicked.connect(self.gpp_4323_help)
        self.pushButton_sweep.clicked.connect(self.Sweep)
        self.pushButton_save_image.clicked.connect(self.saveImage)
        self.pushButton_load_config.clicked.connect(self.loadConfig)
        self.pushButton_save_config.clicked.connect(self.saveConfig)

        # Connect sliders to their respective functions
        self.brightness_slider.valueChanged.connect(self.gpp_4323_brightness_slider_changed)
        self.brightness_slider.sliderReleased.connect(self.gpp_4323_brightness_slider_released)

        # Ensure required time recalculation after modification
        self.spinBox_time_per_pixel.valueChanged.connect(self.required_time)
        self.spinBox_image_size.valueChanged.connect(self.required_time)

        # Initialize instance variables
        self.port_dev = None
        self.gpp_power_supply = None
        self.sweep_thread = None
        self.population_thread = None
        self.progressBarThread = None
        self.currentImage = None

        # Initialize the comboBoxes
        self.populate_dev_combobox()
        self.populate_gpp_4323_combobox()

        # Initialize the required time
        self.required_time()

        # Initialize the image to black
        self.displayImage(np.zeros(self.spinBox_image_size.value()**2, dtype=np.uint8))

    # Function to quit the application

    def quit(self):
        if self.gpp_power_supply is not None:
            self.gpp_power_supply.disconnect()
        QtCore.QCoreApplication.instance().quit()

    #########################################################################################
    # NI connection part

    # Function to display the current available devices
    def populate_dev_combobox(self):
        try:
            system = nidaqmx.system.System.local()
            items = [device.name for device in system.devices]  # Lists the connected NI devices
            self.comboBox_dev.clear()  # Clear existing items
            self.comboBox_dev.addItems(items)  # Add new items

        except Exception as e:
            self.Message('Error', f"populate_dev_combobox function returned : {e}")

    # Connection to the NI Card and verification
    def connect_to_card(self):
        try:
            self.port_dev = self.comboBox_dev.currentText()
            system = nidaqmx.system.System.local()
            if (not self.comboBox_dev.currentText() in system.devices) or (
                    self.comboBox_dev.currentText() == ""):  # Checks if the device is connected
                self.Message('Error', 'Wrong port choice')
                self.populate_dev_combobox()
                self.port_dev = None
            else:  # If the device is connected, we do this
                self.port_dev = self.comboBox_dev.currentText()
                device = nidaqmx.system.Device(self.port_dev)
                ao_channels = [chan.name for chan in
                               device.ao_physical_chans]  # Lists the available analog output channels
                ai_channels = [chan.name for chan in
                               device.ai_physical_chans]  # Lists the available analog input channels
                self.comboBox_vs.clear()  # Clear existing items
                self.comboBox_hs.clear()  # Clear existing items
                self.comboBox_vs.addItems(ao_channels)  # Add new items
                self.comboBox_hs.addItems(ao_channels)  # Add new items
                self.comboBox_sensor.clear()  # Clear existing items
                self.comboBox_sensor.addItems(ai_channels)  # Add new items

        except Exception as e:
            self.Message('Error', f"Connect_to_card function returned : {e}")

    #########################################################################################
    # Gpp_4323 connection part

    # Thread to display the current available devices because slow response
    def populate_gpp_4323_combobox(self):
        try:
            self.population_thread = Population()
            self.population_thread.list.connect(self.send_to_GPP_comboBox)
            self.population_thread.finished.connect(self.thread_cleanup)
            self.population_thread.start()
        except Exception as e:
            self.Message('Error', f"populate_gpp_4323_combobox function returned : {e}")

    # Function to display the list to the comboBoxes
    def send_to_GPP_comboBox(self, items):
        self.comboBox_gpp_4323.clear()  # Clear existing items
        self.comboBox_gpp_4323.addItems(items)  # Add new items

    # Connection to the gpp_4323 and verification
    def connect_to_gpp_4323(self):
        try:
            self.gpp_power_supply = PowerSupply(self.comboBox_gpp_4323.currentText())
            error_checker = self.gpp_power_supply.connect()  # None if no error and "error message" otherwise
            if error_checker is None:
                self.brightness_slider.setEnabled(True)  # Enables the brightness slider
            else:
                self.Message('Error', f'Failed to connect to GPP4323 : {error_checker}')
        except Exception as e:
            self.Message('Error', f"Connect_to_gpp_4323 function returned : {e}")

    # Connection help button
    def gpp_4323_help(self):
        self.Message('Help',
                     'Connect both CH1(-) and CH2(-) together and take your output between CH1(+) and CH2('
                     '+).\nConnect the electron detector to CH4.')

    #########################################################################################
    # Sliders part

    # Updates the label as the user changes the slider
    def gpp_4323_brightness_slider_changed(self):
        try:
            tension = self.brightness_slider.value()  # Gets the value of the slider
            self.label_current_brightness.setText(
                f'Brightness tension (V) : {str(tension)}')  # Shows to the user the current tension
        except Exception as e:
            self.Message('Error', f"Gpp_4323_brightness_slider_changed returned : {e}")

    # Updates the value only when the user release the slider
    def gpp_4323_brightness_slider_released(self):
        try:
            self.gpp_power_supply.set_tension(
                self.brightness_slider.value())  # Gets the value of the slider and send it to the power supply
        except Exception as e:
            self.Message('Error', f"Gpp_4323_brightness_slider_released returned : {e}")

    #########################################################################################
    # Sweep part
    def Sweep(self):
        if self.port_dev is None:
            self.Message('Error', f"Please connect to NI Card first")
        elif self.comboBox_hs.currentText() == self.comboBox_vs.currentText():
            self.Message('Error', f"Please choose different channels for horizontal and vertical sweep")
        elif self.gpp_power_supply is not None:
            self.Message('Error', f"Please connect to GPP power supply first")
        elif self.spinBox_time_per_pixel.value() < 1000000/self.spinBox_sampling_frequency.value():
            self.Message('Error', f"You must be at least have {math.ceil(1000000/self.spinBox_sampling_frequency.value())} µs per pixel")
        else:
            try:
                # Gets the values from the comboBoxes
                time_per_pixel = self.spinBox_time_per_pixel.value()
                sampling_frequency = self.spinBox_sampling_frequency.value()
                pixels_number = self.spinBox_image_size.value()
                channel_lr = self.comboBox_hs.currentText()
                channel_ud = self.comboBox_vs.currentText()
                channel_read = self.comboBox_sensor.currentText()

                # Sweep signal generation in a thread
                self.sweep_thread = SweepThread(time_per_pixel, sampling_frequency, pixels_number, channel_lr,
                                                channel_ud, channel_read)
                self.sweep_thread.errorOccurred.connect(self.handleSweepError)
                self.sweep_thread.image.connect(self.displayImage)
                self.sweep_thread.finished.connect(self.thread_cleanup)

                self.progressBarThread = ProgressBar(time_per_pixel, pixels_number)
                self.progressBarThread.progressUpdated.connect(self.updateProgressBar)
                self.progressBarThread.finished.connect(self.thread_cleanup)

                self.sweep_thread.start()
                self.progressBarThread.start()

            except Exception as e:
                self.Message('Error', f"Sweep function returned : {e}")

    # If an error occurred in the thread, we display it to the user
    def handleSweepError(self, error_message):
        self.Message('Error', f"Sweep function returned: {error_message}")

    # Update the progression bar
    def updateProgressBar(self, value):
        self.progressBar_sweep.setValue(value)

    #########################################################################################
    # Image part

    # Display the image
    def displayImage(self, image):
        try:
            pixels_number = self.spinBox_image_size.value()
            np_image = np.array(image).reshape(pixels_number, pixels_number)

            # Normalise the values between 0 and 255
            min_val = np_image.min()
            max_val = np_image.max()
            if max_val > min_val:
                np_image = ((np_image - min_val) / (max_val - min_val)) * 255
                np_image = np_image.astype(np.uint8)

            self.currentImage = np_image   # Useful to save the image

            stride = pixels_number  # Number of bytes per line for a grayscale image
            qImage = QImage(np_image.data, pixels_number, pixels_number, stride, QImage.Format.Format_Grayscale8)
            pixmap = QPixmap.fromImage(qImage)
            pixmap = pixmap.scaled(self.QPixmap_ui.width(), self.QPixmap_ui.height(),
                                   Qt.AspectRatioMode.KeepAspectRatio)
            self.QPixmap_ui.setPixmap(pixmap)
            self.repaint()

        except Exception as e:
            self.Message('Error', f" Couldn't display the image : {e}")

    # Save the image
    def saveImage(self):
        try:
            # Get the save name
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Image", "",
                                                                "PNG Files (*.png);;JPEG Files (*.jpeg);;All Files (*)")
            if filename:
                # Save the image currently displayed on the QPixmap
                img = Image.fromarray(self.currentImage)
                img.save(filename)
        except Exception as e:
            self.Message('Error', f"Failed to save image : {e}")

    #########################################################################################
    # Config part
    def saveConfig(self):
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
            self.Message('Success', "Config saved successfully")

        except Exception as e:
            self.Message('Error', f"Couldn't save config : {e}")

    def loadConfig(self):
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

        # Handles errors
        except FileNotFoundError:
            self.Message('Error', "Configuration file not found.")
        except json.JSONDecodeError:
            self.Message('Error', "Error reading the configuration file.")
        except Exception as e:
            self.Message('Error', f"Failed to load the config : {e}")

    #########################################################################################
    # Others part

    # Error message that doesn't freeze the interface
    def Message(self, title, message):
        # Create a non-modal message box
        msgBox = QtWidgets.QMessageBox(self)  # Message box
        msgBox.setIcon(QtWidgets.QMessageBox.Icon.Information)  # Icon
        msgBox.setText(message)  # Main message
        msgBox.setWindowTitle(title)  # Title of the window
        msgBox.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)  # Ok button
        msgBox.setModal(False)  # Make it non-modal
        msgBox.show()  # Show the message box

    # Clean up the used thread resources
    def thread_cleanup(self):
        sender = self.sender()  # Retrieves the object that emitted the signal (in this case, the finished thread)
        if sender:
            sender.deleteLater()  # Safely deletes the thread object to free up resources

    # Calculation of the required time
    def required_time(self):
        time_per_pixel = self.spinBox_time_per_pixel.value() / 1000000   # µs to s
        pixels_number = self.spinBox_image_size.value() + 2

        # Change the display format to minutes if there are more than 60 seconds required
        seconds = int(time_per_pixel * pixels_number ** 2)
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if minutes == 0:
            result_str = f"{remaining_seconds} seconds"
        else:
            result_str = f"{minutes}mn {remaining_seconds}s"

        self.label_time.setText(f"Acquisition time : {result_str}")   # Write the required time on the UI


#########################################################################################
# Classes


# Class for the GPP4323 power supply
class PowerSupply:
    def __init__(self, port):
        self.port = port
        self.device = None

    # Connects and initialise the power supply
    def connect(self):
        try:
            rm = pyvisa.ResourceManager()
            self.device = rm.open_resource(self.port)
            print(self.device.query('*IDN?'))
            print("A CHANGER IMPERATIVEMENT")
            self.device.write(f'ISET1:0.03')
            self.device.write(f'ISET2:0.03')
            self.device.write(f'ISET4:0.03')
            self.device.write(f'VSET1:32')
            self.device.write(f'VSET2:32')
            self.device.write(f'VSET3:0')
            self.device.write(f'VSET4:0')
            self.device.write(f':ALLOUTON')
        except Exception as e:
            return e

    # Sends to the power supply the requested tension
    def set_tension(self, tension):
        self.device.write(f'VSET4:{tension}')

    # Disconnects the power supply
    def disconnect(self):
        if self.device is not None:
            self.device.write(f'ISET1:0')
            self.device.write(f'ISET2:0')
            self.device.write(f'ISET4:0')
            self.device.write(f'VSET1:0')
            self.device.write(f'VSET2:0')
            self.device.write(f'VSET3:0')
            self.device.write(f'VSET4:0')
            self.device.write(f':ALLOUTOFF')
            self.device.close()


# Thread class for sweep
class SweepThread(QThread):
    errorOccurred = QtCore.pyqtSignal(str)  # Signal to handle possible errors
    image = QtCore.pyqtSignal(list)

    def __init__(self, time_per_pixel, sampling_frequency, pixels_number, channel_lr, channel_ud, channel_read,
                 parent=None):
        super(SweepThread, self).__init__(parent)  # Initialize the QThread parent class
        self.time_per_pixel = time_per_pixel
        self.sampling_frequency = sampling_frequency
        self.pixels_number = pixels_number
        self.channel_lr = channel_lr
        self.channel_ud = channel_ud
        self.channel_read = channel_read

    # Get the list of pixels and send it back
    def run(self):
        try:
            # Sweep signal generation from "Sweep.py"
            data = Sweep.Sweep(self.time_per_pixel, self.sampling_frequency, self.pixels_number, self.channel_lr,
                               self.channel_ud, self.channel_read)
            self.image.emit(data)
        except Exception as e:
            self.errorOccurred.emit(str(e))


# Thread class for GPP ComboBox population
class Population(QThread):
    list = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(Population, self).__init__(parent)  # Initialize the QThread parent class

    # Get the list of connected devices and send it back
    def run(self):
        rm = pyvisa.ResourceManager()
        items = rm.list_resources()  # Lists the connected VISA devices
        rm.close()
        self.list.emit(items)


# Thread class for the progress bar
class ProgressBar(QThread):
    progressUpdated = pyqtSignal(int)  # Signal to update the progression

    def __init__(self, time_per_pixel, pixels_number, parent=None):
        super(ProgressBar, self).__init__(parent)
        time_per_pixel = time_per_pixel / 1000000
        self.total_time = time_per_pixel * (pixels_number +2) ** 2
        self.interval = time_per_pixel  # Update interval

    # Calculates the percentage progress and send it back
    def run(self):
        start_time = time.time()
        while time.time() - start_time < self.total_time:
            elapsed_time = time.time() - start_time
            progress = int((elapsed_time / self.total_time) * 100)
            self.progressUpdated.emit(progress)
            time.sleep(self.interval)  # Wait for the next update
        self.progressUpdated.emit(100)


#########################################################################################


# Starts the interface
def run_interface():
    app = QtWidgets.QApplication(sys.argv)  # Create a Qt application
    window = MyWindow()  # Create an instance of MyWindow
    window.show()  # Show the window
    sys.exit(app.exec())  # Start the application event loop


# Main function
if __name__ == '__main__':
    run_interface()
