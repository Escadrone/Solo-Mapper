#!/usr/bin/python
from LogConfig import LogSystem
import logging
import os
from MavlinkConfig import MavConfig

########## Stat logging init ########

#Create a log folder if necessary
logFolderPath = "/mnt/Usb-Solo-Mapper"
logDirectoryName = "Logs"
existingDirectory = False
dirList = os.listdir(logFolderPath)

for dossier in dirList:  
  if dossier.find(logDirectoryName) == 0: #If log folder already exists
   existingDirectory = True

if existingDirectory == False:
 os.makedirs(''+logFolderPath+'/'+logDirectoryName+'')
 print 'Log folder created!'

else:
  print 'Log folder found'

#Open main logging file
loggerName = "SOLO Mapper Logger"
logFile = "activity"
logManager = LogSystem(loggerName,logFile,True) #On cree une instance de configuration du log
logger = logManager.getGlobalLogger()
print 'LOGGER :',logger
############ End logging init #############



import threading
import subprocess
import time

from SoloMapper_Servo import GimbalServo
from SoloMapper_QX1 import SoloCamera
import ConfigParser
from dronekit import connect, Vehicle, mavutil
#from UsbLogger import UsbLoggerThread
from PhotoCommand import PhotoCommandThread
from MavlinkConfig import MavConfig
from FlagManager import FlagSystem
import datetime


commandeNacelle = 0



# init the SoloCamera module which connects to the Sony QX1 and starts liveview streaming
#Bloquant si n'arrive pas a se connecter a l'appareil photo - si appareil photo pas allume
logger.info('*****************************************************************************************************')
logger.info('******************************************NOUVEAU VOL************************************************')
logger.info('*****************************************************************************************************')
logger.info('*****************************SOLO Mapper - Version 3.0, Escadrone************************************')
logger.info('*****************************************************************************************************')

# Parse the configuration file and fetch Solo connection parameters
ConfigSolo = ConfigParser.ConfigParser()
ConfigSolo.read("/mnt/Usb-Solo-Mapper/SoloMapperConfig.txt")
logger.info('ConfigSolo : %s', ConfigSolo)

# Fetch camera informations
SoloSerialPort = ConfigSolo.get("Solo", "SoloSerialPort") #default /dev/ttyUSB0
logger.info('SoloSerialPort : %s', SoloSerialPort)
SoloSerialBaudrate = ConfigSolo.get("Solo", "SoloSerialBaudrate") #230400
logger.info('SoloSerialBaudrate : %s', SoloSerialBaudrate)

try:
 vehicle = connect(SoloSerialPort, baud = SoloSerialBaudrate, wait_ready=['system_status','attitude','channels'], heartbeat_timeout=30)
 logger.info('vehicle : %s', vehicle)
except Exception as e:
 try:
  vehicle = connect(SoloSerialPort, baud = SoloSerialBaudrate, wait_ready=['system_status','attitude','channels'], heartbeat_timeout=30)
  logger.info('vehicle : %s', vehicle)
 except Exception as e:
  vehicle.close()
  logger.error('Erreur de connection au drone SOLO : %s',e)
  time.sleep(0.5)
  #SoloGimbalServo.updateRGColor(0,0) # LED eteinte
  #subprocess.call("umount /dev/sda",shell=False)
  subprocess.call("umount /dev/sda1",shell=True)
  os.system("shutdown now -r")

# Configure le stream des messages du drone vers le RasberryPi (Serial Port 4)
configurationMavlink = MavConfig(vehicle) 
configurationMavlink.ConfigureStreamMessage()


##Config + lancement du thread de check des ports USB
#checkUSBportThread = UsbLoggerThread(logger) #creation nouvelle instance
#try:
#  checkUSBportThread.setDaemon(True)
#  checkUSBportThread.start() #lancement thread
#  logger.info('Starting checkUSBportThread')
#except BaseException, exc:
#  logger.error('Error launching checkUSBportThread : %s',exc)


logger.info('Mode : %s', vehicle.mode.name)



