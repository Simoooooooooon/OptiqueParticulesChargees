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
#L'utilisation de divmod permet d'avoir une boucle if plutôt que for, ce qui permet d'avoir une pause/resume/relance 
#sans multithread 
    def update_image(self):
        i, j = divmod(self.x, self.taille) 
        if i * self.taille + j < self.taille * self.taille:
            self.majtab(i, j)
            b = self.generer_image(self.tab)
            self.pixmap(b)
            self.update_progress()
            QApplication.processEvents()  
            self.x += 1
            if j == self.taille - 1:
                self.x += self.taille - j  
            if i == self.taille - 1 and j == self.taille - 1:
                self.timer.stop()
                self.show_finished_popup()
        else:
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
        self.timer.stop() 
        if not self.paused:
            self.timer.start(100)

    def stop(self):
        self.paused = True
        self.timer.stop()

    def resume(self):
        if self.paused:
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
    taille = 1024
    window = MainW(taille)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()