import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
import random
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.uic import loadUi
import sys
import numpy as np

class MainW(QMainWindow):
    def __init__(self, taille):
        super(MainW, self).__init__()

        ui_file_path = "C:/Users/tp_tp4/Documents/projet_multi_23_24/InterfacesUI/V1_NoShift.ui"
        loadUi(ui_file_path, self)

        self.tab = np.zeros((taille, taille), float)
        self.pixmap(self.generer_image(self.tab))  # Affiche une image vide au début

        self.progressBar.setValue(0)
        self.show()

        self.taille = taille
        self.delay_before_close = 500
        self.timer = QTimer(self)
        self.progressBar.setMaximum(100)
        self.paused = False
        self.acquisition_active = False
        self.x = 0
        self.port_dev = "Dev1"
        self.first_token=0
        self.connect_token=0
        self.init_ui()

        
    def init_ui(self):
        
        self.Relancer.clicked.connect(self.restart)
        self.Connect.clicked.connect(self.connect_to_card)
        self.Lancer.clicked.connect(self.start)
        self.STOP.clicked.connect(self.stop)
        self.quit.clicked.connect(self.close)
    
        

        
    def close(self):
         
        self.read_task.close()
                
        QTimer.singleShot(self.delay_before_close, super().close)
        QApplication.quit()
        
    def majtab(self, i, j):
        try:
            # Vérifier si la tâche de lecture a des canaux
            if self.read_task.ai_channels:
                data = self.read_task.read(1)
                # Calculer la moyenne des valeurs dans la liste de données
                average_value = np.mean(data) if data else 0
                self.tab[i][j] = abs(average_value/0.15)
            else:
                print("Aucun canal défini dans la tâche de lecture.")
        except nidaqmx.DaqError as e:
            print(f"Erreur DAQ: {e}")
        except ValueError as e:
            print(f"Erreur de valeur: {e}")

        
    def generer_image(self, tableau):
        tableau_normalise = (tableau *255).astype(np.uint8)
        height, width = tableau_normalise.shape
        qimage = QImage(
            tableau_normalise.data, width, height, -1, QImage.Format.Format_Grayscale8
        )
        return qimage

    def update_image(self):
        
        if self.acquisition_active==True:
            for i in range(self.taille):
                for j in range(self.taille):
                    if not self.paused:
                        self.majtab(i, j)
                        b = self.generer_image(self.tab)
                        self.pixmap(b)
                        self.update_progress()
                        QApplication.processEvents()
                        self.x += 1
    
        if self.paused==False:    
            self.show_finished_popup()
            self.timer.stop()
            self.acquisition_active=False
            self.read_task.stop()


    def show_finished_popup(self):
        msg = QMessageBox()
        msg.setWindowTitle("Image terminée")
        msg.setText("L'image est générée avec succès !")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()


    def pixmap(self, image):
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(self.label.width(), self.label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        self.label.setPixmap(pixmap)
        self.repaint()



    def start(self):
        if self.connect_token!=1:
            msg = QMessageBox()
            msg.setWindowTitle("Warning")
            msg.setText("Connecter la carte")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            return
        
        if self.first_token==1:
            
            msg = QMessageBox()
            msg.setWindowTitle("Warning")
            msg.setText("Pour lancer une nouvelle acquisition appuyez sur Relancer")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            return
        
        self.read_task = nidaqmx.Task()
        self.x = 0
        self.paused = False
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)
    
        f_read_ech = 1000 
        self.ai = "AI1"
        
        # Ajouter le canal à la tâche de lecture
        self.read_task.ai_channels.add_ai_voltage_chan(
            f"{self.port_dev}/{self.ai}",
            min_val=-float(0),
            max_val=float(5),
            terminal_config=TerminalConfiguration.DIFF
        )
    
        # Configurer le timing après avoir ajouté le canal
        self.read_task.timing.cfg_samp_clk_timing(
            rate=f_read_ech,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS
        )
    
        self.read_task.start()
        self.acquisition_active = True
        self.first_token=1
        
    def restart(self) :
        if self.acquisition_active:
            msg = QMessageBox()
            msg.setWindowTitle("Warning")
            msg.setText("Pour lancer une nouvelle acquisition appuyez sur STOP puis Relancer")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.exec()
            return
        self.paused = False
        self.x =0
        self.acquisition_active = True
        self.read_task.start()
        self.timer.start(100)
        
        
        
        
    def stop(self):
        if self.acquisition_active:
            self.paused = True
            self.read_task.stop()
            self.timer.stop()
            self.acquisition_active = False

    def update_progress(self):
        c = round(self.x * 100 / (self.taille ** 2))
        self.progressBar.setValue(c)
        
        
    def connect_to_card(self):
        try:
            self.port_dev = "Dev1"
            system = nidaqmx.system.System.local()
            if (not "Dev1" in system.devices):
                QMessageBox.information(self, 'Error', 'Wrong port choice')
            else:
                print("Connected")
                self.connect_token=1
    
        except Exception as e:
            QMessageBox.information(self, 'Error', f"Connect_to_card function returned : {e}")        

def main():
    app = QApplication(sys.argv)
    taille = 64
    window = MainW(taille)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
