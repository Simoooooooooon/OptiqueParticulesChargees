import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import sys
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QApplication, QMainWindow
import pyvisa
import traceback

# Load the UI file created with QT Designer
Ui_MainWindow, QtBaseClass = uic.loadUiType("Interface_finale.ui")


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
        self.pushButton_gpp_2323_refresh.clicked.connect(self.populate_gpp_2323_combobox)
        self.pushButton_connect_gpp_2323.clicked.connect(self.connect_to_gpp_2323)
        self.pushButton_connect_gpp_2323_help.clicked.connect(self.gpp_2323_help)
        self.pushButton_gpp_4323_refresh.clicked.connect(self.populate_gpp_4323_combobox)
        self.pushButton_connect_gpp_4323.clicked.connect(self.connect_to_gpp_4323)
        self.pushButton_connect_gpp_4323_help.clicked.connect(self.gpp_4323_help)

        # Connect sliders to their respective functions
        self.gpp_2323_tension_slider.valueChanged.connect(self.gpp_2323_slider_changed)
        self.gpp_2323_tension_slider.sliderReleased.connect(self.gpp_2323_slider_released)
        self.gpp_4323_tension_slider.valueChanged.connect(self.gpp_4323_tension_slider_changed)
        self.gpp_4323_tension_slider.sliderReleased.connect(self.gpp_4323_tension_slider_released)
        self.brightness_slider.valueChanged.connect(self.gpp_4323_brightness_slider_changed)
        self.brightness_slider.sliderReleased.connect(self.gpp_4323_brightness_slider_released)

        # Initialize instance variables
        self.port_dev = None
        self.port_gpp_2323 = None
        self.port_gpp_4323 = None
        self.gpp_2323 = None
        self.gpp_4323 = None
        self.update_gpp_2323_thread = None
        self.update_gpp_4323_thread = None

        # Initialize the comboBoxes
        self.populate_dev_combobox()
        self.populate_gpp_2323_combobox()
        self.populate_gpp_4323_combobox()

    # Function to quit the application

    def quit(self):
        if self.gpp_2323 is not None:
            self.gpp_2323.write(f'ISET1:0')  # Fixes the maximum current so we can have a tension
            self.gpp_2323.write(f'ISET2:0')  # Fixes the maximum current so we can have a tension
            self.gpp_2323.write(f'VSET1:0')  # Sets the channel tension to 0V
            self.gpp_2323.write(f'VSET2:0')  # Sets the channel tension to 0V
            self.gpp_2323.write(f':ALLOUTOFF')  # Enables every channel
        if self.gpp_4323 is not None:
            self.gpp_4323.write(f'ISET1:0')  # Fixes the maximum current so we can have a tension
            self.gpp_4323.write(f'ISET2:0')  # Fixes the maximum current so we can have a tension
            self.gpp_4323.write(f'ISET4:0')  # Fixes the maximum current so we can have a tension
            self.gpp_4323.write(f'VSET1:0')  # Sets the channel tension to 0V
            self.gpp_4323.write(f'VSET2:0')  # Sets the channel tension to 0V
            self.gpp_4323.write(f'VSET3:0')  # Sets the channel tension to 0V
            self.gpp_4323.write(f'VSET4:0')  # Sets the channel tension to 0V
            self.gpp_4323.write(f':ALLOUTOFF')  # Enables every channel
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
            QtWidgets.QMessageBox.information(self, 'Error', f"populate_dev_combobox function returned : {e}")

    # Connection to the NI Card and verification
    def connect_to_card(self):
        try:
            self.port_dev = self.comboBox_dev.currentText()
            system = nidaqmx.system.System.local()
            if (not self.comboBox_dev.currentText() in system.devices) or (
                    self.comboBox_dev.currentText() == ""):  # Checks if the device is connected
                QtWidgets.QMessageBox.information(self, 'Error', 'Wrong port choice')
                self.populate_dev_combobox()
                self.port_dev = None
            else:  # If the device is connected, we do this
                self.port_dev = self.comboBox_dev.currentText()
                device = nidaqmx.system.Device(self.port_dev)
                ao_channels = [chan.name for chan in
                               device.ao_physical_chans]  # Lists the available analog output channels
                ai_channels = [chan.name for chan in
                               device.ai_physical_chans]  # Lists the available analog input channels
                self.comboBox_ao.clear()  # Clear existing items
                self.comboBox_ao.addItems(ao_channels)  # Add new items
                self.comboBox_ai.clear()  # Clear existing items
                self.comboBox_ai.addItems(ai_channels)  # Add new items

        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Connect_to_card function returned : {e}")

    #########################################################################################
    # Gpp_2323 connection part

    # Function to display the current available devices
    def populate_gpp_2323_combobox(self):
        try:
            rm = pyvisa.ResourceManager()
            items = rm.list_resources()  # Lists the connected VISA devices
            self.comboBox_gpp_2323.clear()  # Clear existing items
            self.comboBox_gpp_2323.addItems(items)  # Add new items

        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"populate_gpp_2323_combobox function returned : {e}")

    # Connection to the Gpp_2323 and verification
    def connect_to_gpp_2323(self):
        try:
            self.port_gpp_2323 = self.comboBox_gpp_2323.currentText()
            rm = pyvisa.ResourceManager()
            items = rm.list_resources()  # Lists the connected VISA devices
            if (not self.comboBox_gpp_2323.currentText() in items) or (
                    self.comboBox_gpp_2323.currentText() == ""):  # Checks if the device is connected
                QtWidgets.QMessageBox.information(self, 'Error', 'Wrong choice')
                self.populate_gpp_2323_combobox()
                self.port_gpp_2323 = None
            else:  # If the device is connected, we do this
                self.port_gpp_2323 = self.comboBox_gpp_2323.currentText()
                self.gpp_2323 = rm.open_resource(self.port_gpp_2323)
                print(self.gpp_2323.query('*IDN?'))
                try:
                    self.gpp_2323_tension_slider.setEnabled(True)  # Allow the user to use the slider
                    self.gpp_2323.write(f'ISET1:0.03')  # Fixes the maximum current so we can have a tension
                    self.gpp_2323.write(f'ISET2:0.03')  # Fixes the maximum current so we can have a tension
                    self.gpp_2323.write(f'VSET1:0')  # Sets the channel tension to 0V
                    self.gpp_2323.write(f'VSET2:0')  # Sets the channel tension to 0V
                    self.gpp_2323.write(f':ALLOUTON')  # Enables every channel
                except Exception as e:
                    QtWidgets.QMessageBox.information(self, 'Error', f"Couldn't connect to the instrument : {e}")
                    self.gpp_2323_tension_slider.setEnabled(False)  # Prevent the user from using the slider
                    self.populate_gpp_2323_combobox()
                    self.port_gpp_2323 = None

        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Connect_to_gpp_2323 function returned : {e}")

    # Connection help button
    def gpp_2323_help(self):
        QtWidgets.QMessageBox.information(self, 'Help',
                                          'Connect both CH1(-) and CH2(-) together and take your output between CH1(+) and CH2(+).')

    #########################################################################################
    # Gpp_4323 connection part

    # Function to display the current available devices
    def populate_gpp_4323_combobox(self):
        try:
            rm = pyvisa.ResourceManager()
            items = rm.list_resources()  # Lists the connected VISA devices
            self.comboBox_gpp_4323.clear()  # Clear existing items
            self.comboBox_gpp_4323.addItems(items)  # Add new items

        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"populate_gpp_4323_combobox function returned : {e}")

    # Connection to the gpp_4323 and verification
    def connect_to_gpp_4323(self):
        try:
            self.port_gpp_4323 = self.comboBox_gpp_4323.currentText()
            rm = pyvisa.ResourceManager()
            items = rm.list_resources()  # Lists the connected VISA devices
            if (not self.comboBox_gpp_4323.currentText() in items) or (
                    self.comboBox_gpp_4323.currentText() == ""):  # Checks if the device is connected
                QtWidgets.QMessageBox.information(self, 'Error', 'Wrong choice')
                self.populate_gpp_4323_combobox()
                self.port_gpp_4323 = None
            else:  # If the device is connected, we do this
                self.port_gpp_4323 = self.comboBox_gpp_4323.currentText()
                self.gpp_4323 = rm.open_resource(self.port_gpp_4323)
                print(self.gpp_4323.query('*IDN?'))
                try:
                    self.gpp_4323_tension_slider.setEnabled(True)  # Allow the user to use the slider
                    self.brightness_slider.setEnabled(True)  # Allow the user to use the slider
                    self.gpp_4323.write(f'ISET1:0.03')  # Fixes the maximum current so we can have a tension
                    self.gpp_4323.write(f'ISET2:0.03')  # Fixes the maximum current so we can have a tension
                    self.gpp_4323.write(f'ISET4:0.03')  # Fixes the maximum current so we can have a tension
                    self.gpp_4323.write(f'VSET1:0')  # Sets the channel tension to 0V
                    self.gpp_4323.write(f'VSET2:0')  # Sets the channel tension to 0V
                    self.gpp_4323.write(f'VSET3:0')  # Sets the channel tension to 0V
                    self.gpp_4323.write(f'VSET4:0')  # Sets the channel tension to 0V
                    self.gpp_4323.write(f':ALLOUTON')  # Enables every channel
                except Exception as e:
                    QtWidgets.QMessageBox.information(self, 'Error', f"Couldn't connect to the instrument : {e}")
                    self.gpp_4323_tension_slider.setEnabled(False)  # Prevent the user from using the slider
                    self.brightness_slider.setEnabled(False)  # Prevent the user from using the slider
                    self.populate_gpp_4323_combobox()
                    self.port_gpp_4323 = None

        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Connect_to_gpp_4323 function returned : {e}")

    # Connection help button
    def gpp_4323_help(self):
        QtWidgets.QMessageBox.information(self, 'Help',
                                          'Connect both CH1(-) and CH2(-) together and take your output between CH1(+) and CH2(+).\nConnect the electron detector to CH4.')

    #########################################################################################
    # Sliders part
    def gpp_2323_slider_changed(self):
        try:
            tension = self.gpp_2323_tension_slider.value()  # Gets the value of the slider
            self.label_current_tension_gpp_2323.setText(
                f'Supply voltage (V) : {str(tension)}')  # Shows to the user the current tension
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Gpp_2323_slider_changed returned : {e}")

    def gpp_2323_slider_released(self):
        try:
            tension = self.gpp_2323_tension_slider.value()  # Gets the value of the slider
            self.update_gpp_2323_thread = GPP2323UpdateThread(self.gpp_2323, tension)
            self.update_gpp_2323_thread.finished.connect(self.thread_cleanup)  # Cleans the thread when done
            self.update_gpp_2323_thread.start()  # Starts the thread
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Gpp_2323_slider_released returned : {e}")

    def gpp_4323_tension_slider_changed(self):
        try:
            tension = self.gpp_4323_tension_slider.value()  # Gets the value of the slider
            self.label_current_tension_gpp_4323.setText(
                f'Supply voltage (V) : {str(tension)}')  # Shows to the user the current tension
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Gpp_4323_slider_changed returned : {e}")

    def gpp_4323_tension_slider_released(self):
        try:
            tension = self.gpp_4323_tension_slider.value()  # Gets the value of the slider
            self.update_gpp_4323_thread = GPP4323UpdateThread(self.gpp_4323, tension)
            self.update_gpp_4323_thread.finished.connect(self.thread_cleanup)  # Cleans the thread when done
            self.update_gpp_4323_thread.start()  # Starts the thread
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Gpp_4323_slider_released returned : {e}")

    def gpp_4323_brightness_slider_changed(self):
        try:
            tension = self.brightness_slider.value()  # Gets the value of the slider
            self.label_current_brightness.setText(
                f'Brightness tension (V) : {str(tension)}')  # Shows to the user the current tension
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Gpp_4323_brightness_slider_changed returned : {e}")

    def gpp_4323_brightness_slider_released(self):
        try:
            tension = self.brightness_slider.value()  # Gets the value of the slider
            self.gpp_4323.write(f'VSET4:{tension}')
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Gpp_4323_brightness_slider_released returned : {e}")

    #########################################################################################
    # Multithreading part

    # Clean up the used thread resources
    def thread_cleanup(self):
        sender = self.sender()  # Retrieves the object that emitted the signal (in this case, the finished thread)
        if sender:
            sender.deleteLater()  # Safely deletes the thread object to free up resources