#Update the Raspi Date and time once with the first SYSTEM_TIME message from the SOLO
#Check that Mavlink messages are well send from the SOLO (/20s)
#Tuned to 1 SYSTEM_TIME message by second
@vehicle.on_message('SYSTEM_TIME')
def listener(self, name, message):
 if FlagSystem.dateUpdated == False:
  if message.time_unix_usec != 0: #If GPS messages containing actual date/time have already been received by the SOLO
   unix_time = (int) ((message.time_unix_usec)/1000000)   
   try:
    dateUpdate_process = subprocess.Popen('sudo date -s \"'+ str(datetime.datetime.fromtimestamp(unix_time)) +'\"', stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    logger.info('Date and time updated to: %s',str(datetime.datetime.fromtimestamp(unix_time)))    
    FlagSystem.dateUpdated = True
   except Exception as e:
     logger.error('Error updating Raspi date and time')

 FlagSystem.checkMavlinkMessages += 1 
 if FlagSystem.checkMavlinkMessages >= 20:
  logger.info('MAVLINK messages well received') #Si pas de log pendant plus de 20 secondes, on sait que le lien MAVLINK est perdu...
  FlagSystem.checkMavlinkMessages = 0

 

# Get gimbal tuning
MinPosYaw = int(ConfigSolo.get("Servos","MinPosYaw"))
logger.debug('MinPosYaw has been set to : %s', MinPosYaw)
MaxPosYaw = int(ConfigSolo.get("Servos","MaxPosYaw"))
logger.debug('MaxPosYaw has been set to : %s', MaxPosYaw)
MinPosPitch = int(ConfigSolo.get("Servos","MinPosPitch"))
logger.debug('MinPosPitch has been set to : %s', MinPosPitch)
MaxPosPitch = int(ConfigSolo.get("Servos","MaxPosPitch"))
logger.debug('MaxPosPitch has been set to : %s', MaxPosPitch)
ButeeMinPitch = int(ConfigSolo.get("Servos","ButeeMinPitch"))
logger.debug('ButeeMinPitch has been set to : %s', ButeeMinPitch)
ButeeMaxPitch = int(ConfigSolo.get("Servos","ButeeMaxPitch"))
logger.debug('ButeeMaxPitch has been set to : %s', ButeeMaxPitch)
tiltOffsetFactor = float(ConfigSolo.get("Servos","tiltOffsetFactor"))
logger.debug('tiltOffsetFactor has been set to : %s', tiltOffsetFactor)
#Get camera type/name
cameraName = str(ConfigSolo.get("Camera","Name"))
#Get manual photo trigger tuning
tiltMaxLevel = int(ConfigSolo.get("ManualPhotoTrigger","TiltLevel"))

if cameraName == "SonyQX1":
 SoloQX1 = SoloCamera(logger)
 logger.info('SoloQX1 : %s', SoloQX1)
else:
 logger.info('Camera : %s',cameraName)



SoloGimbalServo = GimbalServo(0, 1, 0x40, MinPosYaw, MaxPosYaw, MinPosPitch, MaxPosPitch, ButeeMinPitch, ButeeMaxPitch, tiltOffsetFactor, logger)
SoloGimbalServo.initRG(6,7)
SoloGimbalServo.updateRGColor(0,4095) # LED Verte
logger.info('Setting led green now')


# Config + lancement du thread de prise de photo
if cameraName == "SonyQX1":
  photothread = PhotoCommandThread(SoloQX1, vehicle, SoloGimbalServo, tiltMaxLevel, logger) 
  try:
    photothread.setDaemon(True)
    photothread.start()
    logger.info('Starting photoThread')
  except BaseException, exc:
    logger.error('Error launching photothread : %s',exc)
   
    
# Trigger a picture on DO_DIGICAM_CONTROL (Ecoute message de commande de prise de photo)
@vehicle.on_message('CAMERA_FEEDBACK')
def listener(self, name, message):
 FlagSystem.QX1PhotoOrder = True
 logger.info('CAMERA_FEEDBACK message received')




#Listener pour savoir si le drone a effectue un cycle complet de vol (vol/atterissage avec prise de photos) - QUELQUE SOIT LE MODE DE VOL!
@vehicle.on_attribute('system_status')
def stateListener(self, attr_name, msg):
 if vehicle.system_status.state == 'ACTIVE':
  FlagSystem.droneIsFlying = True
 elif vehicle.system_status.state == 'STANDBY':
  if FlagSystem.droneIsFlying == True:
   FlagSystem.droneIsFlying = False
   FlagSystem.droneIsLanding = True
 elif vehicle.system_status.state == 'CRITICAL':
  if FlagSystem.droneIsFlying == True:
   FlagSystem.droneIsFlying = False
   FlagSystem.droneIsLanding = True
 elif vehicle.system_status.state == 'EMERGENCY':
  if FlagSystem.droneIsFlying == True:
   FlagSystem.droneIsFlying = False
   FlagSystem.droneIsLanding = True
 elif vehicle.system_status.state == 'POWEROFF':
  #subprocess.call("umount /dev/sda",shell=False)
  vehicle.close()
  subprocess.call("umount /dev/sda1",shell=True)
  os.system("shutdown now -P")

 logger.debug('system_status stateListener %s', msg)

 
# # Create a message listener for all messages.
# @vehicle.on_message('*')
# def listener(self, name, message):
#   print 'message: %s' % message


try:
##############################
#######  MAIN LOOP ###########
##############################
  while 1:
   #commande servo
   #Si l'on est pas en commande photo, on met a jour normalement la commande nacelle. Sinon, on garde la valeur precedente. 
   if FlagSystem.QX1IsTakingPicture == False:
    commandeNacelle = vehicle.channels['6']
   
   SoloGimbalServo.updatePosition(-vehicle.attitude.roll, vehicle.attitude.pitch, commandeNacelle) 
   
   time.sleep(0.02)

except BaseException, e:
  SoloGimbalServo.updateRGColor(0,0) # LED eteinte
  logger.error('Error main thread !')
  logger.error('Main thread except e : %s', e)
  

