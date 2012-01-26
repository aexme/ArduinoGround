#!/usr/bin/python
# coding: utf-8
import socket, os, re
import sys
import serial
import time
from datetime import datetime
import datetime
from mpd import (MPDClient, CommandError)
from socket import error as SocketError
import SocketServer
import threading 
import thread
import ConfigParser
import urllib
import scipy
import numpy
import scipy.fftpack

HOST = '192.168.200.18'
PORT = '6600'
PASSWORD = False
##
CON_ID = {'host':HOST, 'port':PORT}
iRadioURL = {1:'',2:'',3:'',4:'',5:'',6:''}

iRadio_cfg = '/root/iradio.cfg'
alarm_cfg = '/root/alarm.cfg'
htdocs = "/root/htdocs/"
#iRadio_cfg = '/home/aex/sketchbook/iradio.cfg'
#alarm_cfg = '/home/aex/sketchbook/alarm.cfg'
#htdocs = "/home/aex/sketchbook/htdocs/"
#ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
#bufferSize=2**14
bufferSize=2**9
PCMData = []

# ADJUST THIS TO CHANGE SPEED/SIZE OF FFT
sampleRate=44100

chunks=[]
ffts=[]

class MyArduino():
    def __init__(self):
	locations=['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
	    '/dev/ttyS0','/dev/ttyS1','/dev/ttyS2','/dev/ttyS3']
	self.lock=thread.allocate_lock()

	for device in locations:
	  try:
	    self.arduino = serial.Serial(device, 57600)
	    self.arduino.timeout = 0 
	    print "Connected on",device
	    break
	  except:
	    print "Failed to connect on",device
	
    def write(self, text):
      self.lock.acquire() 
      self.arduino.write(text)
      self.lock.release()
      
    def read(self):
      data = self.arduino.read(9999)

      if len(data) > 7:
        return data
      else: return ''

      return 

class IRadio():
    
    def __init__(self):
	self.iradioList = {'1' : ' ', '2' : ' ', '3' : ' ', '4' : ' ', '5' : ' ', '6':' '}
	self.loadList()
	
    def loadList(self):
	iradioFile = open(iRadio_cfg, 'r')

	for line in iradioFile:
	    timerLine = line.split(';')
	    if (line!=''):		
		self.iradioList[timerLine[0]] = timerLine[1]

	iradioFile.close()
	
    def updateTimerList(self):
	self.loadList()
    
    def getIRadio(self, name=''):	
	if(name == ''): 
	    return self.iradioList
	else:	
	    return self.iradioList[name]
	    
    def addIRadio(self,_id, pls):	
	self.iradioList[_id] = pls
	
    def writeConfig(self):
	iradioFile = open(iRadio_cfg, 'w')
	for _id, url in self.iradioList.iteritems():
	    if (url == ' ' or url == "\n" or url == '' ):
		print "not again!"
	    else: iradioFile.write(_id + ";" + url + '\n')
    
    def deleteRadio(self, _id):
	del self.iradioList[_id]
	
    def parsePLS(self, url):
      
      tmp = url.split('.')
      last = len(tmp)-1
      opener = urllib.FancyURLopener({})
      f = opener.open(url)
      i=1
      items = {}
      
      if tmp[last].lower().rstrip() == 'pls':

	  config = ConfigParser.RawConfigParser()
	  config.readfp(f)
	  numberOfItems = int(config.get('playlist', 'NumberOfEntries'))
	  
	  while i <= numberOfItems:
	      items[i] = config.get('playlist', 'File' + str(i))
	      i +=1    
	  
      elif tmp[last].lower().rstrip() == 'm3u':  
	  while True:
	    line = f.readline()
	    lineSplit = line.split(':')
	    if (lineSplit[0].lower().rstrip() == 'http'):
		if line!=' ': items[i] = line.rstrip()
		i+=1
	    if line=='':
		break
      else: items[1] = url.rstrip()
		
      f.close()
      return items
	  
	