# Thread Class for Updating GPP2323's tension (-32V ; +32V)
class GPP2323UpdateThread(QThread):
    def __init__(self, gpp_2323, tension, parent=None):
        super(GPP2323UpdateThread, self).__init__(parent)  # Initialize the QThread parent class
        self.gpp_2323 = gpp_2323  # Stores the reference to the GPP2323 device object
        self.tension = tension  # Stores the tension value to be set

    def run(self):
        if self.tension >= 0:
            self.gpp_2323.write(f'VSET1:{self.tension}')
            self.gpp_2323.write(f'VSET2:0')
        else:
            self.gpp_2323.write(f'VSET1:0')
            self.gpp_2323.write(f'VSET2:{-self.tension}')


# Thread Class for Updating GPP4323's tension (-32V ; +32V)
class GPP4323UpdateThread(QThread):
    def __init__(self, gpp_4323, tension, parent=None):
        super(GPP4323UpdateThread, self).__init__(parent)  # Initialize the QThread parent class
        self.gpp_4323 = gpp_4323  # Stores the reference to the GPP4323 device object
        self.tension = tension  # Stores the tension value to be set

    def run(self):
        # Sends the value requested by the user to the device
        if self.tension >= 0:
            self.gpp_4323.write(f'VSET1:{self.tension}')
            self.gpp_4323.write(f'VSET2:0')
        else:
            self.gpp_4323.write(f'VSET1:0')
            self.gpp_4323.write(f'VSET2:{-self.tension}')

    #########################################################################################


# Starts the interface
def run_interface():
    try:
        app = QtWidgets.QApplication(sys.argv)  # Create a Qt application
        window = MyWindow()  # Create an instance of MyWindow
        window.show()  # Show the window
        sys.exit(app.exec())  # Start the application event loop
    except Exception as e:
        QtWidgets.QMessageBox.information(self, 'Error', f"Run_interface returned : {e}")


# Main function
if __name__ == '__main__':
    run_interface()
