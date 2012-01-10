#!/usr/bin/python
# coding: utf-8
import socket, os, re
import sys
import serial
import time
import pprint

from mpd import (MPDClient, CommandError)
from socket import error as SocketError
import SocketServer
import threading 

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
	
    def getStatus(self):
	return self.client.status()


class MyRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
	responsePrefix = "HTTP/1.0 200 OK\r\n" #Server:Affixserver/1.0\r\n"
	self.arduino = self.server.arduino
	self.mpdclient = self.server.mympdClient
	
	print self.mpdclient
	
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
	
	if m:
	    word1=m.group(1)
	    unixpath1=m.group(2)
	    word2=m.group(3)
	    print "("+word1+")"+"("+unixpath1+")"+"("+word2+")"+"\n"
	    if unixpath1 == "/1.1":
		unixpath1 = "/index.html"      
	  
	if command[1] == "":
	    command[1] = "index.html"	    
	
	if os.path.exists("/home/aex/sketchbook/htdocs/" + command[1]):
	      print "+ Attempting to serve "+ unixpath1 +"\n"
	      file = open("/home/aex/sketchbook/htdocs/"  + command[1], "r")
	      
	      self.request.send( responsePrefix )
	      self.request.send("Content-Type: text/html\r\n")
	      # send file in 1024 byte chunks
	      while 1:
		  data = file.read(1024)
		  if not data:
		      break
		  time.sleep(0.05)
		  self.request.sendall( data )
			
	elif command[1] == "cmd":
	    print "+ Attempting to send cmd "+ unixpath1 +"\n"
	    if len(command) > 6:

		try:
		    self.arduino.write(command[2]+command[3]+command[4]+command[5]+command[6]+'\0')
		    self.request.send("cmd sent")	
		    time.sleep(1)
		except:
		    time.sleep(0)
		    
	elif command[1] == "mpd":

	    if(command[2]=="currentsong"):
		lock.acquire() 

		mpd_currentSong = self.mpdclient.getCurrentsong()
		lock.release()
		
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
		    
	    elif(command[2]=="time"):
		
		if(command[3] == "0"):
		    lock.acquire() 
		    self.mpd_status = self.mpdclient.getStatus()
		    lock.release()
		    
		    track_time = mpd_status['time'].split(':')
		    
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

	else:
		print "+ File was not found!\n"
		self.request.send("<html><head><title>404</title></head><body><h1>404 File not Found</h1><br />The file you requested was not found on the server<hr /><small>Affix’ Simple Python HTTP Server 0.0.1</small></body></html>")
	self.request.close()

    
class TCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        self.allow_reuse_address = True
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)	
        
def main():
      
      arduino = MyArduino()
      mympdClient = MyMPDClient()
      
      myServer = TCPServer(("", 8001), MyRequestHandler)
      myServer_thread = threading.Thread(target=myServer.serve_forever)
      myServer_thread.setDaemon(True)
      myServer_thread.start()
      myServer.arduino = arduino
      myServer.mympdClient = mympdClient
      
      print 'Hello, my name is', myServer_thread.getName()
      
      while True:
	print "still serving"
	eingabe = raw_input("> ") 
	if eingabe == "en": 
	    break 

	time.sleep(5)
	
      myServer.shutdown()

def mpdConnect(client, con_id):
    """
    Simple wrapper to connect MPD.
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
