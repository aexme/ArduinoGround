#!/usr/bin/python
# coding: utf-8
import socket, os, re
import sys
import serial
import time
from datetime import datetime
import pprint
import datetime
from mpd import (MPDClient, CommandError)
from socket import error as SocketError
import SocketServer
import threading 
import thread
import ConfigParser
import csv
import urllib

HOST = '192.168.200.18'
PORT = '6600'
PASSWORD = False
##
CON_ID = {'host':HOST, 'port':PORT}

class MyArduino():
    def __init__(self):
	locations=['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
	    '/dev/ttyS0','/dev/ttyS1','/dev/ttyS2','/dev/ttyS3']
	self.lock=thread.allocate_lock()

	for device in locations:
	  try:
	    self.arduino = serial.Serial(device, 9600)
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

class MyTimer():
    def __init__(self):
	self.timerList = {}
	self.loadTimer()
	
    def updateTimerList(self):
	self.loadTimer()
	
    def loadTimer(self):
	timerFile = open('alarm.cfg', 'r')

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
	timerFile = open('alarm.cfg', 'w')
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
	
	
class MyRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
      
	responsePrefix = "HTTP/1.0 200 OK\r\n" #Server:Affixserver/1.0\r\n"
	self.arduino = self.server.arduino
	self.mpdclient = self.server.mympdClient
	self.lock = self.server.lock
	self.timer = self.server.timer

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
	  
	if command[1] == "":
	    command[1] = "index.html"	    
		
	if command[1] == "cmd":
	    print "+ Attempting to send cmd "+ self.unixpath1 +"\n"
	    if len(command) > 6:

		try:
		    self.arduino.write(command[2]+command[3]+command[4]+command[5]+command[6]+'\0')
		    self.request.send("cmd sent")
		    time.sleep(0.01)		    
		except:
		    time.sleep(0)
		    
	elif command[1] == "alarm":
	    if(command[2] == "set"):
		self.lock.acquire() 
		self.timer.addTimer(command[3] + ';' + command[4] + ';' + command[5] + ';' + command[6])
		self.timer.writeConfig()
		self.lock.release()
		s = "OK"
	    
	    elif(command[2] == "rm"):
		self.lock.acquire() 
		self.timer.deleteTimer(command[3])
		self.lock.release()
		s = "OK"
	    elif(command[2] == "flip"):
		self.lock.acquire() 
		self.timer.flipTimer(command[3])
		self.timer.writeConfig()
		self.lock.release()
		s= "OK"
		
	    elif(command[2] == "get"):
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

	    if(command[2]=="currentsong"):
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
		    		    
		if(command[3]=='0'):
		    s = '<div id ="title">' + mpd_currentSong['title'] + '</div></br><div id = "name">' + name + "</div>"
		    print "+ Attempting to send mpdStats " + s +"\n"    
		elif(command[3]=="1"):
		    s = name
		    print "+ Attempting to send mpdStats "+ s +"\n"
		    
		elif(command[3]=="2"):
		    s = mpd_currentSong['title']
		    print "+ Attempting to send mpdStats "+ s +"\n"
	    
	    elif(command[2]=="pause"):
		self.mpdclient.pause();
		s='OK'
	    elif(command[2]=="previous"):
		self.mpdclient.previous();
		s='OK'
  	    elif(command[2]=="next"):
		self.mpdclient._next();
		s='OK'
	    elif(command[2]=="stop"):
		self.mpdclient.stop();
		s='OK'
	    elif(command[2]=="play"):
		self.mpdclient.play();
		s='OK'
	    elif(command[2]=="iRadio"):
		if command[3] == 'set':
		    pass
		elif command[3]=='play':
		    pass
		s='OK'

	    elif(command[2]=="time"):
		if(command[3] == "0"):

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
		    
		elif(command[3]=="1"): 
		    s = mpd_status['time']		      
		    print "+ Attempting to send mpdStats "+ s +"\n"
		
		elif(command[3]=="2"):
		    s = mpd_status['elapsed']
		    print "+ Attempting to send mpdStats "+ s +"\n"
		  
	    self.request.send(s)
	
	elif command[1] == "sys":
	    if command[2] == "cpuLoad":
		self.cpuLoad = deltaTime(1)
	    	    
		cpuPct = 100 - (self.cpuLoad[len(self.cpuLoad) - 1] * 100.00 / sum(self.cpuLoad))
		s = "CPU Load: " +  str('%.2f' %cpuPct) +"%"
	    elif command[2] == "meminfo":
		meminfo = getMeminfo()
		s = 'Free Memory: ' + meminfo[1] + ' / ' + meminfo[0] 
	    
	    self.request.send(s)
	
	elif os.path.exists("/home/aex/sketchbook/htdocs/" + command[1]):
	      print "+ Attempting to serve "+ self.unixpath1 +"\n"
	      file = open("/home/aex/sketchbook/htdocs/"  + command[1], "r")
	      
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
		self.request.send("<html><head><title>404</title></head><body><h1>404 File not Found</h1><br />The file you requested was not found on the server<hr /><small>Affix’ Simple Python HTTP Server 0.0.1</small></body></html>")
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
      
      print "noch daa"

