from dronekit import Vehicle
"""
# Classe de configuration, utilise le protocole MavLink

# Voir les parametres configurables : "http://mavlink.org/messages/common#PARAM_SET" et
# "http://python.dronekit.io/guide/copter/guided_mode.html#guided-mode-how-to-send-commands"
"""

class MavConfig:

 droneSolo = 0

 def __init__(self,vehicle):
  self.droneSolo = vehicle

 
 # Configuration des messages envoyes depuis le Pixhawk vers le RasPi
 def ConfigureStreamMessage(self):
  msg = self.droneSolo.message_factory.request_data_stream_encode(
  	0,
  	0,
  	1,
  	0,0)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)


  msg = self.droneSolo.message_factory.request_data_stream_encode(
  	0,
  	0,
  	2,
  	0,0)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)

  msg = self.droneSolo.message_factory.request_data_stream_encode(
  	0,
  	0,
  	4,
  	0,0)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)


  msg = self.droneSolo.message_factory.request_data_stream_encode(
  	0,
  	0,
  	11,
  	0,0)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)

  msg = self.droneSolo.message_factory.request_data_stream_encode(
  	0,
  	0,
  	12,
  	0,0)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)


  msg = self.droneSolo.message_factory.request_data_stream_encode(
    0,
    0,
    3,
    20000,1)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)


  msg = self.droneSolo.message_factory.request_data_stream_encode(
  	0,
  	0,
  	10,
  	1000,1)

  #send command to vehicle
  self.droneSolo.send_mavlink(msg)





