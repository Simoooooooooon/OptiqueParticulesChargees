import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import sys
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import QTimer
import pyqtgraph
import numpy as np

# Load the UI file created with QT Designer
Ui_MainWindow, QtBaseClass = uic.loadUiType("interface.ui")


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

    # Function to quit the application
    def quit(self):
        QtCore.QCoreApplication.instance().quit()
        self.stop_read()
        self.write_sin_task.stop()
        self.write_sin_task.close()
        self.reset()
        self.close()

    #########################################################################################
    # Connection part

    # Connection to the NI Card and verification
    def connect_to_card(self):
        self.port_dev = self.comboBox_dev.currentText()
        system = nidaqmx.system.System.local()
        if not self.comboBox_dev.currentText() in system.devices:
            QtWidgets.QMessageBox.information(self, 'Error', 'Wrong port choice')
        else:
            self.port_dev = self.comboBox_dev.currentText()
            print(f"Connected to {self.port_dev}")

    #########################################################################################
    # Single value analog write part

    # Write the analog tension to the corresponding card/port
    def write(self, value=None):
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

    #########################################################################################
    # Reading part

    # Get the channel and the calibre then start a thread
    def start_read(self):
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

    # Gets the data from the card buffer
    def acquire_data(self):
        f_read_ech = self.spinBox_read_freq_ech.value()  # Get the reading frequency sampling rate
        samples_per_read = int(f_read_ech * self.timer_data_acq / 1000)
        val = self.read_task.read(number_of_samples_per_channel=samples_per_read)
        self.data_acquired.emit([val[0]])

    # Stops the reading
    def stop_read(self):
        self.Y_read.clear()  # Clear the read buffer
        self.timer.stop()  # Stop the QTimer
        self.read_task.stop()  # Stop the NI task

        self.read_task.close()  # Close the NI task

        self.read_task = nidaqmx.Task()  # Initialize a new empty task
        self.update_read_button_states(True, False)  # Update the button states

    # Dynamically changes the calibre
    def calibre_changed(self):
        self.read_graph.setYRange(-float(self.calibre), float(self.calibre))
        if self.timer is not None:  # Prevent an error
            if self.timer.isActive():  # If there is a timer running
                self.stop_read()
                self.start_read()

    #########################################################################################
    # Sinus writing part

    # Sends a sin function to be written
    def sin_start(self):
        if self.port_dev is not None:
            self.update_write_button_states(False, True)
            freq = self.spinBox_freq.value()
            freq_ech = self.spinBox_write_freq_ech.value()
            amp = self.doubleSpinBox_ao.value()
            temps = np.linspace(0, 1 / freq, int(freq_ech / freq), endpoint=False)
            signal = amp * np.sin(2 * np.pi * freq * temps)
            self.Y_write_sin = signal.tolist()
            self.write_sin_task = nidaqmx.Task()
            self.write_sin_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/{self.comboBox_ao.currentText()}")
            self.write_sin_task.timing.cfg_samp_clk_timing(freq_ech, sample_mode=AcquisitionType.CONTINUOUS)
            self.write_sin_task.write(signal)
            self.write_sin_task.start()
            self.prepare_plot_write_sin()

        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')

    # Stops the sinus generation
    def sin_stop(self):
        self.write_sin_task.stop()
        self.write_sin_task.close()  # Removes the task in order to start it again if we need
        self.write_sin_task = nidaqmx.Task()  # Make a new empty task
        self.Y_write_sin.clear()  # Clear the write buffer
        self.update_write_button_states(True, False)  # Update the button states
        self.write_graph.clear()
        self.write(0)

    # Changes the values of the sinus dynamically with the one from the interface
    def freq_amp_changed(self):
        if not self.pushButton_test_sin.isEnabled():
            freq = self.spinBox_freq.value()
            freq_ech = self.spinBox_write_freq_ech.value()
            amp = self.doubleSpinBox_ao.value()
            temps = np.linspace(0, 1 / freq, int(freq_ech / freq), endpoint=False)
            signal = amp * np.sin(2 * np.pi * freq * temps)
            self.Y_write_sin = signal.tolist()
            self.Y_write_sin.clear()
            self.write_graph.clear()
            self.prepare_plot_write_sin()
            self.sin_stop()
            self.sin_start()

    #########################################################################################
    # Plotting part

    # Write-plot settings
    def prepare_plot_write_sin(self):
        my_pen = pyqtgraph.mkPen(color=(0, 255, 0))
        self.data_line2 = self.write_graph.plot(self.Y_write_sin, pen=my_pen)

    # Read-plot settings
    def prepare_plot_read(self):
        my_pen = pyqtgraph.mkPen(color=(255, 0, 0))
        self.data_line1 = self.read_graph.plot(self.Y_read, pen=my_pen)

    # Plots to the read graph
    def plot_read(self, value):
        self.Y_read.append(value[0])
        self.data_line1.setData(self.Y_read)
        self.read_graph.setYRange(-float(self.calibre), float(self.calibre))
        # Chart scrolling
        n_points = 100  # Number of points to display
        if len(self.Y_read) > n_points:
            self.Y_read.pop(0)  # Removes the first element
            self.read_graph.setXRange(len(self.Y_read) - n_points, len(self.Y_read))  # Adjusts the x-axis

    # Clears the read graph
    def clear_read(self):
        self.read_graph.clear()
        self.Y_read.clear()

    # Clears the write graph
    def clear_write(self):
        self.write_graph.clear()

    #########################################################################################
    # Button states part

    # Change the "Start" and "Stop" button states
    def update_read_button_states(self, start_disabled, stop_enabled):
        self.pushButton_start_read.setEnabled(start_disabled)
        self.pushButton_stop_read.setEnabled(stop_enabled)

    # Change the "Sin test" and "Stop sin" button states
    def update_write_button_states(self, start_disabled, stop_enabled):
        self.pushButton_test_sin.setEnabled(start_disabled)
        self.pushButton_stop_sin.setEnabled(stop_enabled)

    #########################################################################################
    # Reset part

    # Resets analog outputs => Writes 0V to both
    def reset(self):
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

    #########################################################################################


# Starts the interface
def run_interface():
    app = QtWidgets.QApplication(sys.argv)  # Create a Qt application
    window = MyWindow()  # Create an instance of MyWindow
    window.show()  # Show the window
    sys.exit(app.exec_())  # Start the application event loop


# Main function
if __name__ == '__main__':
    run_interface()
