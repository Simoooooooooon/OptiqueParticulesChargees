import nidaqmx
import sys
import time
import random
from PyQt5 import QtCore, QtWidgets, uic
import pyqtgraph
import math


# Resets the tasks that might not have been closed
def reset_tasks(n):
    tasks = [nidaqmx.Task() for _ in range(n)]
    for task in tasks:
        task.close()


# QT Designer interface file
Ui_MainWindow, QtBaseClass = uic.loadUiType("interface.ui")


# Interface class
class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    frequency_changed = QtCore.pyqtSignal(float)  # Signal to update frequency in real time
    amplitude_changed = QtCore.pyqtSignal(float)  # Signal to update amplitude in real time

    # Interface initialization
    def __init__(self):
        super(MyWindow, self).__init__()
        self.data_line2 = None
        self.sinus_thread = None
        self.data_line1 = None
        self.calibre = None
        self.port_dev = None
        self.ai = None
        self.ao = None
        self.setupUi(self)
        self.setWindowTitle("IHM")
        self.pushButton_quit.clicked.connect(self.quit)
        self.pushButton_connect.clicked.connect(self.connect_to_card)
        self.pushButton_reset.clicked.connect(self.reset)
        self.pushButton_write.clicked.connect(self.write)
        self.pushButton_clear_read.clicked.connect(self.clear_read)
        self.pushButton_clear_write.clicked.connect(self.clear_write)
        self.pushButton_start_read.clicked.connect(self.start_read)
        self.pushButton_stop_read.clicked.connect(self.stop_read)
        self.pushButton_test_sin.clicked.connect(self.sin_test)
        self.pushButton_stop_sin.clicked.connect(self.sin_stop)
        self.spinBox_freq.valueChanged.connect(self.emit_frequency_changed)
        self.doubleSpinBox_ao.valueChanged.connect(self.emit_amplitude_changed)
        self.thread = {}
        self.Y_read = []
        self.Y_write = []

    # Quit function linked to the quit button
    def quit(self):
        QtCore.QCoreApplication.instance().quit()
        self.close()

    # Connection to the NI Card
    def connect_to_card(self):
        self.port_dev = self.comboBox_dev.currentText()
        print(f"Connected à {self.port_dev}")
        '''
        system = nidaqmx.system.System.local()
        if not self.comboBox_dev.currentText() in system.devices : QMessageBox.information(self, 'Error','Wrong port choice')
        else :  
            self.port_dev = self.comboBox_dev.currentText()
            print(f"Connected to {self.port_dev}")
        '''

    # Write the analog tension to the corresponding card/port
    def write(self, value=None):
        # Gets and converts the values to write an analog tension
        self.ao = self.comboBox_ao.currentText()
        if value is False:
            write_ao = float(self.doubleSpinBox_ao.text().replace(',', '.'))
        else:
            write_ao = value

        if self.port_dev is not None:
            print(f"Writing {write_ao} to {self.port_dev}/{self.ao}")
            '''
            write_task=nidaqmx.Task()   
            write_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/{self.ao}")
            write_task.write(write_ao)
            write_task.close()
            '''
            print("Write success")
        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')

    # Clear the read graph
    def clear_read(self):
        self.read_graph.clear()
        self.Y_read.clear()

    # Get the channel and the calibre then start a thread
    def start_read(self):
        if self.port_dev is not None:
            self.ai = self.comboBox_ai.currentText()
            self.calibre = self.comboBox_calibre.currentText()
            self.clear_read()
            print(f"Reading from {self.port_dev}/{self.ai} with calibre {self.calibre}")
            self.prepare_and_start_thread()
        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')

    # Starts a thread
    def prepare_and_start_thread(self):
        self.thread[1] = ReadThread(parent=None, index=1)  # Create a thread
        self.thread[1].finished.connect(self.thread[1].deleteLater)  # Deletes the thread when finished
        self.thread[1].start()  # Starts the thread
        self.thread[1].mon_signal.connect(self.display_read)  # Display each time "mon_signal" gets updated
        self.update_read_button_states(False, True)  # Switch button states
        self.prepare_plot_read()  # Plot the result

    # Read plot settings
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
                self.Y_read.pop(0)  # retire le premier élément
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
        try:
            print(f"Writing 0 to {self.port_dev}/ao0")
            print(f"Writing 0 to {self.port_dev}/ao1")
            '''
            write_task=nidaqmx.Task()   
            write_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/ao0")
            write_task.write(0)
            write_task.close()
            write_task=nidaqmx.Task()   
            write_task.ao_channels.add_ao_voltage_chan(f"{self.port_dev}/a01")
            write_task.write(0)
            write_task.close()
            '''
            print("Reset success")
        except Exception as e:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')
            print(str(e))

    # Sends a sin function to be written
    def sin_test(self):
        if self.port_dev is not None:
            frequency = float(self.spinBox_freq.text())
            amplitude = self.doubleSpinBox_ao.value()
            self.clear_write()
            self.sinus_thread = SinusThread(parent=None, amplitude=amplitude, frequency=frequency)
            self.sinus_thread.finished.connect(self.sinus_thread.deleteLater)  # Deletes the thread when finished
            self.frequency_changed.connect(self.sinus_thread.update_frequency)
            self.amplitude_changed.connect(self.sinus_thread.update_amplitude)
            self.sinus_thread.start()
            self.sinus_thread.sin_signal.connect(lambda: self.write(float(self.Y_write[-1])))
            self.update_write_button_states(False, True)  # Switch button states
            self.prepare_plot_write()
        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'No device connected')

    # Check for a frequency change
    def emit_frequency_changed(self):
        new_frequency = float(self.spinBox_freq.text())
        self.update_x_axis(new_frequency)
        self.frequency_changed.emit(new_frequency)

    # Check for an amplitude change
    def emit_amplitude_changed(self):
        new_amplitude = float(self.doubleSpinBox_ao.text().replace(',', '.'))
        self.update_y_axis(new_amplitude)
        self.amplitude_changed.emit(new_amplitude)

    # Write plot settings
    def prepare_plot_write(self):
        my_pen = pyqtgraph.mkPen(color=(255, 0, 0))
        self.data_line2 = self.write_graph.plot(self.Y_write, pen=my_pen)
        self.sinus_thread.sin_signal.connect(self.plot_write)

    # Plots to the write graph
    def plot_write(self, sin_signal):
        self.Y_write.append(float(sin_signal))
        self.data_line2.setData(self.Y_write)
        self.update_x_axis(float(self.spinBox_freq.text()))

    # Update the x-axis
    def update_x_axis(self, frequency):
        n_points = 500 / frequency
        if len(self.Y_write) > n_points:
            self.Y_write.pop(0)  # Removes the first element
            self.write_graph.setXRange(len(self.Y_write) - n_points, len(self.Y_write))  # Adjusts the x-axis

    # Update the y-axis
    def update_y_axis(self, amplitude):
        self.write_graph.setYRange(-amplitude, amplitude)

    # Clear the write graph
    def clear_write(self):
        self.write_graph.clear()
        self.Y_write.clear()

    # Stops the reading
    def sin_stop(self):
        self.sinus_thread.stop()
        self.update_write_button_states(True, False)

    # Change the "Sin test" and "Stop sin" button states
    def update_write_button_states(self, start_disabled, stop_enabled):
        self.pushButton_test_sin.setEnabled(start_disabled)
        self.pushButton_stop_sin.setEnabled(stop_enabled)


