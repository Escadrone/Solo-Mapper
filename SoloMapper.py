import threading
import time
from SoloMapper_Servo import GimbalServo
from SoloMapper_QX1 import SoloCamera
import ConfigParser
from dronekit import connect, Vehicle, mavutil
from PhotoCommand import PhotoCommandThread
from MavlinkConfig import MavConfig
from FlagManager import FlagSystem
import logging


commandeNacelle = 0

#Initialisation fichier de log
LOG_FILENAME2 = '/mnt/Usb-Solo-Mapper/solom.log'
open(LOG_FILENAME2, 'w').close() #on vide le fichier de log
logging.basicConfig(filename=LOG_FILENAME2,level=logging.DEBUG)
logging.debug('NOUVEAU VOL')

# init the SoloCamera module which connects to the Sony QX1 and starts liveview streaming
#Bloquant si n'arrive pas a se connecter a l'appareil photo - si appareil photo pas allume
SoloQX1 = SoloCamera()

# Parse the configuration file and fetch Solo connection parameters
ConfigSolo = ConfigParser.ConfigParser()
ConfigSolo.read("/mnt/Usb-Solo-Mapper/SoloMapperConfig.txt")

# Fetch camera informations
SoloSerialPort = ConfigSolo.get("Solo", "SoloSerialPort") #default /dev/ttyUSB0
SoloSerialBaudrate = ConfigSolo.get("Solo", "SoloSerialBaudrate") #230400
try:
 vehicle = connect(SoloSerialPort, baud = SoloSerialBaudrate, wait_ready=True) 
except Exception:
 logging.debug('Erreur de connection au drone SOLO!')

# Configure le stream des messages du drone vers le RasberryPi (Serial Port 4)
configurationMavlink = MavConfig(vehicle) 
configurationMavlink.ConfigureStreamMessage()

print " Mode: %s" % vehicle.mode.name

# Init the GimbakServo module which controls the servos and RG status LED
#                            (rool, pitch, adresse I2C, positons min max de chaque voie)
MinPosYaw = int(ConfigSolo.get("Servos","MinPosYaw"))
MaxPosYaw = int(ConfigSolo.get("Servos","MaxPosYaw"))
MinPosPitch = int(ConfigSolo.get("Servos","MinPosPitch"))
MaxPosPitch = int(ConfigSolo.get("Servos","MaxPosPitch"))
ButeeMinPitch = int(ConfigSolo.get("Servos","ButeeMinPitch"))
ButeeMaxPitch = int(ConfigSolo.get("Servos","ButeeMaxPitch"))
tiltOffsetFactor = float(ConfigSolo.get("Servos","tiltOffsetFactor"))


SoloGimbalServo = GimbalServo(0, 1, 0x40, MinPosYaw, MaxPosYaw, MinPosPitch, MaxPosPitch,ButeeMinPitch,ButeeMaxPitch,tiltOffsetFactor)
SoloGimbalServo.initRG(6,7)
SoloGimbalServo.updateRGColor(0,4095) # LED Verte


# Config + lancement du thread de prise de photo
photothread = PhotoCommandThread(SoloQX1,vehicle,SoloGimbalServo) 
try:
  photothread.setDaemon(True)
  photothread.start()
except BaseException, exc:
  logging.debug('!!!!!!!PHOTOTHREAD!!!!!!!')
  logging.debug(exc)
  print'!!!!!!!PHOTOTHREAD!!!!!!!'
  print exc

# Trigger a picture on DO_DIGICAM_CONTROL (Ecoute message de commande manuelle de prise de photo)
@vehicle.on_message('CAMERA_FEEDBACK')
def listener(self, name, message):
 FlagSystem.QX1PhotoOrder = True
 print 'MESSAGE: %s' % message



#Listener pour savoir si le drone a effectuer un cycle complet de vol (vol/atterissage avec prise de photos) - QUELQUE SOIT LE MODE DE VOL!
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

 print msg
 logging.debug(msg)

 
#Create a message listener for all messages.
@vehicle.on_message('RC_CHANNELS_RAW')
def listener(self, name, message):
    print 'message: %s' % message


try:

  #main loop
  while 1:
   #commande servo
   #Si l'on est pas en commande photo, on met a jour normalement la commande nacelle. Sinon, on garde la valeur precedente. 
   if FlagSystem.QX1IsTakingPicture == False:
    commandeNacelle = vehicle.channels['6']
   
   SoloGimbalServo.updatePosition(-vehicle.attitude.roll, vehicle.attitude.pitch, commandeNacelle) 
   
   time.sleep(0.02)

except BaseException, e:
  logging.debug('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ARRET BOUCLE PRINCIPALE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
  logging.debug(e)
  print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
  print e