class MyTimer():
  
    def __init__(self):
	self.timerList = {}
	self.loadTimer()
	
    def updateTimerList(self):
	self.loadTimer()
	
    def loadTimer(self):
	timerFile = open(alarm_cfg, 'r')

	for line in timerFile:
	    timerLine = line.split(';')
	    if (line!=''):
		self.timerList[timerLine[0]] = line
		
	timerFile.close()
	
    def getTimer(self, name=''):
	if(name == ''): 
	    return self.timerList
	else:	
	    return self.timerList[name]

    def addTimer(self, timer):
	timerSplit = timer.split(';')
	self.timerList[timerSplit[0]] = timer
	
    def writeConfig(self):
	timerFile = open(alarm_cfg, 'w')
	for name, line in self.timerList.iteritems():
	    if (line == ' ' or line == "\n" or line == '' ):
		print "not again!"
	    else: timerFile.write(line + '\n')
    
    def deleteTimer(self, timer):
	del self.timerList[timer]
	
    def getdecodeRepeatCode(self, repeat):
	
	repeatDays = {'Mo': 0, 'Di': 0, 'Mi': 0, 'Do': 0, 'Fr': 0, 'Sa': 0, 'So': 0}
	
	if(repeat - 64 >= 0):
	    repeatDays['So'] = 1
	    repeat -=64  

	if(repeat-32 >= 0):
	    repeatDays['Sa'] = 1
	    repeat -=32
	    
	if(repeat-16 >= 0):
	    repeatDays['Fr'] = 1
	    repeat -=16
	if(repeat-8 >= 0):
	    repeatDays['Do'] = 1
	    repeat -=8
	if(repeat-4 >= 0):
	    repeatDays['Mi'] = 1
	    repeat -=4
	if(repeat-2 >= 0):
	    repeatDays['Di'] = 1
	    repeat -=2
	if(repeat-1 >= 0):
	    repeatDays['Mo'] = 1
	    repeat -=1
	    
	return repeatDays
	
    def flipTimer(self, timer):
	myTimer = self.timerList[timer]
	myTimerSplit = myTimer.split(';')

	if (myTimerSplit[3] == '0' ): 
	    myTimerSplit[3] = '1'	    
	else:  
	    myTimerSplit[3] = '0'
	    
	self.timerList[timer] = ';'.join(myTimerSplit)

class MyMPDClient():
    def __init__(self):
	## MPD object instance
	self.client = MPDClient()
	if mpdConnect(self.client, CON_ID):
	    print 'Got connected!'
	else:
	    print 'fail to connect MPD server.'
	    sys.exit(1)

	# Auth if password is set non False
	if PASSWORD:
	    if mpdAuth(client, PASSWORD):
		print 'Pass auth!'
	    else:
		print 'Error trying to pass auth.'
		self.client.disconnect()
		sys.exit(2)
	
    def getCurrentsong(self):
	return self.client.currentsong()
	
    def pause(self):
	return self.client.pause()
    def previous(self):
	return self.client.previous()
    def _next(self):
	return self.client.next()
    def stop(self):
	return self.client.stop()

    def play(self):
	return self.client.play()

    def getStatus(self):
	return self.client.status()
    
    def add(self, item):
	self.client.add(item)
    
    def playlist(self):
	return self.client.playlist()
      
    def getPlaylistid(self):
	return self.client.playlistid()
	
    def playId(self,_id):
	self.client.playid(_id)
    
    def getItemIdInPLaylist(self, item):
      
	playlist =  self.getPlaylistid()
	for pos in playlist:
	      if pos['file'] == item:
		  return pos['id']
	return '-1'
    
class MyRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
      
	responsePrefix = "HTTP/1.0 200 OK\r\n" #Server:Affixserver/1.0\r\n"
	self.arduino = self.server.arduino
	self.mpdclient = self.server.mympdClient
	self.lock = self.server.lock
	self.timer = self.server.timer
	self.iradio = self.server.iradio
	
	data = self.request.recv(100)
	self.cpuLoad = [0,0,0,0]
	
	re1='(GET)'
	re2='.*?'
	re3='((?:\\/[\\w\\.\\-]+)+)'
	re4='.*?'
	re5='((?:[a-z][a-z]+))'
	rg = re.compile(re1+re2+re3+re4+re5,re.IGNORECASE|re.DOTALL)
	m = rg.search(data)
	
	splitURL = data.split(' ')
	command = splitURL[1].split('/')
	self.unixpath1=''
	if m:
	    word1=m.group(1)
	    self.unixpath1=m.group(2)
	    word2=m.group(3)
	    print "("+word1+")"+"("+self.unixpath1+")"+"("+word2+")"+"\n"
	    if self.unixpath1 == "/1.1":
		self.unixpath1 = "/index.html"      
	  
	if command[1] == "": command[1] = "index.html"	 

	if command[1] == "cmd":
	    if len(command)>2: parameter = command[2].split('&')
	    print "+ Attempting to send cmd "+ self.unixpath1 +"\n"

	    if len(parameter) > 4:
		try:
		    self.arduino.write(parameter[0]+parameter[1]+parameter[2]+parameter[3]+parameter[4]+'\0')
		    self.request.send("cmd sent")
		    time.sleep(0.01)		    
		except:
		    time.sleep(0)
		    
	elif command[1] == "alarm":
	    if len(command)>2: parameter = command[2].split('&')
	    if(parameter[0] == "set"):
		self.lock.acquire() 
		self.timer.addTimer(parameter[1] + ';' + parameter[2] + ';' + parameter[3] + ';' + parameter[4])
		self.timer.writeConfig()
		self.lock.release()
		s = "OK"
	    
	    elif(parameter[0] == "rm"):
		self.lock.acquire() 
		self.timer.deleteTimer(parameter[1])
		self.lock.release()
		s = "OK"
	    elif(parameter[0] == "flip"):
		self.lock.acquire() 
		self.timer.flipTimer(parameter[1])
		self.timer.writeConfig()
		self.lock.release()
		s= "OK"
		
	    elif(parameter[0] == "get"):
		self.timerList = self.timer.getTimer()
		s=' '
		
		for name, line in self.timerList.iteritems():
		    if (line=="" or line == "\n" or line  == " "):
		      print "error"
		    else:
			timerSplit = line.split(';')
			
			hrTime = time.strftime("%H:%M", time.localtime(int(timerSplit[1])))
			timerEnabled = ''

			if(timerSplit[3].rstrip() == '1'):
			    timerEnabled = 'checked'		
			hrRepeat = ''

			repeat = int(timerSplit[2])
			
			if (repeat == 127): hrRepeat = 'Everyday'
			elif (repeat == 0): hrRepeat = 'once'
			else:		
			    repeatDays = self.timer.getdecodeRepeatCode(repeat)
			    for tag, enabled in repeatDays.iteritems():
				if(enabled==1): hrRepeat += tag + ','
				
			s += timerSplit[0] + ": " + hrTime + " " + hrRepeat
			s += ' <input type="checkbox" name="timerEnabled" value="1" '
			s += timerEnabled + " onchange=flipTimer('" + timerSplit[0] + "')"
			s += "><button onClick=rmTimer('" + timerSplit[0] + "')>delete</button><br>"

	    self.request.send(s)
		
	elif command[1] == "mpd":
	    
	    if len(command)>2: parameter = command[2].split('&')
	    
	    if(parameter[0]=="currentsong"):
		self.lock.acquire() 
		mpd_currentSong = self.mpdclient.getCurrentsong()
		time.sleep(0.001)
		self.lock.release()
		
		name = "" 
		try:	    
		    name = mpd_currentSong['artist']
		except:
		    print "Failed to connect on"
		try:
		    name = mpd_currentSong['name']		      
		except:
		    print "Failed to connect on"
		    		    
		if(parameter[1]=='0'):
		    s = '<div id ="title">' + mpd_currentSong['title'] + '</div></br><div id = "name">' + name + "</div>"
		    print "+ Attempting to send mpdStats " + s +"\n"    
		elif(parameter[1]=="1"):
		    s = name
		    print "+ Attempting to send mpdStats "+ s +"\n"
		    
		elif(parameter[1]=="2"):
		    s = mpd_currentSong['title']
		    print "+ Attempting to send mpdStats "+ s +"\n"
	    
	    elif(parameter[0]=="pause"):
		self.mpdclient.pause();
		s='OK'
	    elif(parameter[0]=="previous"):
		self.mpdclient.previous();
		s='OK'
  	    elif(parameter[0]=="next"):
		self.mpdclient._next();
		s='OK'
	    elif(parameter[0]=="stop"):
		self.mpdclient.stop();
		s='OK'
	    elif(parameter[0]=="play"):
		self.mpdclient.play();
		s='OK'
	    elif(parameter[0]=="iRadio"):
		print "iradio"
		print parameter
		
		if parameter[1] == 'set':
		    url = urllib.unquote(splitURL[1].split('&')[3])
		    self.iradio.addIRadio(parameter[2], url)
		    self.iradio.writeConfig()
		    s='OK'
		elif parameter[1]=='play':		  
		    playIradio(self.iradio, self.mpdclient, parameter[2])
		    s='OK'
		elif parameter[1]=='get':  
		    
		    self.iradioList = self.iradio.getIRadio()
		    s=''
		    for _id, url in self.iradioList.iteritems():
			  
			  if (_id == ' ' or url == "\n"):
			      print "not again!"
			  else: 			      
			      s += 'iRadio ' + _id + ' <input name="iradio' + _id
			      s += '" type="text" size="30" value="' + url + '">'
			      s += '<input type="button" onClick="playiRadio(' + _id + '); return false;" value="play" /><br>'
		else: s='NotOK'
		
	    elif(parameter[0]=="time"):
		if(parameter[1] == "0"):

		    self.lock.acquire()
		    self.mpd_status = self.mpdclient.getStatus()
		    time.sleep(0.001)
		    self.lock.release()
		    
		    track_time = self.mpd_status['time'].split(':')
		    
		    sec2 = int(track_time[1]) % 60
		    mm2 = (int(track_time[1]) - sec2) / 60
		    sec1 = int(track_time[0]) % 60
		    mm1 = (int(track_time[0]) - sec1) / 60

		    s = "%.2d" % mm1 + ":" + "%.2d" % sec1 + " / " + "%.2d" % mm2 + ":" + "%.2d" % sec2
		    print "+ Attempting to send mpdStats "+ s +"\n"
		    
		elif(parameter[1]=="1"): 
		    s = mpd_status['time']		      
		    print "+ Attempting to send mpdStats "+ s +"\n"
		
		elif(parameter[1]=="2"):
		    s = mpd_status['elapsed']
		    print "+ Attempting to send mpdStats "+ s +"\n"
		  
	    self.request.send(s)
	
	elif command[1] == "sys":	  
	    if len(command)>2: parameter = command[2].split('&')
	    if parameter[0] == "cpuLoad":
		self.cpuLoad = deltaTime(1)
	    	    
		cpuPct = 100 - (self.cpuLoad[len(self.cpuLoad) - 1] * 100.00 / sum(self.cpuLoad))
		s = "CPU Load: " +  str('%.2f' %cpuPct) +"%"
	    elif parameter[0] == "meminfo":
		meminfo = getMeminfo()
		s = 'Free Memory: ' + meminfo[1] + ' / ' + meminfo[0] 
	    
	    self.request.send(s)
	
	elif os.path.exists(htdocs + command[1]):
	      print "+ Attempting to serve "+ self.unixpath1 +"\n"
	      file = open(htdocs  + command[1], "r")
	      
	      self.request.send( responsePrefix )
	      self.request.send("Content-Type: text/html\r\n")
	      # send file in 1024 byte chunks
	      while 1:
		  data = file.read(1024)
		  if not data:
		      break
		  time.sleep(0.01)
		  self.request.sendall( data )		
	else:
		print "+ File was not found!\n"
		self.request.send("<html><head><title>404</title></head><body><h1>404 File not Found</h1>The file you requested was not found on the server</body></html>")
	self.request.close()

    
