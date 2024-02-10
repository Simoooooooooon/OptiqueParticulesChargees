# -*- coding: utf-8 -*-

"""
Created on Sat Apr 10 15:31:15 2021

@author: GRP-24

"""
import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic 
from PyQt5.QtCore import QObject, QThread
from PyQt5.QtGui import QPixmap
import numpy as np
import qimage2ndarray
import threading
from threading import Timer
import cv2
import nidaqmx
from time import sleep
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_writers import AnalogMultiChannelWriter
from nidaqmx.stream_writers import DigitalSingleChannelWriter

import ctypes
    
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowIcon(QtGui.QIcon("meb.png"))
        uic.loadUi('GUI_simplif-stable1.ui',self)        
        #variable utilisée pour gérer le nettoyage de la scene dans gestion evenement
        self.flag = 0                                       
        #variables utilisées pour gérer l'amplitude des rampes envoyées
        self.amplitude_AO_column = 4
        self.amplitude_AO_ligne = 6.5
        #calcul taille réelle de un pixel 
        self.size_hole_grid = 37 #µm
        self.size_hole_image = 147 #pix
        self.mag_calibration = 750        
        self.onepix = self.mag_calibration*self.size_hole_grid/(self.size_hole_image)
        #on peut rogner l'image de quelque pixels si problemenb en debut ou fin de ligne
        self.crop = 50
        #inversion des niveaux de gris (image en negatif) 0=Non 1=Oui
        self.inversion_image = 1
        self.resol = 850
        
        #self.val = 0 #A VERIFIER SI SUPPRESSION OK
               
        '''                    BINDS                            '''       
        self.Sauver.clicked.connect(self.file_save)
        self.Grandissement.textChanged.connect(self.bind_acq)            
        self.scan_hor = ""
        self.scan_vert = ""
        self.analog_in = ""      
        self.Acquerir.clicked.connect(self.Demarrer_Acquisition)
        self.pushButton_Quit.clicked.connect(self.quit)  
        self.dev=nidaqmx.system.Device("dev1")       
        self.dev.reset_device() # permet de tuer toutes les taches mal fermées
        
        
        QtCore.QCoreApplication.instance().quit()
        QtWidgets.QMainWindow.close(self) 
        

    def Demarrer_Acquisition(self):
        
        if self.Grandissement.text() == "" or self.Grandissement.text() == "0":
            self.error = QtWidgets.QMessageBox.warning(self, 'Text Error Dialog', 'Entrer un grandissement')
        else:
            self.open_inhibition()
            self.channel()
            # self.resolution()
            self.NiveauxGris()
            self.acq_time()
            self.param()
            self.refresh()
            self.time_control()
            self.scanning()
            self.affiche_image()
            self.close_inhibition()
            self.dev.reset_device()
    
    def file_save(self):
        '''fonction qui permet de sauvegarder l'image acquise'''
        
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Image', r"C:/Users/morin/Desktop/PM_/save", "Image files (*.tif)", options=QtWidgets.QFileDialog.DontUseNativeDialog)
        self.pixmap.save(file_name[0], "TIF")  
        
    # def get_image_file(self):
    #     file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open Image File', r"C:/Users/morin/Desktop/PM_/save", "Image files (*.tif)")  
    #     pixmap = QPixmap(file_name[0], "TIF")
    #     # self.pixmap.load(file_name[0], "TIF")
    #     # self.view_current()
    #     self.scene = QtWidgets.QGraphicsScene()
        
    #     self.scene.setSceneRect(0, 0, 800, 800)
    #     self.pixmap_item = self.scene.addPixmap(pixmap)                   
    #     self.graphicsView.setScene(self.scene)
    #     self.scene.installEventFilter(self) 
    
    def affiche_image(self):
        '''on passe le tableau d'entrée en int puis on le reshape en un tableau numpy2D pour 
           le convertir en QImage puis en QPixmap de 800*800 (on gère aussi l'affichage de la scalebar)'''

        image = np.reshape(self.input_array, (self.points_per_ramp,self.ramps))
        # correction contraste brillance
        image=(image/max(self.input_array))*self.shade
        image = image - np.min(image)       
        image=image/np.max(image)*self.shade  
        
        if self.inversion_image == 1:          
            image = self.shade-image #inversion des niveaux de gris pour MEB AIME  
      
        if self.magnification < 100:
            texte = 500
            print('G < 100')           
        if self.magnification >= 100 and self.magnification < 200:
            texte = 200
            print('G: 100-350')      
        if self.magnification >= 200 and self.magnification < 350:
            texte = 100
            print('G: 200-350')
        if self.magnification >= 350 and self.magnification < 500:
            texte = 50
            print('G: 350-500')         
        if self.magnification >= 500 and self.magnification < 1000:
            texte = 40
            print('G: 500-1000')         
        if self.magnification >= 1000 and self.magnification < 2000:
            texte = 30
            print('G: 1000-2000')          
        if self.magnification >= 2000 and self.magnification < 5000:
            texte = 10
            print('G: 2000-5000')          
        if self.magnification >= 5000 and self.magnification < 10000:
            texte = 5
            print('G: 5000-10000')       
        if self.magnification >= 10000 and self.magnification < 20000:
            texte = 3
            print('G: 10 000-20 000') 
        if self.magnification >= 20000 and self.magnification < 50000:
            texte = 1
            print('G: 20 000-50 000')       
        if self.magnification >= 50000 and self.magnification < 100000:
            texte = 0.5
            print('G: 50 000-100 000')  
            
        if self.magnification >= 100000 and self.magnification < 200000:
            texte = 0.2
            print('G: 100 000-200 000')          
        
        
        #Barre d'echelle
        length_bar = texte/self.onepix*self.magnification
        print('-------------------------')
        print('bar',length_bar)
        print('onePix',self.onepix)
        print('mag',self.magnification)
        print('texte',texte)
        print('-------------------------')
        
        cv2.rectangle(image, (0,self.resol-60),(self.resol,self.resol), (0,0,0), -1)   
       
        deb = int(self.resol-100-length_bar),self.resol-15
        fin = self.resol-100 ,self.resol-15
        print('deb',deb,'fin',fin)
        cv2.line(image,deb,fin,(self.shade,self.shade,self.shade),3)
        
        cv2.putText(image,str(texte)+'mic.',(deb[0],deb[1]-20),cv2.FONT_HERSHEY_DUPLEX,0.8,(self.shade,self.shade,self.shade),2,cv2.LINE_AA)
        
        #crop image pour éviter début de ligne déformés
        cv2.imwrite('image.png',image)
        image_crop = image [self.crop:self.resol, self.crop:self.resol]
        
        # cv2.rectangle(image, (20,20),(self.resol,self.resol), (0,0,0), -1)   
        
        
        cv2.imwrite('image_crop.png',image_crop)
        # self.str = self.Grandissement.text() #VERIFIER SI SUPPRESSION OK
        print('taile image_crop = ', image_crop.shape)
        self.current_image = qimage2ndarray.array2qimage(image_crop)     
        self.w_pix, self.h_pix = image_crop.shape[0],image_crop.shape[1]                                                      
        self.pixmap = QtGui.QPixmap.fromImage(self.current_image.scaled( self.w_pix, self.h_pix, QtCore.Qt.KeepAspectRatio))
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.setSceneRect(0, 0, self.w_pix, self.h_pix)
        self.pixmap_item = self.scene.addPixmap(self.pixmap)                   
        self.graphicsView.setScene(self.scene)
        self.scene.installEventFilter(self)                                                  
        
       
        
    def eventFilter(self, object, event):
        '''cette fonction permet de récupérer les positions du curseur souris sur la QGraphicsScene lorsque l'on clique dessus
           de plus lorqu'on relâche le clic la fonction mémorise la position et trace un trait entre les deux points du clic 
           et du relâchement de celui-ci tout en affichant la distance entre ces deux points
           un nettoyage de la scene est effectué lorque l'on retrace un trait ou lorque l'on change les paramètres d'acquisition'''
       
        if object is self.scene and event.type() == QtCore.QEvent.GraphicsSceneMousePress:
            spf = event.scenePos()
            lpf = self.pixmap_item.mapFromScene(spf)
            brf = self.pixmap_item.boundingRect()
            if brf.contains(lpf):
                lp = lpf.toPoint()
                self.x1 = int(lp.x())
                self.y1 = int(lp.y())
                
                

        if object is self.scene and event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
            spf = event.scenePos()
            lpf = self.pixmap_item.mapFromScene(spf)
            brf = self.pixmap_item.boundingRect()
            if brf.contains(lpf):
                lp = lpf.toPoint()
                pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.red))
                p1x = float(self.x1)
                p1y = float(self.y1)
                p2x = float(str(lp.x()))
                p2y = float(str(lp.y()))
                self.x2 = int(lp.x())
                self.y2 = int(lp.y())
                
                
                if (self.flag == 1):
                    self.scene.removeItem(self.line)
                    self.flag = 0
                    

                self.line = self.scene.addLine(p1x, p1y, p2x, p2y, pen)
                
                self.dist_pix = np.sqrt(((abs(p2y-p1y))**2)+((abs(p2x-p1x))**2))
                self.dist = self.dist_pix*self.onepix/self.magnification              
                self.flag = 1
                
                self.pos_x.setText(str(lp.x()))
                self.pos_y.setText(str(lp.y()))
                
                self.Distance.setText(str(round(self.dist, 3)))
                self.lineEdit_mesureDist.setText(str(round(self.dist, 3)))
                self.lineEditDistance_pix.setText(str(round(self.dist_pix,3)))

                
                
        if object is self.scene and event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
            
            spf = event.scenePos()
            lpf = self.pixmap_item.mapFromScene(spf)
            brf = self.pixmap_item.boundingRect()
            if brf.contains(lpf):
                lp = lpf.toPoint()
                pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.red))
                p1x = float(self.x1)
                p1y = float(self.y1)
                p2x = float(str(lp.x()))
                p2y = float(str(lp.y()))
                
                
                if (self.flag == 0):
                    self.line =  self.scene.addLine(p1x, p1y, p2x, p2y, pen)
                    self.flag = 1
                    
                if (self.flag ==1):
                        self.scene.removeItem(self.line)
                        self.flag=0 
                        self.line =  self.scene.addLine(p1x, p1y, p2x, p2y, pen)
                        self.flag=1

                
                self.dist_pix = np.sqrt(((abs(p2y-p1y))**2)+((abs(p2x-p1x))**2))
                self.dist = self.dist_pix*self.onepix/self.magnification              

                
                self.pos_x.setText(str(lp.x()))
                self.pos_y.setText(str(lp.y()))
                
                self.Distance.setText(str(round(self.dist, 3))) 
                self.lineEdit_mesureDist.setText(str(round(self.dist, 3)))
                self.lineEditDistance_pix.setText(str(round(self.dist_pix,3)))
                
                
                # print('dist pix = ',self.dist_pix)
                # print('dist micron = ',self.dist)
         
        return super().eventFilter(object, event)    
    
  
            
    def bind_acq(self):
        '''si après modification le grandissement est différent que 0 la fonction débloque le bouton d'acquisition sinon il affiche un message d'erreur'''
        
        self.magnification = int(self.Grandissement.text())  

        
    def channel(self):
        '''on bind les voies d'acquisition de la carte NiDAQ'''
        
        self.scan_hor = self.AOchanH.currentText()
        self.scan_vert = self.AOchanV.currentText()
        self.analog_in = self.AIchan.currentText()

    # def resolution(self):
    #     '''on bind la résolution choisie par l'utilisateur '''
        
    #     self.resol = int(self.Resolution.currentText())
                                 ####################################################################################

    def NiveauxGris(self):
        '''on bind la nuance image choisie par l'utilisateur '''
        
        self.shade = int(self.Nuance.currentText())
        
    def acq_time(self):
        '''on bind le temps d'acquisition choisi par l'utilisateur '''
        
        self.time_acq = int(self.Temps.currentText())

    def param(self):
        '''on définit tous les paramètres utiles pour créer le tableau que nous allons envoyer à la carte qui gére
           les balayages horizontal et vertical du MEB 
           on crée aussi le tableau qui sera rempli par la carte en entrée                                         '''
        print('self.resol :',self.resol)
        self.points_per_ramp = self.resol
        self.ramps = self.resol
        self.sampleRate_buff=(self.points_per_ramp*self.ramps)/(self.time_acq)
        
        # if  self.time_acq == 10 and (self.resol == 512 or self.resol == 1024 or self.resol == 800):
        #     self.sampleRate = np.round(self.sampleRate_buff,-3)
            
        #     print(self.sampleRate)
        #     self.timeout = self.time_acq*2
        # else:    
        self.sampleRate = self.sampleRate_buff
        self.timeout = self.time_acq
            
        self.input_array = np.zeros(self.ramps*self.points_per_ramp, dtype=np.float64)
        
        times_out = np.linspace(0, self.time_acq, num=self.ramps)
        
        self.y1 = np.zeros(self.points_per_ramp*self.ramps, dtype=np.float64)   
        self.y2 = np.zeros(self.points_per_ramp*self.ramps, dtype=np.float64)           
        for i  in range(self.points_per_ramp):
            self.y1[i*self.ramps:(i+1)*self.points_per_ramp] = self.amplitude_AO_column*(1-2*times_out/self.time_acq) 
            self.y2[i*self.ramps:(i+1)*self.points_per_ramp] = self.amplitude_AO_ligne*(1-2*i/self.points_per_ramp)
            
        self.output_array = np.array([self.y2,self.y1])
        

            
    def open_inhibition(self):
        '''cette fonction gère la mise en marche de l'inhibition du MEB en envoyant des signaux sur les voies associées de la carte lorsque l'on lance l'acquisition'''
        
    
        
        with nidaqmx.Task() as Task_Open2:   
            
            Task_Open2.do_channels.add_do_chan("/Dev1/port0/line1")
            stream_writerDO1 = DigitalSingleChannelWriter(Task_Open2.out_stream)
            stream_writerDO1.write_one_sample_one_line(0) 
            
            Task_Open2.start()  
                  
 

    def close_inhibition(self):
        '''cette fonction gère l'arrêt de l'inhibition du MEB en envoyant des signaux sur les voies associées de la carte lorsque l'on stoppe le programme'''

        with nidaqmx.Task() as Task_Close2:   
            
            Task_Close2.do_channels.add_do_chan("/Dev1/port0/line1")
            stream_writerDO1 = DigitalSingleChannelWriter(Task_Close2.out_stream)
            stream_writerDO1.write_one_sample_one_line(1) 
            
            Task_Close2.start()  
            
            # self.Inhibition.setEnabled(False)     
    def scanning(self):
        '''ce thread permet d'écrire sur une sortie de la carte NIDAQ le tableau "output_array" construit dans la fonction param et de lire en même temps les niveaux de tension renvoyés 
           par le MEB pour les mettre dans le tableau "input_array" '''

        def write():
            with nidaqmx.Task() as task_write:                                #creation d'une tâche nidaqmx
                
                task_write.ao_channels.add_ao_voltage_chan(self.scan_vert)   
                task_write.ao_channels.add_ao_voltage_chan(self.scan_hor)
                
                task_write.timing.cfg_samp_clk_timing(rate = self.sampleRate, sample_mode = nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan = self.ramps*self.points_per_ramp)
                task_write.export_signals.export_signal(nidaqmx.constants.Signal.START_TRIGGER, "/Dev1/PFI0")
                
                stream_writer = AnalogMultiChannelWriter(task_write.out_stream)     #creation d'un stream    
                #modifie ici pour commencer balayage par le haut et non par le bas
                stream_writer.write_many_sample(-self.output_array)                           #write d'un tableau numpy dans la sortie
                
                
           
                
                
                task_write.start()                                               #démarrage de la tâche
                sleep(self.time_acq)                                          #durée de du programme python (pour pas qu'il s'arrête a l'éxécution)
        
        def read():
            with nidaqmx.Task() as task_read:        
                # création de la tâche d'acquisition
                task_read.ai_channels.add_ai_voltage_chan(self.analog_in, max_val=10, min_val=-10, terminal_config = TerminalConfiguration.RSE)
                task_read.timing.cfg_samp_clk_timing(rate = self.sampleRate, sample_mode = nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan = self.ramps*self.points_per_ramp)
                task_read.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source = "/Dev1/PFI0")
                                
                # création du stream read
                stream_read = AnalogSingleChannelReader(task_read.in_stream)
                # acquisition et stockage des données dans le tableau
                stream_read.read_many_sample(self.input_array, number_of_samples_per_channel = self.ramps*self.points_per_ramp, timeout = self.timeout)
                
                
              

                
                task_read.start()
                  
                #for i in range(0,self.ramps*self.points_per_ramp):
                     #self.input_array[i] = (((self.input_array[i]+10)*self.shade)/20)
       
        th2 = threading.Thread(target=read)
        th1 = threading.Thread(target=write)

        th2.start()
        th1.start()

        th2.join()
        th1.join()

    def refresh(self):
        '''cette fonction permet d'initialiser le timer et la progressBar à chaque fois que l'on fait une acquisition'''
        
        self.value = 0
        self.progressBar.setValue(0)
        self.t = 0
    
    def time_control(self):
        '''la progressBar est rafraîchie tout les 1/10 du time_acq choisi'''

        app.processEvents()
        self.time = self.time_acq/10
        
        if (self.t==0):
            pass
        else:
            self.value += int((self.time/(self.time_acq))*100)
            self.progressBar.setValue(self.value)
            
         
            
        
        if (self.value == 100):
            pass
        else:
            self.t = 1
            Timer(self.time, self.time_control).start()


        
    def quit(self):
        
        self.dev.reset_device()    
        QtCore.QCoreApplication.instance().quit()
        QtWidgets.QMainWindow.close(self) 
        
        
        

        
if __name__==  "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    
