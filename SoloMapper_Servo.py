"""
SoloMapper_Servo.py
File used to control the Servo/PWM Pi Hat board on top of the Raspberry Pi
It uses mainly Adafruit PWM librairy
"""
from Adafruit_PWM_Servo_Driver import PWM

# GimbalServo Class for controlling both Pitch and Roll servos off the camera's gimbal
class GimbalServo:
 def __init__(self, channelYaw=0, channelPitch=1, I2C_address = 0x40, MinPosYaw=200, MaxPosYaw=300, MinPosPitch=200, MaxPosPitch=300):
  # init and configure PWM module
  self.pwm = PWM(I2C_address) # Create the PWM object
  self.pwm.setPWMFreq(60) # Set frequency to 60 Hz
  # store arguments
  # channels
  self.channelYaw = channelYaw 
  self.channelPitch = channelPitch
  
  # servos min and max positions
  # check if argument are positive values
  if MinPosYaw > 0 and \
     MaxPosYaw > 0 and \
     MinPosPitch > 0 and \
     MaxPosPitch > 0 :
  
    # yaw
    # check if min<max
    if MinPosYaw < MaxPosYaw:
     self.MinPosYaw = MinPosYaw 
     self.MaxPosYaw = MaxPosYaw
    else:
     self.MinPosYaw = MaxPosYaw 
     self.MaxPosYaw = MinPosYaw
     
    # pitch
    # check if min<max
    if MinPosPitch < MaxPosPitch:
     self.MinPosPitch = MinPosPitch
     self.MaxPosPitch = MaxPosPitch
    else:
     self.MinPosPitch = MaxPosPitch   
     self.MaxPosPitch = MinPosPitch
  else:
   #if position values are negative affect dummy values
   self.MinPosYaw=200
   self.MaxPosYaw=300
   self.MinPosPitch=200
   self.MaxPosPitch=300
	
  #Compute values from radian to servo PWM unit
  self.gainYaw = (self.MaxPosYaw - self.MinPosYaw) / 3.1415 # pi -> 180 degree
  self.offsetYaw = (self.MaxPosYaw + self.MinPosYaw) / 2 # zero position
  
  self.gainPitch = (self.MaxPosPitch - self.MinPosPitch) / 3.1415 # pi -> 180 degree
  self.offsetPitch = (self.MaxPosPitch + self.MinPosPitch) / 2 # zero position    
  
  #print "Min Yaw: ", self.MinPosYaw, "Max Yaw: ", self.MaxPosYaw, "Min Pitch: ", self.MinPosPitch, "Max Pitch: ", self.MaxPosPitch # debug
  #print "Gain Yaw: ", self.gainYaw, "Offset Yaw: ", self.offsetYaw, "Gain Pitch: ", self.gainPitch, "Offset Pitch: ", self.offsetPitch # debug
  
 #update servos position uppon yaw and pitch values given in radian, and tilt given in raw channel value
 def updatePosition(self, yaw, pitch, tilt):
  # Check if yaw and pitch value are good ( must be from -pi/2 to +pi/2)
  if abs(yaw) < 2 and abs(pitch) < 2:
   # Compute tilt offset (tilt channel varies from 1000 to 1520 respectively 0 and 90 degree
   tiltOffset = (tilt - 1000)/4
   # Compute servo values
   yawValue = self.offsetYaw + ( self.gainYaw * yaw)
   pitchValue = self.offsetPitch + tiltOffset + ( self.gainPitch * pitch) 
   
   #clamp values to min and max servo position
   if yawValue > self.MaxPosYaw:
    yawValue = self.MaxPosYaw
   if yawValue < self.MinPosYaw:
    yawValue = self.MinPosYaw
    
   if pitchValue > self.MaxPosPitch:
    pitchValue = self.MaxPosPitch
   if pitchValue < self.MinPosPitch:
    pitchValue = self.MinPosPitch
   self.pwm.setPWM(self.channelYaw,0, int(yawValue))
   self.pwm.setPWM(self.channelPitch,0, int(pitchValue))
   #print "Yaw: ", int(yawValue), "Pitch: ", int(pitchValue) #debug
 
 #update RGB led Color
 def initRGB(self, channelRed=13, channelGreen=14, channelBlue=15):
  # channels
  self.channelRed = channelRed
  self.channelGreen = channelGreen
  self.channelBlue = channelBlue
 
 #update RGB led colors
 def updateRGBColor(self, R, G, B):
  self.pwm.setPWM(self.channelRed,0, int(R))
  self.pwm.setPWM(self.channelGreen,0, int(G))   
  self.pwm.setPWM(self.channelBlue,0, int(B)) 
  
 def __del__(self):
  # Release servo power on garbage collect
  self.pwm.softwareReset()

   
 
 