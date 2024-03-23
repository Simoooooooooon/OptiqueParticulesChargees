# @author: Leo CHAKRI

import time
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox
import serial
from serial import SerialException
from threading import Thread, Lock

# Load the UI file created with QT Designer
Ui_MainWindow, _ = uic.loadUiType("Source_Lenses.ui")


class Window(QtWidgets.QMainWindow, Ui_MainWindow):  # Creation of the window class

    def __init__(self):  # Init function (variables, window, controls)
        """
        Initializes the main window, setting up UI components, establishing connections between UI elements
        and their respective functions, and initializing instance variables for managing state, communication ports,
        and thread locks for concurrent operations. The initialization process includes setting voltage ranges,
        configuring initial communication states, disabling certain UI elements until devices are connected,
        and connecting UI events to their corresponding methods.
        """

        try:
            # Window Init
            QtWidgets.QMainWindow.__init__(self)
            Ui_MainWindow.__init__(self)
            self.setupUi(self)
            self.setWindowTitle("Source and lenses control")  # Set window title

            # Initialize communication state flags and instance variables
            self.VRange = [0, 10000]  # Voltage range for all power supplies

            # Communication states with the source (energy, extractor, suppressor and condenser (L1)) and the L2
            self.Source_state = False
            self.L2_state = False
            self.Source_connection_tried = False
            self.L2_connection_tried = False
            self.Source_port_survive = True
            self.L2_port_survive = True

            # Configure initial UI element states
            self.L2_COM_Status.setEnabled(False)
            self.L2_COM_Status.setChecked(False)
            self.Source_COM_Status.setEnabled(False)
            self.Source_COM_Status.setChecked(False)
            self.Source_Gun_Status.setEnabled(False)
            self.Source_Gun_Status.setChecked(False)

            # Disable control buttons until devices are connected
            self.Source_Gun.setEnabled(False)
            self.Source_PowerSuppliesControl.setEnabled(False)
            self.L1.setEnabled(False)
            self.L2.setEnabled(False)
            self.Lenses_SendValues.setEnabled(False)

            # Connect UI elements to their respective functions
            self.Source_Connect.clicked.connect(self.connectSource)
            self.Source_Gun.clicked.connect(self.gun)
            self.L2_Connect.clicked.connect(self.connectL2)
            self.Source_SendValues.clicked.connect(self.setVoltageSource)
            self.Lenses_SendValues.clicked.connect(self.setVoltageLenses)
            self.Hide.clicked.connect(self.hide_window)

            # Initialize other instance variables for serial connections and threading
            self.Source_port = None
            self.Source_lock = None
            self.L1_voltage = None
            self.L2_voltage = None
            self.Suppressor_voltage = None
            self.Extractor_voltage = None
            self.Energy_voltage = None
            self.L2_thread = None
            self.L2_lock = None
            self.L2_port = None
            self.Source_thread = None

        except Exception as e:
            raise Exception(f"\nCouldn't initialize the Source/Lenses UI : {e}")

    def connectSource(self):
        """
        Toggles the connection state of the source power supply. If already connected, it disconnects and resets the UI.
        If not connected, it attempts to establish a serial connection based on the selected COM port, configuring
        the power supply for operation and updating the UI to reflect the connection status.
        """

        try:
            if self.Source_connection_tried:
                self.Source_Connect.setText("Connect")
                self.Source_port.close()
                self.Source_connection_tried = False

            else:
                try:
                    self.Source_port = serial.Serial(port=self.Source_COM_Choice.currentText(), baudrate=57600,
                                                     bytesize=8, timeout=0.5, stopbits=1)
                    self.Source_COM_Status.setChecked(True)
                    self.Source_connection_tried = True
                    self.Source_Connect.setText("Disconnect")

                except SerialException:
                    QMessageBox.information(self, 'Communication Error', 'Wrong port choice or power supply off.')
                    self.Source_COM_Status.setChecked(False)

                if self.Source_COM_Status.isChecked():
                    self.Source_port.write(b'>3,17,0,100,100,65,65,65,65,1.0,1.0,1\r')
                    if self.Source_port.readline() != b'>3,17,2\r':
                        QMessageBox.information(self, 'Power Supply Error',
                                                'High Voltages Power Supply could not be activated.')
                    else:
                        self.Source_Gun.setEnabled(True)
                        self.Source_state = True

                        self.Source_lock = Lock()
                        self.Source_thread = Thread(target=self.Source_Readingloop,
                                                    args=(self.Source_port, self.Source_lock))
                        self.Source_thread.start()

        except Exception as e:
            self.message('Error', f"Failed to connect to the source : {e}")

    def gun(self):
        """
        Toggles the state of the gun power supply. If the gun is currently activated, it deactivates it, and vice versa.
        Updates the gun status button text and enabled state of related controls based on the gun's current state.
        """

        try:
            if self.Source_Gun_Status.isChecked():
                self.Source_port.write(b'>1,10,0\r')  # CMD_SET_GUN_STATUS Off
                self.Source_Gun.setText("Gun ON")
                self.Source_Gun_Status.setChecked(False)
                self.L1.setEnabled(False)
                self.Source_PowerSuppliesControl.setEnabled(False)
                self.Lenses_SendValues(False)

            else:
                self.Source_port.write(b'>1,10,2\r')  # CMD_SET_GUN_STATUS On
                self.Source_Gun.setText("Gun OFF")
                self.Source_Gun_Status.setChecked(True)
                self.L1.setEnabled(True)
                self.Source_PowerSuppliesControl.setEnabled(True)
                self.Lenses_SendValues(True)

        except Exception as e:
            self.message('Error', f"Failed to toggle the gun : {e}")

    def connectL2(self):
        """
        Toggles the connection state of the L2 power supply. Similar to connectSource, it either disconnects or
        attempts to establish a serial connection based on the selected COM port, updating the UI to reflect the
        connection status.
        """

        try:
            if self.L2_connection_tried:
                self.L2_Connect.setText("Connect")
                self.L2_port.close()
                self.L2_connection_tried = False

            else:
                try:
                    self.L2_port = serial.Serial(port=self.L2_COM_Choice.currentText(), baudrate=57600, bytesize=8,
                                                 timeout=0.05, stopbits=1)  # Open and configure the port
                    self.L2_COM_Status.setChecked(True)
                    self.L2_connection_tried = True
                    self.L2_Connect.setText("Disconnect")

                except SerialException:
                    QMessageBox.information(self, 'Communication Error', 'Wrong port choice or power supply off.')
                    self.L2_COM_Status.setChecked(False)

                if self.L2_COM_Status.isChecked():
                    self.L2_port.write(b'>1,10,2\r')
                    if self.L2_port.readline() != b'>1,10,2\r':
                        QMessageBox.information(self, 'Power Supply Error',
                                                'High Voltages Power Supply could not be activated.')
                    else:
                        self.L2.setEnabled(True)
                        self.Lenses_SendValues(True)
                        self.L2_state = True

                        self.L2_lock = Lock()
                        self.L2_thread = Thread(target=self.L2_Readingloop, args=(self.L2_port, self.L2_lock))
                        self.L2_thread.start()

        except Exception as e:
            self.message('Error', f"Failed to connect to L2 lens : {e}")

    def setVoltageSource(self):
        """
        Sets the voltage for the energy, extractor, and suppressor based on user input, if within the specified range.
        Displays an error message if the set voltage is out of range.
        """

        try:
            self.Energy_voltage = self.Energy_TargetVoltage.value()
            self.Extractor_voltage = self.Extractor_TargetVoltage.value()
            self.Suppressor_voltage = self.Suppressor_TargetVoltage.value()

            if self.VRange[0] <= self.Energy_voltage <= self.VRange[1]:
                self.Source_port.write(b'>1,1,%f,0\r' % float(self.Energy_voltage))  # CMD_SET_VOLTAGE for Energy

            elif self.VRange[0] <= self.Extractor_voltage <= self.VRange[1]:
                self.Soure_port.write(b'>3,1,%f,0\r' % float(self.Extractor_voltage))  # CMD_SET_VOLTAGE for Extractor

            elif self.Suppressor_voltage >= self.VRange[0] and self.Energy_voltage <= self.VRange[1]:
                self.Source_port.write(b'>2,1,%f,0\r' % float(self.Energy_voltage))  # CMD_SET_VOLTAGE for Suppressor

            else:
                QMessageBox.information(self, 'Source Voltage Error', 'The voltage you are trying to set is out of '
                                                                      'range.')

        except Exception as e:
            self.message('Error', f"Failed to set source voltage : {e}")

    def setVoltageLenses(self):
        """
        Sets the voltage for L2 and L1 lenses based on user input, if within the specified range and if the relevant
        power supply is connected. Displays an error message if the set voltage is out of range or the power supply
        is not connected.
        """

        try:
            self.L2_voltage = self.L2_TargetVoltage.value()
            self.L1_voltage = self.L1_TargetVoltage.value()

            if self.VRange[0] <= self.L2_voltage <= self.VRange[1] and self.L2_state:
                self.L2_port.write(b'>1,1,%f,0\r' % float(self.voltage))

            elif self.VRange[0] <= self.L1_voltage <= self.VRange[1] and self.Source_state:
                self.Source_port.write(b'>4,1,%f,0\r' % float(self.L1_voltage))  # CMD_SET_VOLTAGE for L1

            else:
                QMessageBox.information(self, 'Lenses Voltage Error', 'The voltage you are trying to set is out of '
                                                                      'range.')

        except Exception as e:
            self.message('Error', f"Failed to set source voltage : {e}")

    def Source_Readingloop(self, port, lock):
        """
        Continuously reads and updates the actual voltage and current values from the source power supply. This loop
        runs in a separate thread and updates the UI with the most recent measurements.
        """

        try:
            while self.Source_port_survive:
                lock.acquire()

                port.write(b'>1,2\r')
                energy_line = str(port.readline())
                if len(energy_line) > 3:
                    self.label_Actual_Voltage.setText(energy_line.split(",")[2])
                    self.label_Actual_Current.setText(energy_line.split(",")[3])

                port.write(b'>3,2\r')
                extractor_line = str(port.readline())
                if len(extractor_line) > 3:
                    self.label_Actual_Voltage.setText(extractor_line.split(",")[2])
                    self.label_Actual_Current.setText(extractor_line.split(",")[3])

                port.write(b'>2,2\r')
                suppressor_line = str(port.readline())
                if len(suppressor_line) > 3:
                    self.label_Actual_Voltage.setText(suppressor_line.split(",")[2])
                    self.label_Actual_Current.setText(suppressor_line.split(",")[3])

                port.write(b'>4,2\r')
                l1_line = str(port.readline())
                if len(l1_line) > 3:
                    self.label_Actual_Voltage.setText(l1_line.split(",")[2])
                    self.label_Actual_Current.setText(l1_line.split(",")[3])

                lock.release()
                time.sleep(1.1)

        except Exception as e:
            self.message('Error', f"Error within the source's current reading loop : {e}")

    def L2_Readingloop(self, port, lock):
        """
        Continuously reads and updates the actual voltage and current values from the L2 power supply. Similar to
        Source_Readingloop, this function runs in a separate thread and ensures the UI is updated with the latest
        measurements.
        """

        try:
            while self.L2_port_survive:
                lock.acquire()

                port.write(b'>1,2\r')
                line = str(port.readline())
                if len(line) > 3:
                    self.label_Actual_Voltage.setText(line.split(",")[2])
                    self.label_Actual_Current.setText(line.split(",")[3])

                lock.release()
                time.sleep(1.1)

        except Exception as e:
            self.message('Error', f"Error within the L2 lens current reading loop : {e}")

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

    # Function to hide the window
    def hide_window(self):
        """
        Hides the main window, providing a way to minimize the application without stopping any ongoing operations.
        """
        try:
            super().hide()

        except Exception as e:
            self.message('Error', f"Couldn't hide the window : {e}")

    # Function called when stopping the program
    def stop(self):
        """
        Gracefully stops all operations by sending shutdown commands to the connected power supplies, closing
        any open serial connections, and terminating any running threads. This method ensures the application
        closes cleanly and safely.
        """

        try:
            if self.Source_COM_Status.isChecked():
                self.Source_port.write(b'>1,1,0,0\r')
                self.Source_port.write(b'>1,10,0\r')
                self.Source_port.write(b'>3,1,0,0\r')
                self.Source_port.write(b'>3,10,0\r')
                self.Source_port.write(b'>2,1,0,0\r')
                self.Source_port.write(b'>2,10,0\r')
                self.Source_port.write(b'>4,1,0,0\r')
                self.Source_port.write(b'>4,10,0\r')

            if self.Source_Gun_Status.isChecked():
                self.Source_port.write(b'>1,10,0\r')

            if self.L2_COM_Status.isChecked():
                self.L2_port.write(b'>1,1,0,0\r')
                self.L2_port.write(b'>1,10,0\r')

            if self.Source_connection_tried:
                self.Source_port.close()

            if self.L2_connection_tried:
                self.L2_port.close()

            self.Source_port_survive = False
            self.L2_port_survive = False
            QtWidgets.QMainWindow.close(self)

        except Exception as e:
            self.message('Error', f"An error occurred while closing the program : {e}")

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
