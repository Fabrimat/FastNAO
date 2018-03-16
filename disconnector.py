#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.7'

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

session = qi.Session()
ChorDisconnect = None
memory = None

class CorDisconnectModule(ALModule):
	def __init__(self, name):
		ALModule.__init__(self, name)
		
		try:
			self.tts = ALProxy("ALTextToSpeech")
		except:
			self.logger.warn("ALTextToSpeech is not available")
			self.tts = None
			
			
		global memory
		memory = ALProxy("ALMemory")
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			"ChorDisconnect",
			"onTriplePress")
		pass

	def onTriplePress(self, *_args):
		memory.unsubscribeToEvent("ALChestButton/TripleClickOccurred",
			"ChorDisconnect")
		
		self.disconnect()
		
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			"ChorDisconnect",
			"onTriplePress")
		pass
			
	def disconnect(self):
		services = session.services()
		self.tts.setLanguage("English")
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
					self.tts.say("Choregraphe connection removed successfully.")
				removed = True
		if not removed:
			self.tts.say("Choregraphe connection not found.")
		pass
		
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
	global pip
	global pport
	pip   = opts.pip
	pport = opts.pport
	
	
	session.connect("tcp://" + str(pip) + ":" + str(pport))
	myBroker = ALBroker("myBroker",
	   "0.0.0.0",
	   0, 
	   pip,
	   pport)
	global ChorDisconnect
	ChorDisconnect = CorDisconnectModule("ChorDisconnect")
	
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
