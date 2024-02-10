"""Pilotage de la carte Supervisor V2"""
"""Emma Lisoir & Nina Alméras"""
"""4GP - Année 2022-2023"""

import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
'''import serial
from serial import SerialException'''
import pyqtgraph as pg

qtCreatorFile = "Interface finale.ui"  # Enter file here.
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class Window(QtWidgets.QMainWindow, Ui_MainWindow):
    port = QtCore.pyqtSignal(object)  # Signal emitted by the Window class and received in the ThreadWorker class

    def __init__(self):

        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.pushButton_connect.clicked.connect(
            self.port_connect)  # Connect a function to a clicked element on the GUI
        self.pushButton_gun_on.clicked.connect(self.gun_on)
        self.pushButton_gun_off.clicked.connect(self.gun_off)
        self.pushButton_quit.clicked.connect(self.quit)

        self.pushButton_gun_on.setEnabled(True)
        self.pushButton_gun_off.setEnabled(False)

        self.Y1 = []  # Create a empty list
        self.Y2 = []

        self.state = 0  # Create variable initialize to zero

        # Slider
        self.slider_condensor.valueChanged.connect(self.slider)
        self.comboBox_condensor.activated.connect(self.combo_condensor)
        self.slider_condensor.setMaximum(30000)

    def connectSignalSlots(self):
        self.pushButton_validate.clicked.connect(self.set_voltage)

    # Slider Condensor
    def slider(self):
        self.target = self.slider_condensor.value()
        self.label_condensor.setText(str(self.target))

    def combo_condensor(self):
        if self.comboBox_condensor.currentText() == 'Coarse':
            self.slider_condensor.setMinimum(0)
            self.slider_condensor.setMaximum(30000)

        if self.comboBox_condensor.currentText() == 'Medium':
            mini = self.target - 5000
            maxi = self.target + 5000

            # To stay between 0 and 30 000
            if mini < 0:
                mini = 0
            if maxi > 30000:
                maxi = 30000

            self.slider_condensor.setMinimum(mini)
            self.slider_condensor.setMaximum(maxi)

        if self.comboBox_condensor.currentText() == 'Fine':
            mini = self.target - 100
            maxi = self.target + 100

            # To stay between 0 and 30 000
            if mini < 0:
                mini = 0
            if maxi > 30000:
                maxi = 30000

            self.slider_condensor.setMinimum(mini)
            self.slider_condensor.setMaximum(maxi)

        # initiate the new slider range
        val_min = self.slider_condensor.minimum()
        self.label_min.setText(str(val_min))
        val_max = self.slider_condensor.maximum()
        self.label_max.setText(str(val_max))

    # Push Button to set the card in Gun ON mode
    def gun_on(self):
        self.ser.write(b'>1,10,2\r')  # CMD_SET_GUN_STATUS On
        self.pushButton_gun_on.setEnabled(False)
        self.pushButton_gun_off.setEnabled(True)

    # Push Button OFF to set the card in Gun OFF mode
    def gun_off(self):
        self.ser.write(b'>1,10,0\r')  # CMD_SET_GUN_STATUS Off
        self.pushButton_gun_off.setEnabled(False)
        self.pushButton_gun_on.setEnabled(True)

    # Initilization of the port connection, the thread and the graphs
    def port_connect(self):
        self.port_com = self.comboBox_portcom.currentText()  # Read the port choice chosen by the user on the GUI

        try:
            self.ser = serial.Serial(port=self.port_com, baudrate=57600, bytesize=8, timeout=0.5,
                                     stopbits=1)  # Open and configure the port
            self.label_port_connected.setStyleSheet("color : green;")  # Set the color of the message displayed
            self.label_port_connected.setText("Sucess : the port is connected")
            self.Comcheck = True

        except serial.SerialException:
            QMessageBox.information(self, 'Error', 'Wrong port choice')
            self.Comcheck = False

        if self.Comcheck:
            self.ser.write(b'>3,17,0,100,100,65,65,65,65,1.0,1.0,1\r')  # CMD_SET_MODE_STATUS
            self.state = 1;

            self.proofreading()

    def proofreading(self):
        # Thread initialization
        self.worker = ThreadWorker(self.port)  # Create a thread instance from the class ThreadWorker
        self.connectSignalSlots()
        self.worker.start()  # Start the thread

        self.port.emit(
            self.ser)  # Create a signal that is emitted and can be read in the thread. Here, the signal is the status of the port.
        self.worker.data.connect(self.actual_values)

        # Graph1 for energy current

        pen1 = pg.mkPen(color=(255, 0, 0))  # Color of the line
        self.data_line1 = self.graph_energy_current.plot(self.Y1,
                                                         pen=pen1)  # Graph initialization. This graph is empty in the beginning.
        self.worker.data.connect(self.plot1)  # Plot the signal 'data' emitted by the thread on the GUI.

        # Graph2 for suppressor voltage
        pen2 = pg.mkPen(color=(0, 0, 255))
        self.data_line2 = self.graph_suppressor_voltage.plot(self.Y2, pen=pen2)
        self.worker.data.connect(self.plot2)

    def plot1(self, data):  # Plot the evolution of the energy current
        try:
            self.Y1.append(float(data[1]))  # Append the last read value to the list 'data'
            self.data_line1.setData(self.Y1)  # Plot actualization
        except:
            pass

    def plot2(self, data):
        try:
            self.Y2.append(float(data[4]))
            self.data_line2.setData(self.Y2)
        except:
            pass

    # The actual values of current and voltage received from the thread are displayed on the GUI.
    def actual_values(self, vals):
        self.label_actual_energy.setText(vals[0])
        self.label_actual_emission_current.setText(vals[1])
        self.label_actual_extractor.setText(vals[2])
        self.label_extractor_current.setText(vals[3])
        self.label_actual_suppressor.setText(vals[4])
        self.label_suppressor_current.setText(vals[5])
        self.label_actual_condensor.setText(vals[6])

    @QtCore.pyqtSlot()  # Slot declare
    # Send voltage values when the PushButton 'Send values' is clicked
    def set_voltage(self):

        # Read the values displayed on the GUI
        self.energy_voltage = self.spinBox_energy.value()
        self.extractor_voltage = self.spinBox_extractor.value()
        self.suppressor_voltage = self.spinBox_suppressor.value()
        self.condensor_voltage = self.slider_condensor.value()

        self.ser.write(b'>1,1,%f,0\r' % float(self.energy_voltage))  # CMD_SET_VOLTAGE for Energy
        self.ser.write(b'>3,1,%f,0\r' % float(self.extractor_voltage))  # CMD_SET_VOLTAGE for Extractor
        self.ser.write(b'>2,1,%f,0\r' % float(self.suppressor_voltage))  # CMD_SET_VOLTAGE for Supressor
        self.ser.write(b'>4,1,%f,0\r' % float(self.condensor_voltage))  # CMD_SET_VOLTAGE for Condensor

    # End of the program
    def quit(self):
        if self.state == 1:
            self.worker.requestInterruption()

        QtCore.QCoreApplication.instance().quit()
        QtWidgets.QMainWindow.close(self)

    # Creation of a new class


