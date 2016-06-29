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
import os,sys
import signal
from SoloMapper_File import ExifWriter
from dronekit import connect, Vehicle
from FlagManager import FlagSystem
import logging



# GimbalServo Class for controlling both Pitch and Roll servos off the camera's gimbal
class SoloCamera:

 picturefilestringList = list()
 picturenameList = list()
 latList = list()
 longList = list()
 altitudeList = list()

 proc2 = 0
 vehicle = 0 

 

 def __init__(self):
  # Parse configuration file
  Config = ConfigParser.ConfigParser()
  Config.read("/mnt/Usb-Solo-Mapper/SoloMapperConfig.txt")
  #Config.read("SoloMapperConfig.txt")
  # Fetch camera informations
  self.CameraIP = Config.get("Camera", "CameraIP")
  self.CameraSSID = Config.get("Camera", "CameraSSID")
  self.CameraPSK = Config.get ("Camera", "CameraPSK")
  self.CameraPicturePath = Config.get ("Camera", "CameraPicturePath")
  self.CameraPictureDirectoryName = Config.get ("Camera", "CameraPictureDirectoryName")


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
  FlagSystem.QX1IsRunning = True
  #connect with the camera using sony api
  self.api = pysony.SonyAPI( "http://"+ self.CameraIP + ":8080")
  #put the camera in remote shooting mode
  self.api.setCameraFunction("Remote Shooting")
  #scpecify the postview image size format
  self.api.setPostviewImageSize("Original")
  print "Connected with QX1"
  #launch the liveview thread
  try:
   self.threadLV = LiveViewThread(3, "LiveViewThread", self.api,self.CameraIP)
   self.threadLV.start()
   
  except:
   FlagSystem.QX1IsRunning = False
   proc4 = subprocess.Popen("omxplayer" + " -o hdmi videos/connexionLost.mp4", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
   print "Error: unable to start Live View thread"
   logging.debug('Error: unable to start Live View thread')



 # 
 # Prend une photo et stock son chemin (carte sd) ainsi que les donnees GPS associees
 #
 def takePicture(self, lat, longit, altitude):

  self.proc2 = subprocess.Popen("omxplayer" + " -o hdmi videos/pictureTaken4.mp4", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
  
  try :   
   pictureTaken=self.api.actTakePicture()   
   #retrieve name of the picture taken
   print ("Picture taken: ")
   #actTakePicture return a json Array of array and the name of the picture is given under 'result' field
   picturefilestring = pictureTaken['result'][0][0] 
   #removing the backslashes
   picturefilestring = picturefilestring.replace('\\',"")
   #get the picture name
   print'picturefilestring :',picturefilestring
   picturename = re.search('DSC.*\.JPG', picturefilestring).group(0)
  
   self.picturefilestringList.append(picturefilestring)
   self.picturenameList.append(picturename)
   self.latList.append(lat)
   self.longList.append(longit)
   self.altitudeList.append(altitude)
  
      
  except Exception: 
   proc5 = subprocess.Popen("omxplayer" + " -o hdmi /mnt/Usb-Solo-Mapper/videos/errorTakingPicture.mp4", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
   proc5.wait()
   logging.debug('errorTakingPicture!')

 # 
 # Telecharge les photos prises pendant le vol, et ecrit dans les .exif les donnees GPS sauvegardees
 #
 def downloadTakenPictures(self): 
  j = 0
  k = 0
  preexistingDirectory = 0

  nbPhotos = len(self.picturefilestringList)

  #Si l'on a pris au moins une photo en vol, on cree un nouveau dossier et on telecharge les photos
  if nbPhotos > 0:

    #Liste des dossiers
    dirList = os.listdir(self.CameraPicturePath)
    for dossier in dirList:  
      if dossier.find(self.CameraPictureDirectoryName) == 0: #Si l'on trouve un dossier dont le nom contient "Usb_Solo_Mapper", longueur = 15
       preexistingDirectory = 1
       if len(dossier) == 16: #"Usb_Solo_Mapper1" a "Usb_Solo_Mapper9"
        j = int(dossier[15])      
        if j > k:
         k = j
        
       if len(dossier) == 17: #"Usb_Solo_Mapper10" a "Usb_Solo_Mapper99"
        j = int(dossier[15:17])
        if j > k:
         k = j   

    if preexistingDirectory == 1:
     k = k+1
     self.CameraPictureFullPath = self.CameraPicturePath + '/' +  self.CameraPictureDirectoryName + str(k)
     os.makedirs(self.CameraPictureFullPath)

    else : #Si l'on a trouve aucun dossier dont le nom commence par "Usb_Solo_Mapper", on en cree un 1er   
     self.CameraPictureFullPath = self.CameraPicturePath + '/' + self.CameraPictureDirectoryName
     os.makedirs(self.CameraPictureFullPath)


    #download the pictures from the QX1 to the raspberry Pi
    i = 0  

    #On depile les listes
    while i < nbPhotos:  
     print 'Chemin : ',self.CameraPictureFullPath + '/' + self.picturenameList[i]
     urllib.urlretrieve(self.picturefilestringList[i],self.CameraPictureFullPath + '/' + self.picturenameList[i])
     size = os.path.getsize(self.CameraPictureFullPath + '/' + self.picturenameList[i])
     print'size : ',size
     ExifWriter.write_gps(self.CameraPictureFullPath + '/' + self.picturenameList[i],self.latList[i], self.longList[i], self.altitudeList[i])
     i+=1

  #On vide les listes
  del self.picturefilestringList[:]
  del self.picturenameList[:]
  del self.latList[:]
  del self.longList[:]
  del self.altitudeList[:]

  return nbPhotos
  
  
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

  reLaunchLiveView = True  

  while reLaunchLiveView: 
   if FlagSystem.QX1IsRunning: 
    try:   
     print "Starting " + self.name
     print self.api.startLiveview()
     # Video is streamed with omxplayer
     print "Launching omxplayer"
     
     retcode = subprocess.call("omxplayer" + " --live -o hdmi http://"+ self.CameraIP + ":8080/liveview/liveviewstream" , shell=True)     
     if retcode < 0:
      print "Omxplayer was terminated by signal"
      logging.debug('Omxplayer was terminated by signal')
      reLaunchLiveView = False
     else:
      print "Omxplayer returned"

      FlagSystem.QX1IsRunning = False
      proc3 = subprocess.Popen("omxplayer" + " -o hdmi videos/connexionLost.mp4", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)   
      time.sleep(2)#On s'assure que la connexion est bien perdue
      #proc3.wait() 
      logging.debug('QX1 connexion lost!')
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
      proc3.kill()
  

      FlagSystem.QX1IsRunning = True
    except OSError as e: # Si echec de connexion avec le QX1
     print >>sys.stderr, "Omxplayer Execution failed:", e
     logging.debug('Omxplayer Execution failed:')
     FlagSystem.QX1IsRunning = False
     proc4 = subprocess.Popen("omxplayer" + " -o hdmi videos/connexionLost.mp4", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
    print "Exiting " + self.name  
   time.sleep(2) #on attend un peu...
 


class TemplateError(Exception):
 def __init__(self, value):
  self.value = value
 def __str__(self):
  return repr(self.value)
