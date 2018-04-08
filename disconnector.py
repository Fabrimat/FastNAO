#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.8.6'

import config
try:
	lang = __import__("%s-lang" %(config.language))
except ImportError:
	if config.language is not "EN":
		try:
			lang = __import__("EN-lang")
		except ImportError:
			print("Lang file not found.")
			logging.error("Lang file not found.")
			sys.exit(1)
	else:
		print("Lang file not found.")
		logging.error("Lang file not found.")
		sys.exit(1)
	


import logging

#Configuring logging
logger = logging.getLogger('LogScanner')
logging.basicConfig(filename='naoDisconnector.log',format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

logging.info("Default values:")
logging.info("NAO_IP: %s" %(NAO_IP))
logging.info("NAO_PORT: %i" %(NAO_PORT))
logging.info("tetheringSSID: %s" %(tetheringSSID))
logging.info("tetheringPassword: %s" %(tetheringPassword))
logging.info("wifiCountry: %s" %(wifiCountry))

import sys
import time
import subprocess

from optparse import OptionParser

try:
	from naoqi import ALProxy
	from naoqi import ALBroker
	from naoqi import ALModule
	import qi
	logging.info("NAOqi Python SDK found!")
except:
	print("NAOqi Python SDK not found, quitting...")
	logging.error("NAOqi Python SDK not found, quitting...")
	sys.exit(1)

session = qi.Session()
memory = None

class CorMenuModule(ALModule):

	menuVal = 0
	menu = ["init","disconnect","activateWiFi","deactivateWiFi","autonomousLifeToggle","changeOffsetFromFloor","changeVolume","status","fastReboot","close"]
	
	def __init__(self, name):
		ALModule.__init__(self, name)
		
		try:
			self.motion = ALProxy("ALMotion")
		except:
			self.logger.warn("ALMotion is not available")
			self.motion = None
		
		try:
			self.autoLife = ALProxy("ALAutonomousLife")
		except:
			self.logger.warn("ALAutonomousLife is not available")
			self.autoLife = None
		
		try:
			self.tts = ALProxy("ALTextToSpeech")
		except:
			self.logger.warn("ALTextToSpeech is not available")
			self.tts = None
			
		try:
			self.sys = ALProxy("ALSystemProxy")
		except:
			self.logger.warn("ALSystemProxy is not available")
			self.sys = None
			
		try:
			self.connectionManager = ALProxy("ALConnectionManager", NAO_IP, NAO_PORT)
		except:
			self.logger.warn("ALConnectionManager is not available")
			self.connectionManager = None
		
		try:
			self.postureProxy = ALProxy("ALRobotPosture")
		except:
			self.logger.warn("ALRobotPosture is not available")
			self.postureProxy = None
			
		global memory
		memory = ALProxy("ALMemory")
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
	
	
	def disconnect(self):
		services = session.services()
		removed = 0
		for s in services :
			strName = s["name"];
			try:
				serviceID = s["serviceId"];
			except:
				serviceID = s[1]
			if strName in ["ALChoregraphe", "ALChoregrapheRecorder"] :
				session.unregisterService( serviceID )
				removed += 1
		if removed == 2:
			self.tts.say("Choregraphe connection removed successfully.")
		elif removed == 0:
			self.tts.say("Choregraphe connection not found.")
		else:
			self.tts.say("Error removing Choregraphe connection.")
		
	def onTripleChest(self, *_args):
		global memory
		memory.unsubscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName())
		
		self.language = self.tts.getLanguage()
		self.tts.setLanguage("English")
		
		self.tts.say("You entered the advanced menu, hope you know what you are doing!")
		self.tts.say("Use my head sensors to move between the options.")
		
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")
	
	def onFrontOffset(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		self.offset += 1
		
		self.tts.say("Offset: %s" %(self.offset))
		
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontOffset")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleOffset")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearOffset")
		
	def onMiddleOffset(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		self.autoLife.setRobotOffsetFromFloor(self.offset)
		self.tts.say("Offset set to %s!" %(self.offset))
		
		self.close()
	
	def onRearOffset(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		if self.offset > 0:
			self.offset -= 1
			self.tts.say("Offset: %s" %(self.offset))
		else:
			self.tts.say("Cannot do it")
			
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontOffset")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleOffset")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearOffset")
	
	def onFrontHead(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
			
		if self.menuVal >= 0 and self.menuVal < len(self.menu)-1:
			self.menuVal += 1
		elif self.menuVal == len(self.menu)-1:
			self.menuVal = 1
		else:
			self.tts.say("Unknown error.")
		
		self.tts.say("%s selected!" %(self.menu[self.menuVal]))
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")
			
	def onMiddleHead(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		flag_Return = False
		
		if self.menu[self.menuVal] == "init":
			self.tts.say("Nothing selected! Quitting.")
		elif self.menu[self.menuVal] == "disconnect":
			self.disconnect()
		elif self.menu[self.menuVal] == "activateWiFi":
			self.activateWiFi()
		elif self.menu[self.menuVal] == "deactivateWiFi":
			self.deactivateWiFi()
		elif self.menu[self.menuVal] == "status":
			self.status()
		elif self.menu[self.menuVal] == "autonomousLifeToggle":
			self.autonomousLifeToggle()
		elif self.menu[self.menuVal] == "changeOffsetFromFloor":
			flag_Return = True
			self.offset = self.autoLife.getRobotOffsetFromFloor()
			memory.subscribeToEvent("FrontTactilTouched",
				self.getName(),
				"onFrontOffset")
			memory.subscribeToEvent("MiddleTactilTouched",
				self.getName(),
				"onMiddleOffset")
			memory.subscribeToEvent("RearTactilTouched",
				self.getName(),
				"onRearOffset")
		elif self.menu[self.menuVal] == "changeVolume":
			self.changeVolume()
		elif self.menu[self.menuVal] == "close":
			self.close()
		else:
			self.tts.say("Unknown error.")
		
		if not flag_Return:
			self.close()
			
		
	def onRearHead(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		if self.menuVal <= 1:
			self.menuVal = len(self.menu)-1
		else :
			self.menuVal = self.menuVal - 1
		
		self.tts.say("%s selected!" %(self.menu[self.menuVal]))
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")
			
	def activateWiFi(self):
		if self.connectionManager is None:
			self.tts.say("Error, ALConnectionManager is no longer avaiable")
			return
		if not self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.setCountry(wifiCountry)
			self.connectionManager.enableTethering("wifi", tetheringSSID, tetheringPassword)
			self.tts.say("Wifi Tethering activated.")
		else:
			self.tts.say("Wifi Tethering is already active.")
			
	def deactivateWiFi(self):
		if self.connectionManager is None:
			self.tts.say("Error, ALConnectionManager is no longer avaiable")
			return
		if self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.disableTethering("wifi")
			self.tts.say("Wifi Tethering deactivated.")
		else:
			self.tts.say("Wifi Tethering is already inactive.")
		
	def status(self):
		global memory
		realNotVirtual = False
		try:
			memory.getData( "DCM/Time" )
			if( memory.getData( "DCM/Simulation" ) != 1 ):
				realNotVirtual = True
			else:
				import os
				realNotVirtual = os.path.exists("/home/nao")
		except:
			pass 

		if realNotVirtual:
			import socket
			robotName = socket.gethostname()
			naoName = robotName
		else:
			naoName = "virtual robot"
		
		self.tts.say("My name is %s \pau=300" %(naoName))
		
		batteryCharge = memory.getData("Device/SubDeviceList/Battery/Charge/Sensor/Value")
		self.tts.say("My battery is at %d percent \pau=300" %(batteryCharge*100))
		
		autoLifeStatus = self.autoLife.getState()
		self.tts.say("My autonomous life status is: %s" %(autoLifeStatus))
		
		if(self.connectionManager.getTetheringEnable("wifi")):
			self.tts.say("WiFi Tethering is active")
			
			ssid = self.connectionManager.tetheringName()
			password = self.connectionManager.tetheringPassphrase()
			
			checkSsid = ""
			checkPassword = ""
			
			for char in ssid:
				if char.isupper():
					checkSsid += "Upper %s \pau=100 " %(char)
				else:
					checkSsid += "Lower %s \pau=100 " %(char)
					
			for char in password:
				if char.isupper():
					checkPassword += "Upper %s \pau=100 " %(char)
				else:
					checkPassword += "Lower %s \pau=100 " %(char)
			
			self.tts.say("WiFi Tethering SSID is %s" %(checkSsid))
			self.tts.say("WiFi Tethering password is %s" %(checkPassword))
		else:
			self.tts.say("WiFi Tethering is not active")
		
		try:
			urllib.urlopen('http://www.google.com', timeout=1)
			self.tts.say("I am connected to the Internet")
		except urllib.URLError: 
			self.tts.say("I am not connected to the Internet")
		
		"""
		ipv4
		state
		type
		autoconnect
		security
		strenght
		error
		"""
		
	def autonomousLifeToggle(self):
		lifeState = self.autoLife.getState()
		if lifeState == "solitary" or lifeState == "interactive":
			self.autoLife.setState("disabled")
		elif lifeState == "safeguard":
			self.postureProxy.setMaxTryNumber(3)
			result = self.postureProxy.goToPosture("Stand", 80)
			
			if(result):
				logging.info("Stand reached")
			else:
				logging.error("Failed to stand up")
				self.tts.say("I surrender.")
		else:
			self.autoLife.setState("solitary")
		
	def fastReboot(self):
		self.motion.rest()
		self.tts.say("Rebooting!")
		proc = subprocess.Popen(["nao restart"], stdout=subprocess.PIPE)
		
	def close(self):
		global memory
		self.tts.setLanguage(self.language)
		self.menuVal = 0
		
		for sub in memory.getSubscribers("MiddleTactilTouched"):
			if sub == self.getName():
				memory.unsubscribeToEvent("MiddleTactilTouched",
				self.getName())
		for sub in memory.getSubscribers("FrontTactilTouched"):
			if sub == self.getName():
				memory.unsubscribeToEvent("FrontTactilTouched",
				self.getName())
		for sub in memory.getSubscribers("RearTactilTouched"):
			if sub == self.getName():
				memory.unsubscribeToEvent("RearTactilTouched",
				self.getName())
			
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
	
	def unload(self):
		self.postureProxy.stopMove()
		self.tts.setLanguage(self.language)
		
		for sub in memory.getSubscribers("MiddleTactilTouched"):
			if sub == self.getName():
				memory.unsubscribeToEvent("MiddleTactilTouched",
				self.getName())
		for sub in memory.getSubscribers("FrontTactilTouched"):
			if sub == self.getName():
				memory.unsubscribeToEvent("FrontTactilTouched",
				self.getName())
		for sub in memory.getSubscribers("RearTactilTouched"):
			if sub == self.getName():
				memory.unsubscribeToEvent("RearTactilTouched",
				self.getName())
		for sub in memory.getSubscribers("ALChestButton/TripleClickOccurred"):
			if sub == self.getName():
				memory.unsubscribeToEvent("ALChestButton/TripleClickOccurred",
				self.getName())
			
def main():
	parser = OptionParser()
	parser.add_option("--pip",
		help="Robot address",
		dest="pip")
	parser.add_option("--pport",
		help="NAOqi port",
		dest="pport",
		type="int")
	parser.set_defaults(
		pip=NAO_IP,
		pport=NAO_PORT)

	(opts, args_) = parser.parse_args()
	pip   = opts.pip
	pport = opts.pport
	
	logging.info("Parsed values:")
	logging.info("NAO_IP: %s" %(NAO_IP))
	logging.info("NAO_PORT: %i" %(NAO_PORT))
	
	session.connect("tcp://" + str(pip) + ":" + str(pport))
	myBroker = ALBroker("myBroker",
	   "0.0.0.0",
	   0, 
	   pip,
	   pport)
	
	global CorMenu
	CorMenu = CorMenuModule("CorMenu")
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print "Interrupted by user, shutting down..."
		logging.info("Interrupted by user, shutting down...")
		CorMenu.unload()
		myBroker.shutdown()
		sys.exit(0)
	except Exception as exception:
		logging.error(exception.strerror)
		CorMenu.unload()
		myBroker.shutdown()
		sys.exit(1)

if __name__ == "__main__":
	main()