class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        self.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)	

class myAlarm(threading.Thread):   #deine Threadklasse
   def __init__(self): #musst du initialisieren
      threading.Thread.__init__ (self)  #hier reicht die Methode der Threadklasse
 
   def run(self):             # die Methode, die beim Aufruf von start abgearbeitet wird

      arduino = MyArduino()
      arduino.write('EC310')
      time.sleep(60)
      arduino.write('D1000')
      time.sleep(1)
      arduino.write('EC300')
      
      exit()
    
class readFIFO(threading.Thread):   #deine Threadklasse
   def __init__(self, fp): #musst du initialisieren
      self.lock=thread.allocate_lock()
      threading.Thread.__init__ (self)  #hier reicht die Methode der Threadklasse
      self.fp=fp
      self.PCMData = []
      self.enabled = True
      
   def run(self):             # die Methode, die beim Aufruf von start abgearbeitet wird
      #fp = open('/tmp/mpd.fifo',"rb")
      while self.enabled==True:
	  self.lock.acquire() 
	  self.PCMData = numpy.fromfile(self.fp, dtype='h', count=bufferSize*2)
	  self.lock.release()
	  time.sleep(0.005)
      exit()
      
      
def main():
      global w,fftx,ffty
      print "STARTING!"
      
      arduino = MyArduino()
      mympdClient = MyMPDClient()
      lock=thread.allocate_lock()
      timer = MyTimer()
      iradio = IRadio()
      
      myServer = TCPServer(("", 8001), MyRequestHandler)
      myServer_thread = threading.Thread(target=myServer.serve_forever)
      myServer_thread.setDaemon(True)
      myServer_thread.start()
      myServer.arduino = arduino
      myServer.mympdClient = mympdClient
      myServer.lock = lock
      myServer.timer = timer
      myServer.iradio = iradio
      
      weekdayArray = ['Mo','Di','Mi','Do','Fr','Sa','So']
      myAlarmTime = []
      counterAlarm = 0
      vfdMessagecnt = 0
      vfdTimer = 0
      loadingsymbol = 32
      vfdON = True
      
      defWert = 4
      j=0
      b=[]
      m=[]
      h=[]
      values_nummber=30
      values_nummber_div3 = 10
      while j<values_nummber:
	   b.append(defWert)
	   m.append(defWert)
	   h.append(defWert)
	   j+=1
      
      max_value_b=5
      min_value_b=1
      max_value_m=5
      min_value_m=1
      max_value_h=5
      min_value_h=1
      max_value=5
      min_value=1
      
      value_cnt=0
      i=2
      
      fp = open('/tmp/mpd.fifo',"rb")
      ma_readFIFOThread = readFIFO(fp)
      
      ma_AlarmThread = myAlarm()
      ma_readFIFOThread.start()
      
      # VFD leeren
      cnt = 0
      while cnt<41:
	  arduino.write('C' + chr(cnt) + chr(0) +'00')  
	  cnt = cnt + 1                              
      try:
	  
	while True:
	
	    time.sleep(0.01)
	    if vfdTimer>10: vfdTimer=0
	    
	    if vfdTimer == 0 and vfdON == True:
		mpd_currentSong = mympdClient.getCurrentsong()
		s = "        "
		noartistname=0		       
		try:	    
		    s += mpd_currentSong['artist']
		    noartistname=1
		except:
		    pass
		try:
		    s += mpd_currentSong['name']		      
		    noartistname=1
		except:
		    pass
		if noartistname == 0: s+='NO Artist'
		try:	    
		    s += ' - ' + mpd_currentSong['title']
		except:
		    s+=' NO TITLE'
		 
		if vfdMessagecnt > len(s)-8:
		      s += ' '
		if vfdMessagecnt > len(s)-3:
		      vfdMessagecnt = 0
		
		writeVfdMessage(arduino, s[vfdMessagecnt:vfdMessagecnt+8])
		
		vfdMessagecnt +=1    
		
		arduino.write('C' + chr(10) + chr(4) +'00') # classic stereo sign
		arduino.write('C' + chr(39) + chr(1) +'00') # CD sign
		arduino.write('C' + chr(9) + chr(loadingsymbol+1) +'00') # circle sign
		if loadingsymbol < 128:
		    loadingsymbol  *=2 
		else: loadingsymbol = 32
		
	    vfdTimer+=1
	    
	    arduinoMessage = arduino.read().split(';')

	    if(arduinoMessage[0] == "RF"):
		time.sleep(0.2)
		if(arduinoMessage[1] == "118772"):
		    writeVfdMessage(arduino, ' PAUSE  ')
		    mympdClient.pause()
		elif(arduinoMessage[1] == "118770"):
		    writeVfdMessage(arduino, '  PLAY  ')
		    mympdClient.play()
		elif(arduinoMessage[1] == "118610"):
		    writeVfdMessage(arduino, 'RADIO 1 ')
		    playIradio(iradio, mympdClient, '1')		    
		elif(arduinoMessage[1] == "118608"):
		    playIradio(iradio, mympdClient, '2')
		    writeVfdMessage(arduino, 'RADIO 2 ')
		elif(arduinoMessage[1] == "122984"):
		    writeVfdMessage(arduino, 'RADIO 3 ')
		    playIradio(iradio, mympdClient, '3')		    
		elif(arduinoMessage[1] == "122982"):
		    writeVfdMessage(arduino, 'RADIO 4 ')
		    playIradio(iradio, mympdClient, '4')
		elif(arduinoMessage[1] == "120068"):
		    writeVfdMessage(arduino, 'RADIO 5 ')
		    playIradio(iradio, mympdClient, '5')	    
		elif(arduinoMessage[1] == "120066"):
		    writeVfdMessage(arduino, 'RADIO 6 ')
		    playIradio(iradio, mympdClient, '6')
		elif(arduinoMessage[1] == "123146"):
		    if not vfdON:	writeVfdMessage(arduino, ' VFD ON ')
		    else: 		
			writeVfdMessage(arduino, 'VFD OFF ')
			cnt = 0
			while cnt<41:
			    arduino.write('C' + chr(cnt) + chr(0) +'00')  
			    cnt = cnt + 1
		    vfdON = not vfdON
		elif(arduinoMessage[1] == "123144"):
		    writeVfdMessage(arduino, '  STOP  ')
		    mympdClient.stop()
		elif(arduinoMessage[1] == "120230"):
		    writeVfdMessage(arduino, '  PREV  ')
		    mympdClient.previous()
		elif(arduinoMessage[1] == "120228"):
		    mympdClient._next()
		    writeVfdMessage(arduino, '  NEXT  ')    
		elif(arduinoMessage[1] == "122498"):
		    print 'got RF sw on'
		    time.sleep(0.1)
		    arduino.write('D1000')
		    time.sleep(0.1)
		    writeVfdMessage(arduino, ' SW ON  ')
		elif(arduinoMessage[1] == "122496"):
		    print 'got RF sw off'
		    time.sleep(0.1)
		    arduino.write('D1100') 
		    time.sleep(0.1)
		    writeVfdMessage(arduino, ' SW OFF ')
		elif(arduinoMessage[1] == "123956"):
		    print 'got RF rfsw on'
		    time.sleep(0.1)
		    arduino.write('EC110')
		    arduino.write('EC310')
		    time.sleep(0.1)
		    writeVfdMessage(arduino, 'RF SW ON')
		elif(arduinoMessage[1] == "123954"):
		    print 'got RF rfsw off'
		    time.sleep(0.1)
		    arduino.write('EC100')
		    time.sleep(0.01)
		    arduino.write('EC300')
		    time.sleep(0.1)
		    writeVfdMessage(arduino, 'RFSW OFF')
		time.sleep(0.5)
	    elif arduinoMessage[0] == "VFDkey":
		time.sleep(0.2)
		if(arduinoMessage[1] == "TA"):
		    writeVfdMessage(arduino, '  PLAY  ')
		    mympdClient.play()
		elif(arduinoMessage[1] == "PTY"):
		    writeVfdMessage(arduino, ' PAUSE  ')
		    mympdClient.pause()
		elif(arduinoMessage[1] == "AF"):
		    print "got vfd keyAF"
		elif(arduinoMessage[1] == "Power"):
		    print "got vfd keyPower"
		elif(arduinoMessage[1] == "DSP"):
		    if not vfdON:	writeVfdMessage(arduino, ' VFD ON ')
		    else:
			writeVfdMessage(arduino, 'VFD OFF ')		      	    
			# VFD leeren
			cnt = 0
			while cnt<41:
			    arduino.write('C' + chr(cnt) + chr(0) +'00')  
			    cnt = cnt + 1
		    vfdON = not vfdON
		      
		elif(arduinoMessage[1] == "MODE"):
		    print "got vfd keyMODE"
		elif(arduinoMessage[1] == "EQ"):
		    print "got vfd keyEQ"
		elif(arduinoMessage[1] >= "1" and arduinoMessage[1] <= "6"):
		    playIradio(iradio, mympdClient, arduinoMessage[1])
		    writeVfdMessage(arduino, 'RADIO ' + arduinoMessage[1] + ' ')
		elif(arduinoMessage[1] == "8"):
		    mympdClient.previous()
		    writeVfdMessage(arduino, '  PREV  ')
		elif(arduinoMessage[1] == "BAND"):
		    mympdClient.stop()
		    writeVfdMessage(arduino, '  STOP  ')
		elif(arduinoMessage[1] == "9"):
		    mympdClient._next()
		    writeVfdMessage(arduino, '  NEXT  ')  
		time.sleep(0.5)
		
	    if(counterAlarm > 4500):	counterAlarm=0
	    else: 			counterAlarm += 1
	    
	    if(counterAlarm == 0):
		my_timerList = timer.getTimer()
		
		for name, mytimer in my_timerList.iteritems():
		      if (mytimer=="" or mytimer == "\n" or mytimer  == " "):
			  pass
		      else:
			  my_TimerSplit = mytimer.split(';')
			  if(my_TimerSplit[3].rstrip() == '1'):
			      today = datetime.date.today()

			      weekdayNowInt = today.weekday()
			      weekdayNowstr = weekdayArray[weekdayNowInt]
			      repeatDays = timer.getdecodeRepeatCode(int(my_TimerSplit[2]))
			      if(repeatDays[weekdayNowstr] == 1):
				  myAlarmTime.append(my_TimerSplit[1])
			      else:
				  once = 1
				  for theweekday, en in repeatDays:
				      if (en==1): once = 0
				  if (once == 1): 
				      myAlarmTime.append(my_TimerSplit[1])
				      timer.flipTimer(my_TimerSplit[0])
			      
		for alarmTime in myAlarmTime:
		      
		      if  (time.strftime("%H:%M", time.localtime(int(alarmTime)-300)) == time.strftime("%H:%M", time.localtime())):		            			  
			  ma_AlarmThread.start()
			  print 'ALARM'
			  
	    if vfdON == True:
		[b[i],m[i],h[i]] = getFFT(ma_readFIFOThread.PCMData)
		#print [b[i],m[i],h[i]]
		
		if i==values_nummber_div3:
		    max_value = max( [ numpy.max( b[ 1:len(b)-1] ), numpy.max( m[1: len(m)-1] ), numpy.max( h[1: len(h)-1 ] ) ] )
		
		if i==values_nummber_div3*2:
		    min_value = min( [ numpy.min( b[ 1:len(b)-1] ), numpy.min( m[1: len(m)-1] ), numpy.min( h[1: len(h)-1 ] ) ] )
				
		if i>values_nummber-2:
		    b[0] = b[i]
		    #b[1] = b[i]
		    b[len(b)-1]=b[i-1]
		    m[0] = m[i]
		    #m[1] = m[i]
		    m[len(m)-1]=m[i-1]
		    h[0] = h[i]
		    #h[1] = h[i]
		    h[len(h)-1]=h[i-1]
		    
		    i = 1
		    
		b[i] = scipy.average(b[i-1:i+1])
		bass = encodeFFT(b[i], max_value, min_value)
		m[i] = scipy.average(m[i-1:i+1])
		mid  = encodeFFT(m[i], max_value, min_value)
		h[i] = scipy.average(h[i-1:i+1])
		hig  = encodeFFT(h[i], max_value, min_value)
		
		#print str(b[i]) + " "+  str(m[i]) + " " + str(h[i]) 
		arduino.write('C' + chr(0) + chr(hig) +'00')  
		arduino.write('C' + chr(3) + chr(mid) +'00')  
		arduino.write('C' + chr(6) + chr(bass) +'00')
		
		i+=1
		value_cnt +=1
      except (KeyboardInterrupt, SystemExit):
	  myServer.shutdown()
	  fp.close()
	  ma_readFIFOThread.enabled=False
	  ma_readFIFOThread.join()
	  sys.exit()

