# -*- coding: utf-8 -*-
"""
Created on Sun Oct 15 17:43:10 2023

@author: Thomas
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6 import QtCore
import numpy as np
#import matplotlib_inline 

class DataToImageApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TestImage")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        self.data_input_label = QLabel("Valeurs intensités : ", self)
        self.data_input = QLineEdit(self)

        self.dx_label = QLabel("Nombre de valeurs par ligne -> largeur (dx):", self)
        self.dx_input = QLineEdit(self)

        self.generate_button = QPushButton("Génerer", self)
        self.generate_button.clicked.connect(self.generate_gray_image)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.data_input_label)
        self.layout.addWidget(self.data_input)
        self.layout.addWidget(self.dx_label)
        self.layout.addWidget(self.dx_input)
        self.layout.addWidget(self.generate_button)
        
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_label)
        self.layout.addLayout(image_layout)

        self.central_widget.setLayout(self.layout)

    def generate_gray_image(self):
        data_str = self.data_input.text()
        dx_str = self.dx_input.text()

        # Validation des entrées
        if not data_str or not dx_str:
            print("largeur invalide")
            return

        try:
            data = [float(value) for value in data_str.split(',')]
            dx = int(dx_str)
        except (ValueError, TypeError):
            print("intensités invalides")
            return

        num_columns = dx
        num_rows = int(np.ceil(len(data) / dx))  # Calcul du nombre de lignes=

#pas sur du tout de cette partie -> 
        # Redimensionner la fenêtre en fonction de la taille de l'image
        window_width = max(400, num_columns * 5)  # Largeur minimale de 400 pixels
        window_height = max(400, num_rows * 5)  # Hauteur minimale de 400 pixels
        self.setGeometry(100, 100, window_width, window_height)

        image = QImage(num_columns, num_rows, QImage.Format.Format_Grayscale8)
        
        for x, intensity in enumerate(data):
            gray_value = int(intensity * 255) #On renormalise du 255 pour que ça marche
            row = x // dx
            col = x % dx
            image.setPixelColor(col, row, QColor(gray_value, gray_value, gray_value))

        pixmap = QPixmap.fromImage(image)
        self.image_label.setPixmap(pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataToImageApp()
    window.show()
    sys.exit(app.exec())