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

HOST = '192.168.200.18'
PORT = '6600'
PASSWORD = False
##
CON_ID = {'host':HOST, 'port':PORT}

class MyArduino():
    def __init__(self):
	locations=['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
	    '/dev/ttyS0','/dev/ttyS1','/dev/ttyS2','/dev/ttyS3']
	    
	for device in locations:
	  try:
	    self.arduino = serial.Serial(device, 9600)
	    print "Connected on",device
	    break
	  except:
	    print "Failed to connect on",device
	
    def write(self, text):
      self.arduino.write(text)
    
    def read(self):
      return self.arduino.readline()

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


class MyRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
      
	responsePrefix = "HTTP/1.0 200 OK\r\n" #Server:Affixserver/1.0\r\n"
	self.arduino = self.server.arduino
	self.mpdclient = self.server.mympdClient
	self.lock = self.server.lock
	self.timer = self.server.timer
	
	data = self.request.recv(100)
	
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
		    
		    self.lock.acquire() 
		    self.arduino.write(command[2]+command[3]+command[4]+command[5]+command[6]+'\0')
		    self.request.send("cmd sent")
		    self.lock.release()
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
      
      counterAlarm=0
      
      while True:
	    
	    print arduino.read()
	    
	    if(counterAlarm==45):counterAlarm=0
	    
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

	    time.sleep(1)
	
      myServer.shutdown()

def mpdConnect(client, con_id):
    """
    Simple wrapper to connect MPD .
    """
    try:
        client.connect(**con_id)
    except SocketError:
        return False
    return True

def mpdAuth(client, secret):
    """
    Authenticate
    """
    try:
        client.password(secret)
    except CommandError:
        return False
    return True
if __name__ == "__main__":
    main()