##  Channell C  ##

#E10	118122
#E11	118124
#E20	122496
#E21	122498
#E30	119580
#E31	119582
#E40	123954
#E41	123956
# MPDRadio
#E50	118608
#E51	118610
#E60	122982
#E61	122984
#E70	120066
#E71	120068
#E80	124440
#E81	124442

#E90	118284
#E91	118286
#EA0	122658
#EA1	122660
#EB0	119742
#EB1	119740
#EC0	124116
#EC1	124118
# MPD
#ED0	118770
#ED1	118772
#EE0	123144
#EE1	123146
#EF0	120228
#EF1	120230
#E00	124602
#E01	124604


def mpdConnect(client, con_id):
    """
    Simple wrapper to connect MPD .
    """
    try:
        client.connect(**con_id)
    except SocketError:
        return False
    return True
    
def writeVfdMessage(arduino, message):
    myEncodedMessage = encodeVFDMessage(message)
    for addr, bits in myEncodedMessage.iteritems():
	arduino.write('C' + chr(addr) + chr(bits) +'00')   

def playIradio(iradio, mympdClient, _id):
    
    url = iradio.getIRadio(_id)
    items = iradio.parsePLS(url)
    itemIdInPlaylist = mympdClient.getItemIdInPLaylist(items[1])
    if itemIdInPlaylist!='-1': mympdClient.playId(int(itemIdInPlaylist))
    else:
	  i=1
	  while i <= len(items):
	      mympdClient.add(items[i])
	      i+=1
	      
	  itemIdInPlaylist = mympdClient.getItemIdInPLaylist(items[1])
	  if itemIdInPlaylist!='-1': mympdClient.playId(int(itemIdInPlaylist))