# Class thread for the analog read
class ReadThread(QtCore.QThread):
    mon_signal = QtCore.pyqtSignal(float)

    # Tread class initialization
    def __init__(self, parent=None, index=0):
        super(ReadThread, self).__init__(parent)
        self.index = index
        self.is_running = True

    # What the thread runs
    def run(self):
        print(f"Starting read thread {self.index}")
        '''
        task = nidaqmx.Task()
        task.ai_channels.add_ai_voltage_chan(f"{self.port_dev}/{self.ai}, min_val=-{self.calibre}, max_val={self.calibre},terminal_config=TerminalConfiguration.DIFF")
        '''
        while self.is_running:
            '''
            task.start()
            val = task.read()
            '''
            val = random.random()
            time.sleep(0.5)
            self.mon_signal.emit(val)
            '''task.stop()'''

    # Stop function to stop the thread
    def stop(self):
        reset_tasks(1)
        print(f"Stopping thread {self.index}")
        self.is_running = False


# Class thread for the sinus write
class SinusThread(QtCore.QThread):
    sin_signal = QtCore.pyqtSignal(float)

    # Tread class initialization
    def __init__(self, parent=None, amplitude=0.0, frequency=1.0):
        super(SinusThread, self).__init__(parent)
        self.is_running = True
        self.t = 0
        self.frequency = frequency
        self.amplitude = amplitude

    # To update the frequency in real time
    def update_frequency(self, new_frequency):
        self.frequency = new_frequency

    # To update the amplitude un real time
    def update_amplitude(self, new_amplitude):
        self.amplitude = new_amplitude

    # What the thread runs
    def run(self):
        print("Starting sinus thread")
        n_points = 100  # Number of points you want to generate over the period T
        last_time = time.time()
        while self.is_running:
            T = 1 / self.frequency  # Period in seconds
            time_to_sleep = T / n_points  # Time to sleep between each point in seconds
            current_time = time.time()
            delta_t = current_time - last_time  # Time since the last loop iteration
            last_time = current_time  # Update last_time for the next iteration
            val = self.amplitude * math.sin(2 * math.pi * self.frequency * self.t)
            self.sin_signal.emit(val)
            self.t += delta_t
            time.sleep(time_to_sleep)  # Sleep for the calculated time to ensure points are distributed over T seconds

    # Stop function to stop the thread
    def stop(self):
        print("Stopping sinus thread")
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
