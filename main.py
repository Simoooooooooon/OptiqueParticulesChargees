import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import sys
import time
from PyQt5 import QtCore, QtWidgets, uic
import pyqtgraph
import numpy as np


# Resets the tasks that might not have been closed
def reset_tasks(n):
    tasks = [nidaqmx.Task() for _ in range(n)]
    for task in tasks:
        task.close()


# QT Designer interface file
Ui_MainWindow, QtBaseClass = uic.loadUiType("interface.ui")


# Interface class
class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    # Interface initialization
    def __init__(self):
        super(MyWindow, self).__init__()
        self.data_line2 = None
        self.sinus_thread = None
        self.data_line1 = None
        self.calibre = None
        self.ai = None
        self.setupUi(self)
        self.setWindowTitle("IHM")
        self.port_dev = self.comboBox_dev.currentText()
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
        self.thread = {}
        self.Y_read = []
        self.Y_write = []
        self.write_sin_task = nidaqmx.Task()
        self.spinBox_freq.valueChanged.connect(self.freq_amp_changed)
        self.doubleSpinBox_ao.valueChanged.connect(self.freq_amp_changed)
        self.spinBox_freq_ech.valueChanged.connect(self.freq_amp_changed)
        self.Y_write_sin = []

    # Quit function linked to the quit button
    def quit(self):
        QtCore.QCoreApplication.instance().quit()
        self.write_sin_task.stop()
        self.write_sin_task.close()
        self.reset()
        self.close()

    # Connection to the NI Card
    def connect_to_card(self):
        self.port_dev = self.comboBox_dev.currentText()
        system = nidaqmx.system.System.local()
        if not self.comboBox_dev.currentText() in system.devices:
            QtWidgets.QMessageBox.information(self, 'Error', 'Wrong port choice')
        else:
            self.port_dev = self.comboBox_dev.currentText()
            print(f"Connected to {self.port_dev}")

    # Write the analog tension to the corresponding card/port
    def write(self, value=None):
        # Gets and converts the values to write an analog tension
        if value is False:
            write_ao = float(self.doubleSpinBox_ao.text().replace(',', '.'))
        else:
            write_ao = value

        if self.port_dev is not None:
            # print(f"Writing {write_ao} to {self.port_dev}/{self.ao}")
            write_task = nidaqmx.Task()
            write_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/{self.comboBox_ao.currentText()}")
            write_task.write(write_ao)
            write_task.close()
            # print("Write success")
        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')

    # Clear the read graph
    def clear_read(self):
        self.read_graph.clear()
        self.Y_read.clear()

    def clear_write(self):
        self.write_graph.clear()

    # Get the channel and the calibre then start a thread
    def start_read(self):
        if self.port_dev is not None:
            self.ai = self.comboBox_ai.currentText()
            self.calibre = self.comboBox_calibre.currentText()
            self.clear_read()
            self.prepare_and_start_thread()
        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')

    # Starts a thread
    def prepare_and_start_thread(self):
        self.thread[1] = ReadThread(parent=None, index=1, port_dev=self.port_dev, ai=self.ai,
                                    calibre=self.calibre)  # Create a thread
        self.thread[1].finished.connect(self.thread[1].deleteLater)  # Deletes the thread when finished
        self.thread[1].start()  # Starts the thread
        self.thread[1].mon_signal.connect(self.display_read)  # Display each time "mon_signal" gets updated
        self.update_read_button_states(False, True)  # Switch button states
        self.prepare_plot_read()  # Plot the result

    # Read-plot settings
    def prepare_plot_read(self):
        my_pen = pyqtgraph.mkPen(color=(255, 0, 0))
        self.data_line1 = self.read_graph.plot(self.Y_read, pen=my_pen)
        self.thread[1].mon_signal.connect(self.plot_read)

    # Plots to the graph
    def plot_read(self, mon_signal):
        try:
            self.Y_read.append(float(mon_signal))
            self.data_line1.setData(self.Y_read)

            # Chart scrolling
            n_points = 100  # Number of points to display
            if len(self.Y_read) > n_points:
                self.Y_read.pop(0)  # Removes the first element
                self.read_graph.setXRange(len(self.Y_read) - n_points, len(self.Y_read))  # Adjusts the x-axis
        except Exception as e:
            print(str(e))

    # Change the "Start" and "Stop" button states
    def update_read_button_states(self, start_disabled, stop_enabled):
        self.pushButton_start_read.setEnabled(start_disabled)
        self.pushButton_stop_read.setEnabled(stop_enabled)

    # Stops the reading
    def stop_read(self):
        self.thread[1].stop()
        self.update_read_button_states(True, False)

    # Displays the variable "number" to the UI
    def display_read(self, number):
        self.label_ai.setText(str(number))

    # Resets analog outputs => Writes 0V to both
    def reset(self):
        if not self.pushButton_test_sin.isEnabled():
            self.sin_stop()
        try:
            reset_task = nidaqmx.Task()
            reset_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/ao0")
            reset_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/ao1")
            reset_task.write([0, 0])
            reset_task.close()
            print("Reset success")
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')
            print(str(e))

    # Sends a sin function to be written
    def sin_start(self):
        if self.port_dev is not None:
            self.update_write_button_states(False, True)
            freq = self.spinBox_freq.value()
            freq_ech = self.spinBox_freq_ech.value()
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

    def freq_amp_changed(self):
        if not self.pushButton_test_sin.isEnabled():
            freq = self.spinBox_freq.value()
            freq_ech = self.spinBox_freq_ech.value()
            amp = self.doubleSpinBox_ao.value()
            temps = np.linspace(0, 1 / freq, int(freq_ech / freq), endpoint=False)
            signal = amp * np.sin(2 * np.pi * freq * temps)
            self.Y_write_sin = signal.tolist()
            self.Y_write_sin.clear()
            self.write_graph.clear()
            self.prepare_plot_write_sin()
            self.sin_stop()
            self.sin_start()

    # Stops the sinus
    def sin_stop(self):
        self.write_sin_task.stop()
        self.write_sin_task.close()  # Removes the task in order to start it again if we need
        self.write_sin_task = nidaqmx.Task()  # Make a new empty task
        self.update_write_button_states(True, False)
        self.Y_write_sin = []
        self.write_graph.clear()

    # Prepare the write-sin-plot settings
    def prepare_plot_write_sin(self):
        my_pen = pyqtgraph.mkPen(color=(0, 255, 0))
        self.data_line2 = self.write_graph.plot(self.Y_write_sin, pen=my_pen)

    # Change the "Sin test" and "Stop sin" button states
    def update_write_button_states(self, start_disabled, stop_enabled):
        self.pushButton_test_sin.setEnabled(start_disabled)
        self.pushButton_stop_sin.setEnabled(stop_enabled)


# Thread class for the reading
class ReadThread(QtCore.QThread):
    mon_signal = QtCore.pyqtSignal(float)

    # Tread class initialization
    def __init__(self, parent=None, index=0, port_dev="Dev1", ai="ai0", calibre="10"):
        super(ReadThread, self).__init__(parent)
        self.index = index
        self.is_running = True
        self.port_dev = port_dev
        self.ai = ai
        self.calibre = calibre

    # What the thread runs
    def run(self):
        print(f"Starting read thread {self.index}")
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(f"{self.port_dev}/{self.ai}", min_val=-float(self.calibre),
                                             max_val=float(self.calibre), terminal_config=TerminalConfiguration.DIFF)
        task.start()
        while self.is_running:
            val = task.read()
            time.sleep(0.01)
            self.mon_signal.emit(val)

    # Stop function to stop the thread
    def stop(self):
        reset_tasks(1)
        print(f"Stopping thread {self.index}")
        self.is_running = False


# Starts the interface
def run_interface():
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())


# Main function
if __name__ == '__main__':
    reset_tasks(10)
    run_interface()
