"""
SoloMapper_Servo.py
File used to control the Servo/PWM Pi Hat board on top of the Raspberry Pi
It uses mainly Adafruit PWM librairy
"""

from Adafruit_PWM_Servo_Driver import PWM
import time
from FlagManager import FlagSystem

# GimbalServo Class for controlling both Pitch and Roll servos off the camera's gimbal
class GimbalServo:
 

 def __init__(self, channelYaw, channelPitch, I2C_address, MinPosYaw, MaxPosYaw, MinPosPitch, MaxPosPitch,ButeeMinPitch,ButeeMaxPitch,tiltOffsetFactor,globalLogger): 
  # init and configure PWM module
  self.pwm = PWM(I2C_address) # Create the PWM object
  self.pwm.setPWMFreq(50) # Set frequency to 50 Hz = > Ne pas modifier !!!
  # store arguments
  self.channelYaw = channelYaw 
  self.channelPitch = channelPitch
  self.MinPosYaw = MinPosYaw 
  self.MaxPosYaw = MaxPosYaw
  self.MinPosPitch = MinPosPitch
  self.MaxPosPitch = MaxPosPitch
  self.ButeeMinPitch = ButeeMinPitch
  self.ButeeMaxPitch = ButeeMaxPitch
  self.tiltOffsetFactor = tiltOffsetFactor
  self.logger = globalLogger

  #Compute values from radian to servo PWM unit  
  self.gainYaw = (self.MaxPosYaw - self.MinPosYaw)*3.2727 / 3.1415 # pi/1.1034 -> 55 degrees de course
  self.offsetYaw = (self.MaxPosYaw + self.MinPosYaw) / 2 # zero position
  
  self.gainPitch = (self.MaxPosPitch - self.MinPosPitch) * 2 / 3.1415  # pi/2 -> 90 degree

  


 #Update servos position uppon yaw and pitch values given in radian, and tilt given in raw channel value
 def updatePosition(self, yaw, pitch, tilt):

  # Check if yaw and pitch value are good ( must be approximatively from -pi/2 to +pi/2)
  if abs(yaw) < 2 and abs(pitch) < 2:
   # Compute tilt offset (tilt channel varies from 1000 to 1520 respectively 0 and 90 degree and clamp if rc off
   if 999 < tilt < 1521: 
    tiltOffset = ((1520-tilt)*self.tiltOffsetFactor)   
   elif tilt == 0: #Si la telecommande n'est pas allumee / detectee
    tiltOffset = 0
   else: #Si valeur absurde
    tiltOffset = 0

   # Compute servo values 
   yawValue = self.offsetYaw + ( self.gainYaw * yaw) 
   pitchValue = self.MinPosPitch + tiltOffset + ( self.gainPitch * pitch)  
   
   #Eviter de venir en butee physique
   if pitchValue > self.ButeeMaxPitch:
    pitchValue = self.ButeeMaxPitch
   if pitchValue < self.ButeeMinPitch:
    pitchValue = self.ButeeMinPitch

   #Eviter de venir en butee physique
   if yawValue > self.MaxPosYaw:
    yawValue = self.MaxPosYaw
   if yawValue < self.MinPosYaw:
    yawValue = self.MinPosYaw
  

   #Envoi des commandes aux moteurs
   try : 
    self.pwm.setPWM(self.channelPitch,0, int(pitchValue))
    self.pwm.setPWM(self.channelYaw,0, int(yawValue))
   except Exception as e:
    self.logger.error('PWM servo command crashed : %s', e)

  
 
 #initialize RG led Color
 def initRG(self, channelRed, channelGreen):
  # channels
  self.channelRed = channelRed
  self.channelGreen = channelGreen
  
 
 # #update RGB led colors
 def updateRGColor(self, R, G):
  try:
   self.pwm.setPWM(self.channelRed,0, int(R))
   self.pwm.setPWM(self.channelGreen,0, int(G))  
  except Exception  as err:
   self.logger.error('PWM Led command crashed : %s',err)

# Fait clignoter la LED en rouge pendant le temps qu'elle prend en parametre
 def RedTwinkle(self,deltaT): 
  i = 0
  while i < int(deltaT / 2 + 1):
   self.updateRGColor(4095,0) #LED rouge
   time.sleep(1.5)
   self.updateRGColor(0,0) #LED eteinte
   time.sleep(0.5)
   i+=1


 def __del__(self):
  # Release servo power on garbage collect
  self.pwm.softwareReset()

   
 
 