def getFFT(PCMData):
        global chunks, bufferSize, fftx,ffty, w
        b=0
        m=0
        h=0
	ffty=numpy.fft.rfft(PCMData)
	fftx=numpy.fft.fftfreq(bufferSize*2, 1.0/sampleRate)
	fftx=fftx[0:len(fftx)/4]
	ffty=abs(ffty[0:len(ffty)/2])
	#ffty1=ffty[:len(ffty)/2]
	#ffty2=ffty[len(ffty)/2::]+2
	#ffty2=ffty2[::-1]
	#ffty=ffty1+ffty2
	#ffty=scipy.log(ffty)-2
	i=0
	while fftx[i]<120:
	    i+=1
	basspart = i
	while fftx[i]<1000:
	    i+=1
	midpart = i
	
	if basspart>1: b = numpy.max(ffty[1:basspart])
	else: b = 0

	if midpart>basspart: m = numpy.max(ffty[basspart:midpart])
	else: m = 0

	if len(ffty)>midpart: h = numpy.max(ffty[midpart:len(ffty)])
	else: h = 0
                
        #print '#### bass' + str(b) + '#### mid' + str(m) + '#### treble' + str(h)       
	return [b,m,h]

def encodeFFT(word, max_value, min_value):
	diff_value = max_value-min_value
	tmp = diff_value / 35
	wrt=0
	
	if word > (max_value - tmp):
	  wrt= 127
	elif word > (min_value + (33 * tmp)):
	  wrt= 63
	elif word > (min_value + (28 * tmp)):
	  wrt= 31
	elif word > (min_value + (24 * tmp)):
	  wrt= 15
	elif word > (min_value + (18 * tmp)):
	  wrt= 7
	elif word > (min_value + (10 * tmp)):
	    wrt= 3
	elif word >= min_value:
	    wrt= 1
	
	#print "wert " + str(word) + " max " + str(max_value) + " min " + str(min_value) + " tmp " + str(tmp) + " return " + str(wrt)	
	return wrt

