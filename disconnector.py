#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.8.2'

import sys
import time

from optparse import OptionParser

try:
	from naoqi import ALProxy
	from naoqi import ALBroker
	from naoqi import ALModule
	import qi
except:
	print("NAOqi Python SDK not found")
	sys.exit(1)

NAO_IP = "127.0.0.1"

tetheringSSID = "Nao-WiFi"
tetheringPassword = "Nao12345"
wifiCountry = "IT"

language = None
session = qi.Session()
CorMenuModule = None
memory = None
tts = None
connectionManager = None
pip = None
pport = None
autoLife = None

menuVal = 0

menu = ["init","disconnect","activateWiFi","deactivateWiFi","autonomousLifeToggle","changeOffsetFromFloor","changeVolume","status","close"]

class CorMenuModule(ALModule):
	def __init__(self, name):
		ALModule.__init__(self, name)
		
		self.changeOffset = False
		
		try:
			autoLife = ALProxy("ALAutonomousLife")
		except:
			self.logger.warn("ALAutonomousLife is not available")
			autoLife = None
		
		try:
			tts = ALProxy("ALTextToSpeech")
		except:
			self.logger.warn("ALTextToSpeech is not available")
			tts = None
			
		try:
			connectionManager = ALProxy("ALConnectionManager", "127.0.0.1", 9559)
		except:
			self.logger.warn("ALConnectionManager is not available, hotspot cannot be created")
			connectionManager = None
			
		memory = ALProxy("ALMemory")
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
	
	def disconnect(self):
		services = session.services()
		removed = False
		for s in services :
			strName = s["name"];
			try:
				serviceID = s["serviceId"];
			except:
				serviceID = s[1]
			if strName in ["ALChoregraphe", "ALChoregrapheRecorder"] :
				session.unregisterService( serviceID )
				if not removed:
					tts.say("Choregraphe connection removed successfully.")
				removed = True
		if not removed:
			tts.say("Choregraphe connection not found.")
		
	def onTripleChest(self):
		language = tts.getLanguage()
		tts.setLanguage("English")
		memory.unsubscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName())
			
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onReatHead")
	
	def onFrontHead(self):
		if self.changeOffset:
			self.offset += 1
			return
	
		if menuVal >= 0 and < len(menu)-1:
			menuVal += 1
		elif menuVal == len(menu)-1:
			menuVal = 1
		else:
			tts.say("Unknown error.")
			return
		
		tts.say(menu[menuVal] + " selected!")
		
	def onMiddleHead(self):
		if self.changeOffset:
			autoLife.setRobotOffsetFromFloor(self.offset)
			self.changeOffset = False
			tts.say("Offset set!")
			return
	
		if menu[menuVal] == "init":
			tts.say("Nothing selected! Quitting.")
		elif menu[menuVal] == "disconnect":
			self.disconnect()
		elif menu[menuVal] == "activateWiFi":
			self.activateWiFi()
		elif menu[menuVal] == "deactivateWiFi":
			self.deactivateWiFi()
		elif menu[menuVal] == "status":
			self.status()
		elif menu[menuVal] == "autonomousLifeToggle":
			self.autonomousLifeToggle()
		elif menu[menuVal] == "changeOffsetFromFloor":
			self.changeOffset = True
			self.offset = autoLife.getRobotOffsetFromFloor()
			return
		else:
			tts.say("Unknown error.")
		
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
		tts.setLanguage(language)
		menuVal = 0
		
	def onReatHead(self):
		if self.changeOffset:
			if self.offset > 0
				self.offset -= 1
			else
				tts.say("Cannot do it")
			return
		if menuVal <= 1:
			menuVal = len(menu)-1
		elif menuVal == <= len(menu)-1 and >1 :
			menuVal -= 1
		else:
			tts.say("Unknown error.")
			return
		
		tts.say(menu[menuVal] + " selected!")
		
	def activateWiFi(self):
		if connectionManager is None:
			tts.say("Error, ALConnectionManager is no longer avaiable")
			return
		if not connectionManager.getTetheringEnable("wifi"):
			connectionManager.setCountry(wifiCountry)
			connectionManager.enableTethering("wifi", tetheringSSID, tetheringPassword)
			tts.say("Wifi Tethering activated.")
		else:
			tts.say("Wifi Tethering is already active.")
			
	def deactivateWiFi(self):
		if connectionManager is None:
			tts.say("Error, ALConnectionManager is no longer avaiable")
			return
		if connectionManager.getTetheringEnable("wifi"):
			connectionManager.disableTethering("wifi")
			tts.say("Wifi Tethering deactivated.")
		else:
			tts.say("Wifi Tethering is already inactive.")
		
	def status(self):
		tts.say("Woops! I don't know what to do!")
		pass
		
	def autonomousLifeToggle(self):
		lifeState = autoLife.getState()
		if lifeState == "solitary" or lifeState == "interactive":
			autoLife.setState("disabled")
		elif lifeState == "safeguard":
			pass # Stand Up from Choregraphe
		else:
			autoLife.setState("interactive")
		
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
		pport=9559)

	(opts, args_) = parser.parse_args()
	pip   = opts.pip
	pport = opts.pport
	
	session.connect("tcp://" + str(pip) + ":" + str(pport))
	myBroker = ALBroker("myBroker",
	   "0.0.0.0",
	   0, 
	   pip,
	   pport)
	CorMenuModule = CorMenuModule("CorMenuModule")
	
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print "Interrupted by user, shutting down"
		myBroker.shutdown()
		sys.exit(0)

if __name__ == "__main__":
	main()
