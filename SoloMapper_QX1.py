"""
SoloMapper_QX1.py
File used to control the Sony QX1 camera
"""
import pysony
import ConfigParser
import re
import subprocess
import urllib
import time
import threading
import os
from SoloMapper_File import ExifWriter

# GimbalServo Class for controlling both Pitch and Roll servos off the camera's gimbal
class SoloCamera:
 def __init__(self):
  # Parse configuration file
  Config = ConfigParser.ConfigParser()
  Config.read("SoloMapperConfig.txt")
  # Fetch camera informations
  self.CameraIP = Config.get("Camera", "CameraIP")
  self.CameraSSID = Config.get("Camera", "CameraSSID")
  self.CameraPSK = Config.get ("Camera", "CameraPSK")
  self.CamreaPictureDirectory = Config.get ("Camera", "CamreaPictureDirectory")
  #check if picture directory exists
  if not os.path.isdir(self.CamreaPictureDirectory):
   os.makedirs(self.CamreaPictureDirectory)
  
  # Configure Wifi interfaces with a template
  wifiTemplateParameters = [
    ['%WIFI_SSID%', self.CameraSSID], 
    ['%WIFI_PASSWD%', self.CameraPSK]
]
  # Try to apply the template to the /etc/network/interfaces file
  try:
   self.applyTemplate('/etc/network/interfaces', 'SoloWifiTemplate.txt', wifiTemplateParameters)
  except TemplateError as error:
   print "exception during applyTemplate call"
   print error

  # Check if wifi connection with QX1 works with ping
  print "Trying to connect with Sony QX1..."
  CheckQX1 = 1
  while CheckQX1!=0:
   try:
    CheckQX1 = subprocess.call(["ping","-c 2",self.CameraIP], shell=False)
   except:
    print("Can't connect with Sony QX1")
    CheckQX1 = 0
  print "QX1 has answered and given an IP address"
  #connect with the camera using sony api
  self.api = pysony.SonyAPI( "http://"+ self.CameraIP + ":8080")
  #put the camera in remote shooting mode
  self.api.setCameraFunction("Remote Shooting")
  #scpecify the postview image size format
  self.api.setPostviewImageSize("Original")
  print "Connected with QX1"
  #launch the liveview thread
  try:
   threadLV = LiveViewThread(3, "LiveViewThread", self.api,self.CameraIP)
   threadLV.start()
  except:
   print "Error: unable to start Live View thread"
   
 # 
 # Take a picture and store the GPS coordinates and Altitude into its Exif
 #
 def takePicture(self, lat, long, altitude):
  #take a picture
  pictureTaken=self.api.actTakePicture()
  #retrieve name of the picture taken
  print ("Picture taken: ")
  #actTakePicture return a json Array of array and the name of the picture is given under 'result' field
  picturefilestring = pictureTaken['result'][0][0] 
  #removing the backslashes
  picturefilestring = picturefilestring.replace('\\',"")
  #get the picture name
  picturename = re.search('DSC.*\.JPG', picturefilestring).group(0)
  print "Picture URL: " + self.CamreaPictureDirectory + picturename
  #download the picture from the QX1 to the raspberry Pi
  urllib.urlretrieve(picturefilestring,self.CamreaPictureDirectory + picturename)
  ExifWriter.write_gps(self.CamreaPictureDirectory + picturename,lat, long, altitude)
  
 # 
 # Replace the interfaceFileUrl file content by the templateFileUrl with values following the templatedItems
 #
 def applyTemplate(self,interfaceFileUrl, templateFileUrl, templatedItems):
  # Get the template content
  file_template = open(templateFileUrl, 'r')
  file_string = file_template.read()
  file_template.close()
  
  #Add a warning
  file_string = "#This is a generated file. Please do not edit directly. Instead use the interfaceTemplate file. \n\n" + file_string
  
  # Replace template items
  for item in templatedItems:
   if item[0] not in file_string: 
    raise TemplateError('template item \'' + item[0] + '\' does not exist in ' + interfaceFileUrl)
   file_string = (re.sub(item[0], item[1], file_string))
  
  # New content is written into the file
  file_interface = open(interfaceFileUrl, 'w')
  file_interface.write(file_string)
  file_interface.close()

#
# Live view thread management 
#
class LiveViewThread (threading.Thread):
 def __init__(self, threadID, name, sonyapi, CameraIP):
  threading.Thread.__init__(self)
  self.threadID = threadID
  self.name = name
  self.api = sonyapi
  self.CameraIP = CameraIP
 def run(self):
  print "Starting " + self.name
  print self.api.startLiveview()
  # Video is streamed with omxplayer
  print "Launching omxplayer"
  try:
   retcode = subprocess.call("omxplayer" + " --live -o hdmi http://"+ self.CameraIP + ":8080/liveview/liveviewstream" , shell=True)
   if retcode < 0:
    print "Omxplayer was terminated by signal"
   else:
    print "Omxplayer returned"
  except OSError as e:
    print >>sys.stderr, "Omxplayer Execution failed:", e
  print "Exiting " + self.name	
	
 

class TemplateError(Exception):
 def __init__(self, value):
  self.value = value
 def __str__(self):
  return repr(self.value)
