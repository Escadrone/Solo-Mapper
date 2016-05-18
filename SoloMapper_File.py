import piexif

#Class writing given picture exif
class ExifWriter:

 #write gps coordinates into the given picture exif
 @staticmethod
 def write_gps(filename, lat, long, altitude): #lat and long are decimals
  gps = {} #create array

  #Altitude
  if altitude<0:
   gps[piexif.GPSIFD.GPSAltitudeRef] = 1; #Below see level
  else:
   gps[piexif.GPSIFD.GPSAltitudeRef] = 0; #Above see level
  gps[piexif.GPSIFD.GPSAltitude]= (int(abs(altitude)*100),100)
  
  #Latitude
  if lat<0:
   gps[piexif.GPSIFD.GPSLatitudeRef] = "S"
  else:
   gps[piexif.GPSIFD.GPSLatitudeRef] = "N"
   
  latd,latm,lats = ExifWriter._decdeg2dms(lat)
  gps[piexif.GPSIFD.GPSLatitude] = [(latd,1),(latm,1),(lats,100)];
  
  #Longitude
  if long<0:
   gps[piexif.GPSIFD.GPSLongitudeRef] = "W"
  else:
   gps[piexif.GPSIFD.GPSLongitudeRef] = "E"
  
  longd,longm,longs = ExifWriter._decdeg2dms(long)
  gps[piexif.GPSIFD.GPSLongitude] = [(longd,1),(longm,1),(longs,100)];

  exifdict =  piexif.load(filename)
  exifdict["GPS"] = gps
  
  exif_bytes = piexif.dump(exifdict)
  piexif.insert(exif_bytes, filename)
  exifdict =  piexif.load(filename)
 
 #method converting decimal format to DMS
 @staticmethod
 def _decdeg2dms(dd):
  dd = abs(dd)
  minutes,seconds = divmod(dd*3600,60)
  degrees,minutes = divmod(minutes,60)
  return (degrees,minutes,seconds)
   
 
