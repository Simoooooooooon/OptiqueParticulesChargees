import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import sys
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtCore import QTimer
import pyqtgraph
import numpy as np

# Load the UI file created with QT Designer
Ui_MainWindow, QtBaseClass = uic.loadUiType("Interface_Lecture_Ecriture_NI.ui")


# Main class for the interface
class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    data_acquired = QtCore.pyqtSignal(list)  # Signal to emit acquired data

    # Initialize the interface
    def __init__(self):
        super(MyWindow, self).__init__()  # Initialize the parent class
        self.setupUi(self)  # Load the UI
        self.setWindowTitle("IHM")  # Set window title

        # Connect buttons to their respective functions
        self.pushButton_quit.clicked.connect(self.quit)
        self.pushButton_dev_refresh.clicked.connect(self.populate_dev_combobox)
        self.pushButton_connect.clicked.connect(self.connect_to_card)
        self.pushButton_reset.clicked.connect(self.reset)
        self.pushButton_write.clicked.connect(self.write)
        self.pushButton_clear_read.clicked.connect(self.clear_read)
        self.pushButton_clear_write.clicked.connect(self.clear_write)
        self.pushButton_start_read.clicked.connect(self.start_read)
        self.pushButton_stop_read.clicked.connect(self.stop_read)
        self.pushButton_test_sin.clicked.connect(self.sin_start)
        self.pushButton_stop_sin.clicked.connect(self.sin_stop)

        # Connect prompts to the function that handles their changes
        self.spinBox_freq.valueChanged.connect(self.freq_amp_changed)
        self.doubleSpinBox_ao.valueChanged.connect(self.freq_amp_changed)
        self.spinBox_write_freq_ech.valueChanged.connect(self.freq_amp_changed)
        self.comboBox_calibre.currentIndexChanged.connect(self.calibre_changed)

        # Initialize instance variables
        self.timer = None
        self.data_line2 = None
        self.sinus_thread = None
        self.data_line1 = None
        self.ai = None
        self.port_dev = None
        self.thread = {}
        self.Y_read = []
        self.Y_write_sin = []
        self.write_sin_task = nidaqmx.Task()
        self.read_task = nidaqmx.Task()
        self.calibre = self.comboBox_calibre.currentText()
        self.timer_data_acq = 2  # Time between every read acquisitions
        self.f_read_ech = self.spinBox_read_freq_ech.value()  # Get the reading frequency sampling rate
        self.samples_per_read = int(self.f_read_ech * self.timer_data_acq / 1000)
        self.populate_dev_combobox()

    # Function to quit the application
    def quit(self):
        try:
            QtCore.QCoreApplication.instance().quit()
            try:
                self.stop_read()
            except Exception as e:
                print('Cannot stop the timer because it does not exists :', e)
            self.read_task.stop()
            self.read_task.close()
            self.write_sin_task.stop()
            self.write_sin_task.close()
            self.reset()
            self.close()
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Quit function returned : {e}")

    #########################################################################################
    # Connection part

    # Function to display the current available devices
    def populate_dev_combobox(self):
        system = nidaqmx.system.System.local()
        items = [device.name for device in system.devices]
        self.comboBox_dev.clear()   # Clear existing items
        self.comboBox_dev.addItems(items)   # Add new items

    # Connection to the NI Card and verification
    def connect_to_card(self):
        try:
            self.port_dev = self.comboBox_dev.currentText()
            system = nidaqmx.system.System.local()
            if (not self.comboBox_dev.currentText() in system.devices) or (self.comboBox_dev.currentText() == ""):
                QtWidgets.QMessageBox.information(self, 'Error', 'Wrong port choice')
                self.populate_dev_combobox()
                self.port_dev = None
            else:
                self.port_dev = self.comboBox_dev.currentText()
                print(f"Connected to {self.port_dev}")
                device = nidaqmx.system.Device(self.port_dev)
                ao_channels = [chan.name for chan in device.ao_physical_chans]
                ai_channels = [chan.name for chan in device.ai_physical_chans]
                self.comboBox_ao.clear()  # Clear existing items
                self.comboBox_ao.addItems(ao_channels)  # Add new items
                self.comboBox_ai.clear()  # Clear existing items
                self.comboBox_ai.addItems(ai_channels)  # Add new items

        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Connect_to_card function returned : {e}")

    #########################################################################################
    # Single value analog write part

    # Write the analog tension to the corresponding card/port
    def write(self, value=None):
        try:
            # Gets and converts the values to write an analog tension
            if value is False:
                write_ao = float(self.doubleSpinBox_ao.text().replace(',', '.'))
            else:
                write_ao = value

            if self.port_dev is not None:
                print(f"Writing {write_ao} to {self.port_dev}/{self.comboBox_ao.currentText()}")
                with nidaqmx.Task() as write_task:
                    write_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/{self.comboBox_ao.currentText()}")
                    write_task.write(write_ao)
            else:
                QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Write function returned : {e}")

    #########################################################################################
    # Reading part

    # Get the channel and the calibre then start a thread
    def start_read(self):
        try:
            if self.port_dev is not None:
                f_read_ech = self.spinBox_read_freq_ech.value()  # Get the reading frequency sampling rate
                time = self.timer_data_acq  # Time between every data acquisition in ms
                self.ai = self.comboBox_ai.currentText()
                self.calibre = self.comboBox_calibre.currentText()
                self.clear_read()

                self.read_task.ai_channels.add_ai_voltage_chan(
                    f"{self.port_dev}/{self.ai}",
                    min_val=-float(self.calibre),
                    max_val=float(self.calibre),
                    terminal_config=TerminalConfiguration.DIFF
                )

                self.read_task.timing.cfg_samp_clk_timing(
                    rate=f_read_ech,
                    sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS
                )

                self.read_task.start()

                self.timer = QTimer(self)
                self.timer.timeout.connect(self.acquire_data)
                self.timer.start(time)

                self.prepare_plot_read()
                self.data_acquired.connect(self.plot_read)
                self.update_read_button_states(False, True)  # Switch button states

            else:
                QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Start_read function returned : {e}")

    # Gets the data from the card buffer
    def acquire_data(self):
        try:
            val = self.read_task.read(number_of_samples_per_channel=self.samples_per_read)
            self.data_acquired.emit(val)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Acquire_data function returned : {e}")

    # Stops the reading
    def stop_read(self):
        try:
            self.Y_read.clear()  # Clear the read buffer
            self.timer.stop()  # Stop the QTimer
            self.read_task.stop()  # Stop the NI task

            self.read_task.close()  # Close the NI task

            self.read_task = nidaqmx.Task()  # Initialize a new empty task
            self.update_read_button_states(True, False)  # Update the button states
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Stop_read function returned : {e}")

    # Dynamically changes the calibre
    def calibre_changed(self):
        try:
            self.read_graph.setYRange(-float(self.calibre), float(self.calibre))
            if self.timer is not None:  # Prevent an error
                if self.timer.isActive():  # If there is a timer running
                    self.stop_read()
                    self.start_read()
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Calibre_changed function returned : {e}")

    #########################################################################################
    # Sinus writing part

    # Sends a sin function to be written
    def sin_start(self):
        try:
            if self.port_dev is not None:
                self.update_write_button_states(False, True)
                freq = self.spinBox_freq.value()
                freq_ech = self.spinBox_write_freq_ech.value()
                amp = self.doubleSpinBox_ao.value()
                temps = np.linspace(0, 1 / freq, int(freq_ech / freq), endpoint=False)
                temps_graph = np.linspace(0, 1 / freq, int(freq_ech), endpoint=False)
                signal = amp * np.sin(2 * np.pi * freq * temps)
                signal_graph = amp * np.sin(2 * np.pi * freq * temps_graph)
                self.Y_write_sin = signal_graph.tolist()
                self.write_sin_task = nidaqmx.Task()
                self.write_sin_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/{self.comboBox_ao.currentText()}")
                self.write_sin_task.timing.cfg_samp_clk_timing(freq_ech, sample_mode=AcquisitionType.CONTINUOUS)
                self.write_sin_task.write(signal)
                self.write_sin_task.start()
                self.plot_write_sin()

            else:
                QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Sin_start function returned : {e}")

    # Stops the sinus generation
    def sin_stop(self):
        try:
            self.write_sin_task.stop()
            self.write_sin_task.close()  # Removes the task in order to start it again if we need
            self.write_sin_task = nidaqmx.Task()  # Make a new empty task
            self.Y_write_sin.clear()  # Clear the write buffer
            self.update_write_button_states(True, False)  # Update the button states
            self.write_graph.clear()
            self.write(0)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Sin_stop function returned : {e}")

    # Changes the values of the sinus dynamically with the one from the interface
    def freq_amp_changed(self):
        try:
            self.samples_per_read = int(self.f_read_ech * self.timer_data_acq / 1000)
            if not self.pushButton_test_sin.isEnabled():
                self.Y_write_sin.clear()
                self.write_graph.clear()
                self.plot_write_sin()
                self.sin_stop()
                self.sin_start()
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Freq_amp_changed function returned : {e}")

    #########################################################################################
    # Plotting part

    # Write-plot settings
    def plot_write_sin(self):
        try:
            my_pen = pyqtgraph.mkPen(color=(0, 255, 0))
            self.data_line2 = self.write_graph.plot(self.Y_write_sin, pen=my_pen)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Plot_write_sin function returned : {e}")

    # Read-plot settings
    def prepare_plot_read(self):
        try:
            my_pen = pyqtgraph.mkPen(color=(255, 0, 0))
            self.data_line1 = self.read_graph.plot(self.Y_read, pen=my_pen)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Prepare_plot_read function returned : {e}")

    # Plots to the read graph
    def plot_read(self, value):
        try:
            self.Y_read = value
            self.data_line1.setData(self.Y_read)
            self.read_graph.setYRange(-float(self.calibre), float(self.calibre))
            self.read_graph.setXRange(0, self.samples_per_read)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Plot_read function returned : {e}")

    # Clears the read graph
    def clear_read(self):
        try:
            self.read_graph.clear()
            self.Y_read.clear()
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Clear_read function returned : {e}")

    # Clears the write graph
    def clear_write(self):
        try:
            self.write_graph.clear()
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Clear_write function returned : {e}")

    #########################################################################################
    # Button states part

    # Change the "Start" and "Stop" button states
    def update_read_button_states(self, start_disabled, stop_enabled):
        try:
            self.pushButton_start_read.setEnabled(start_disabled)
            self.pushButton_stop_read.setEnabled(stop_enabled)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Update_read_button_states function returned : {e}")

    # Change the "Sin test" and "Stop sin" button states
    def update_write_button_states(self, start_disabled, stop_enabled):
        try:
            self.pushButton_test_sin.setEnabled(start_disabled)
            self.pushButton_stop_sin.setEnabled(stop_enabled)
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Update_write_button_states function returned : {e}")

    #########################################################################################
    # Reset part

    # Resets analog outputs => Writes 0V to both
    def reset(self):
        try:
            if not self.pushButton_test_sin.isEnabled():
                self.sin_stop()
            if self.port_dev is not None:
                with nidaqmx.Task() as reset_task:
                    reset_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/ao0")
                    reset_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/ao1")
                    reset_task.write([0, 0])
                print("Reset success")
            else:
                QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', f"Reset function returned : {e}")
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
