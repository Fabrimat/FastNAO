#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.8'

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

menuVal = 0

menu = ["init","disconnect","activateWiFi","deactivateWiFi","status"]

class CorMenuModule(ALModule):
	def __init__(self, name):
		ALModule.__init__(self, name)
		
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
		pass
	
	def onFrontHead(self):
		if menuVal == -1:
			menuVal = 1
		elif menuVal >= 1 and < len(menu)-1:
			menuVal += 1
		elif menuVal == len(menu)-1:
			menuVal = 1
		else:
			pass
		
	def onMiddleHead(self):
		if menu[menuVal] == "init":
			pass
		elif menu[menuVal] == "disconnect":
			pass
		elif menu[menuVal] == "activateWiFi":
			pass
		elif menu[menuVal] == "status":
			pass
		elif menu[menuVal] == "deactivateWiFi":
			pass
		else:
			pass
		tts.setLanguage(language)
		
	def onReatHead(self):
		if menuVal == -1:
			menuVal = 2
		elif menuVal == <= len(menu)-1 and >1 :
			menuVal -= 1
		elif menuVal == 1:
			menuVal = len(menu)-1
		else:
			pass
		pass
		
	def activateWiFi(self):
		if connectionManager is None:
			# Error
			return
		if not connectionManager.getTetheringEnable("wifi"):
			connectionManager.setCountry(wifiCountry)
			connectionManager.enableTethering("wifi", tetheringSSID, tetheringPassword)
		else:
			# Already active
			
	def deactivateWiFi(self):
		if connectionManager is None:
			# Error
			return
		if connectionManager.getTetheringEnable("wifi"):
			connectionManager.disableTethering("wifi")
		else:
			# Already inactive
		
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
		print
		print "Interrupted by user, shutting down"
		myBroker.shutdown()
		sys.exit(0)

if __name__ == "__main__":
	main()
