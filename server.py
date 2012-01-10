#!/usr/bin/python
# coding: utf-8
#           _     __  __ _        __  __ _____
#          / \   / _|/ _(_)_  __ |  \/  | ____|
#         / _ \ | |_| |_| \ \/ / | |\/| |  _|  
#        / ___ \|  _|  _| |>  < _| |  | | |___
#       /_/   \_\_| |_| |_/_/\_(_)_|  |_|_____|
#
#       Title           : Simple Python HTTP Server
#       Author          : Affix <affix@affix.me>
#       Website         : http://Affix.ME
#       License         : GNU/GPL V3
#       Description     : Serves simple HTML Pages
#       stored inside a folder called htdocs in the
#       same directory as this script.
#
#       DO NOT EXPECT UPDATES I WAS BORED
#################################################
####    DO NOT EDIT BELOW THIS LINE          ####
#################################################

import socket, os, re
import sys
import serial
import time

import pprint

from mpd import (MPDClient, CommandError)
from socket import error as SocketError

HOST = '192.168.200.18'
PORT = '6600'
PASSWORD = False
##
CON_ID = {'host':HOST, 'port':PORT}

## Some functions
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
##

locations=['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',
'/dev/ttyS0','/dev/ttyS1','/dev/ttyS2','/dev/ttyS3']
responsePrefix = "HTTP/1.0 200 OK\r\n" #Server:Affixserver/1.0\r\n"

for device in locations:
  try:
    arduino = serial.Serial(device, 9600)
    print "Connected on",device
    break
  except:
    print "Failed to connect on",device

serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "+ Server Launched\n"
serverSock.bind(('', 8000))
serverSock.listen(1)

while True:
  
	      ## MPD object instance
	      client = MPDClient()
	      if mpdConnect(client, CON_ID):
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
		      client.disconnect()
		      sys.exit(2)

	      ## Fancy output
	      pp = pprint.PrettyPrinter(indent=4)

	      ## Print out MPD stats & disconnect
	      mpd_status = client.status()
	      
	      ## time  +  elspsed
	      mpd_currentSong = client.currentsong()
	      ## name +  title
              #pp.pprint(client.currentsong())

              chan, details = serverSock.accept()
              data = chan.recv(100)
              print data   
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
		  
              if os.path.exists("/home/aex/Dokumente/htdocs/" + command[1]):
                      print "+ Attempting to serve "+ unixpath1 +"\n"
                      file = open("/home/aex/Dokumente/htdocs/"  + command[1], "r")
                      
		      chan.send( responsePrefix )
		      chan.send("Content-Type: text/html\r\n")
		      # send file in 1024 byte chunks
		      while 1:
			  data = file.read(1024)
			  if not data:
			      break
			  time.sleep(0.05)
			  chan.sendall( data )
			  
	      elif command[1] == "cmd":
		  print "+ Attempting to send cmd "+ unixpath1 +"\n"
		  if len(command) > 5:
		      try:
			  arduino.write(command[2]+command[3]+command[4]+command[5]+command[6]+'\0')
			  chan.send("cmd sent")	
			  time.sleep(1)
		      except:
			  time.sleep(0)
			  
	      elif command[1] == "mpd":
		  name = "" 
		  try:
		      name = mpd_currentSong['artist']		      
		  except:
		      print "Failed to connect on",device
		  try:
		      name = mpd_currentSong['name']		      
		  except:
		      print "Failed to connect on",device
		       
		  if(command[2]=="0"):
		      s = '<div id ="title">' + mpd_currentSong['title'] + '</div></br><div id = "name">' + name + "</div>"
		      print "+ Attempting to send mpdStats " + s +"\n"
		      		     
		  elif(command[2]=="1"):
		      track_time = mpd_status['time'].split(':')
		      print track_time[0]
		      print track_time[1]
		      
		      sec2 = int(track_time[1]) % 60
		      mm2 = (int(track_time[1]) - sec2) / 60
		      sec1 = int(track_time[0]) % 60
		      mm1 = (int(track_time[0]) - sec1) / 60

		      s = "%.2d" % mm1 + ":" + "%.2d" % sec1 + " / " + "%.2d" % mm2 + ":" + "%.2d" % sec2
		      print "+ Attempting to send mpdStats "+ s +"\n"
		      
		  elif(command[2]=="2"):
		      s = mpd_currentSong['title']
		      print "+ Attempting to send mpdStats "+ s +"\n"
		      
		  elif(command[2]=="3"):
		    
		      s = mpd_status['time']		      
		      print "+ Attempting to send mpdStats "+ s +"\n"
		      
		  elif(command[2]=="4"):
		      s = mpd_status['elapsed']
		      print "+ Attempting to send mpdStats "+ s +"\n"
		      	
		  chan.send(s)	
  
	      else:
                      print "+ File was not found!\n"
                      chan.send("<html><head><title>404</title></head><body><h1>404 File not Found</h1><br />The file you requested was not found on the server<hr /><small>Affix’ Simple Python HTTP Server 0.0.1</small></body></html>")
	      chan.close()	
	      client.disconnect()

##  