def encodeVFDMessage(message):
    message = message.upper()
    letters14v1_1 = {}    
    letters14v1_2 = {}    
    letters14v1_1['A'] = 0b11100011
    letters14v1_2['A'] = 0b00001001    
    letters14v1_1['B'] = 0b01001011
    letters14v1_2['B'] = 0b00010001
    letters14v1_1['C'] = 0b00100001
    letters14v1_2['C'] = 0b00011000
    letters14v1_1['D'] = 0b00001011
    letters14v1_2['D'] = 0b00010001
    letters14v1_1['E'] = 0b10100001
    letters14v1_2['E'] = 0b00011000
    letters14v1_1['F'] = 0b10100001
    letters14v1_2['F'] = 0b00001000
    letters14v1_1['G'] = 0b01100001
    letters14v1_2['G'] = 0b00011001
    letters14v1_1['H'] = 0b11100010
    letters14v1_2['H'] = 0b00001001
    letters14v1_1['I'] = 0b00001001
    letters14v1_2['I'] = 0b00010000
    letters14v1_1['J'] = 0b00000010
    letters14v1_2['J'] = 0b00011001
    letters14v1_1['K'] = 0b10110000
    letters14v1_2['K'] = 0b00001010
    letters14v1_1['L'] = 0b00100000
    letters14v1_2['L'] = 0b00011000
    letters14v1_1['M'] = 0b00110110
    letters14v1_2['M'] = 0b00001001    
    letters14v1_1['N'] = 0b00100110
    letters14v1_2['N'] = 0b00001011
    letters14v1_1['O'] = 0b00100011
    letters14v1_2['O'] = 0b00011001
    letters14v1_1['P'] = 0b11100011
    letters14v1_2['P'] = 0b00001000
    letters14v1_1['Q'] = 0b00100011
    letters14v1_2['Q'] = 0b00011011
    letters14v1_1['R'] = 0b11100011
    letters14v1_2['R'] = 0b00001010
    letters14v1_1['S'] = 0b11100001
    letters14v1_2['S'] = 0b00010001
    letters14v1_1['T'] = 0b00001001
    letters14v1_2['T'] = 0b00000000
    letters14v1_1['U'] = 0b00100010
    letters14v1_2['U'] = 0b00011001
    letters14v1_1['V'] = 0b00110000
    letters14v1_2['V'] = 0b00001100
    letters14v1_1['W'] = 0b00100010
    letters14v1_2['W'] = 0b00001111
    letters14v1_1['X'] = 0b00010100
    letters14v1_2['X'] = 0b00000110
    letters14v1_1['Y'] = 0b00010100
    letters14v1_2['Y'] = 0b00000100
    letters14v1_1['Z'] = 0b00010001
    letters14v1_2['Z'] = 0b00010100
    letters14v1_1['0'] = 0b00110011
    letters14v1_2['0'] = 0b00011101
    letters14v1_1['1'] = 0b00010010
    letters14v1_2['1'] = 0b00000001
    letters14v1_1['2'] = 0b11000011
    letters14v1_2['2'] = 0b00011000
    letters14v1_1['3'] = 0b01000011
    letters14v1_2['3'] = 0b00010001
    letters14v1_1['4'] = 0b11100010
    letters14v1_2['4'] = 0b00000001
    letters14v1_1['5'] = 0b11100001
    letters14v1_2['5'] = 0b00010001
    letters14v1_1['6'] = 0b11100001
    letters14v1_2['6'] = 0b01011001
    letters14v1_1['7'] = 0b00010001
    letters14v1_2['7'] = 0b00000100
    letters14v1_1['8'] = 0b11100011
    letters14v1_2['8'] = 0b00011001
    letters14v1_1['9'] = 0b11100011
    letters14v1_2['9'] = 0b00010001
    letters14v1_1[':'] = 0b00001000
    letters14v1_2[':'] = 0b00000000
    letters14v1_1['-'] = 0b11000000
    letters14v1_2['-'] = 0b00000000
    letters14v1_1['/'] = 0b00010000
    letters14v1_2['/'] = 0b00000100
    letters14v1_1[' '] = 0b00000000
    letters14v1_2[' '] = 0b00000000    
    letters14v1_1['('] = 0b00010000
    letters14v1_2['('] = 0b00000010
    letters14v1_1[")"] = 0b00000100
    letters14v1_2[')'] = 0b00000100
    letters14v1_1["!"] = 0b00001000
    letters14v1_2['!'] = 0b00000000
    letters14v1_1["'"] = 0b00010000
    letters14v1_2["'"] = 0b00000000
    letters14v1_1["&"] = 0b11010101
    letters14v1_2["&"] = 0b00011001
    letters14v1_1[","] = 0b00000000
    letters14v1_2[","] = 0b00000100
    letters14v1_1["."] = 0b00000000
    letters14v1_2["."] = 0b00000100
    letters14v1_1["_"] = 0b00000000
    letters14v1_2["_"] = 0b00001000
    addr = [12,13,15,16,18,19,21,22,24,25,27,28,30,31,33,34]
    returnDict = {}
    
    if len(message)>8: lim=8
    else: lim=len(message)
    cnt = 0 
    addrcnt=0
    
    while cnt < lim:
	try:
	  returnDict[addr[addrcnt]] = letters14v1_1[message[cnt]]
	  returnDict[addr[addrcnt+1]] = letters14v1_2[message[cnt]]
	except:
	  returnDict[addr[addrcnt]] = 0
	  returnDict[addr[addrcnt+ 1]] = 0
	cnt = cnt+1
	addrcnt = addrcnt+2
    
    return returnDict

