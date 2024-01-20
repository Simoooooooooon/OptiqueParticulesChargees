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

        ui_file_path = "D:/Thomas/Projetmulti/Interface/V1_NoShift.ui"
        loadUi(ui_file_path, self)

        self.tab = np.zeros((taille, taille), float)
        self.pixmap(self.generer_image(self.tab))  # Affiche une image vide au début

        self.progressBar.setValue(0)
        self.show()

        self.taille = taille
        self.timer = QTimer(self)
        self.progressBar.setMaximum(100)
        self.paused = False
        self.x = 0

        self.init_ui()
        msg = QMessageBox()
        msg.setWindowTitle("Warning")
        msg.setText("Les boutons Relancer, STOP et Reprendre font la même chose")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        
    def init_ui(self):
        self.Reprendre.clicked.connect(self.resume)
        self.Relancer.clicked.connect(self.restart)
        self.Lancer.clicked.connect(self.start)
        self.STOP.clicked.connect(self.toggle_pause)
        self.quit.clicked.connect(self.close)

    def majtab(self, i, j):
        self.tab[i][j] = random.random()

    def generer_image(self, tableau):
        tableau_normalise = (tableau * 255).astype(np.uint8)
        height, width = tableau_normalise.shape
        qimage = QImage(
            tableau_normalise.data, width, height, -1, QImage.Format.Format_Grayscale8
        )
        return qimage
#Implique les boutons Stop/Relance/Reprendre font la même chose et reppartent de 0
    def update_image(self):
        for i in range(self.taille):
            for j in range(self.taille):
                if not self.paused:
                    self.majtab(i, j)
                    b = self.generer_image(self.tab)
                    self.pixmap(b)
                    self.update_progress()
                    QApplication.processEvents()
                    self.x += 1
        if not self.paused:
            self.timer.stop()
            self.show_finished_popup()

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
        self.x = 0
        self.paused = False
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.timer.stop()
        else:
            self.timer.start(100)

    def stop(self):
        self.paused = True
        self.timer.stop()

    def resume(self):
        self.paused = False
        self.timer.stop()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)

    def restart(self):
        self.x = 0
        self.paused = False
        self.timer.stop()
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)

    def update_progress(self):
        c = round(self.x * 100 / (self.taille ** 2))
        self.progressBar.setValue(c)

def main():
    app = QApplication(sys.argv)
    taille = 256
    window = MainW(taille)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()