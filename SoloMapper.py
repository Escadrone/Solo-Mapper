import threading
import time
from SoloMapper_Servo import GimbalServo
from SoloMapper_QX1 import SoloCamera
import ConfigParser
from dronekit import connect, Vehicle


# init the SoloCamera module which connects to the Sony QX1 and starts liveview streaming
SoloQX1 = SoloCamera()
# Parse the configuration file and fetch Solo connection parameters
ConfigSolo = ConfigParser.ConfigParser()
ConfigSolo.read("SoloMapperConfig.txt")
# Fetch camera informations
SoloSerialPort = ConfigSolo.get("Solo", "SoloSerialPort") #default /dev/ttyUSB0
SoloSerialBaudrate = ConfigSolo.get("Solo", "SoloSerialBaudrate") #default 230400
vehicle = connect(SoloSerialPort, baud = SoloSerialBaudrate, wait_ready=True)
print " Mode: %s" % vehicle.mode.name
# init the GimbakServo module which controls the servos and RGB status LED
#                            (rool, pitch, adresse I2C, positons min max de chaque voie)
SoloGimbalServo = GimbalServo(0, 1, 0x40, 220, 550, 200, 500)
SoloGimbalServo.initRGB()

#mettre message mavlink camera feedback ici si on trouve

#main loop
while 1:
 # trigger a picture
 if vehicle.channels['8'] == 1000:
  SoloQX1.takePicture( vehicle.location.global_frame.lat, vehicle.location.global_frame.lon, vehicle.location.global_frame.alt)
 SoloGimbalServo.updatePosition(-vehicle.attitude.roll, -vehicle.attitude.pitch, vehicle.channels['6'])
 
 # check if the solo is about to shut down
 if vehicle.system_status.state == 'POWEROFF':
  os.system("poweroff")
 time.sleep(0.02)