class ThreadWorker(QThread):
    data = pyqtSignal(list)  # Signal to be emitted by the ThreadWorker class and received in the Window class.

    def __init__(self, rs):
        super(ThreadWorker, self).__init__()
        rs.connect(self.port_connection)

    @QtCore.pyqtSlot(object)
    def port_connection(self, val):
        self.rs = val

    def run(self):
        self.list = []  # Empty list

        while True:
            self.list.clear()  # Erase the previous values set in the list

            # Energy control
            self.rs.write(
                b'>1,2\r')  # CMD_GET_STATUS for Energy (Jumper 1). Allows the proofreading of the values sent by the card.
            self.energy = self.rs.readline()  # Read the answer sent afer the status request.
            self.energy = str(self.energy)  # Attribute the vals 'string' to the variable.

            energy_Vmeas = self.energy.split(",")[2]  # Split the command answer to keep only the value that is needed.
            energy_Imeas = self.energy.split(",")[3]

            self.list.append(energy_Vmeas)  # Append the received value to the list
            self.list.append(energy_Imeas)

            # Extractor control
            self.rs.write(b'>3,2\r')  # CMD_GET_STATUS for Extractor (Jumper 3)
            extractor = self.rs.readline()
            extractor = str(extractor)

            extractor_Vmeas = extractor.split(",")[2]
            extractor_Imeas = extractor.split(",")[3]

            self.list.append(extractor_Vmeas)
            self.list.append(extractor_Imeas)

            # Suppressor control
            self.rs.write(b'>2,2\r')  # CMD_GET_STATUS for Suppressor (Jumper 2)
            suppressor = self.rs.readline()
            suppressor = str(suppressor)
            suppressor_Vmeas = suppressor.split(",")[2]
            suppressor_Imeas = suppressor.split(",")[3]

            self.list.append(suppressor_Vmeas)
            self.list.append(suppressor_Imeas)

            # Condensor control
            self.rs.write(b'>4,2\r')  # CMD_GET_STATUS for Suppressor (Jumper 4)
            condensor = self.rs.readline()
            condensor = str(condensor)
            condensor_Vmeas = condensor.split(",")[2]

            self.list.append(condensor_Vmeas)
            self.data.emit(self.list)

            if self.isInterruptionRequested():  # Interruption requested in the Window class.
                self.rs.close()  # Close serial port
                break


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