def main():
      
      arduino = MyArduino()
      mympdClient = MyMPDClient()
      lock=thread.allocate_lock()
      timer = MyTimer()
      myServer = TCPServer(("", 8001), MyRequestHandler)
      myServer_thread = threading.Thread(target=myServer.serve_forever)
      myServer_thread.setDaemon(True)
      myServer_thread.start()
      myServer.arduino = arduino
      myServer.mympdClient = mympdClient
      myServer.lock = lock
      myServer.timer = timer
      
      weekdayArray = ['Mo','Di','Mi','Do','Fr','Sa','So']
      myAlarmTime = []
      counterAlarm = 0

      cnt = 0
      while cnt<41:
	  arduino.write('C' + chr(cnt) + chr(0) +'00')  
	  cnt = cnt + 1
      
      vfdMessagecnt = 0
      vfdTimer = 0
      loadingsymbol = 32
      
      trance = 'http://listen.di.fm/public3/trance.pls'
      
      items = parsePLS(trance)
      i=1
      
      playlist =  mympdClient.client.playlistid()
      itemInPlaylist = false
      for pos in playlist:
	    if pos['file'] == items[1]:
		mympdClient.client.playid(int(pos['id']))
		itemInPlaylist = True
		break
		
      if !itemInPlaylist:
	    while i <= len(items):
		mympdClient.add(items[i])
		i+=1
		
	    playlist =  mympdClient.client.playlistid()
	    for pos in playlist:
		if pos['file'] == items[1]:
		    mympdClient.client.playid(int(pos['id']))		    
		    break
      
      while True:
	
	    time.sleep(0.1)
	    if vfdTimer>3: vfdTimer=0  
	    if vfdTimer==0:
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
		arduino.write('C' + chr(39) + chr(1) +'00') # circle sign
		arduino.write('C' + chr(9) + chr(loadingsymbol+1) +'00') # circle sign
		if loadingsymbol < 128:
		    loadingsymbol  *=2 
		else: loadingsymbol = 32
		
	    vfdTimer+=1
	    arduinoMessage = arduino.read().split(';')

	    if(arduinoMessage[0] == "RF"):
		if(arduinoMessage[1] == "118772"):
		    print 'got RF cmd mpd pause'
		    writeVfdMessage(arduino, ' PAUSE  ')		    		   
		    mympdClient.pause()
		    time.sleep(0.5)
		elif(arduinoMessage[1] == "118770"):
		    print 'got RF mpd play'
		    writeVfdMessage(arduino, '  PLAY  ')		    
		    mympdClient.play()
		    time.sleep(0.5)		    
		elif(arduinoMessage[1] == "123144"):
		    print 'got RF mpd stop'
		    writeVfdMessage(arduino, '  STOP  ')		    
		    mympdClient.stop()
		    time.sleep(0.5)		    
		elif(arduinoMessage[1] == "120230"):
		    print 'got RF mpd previous'
		    writeVfdMessage(arduino, '  PREV  ')		    
		    mympdClient.previous()
		    time.sleep(0.5)		    
		elif(arduinoMessage[1] == "120228"):
		    print 'got RF mpd next'
		    mympdClient._next()
		    writeVfdMessage(arduino, '  NEXT  ')		    
		    time.sleep(0.5)		    
		elif(arduinoMessage[1] == "122498"):
		    print 'got RF sw on'
		    time.sleep(0.1)
		    arduino.write('D1000')
		    time.sleep(0.1)		  
		    writeVfdMessage(arduino, ' SW ON  ')
		    time.sleep(0.5)
		elif(arduinoMessage[1] == "122496"):
		    print 'got RF sw off'
		    time.sleep(0.1)
		    arduino.write('D1100')		    
		    time.sleep(0.1)
		    writeVfdMessage(arduino, ' SW OFF ')
		    time.sleep(0.5)
		elif(arduinoMessage[1] == "123956"):
		    print 'got RF rfsw on'
		    time.sleep(0.1)
		    arduino.write('EC110')
		    arduino.write('EC310')
		    time.sleep(0.1)
		    writeVfdMessage(arduino, 'RF SW ON')
		    time.sleep(0.5)
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
		if(arduinoMessage[1] == "TA"):
		    print "got vfd keyTA"
		elif(arduinoMessage[1] == "PTY"):
		    print "got vfd keyPTY"
		elif(arduinoMessage[1] == "AF"):
		    print "got vfd keyAF"
		elif(arduinoMessage[1] == "Power"):
		    print "got vfd keyPower"
		elif(arduinoMessage[1] == "DSP"):
		    print "got vfd keyDSP"
		elif(arduinoMessage[1] == "MODE"):
		    print "got vfd keyMODE"
		elif(arduinoMessage[1] == "EQ"):
		    print "got vfd keyEQ"
		elif(arduinoMessage[1] == "1"):
		    print "got vfd key1"
		elif(arduinoMessage[1] == "2"):
		    print "got vfd key2"
		elif(arduinoMessage[1] == "3"):
		    print "got vfd key3"
		elif(arduinoMessage[1] == "4"):
		    print "got vfd key4"
		elif(arduinoMessage[1] == "5"):
		    print "got vfd key5"
		elif(arduinoMessage[1] == "6"):
		    print "got vfd key6"
		elif(arduinoMessage[1] == "8"):
		    print "got vfd key8"
		elif(arduinoMessage[1] == "BAND"):
		    print "got vfd keyBAND"
		elif(arduinoMessage[1] == "9"):
		    print "got vfd key9"		
	    if(counterAlarm > 45):	counterAlarm=0
	    else: 			counterAlarm += 0.1
	    
	    if(counterAlarm==0):
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
			  ma_AlarmThread = myAlarm()
			  ma_AlarmThread.start()
			  print 'ALARM'

      myServer.shutdown()
      
##  Channell C  ##

#E10	118122
#E11	118124
#E20	122496
#E21	122498
#E30	119580
#E31	119582
#E40	123954
#E41	123956

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
    
def parsePLS(url):
      opener = urllib.FancyURLopener({})
      f = opener.open(url)

      config = ConfigParser.RawConfigParser()
      config.readfp(f)
      numberOfItems = int(config.get('playlist', 'NumberOfEntries'))
      
      i=1
      items = {}
      while i <= numberOfItems:
	  items[i] = config.get('playlist', 'File' + str(i))
	  i +=1
	  
      return items

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
    
if __name__ == "__main__":
    main()
