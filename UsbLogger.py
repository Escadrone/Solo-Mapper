
"""Thread charge de logger regulierement les etats des ports USB du Raspi """


from threading import Thread, RLock
import subprocess
import os
import time
import logging

verrou = RLock()

class UsbLoggerThread(Thread):
   
    goOn = True
  
    def __init__(self,globalLogger):
        Thread.__init__(self)
        self.logger = globalLogger

 

    def run(self):         
       #Every 10s, we check prospective USB-disconnect messages in kern.log            
        while self.goOn:
         with verrou:            
          try:
            checkProcess = subprocess.Popen("sudo tail -n 5 /var/log/kern.log | grep disconnect >> /mnt/Usb-Solo-Mapper/Logs/usbCheck.log", stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)   
            checkProcess.wait()
            usb_file = open("/mnt/Usb-Solo-Mapper/Logs/usbCheck.log", "a")
            usb_file.close()
          except Exception as e:
            self.logger.error('USB check process failed : %s',e)        
          finally:     
            time.sleep(10)




    def stop(self):
        #Method to stop the thread
        self.goOn = False