def mpdAuth(client, secret):
    """
    Authenticate
    """
    try:
        client.password(secret)
    except CommandError:
        return False
    return True
    
def getTimeList():
    statFile = file("/proc/stat", "r")
    timeList = statFile.readline().split(" ")[2:6]
    statFile.close()
    for i in range(len(timeList))  :
        timeList[i] = int(timeList[i])
    return timeList
def getMeminfo():
    statFile = file("/proc/meminfo", "r")
    memTotal = statFile.readline().split(":")
    memFree = statFile.readline().split(":")
    statFile.close()
    mymemTotal = memTotal[1].lstrip().rstrip().rstrip("kB")
    mymemFree = memFree[1].lstrip().rstrip().rstrip("kB")
    mymemFree = str(int(mymemFree) /1024) + ' Mbyte'
    mymemTotal = str(int(mymemTotal) /1024) + ' Mbyte'
    return [mymemTotal, mymemFree] 
    
def deltaTime(interval)  :
    x = getTimeList()
    time.sleep(interval)
    y = getTimeList()
    for i in range(len(x))  :
        y[i] -= x[i]
    return y

#if __name__ == "__main__":
#    main()
    
if __name__ == "__main__":
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit first parent
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    # do second fork
    try: 
        pid = os.fork() 
        if pid > 0:
            # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid 
            sys.exit(0) 
    except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 

    # start the daemon main loop
    main() 
