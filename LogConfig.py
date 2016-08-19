"""Fichier de parametrage du log"""

import logging
from logging import FileHandler, StreamHandler
from logging.handlers import RotatingFileHandler


class LogSystem:

  def __init__(self,loggerName,logFileName,doConsoleLogging):
	#Formatage log 
	default_formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: '+loggerName+' :: %(message)s')
	console_formatter = logging.Formatter('%(levelname)s :: %(message)s')

	self.mainLogger = logging.getLogger('logger.'+logFileName+'') #on nomme le logger
	self.mainLogger.setLevel(logging.DEBUG) #on met le niveau du logger sur DEBUG, comme ca il ecrit tout

	#Log vers la console
	if doConsoleLogging:
	 console_handler = logging.StreamHandler()
	 console_handler.setLevel(logging.DEBUG)
	 console_handler.setFormatter(console_formatter)
	 self.mainLogger.addHandler(console_handler)

	# creation d'un handler qui va rediriger une ecriture du log vers
	# un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
	file_handler = RotatingFileHandler('/mnt/Usb-Solo-Mapper/Logs/'+logFileName+'.log', 'a', 1000000, 1)
	# on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
	# cree precedement et on ajoute ce handler au logger
	file_handler.setLevel(logging.DEBUG)
	file_handler.setFormatter(default_formatter)
	self.mainLogger.addHandler(file_handler)





  def getGlobalLogger(self):
  	return self.mainLogger