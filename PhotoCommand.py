import random
import sys
from threading import Thread, RLock
import time
from dronekit import Vehicle
from SoloMapper_QX1 import SoloCamera
from FlagManager import FlagSystem
import logging

"""Thread charge d'ecouter la commande de prise de photo """

verrou = RLock()


class PhotoCommandThread(Thread):

    goOn = True
    droneSolo = 0 #drone
    cameraSony = 0 #appareil photo
    pwm = 0 #instance de commande de pwm(LED)
  
  
    def __init__(self,camera,vehicle,commandePWM,tiltMlevel,globalLogger):
        Thread.__init__(self)
        self.droneSolo = vehicle
        self.cameraSony = camera
        self.pwm = commandePWM
        self.tiltLevel = tiltMlevel
        self.logger = globalLogger


 
    def run(self):         
          
        while self.goOn:     
       
         if FlagSystem.QX1IsRunning:
           if (FlagSystem.QX1PhotoOrder or self.droneSolo.channels['8'] >= self.tiltLevel or self.droneSolo.channels['7'] > 1000 ):
            with verrou:                         
             FlagSystem.QX1IsTakingPicture = True
	     self.logger.info('QX1 is taking a picture at lat : %s, long : %s, alt : %s', self.droneSolo.location.global_frame.lat, self.droneSolo.location.global_frame.lon, self.droneSolo.location.global_frame.alt)	
             self.cameraSony.takePicture( self.droneSolo.location.global_frame.lat, self.droneSolo.location.global_frame.lon, self.droneSolo.location.global_frame.alt) 
             FlagSystem.QX1PhotoOrder = False
             FlagSystem.QX1IsTakingPicture = False         

           if FlagSystem.droneIsLanding:
            if FlagSystem.QX1IsRunning:
             with verrou:                
              self.pwm.updateRGColor(4095,0) #LED Rouge
	      self.logger.info('Drone is landing, setting LED red')	

              try:               
               nbPhotosATelecharger = self.cameraSony.downloadTakenPictures()
	       self.logger.info('%s pictures to download', nbPhotosATelecharger) 

               if nbPhotosATelecharger > 0: # Si l' on a au moins pris une photo pendant le vol
                self.pwm.RedTwinkle(55) # On attend 55 secondes (petite marge incluse) le temps que toutes les photos soient bien copiees en memoire sur la cle USB
               self.logger.info('Downloading is completed, setting LED green') 
              except Exception as err: #Si le telechargement plante cad si l'appareil photo s'eteint
               self.pwm.updateRGColor(2500,4095) #LED Orange      
               logging.debug("Error downloading, setting LED orange")         
               logging.debug("Error downloading : %s",err)
               time.sleep(12)     
              self.pwm.updateRGColor(0,4095) #LED Verte
                
            FlagSystem.droneIsLanding = False
          

         time.sleep(0.1)   




    def stop(self):
        """Methode pour arreter le thread"""
        self.goOn = False




