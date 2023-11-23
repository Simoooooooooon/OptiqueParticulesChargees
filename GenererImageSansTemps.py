# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import random
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
import sys
import numpy as np


def generer_intensitetab(i, j):
    tableau = [[random.random() for _ in range(j)] for _ in range(i)]
    return tableau


    
def generer_image(tableau):
    tableau_normalise = np.array(tableau)
    tableau_normalise = (tableau_normalise - np.min(tableau_normalise)) / (np.max(tableau_normalise) - np.min(tableau_normalise)) * 255
    tableau_normalise = tableau_normalise.astype(np.uint8)

    height, width = tableau_normalise.shape
    qimage = QImage(tableau_normalise.data, width, height, width, QImage.Format.Format_Grayscale8)

    return qimage

    
class MainWindow(QMainWindow):
    def __init__(self, tableau):
        super(MainWindow, self).__init__()
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image = generer_image(tableau)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

def main():
    app = QApplication(sys.argv)

    tableau_aleatoire = generer_intensitetab(1024, 1024)

    window = MainWindow(tableau_aleatoire)
    window.setGeometry(100, 100, 800, 600)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()