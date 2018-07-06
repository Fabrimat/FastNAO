#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.8.9'

confVer = 0.2


try:
	import config
	if config.Config_Version != confVer:
		print("Configuration file not valid. Please update it.")
		sys.exit(1)
except ImportError:
	print("Configuration file not found.")

try:
	lang = __import__("%s-lang" %(config.Language))
	if config.Config_Version != confVer:
		print("Language file not valid. Please update it.")
		sys.exit(1)
except ImportError:
	if config.language is not "EN":
		try:
			lang = __import__("EN-lang")
		except ImportError:
			print("Language file not found.")
			sys.exit(1)
	else:
		print("Language file not found.")
		sys.exit(1)

import sys
import time
import subprocess
import urllib

from optparse import OptionParser

try:
	from naoqi import ALProxy
	from naoqi import ALBroker
	from naoqi import ALModule
	import qi
except:
	print("NAOqi Python SDK not found, quitting...")
	sys.exit(1)

session = qi.Session()
memory = None

class CorMenuModule(ALModule):

	menuVal = 0
	menu = ["init","disconnect","activateWiFi","deactivateWiFi","autonomousLifeToggle","changeOffsetFromFloor","changeVolume","status","fastReboot","close"]
	menuLang = ["", lang.Disconnect, lang.WiFiOn, lang.WiFiOff, lang.AutoLifeToggle, lang.ChangeOffsetFloor, lang.ChangeVolume, lang.Status, lang.FastReboot, lang.Close]
	
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
			self.sys = ALProxy("ALSystem")
		except:
			self.logger.warn("ALSystem is not available")
			self.sys = None
			
		try:
			self.touch = ALProxy("ALTouch")
		except:
			self.logger.warn("ALTouch is not available")
			self.touch = None
			
		try:
			self.connectionManager = ALProxy("ALConnectionManager", config.Nao_IP, config.Nao_Port)
		except:
			self.logger.warn("ALConnectionManager is not available")
			self.connectionManager = None
		
		try:
			self.postureProxy = ALProxy("ALRobotPosture")
		except:
			self.logger.warn("ALRobotPosture is not available")
			self.postureProxy = None
			
		try:
			self.audio = ALProxy("ALAudioPlayer")
		except:
			self.logger.warn("ALAudioPlayer is not avaiable")
			self.audio = None
			
		try:
			self.audioDev = ALProxy("ALAudioDevice")
		except:
			self.logger.warn("ALAudioDevice is not avaiable")
			self.audioDev = None
			
		
			
		global memory
		memory = ALProxy("ALMemory")
		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
			
		if lang.LanguageName not in self.tts.getAvailableLanguages():
			self.logger.error("Language not installed on Nao, please install it.")
			sys.exit(1)
	
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
			self.tts.say(lang.ChorDiscSucc)
		elif removed == 0:
			self.tts.say(lang.ChorDiscFail)
		else:
			self.tts.say(lang.ChorDiscError)
		
	def onTripleChest(self, *_args):
		global memory
		
		self.beforeVolume = self.audioDev.getOutputVolume()
		self.audioDev.setOutputVolume(100)
		if self.audioDev.isAudioOutMuted():
			self.audioMute = True
			self.audioDev.muteAudioOut(False)
		else:
			self.audioMute = False
		
		memory.unsubscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName())
		
		self.language = self.tts.getLanguage()
		self.tts.setLanguage(lang.LanguageName)
		
		
		self.audio.playFile("/usr/share/naoqi/wav/bip_gentle.wav")
		if config.Intro:
			self.tts.say(lang.Welcome1)
			self.tts.say(lang.Welcome2)
		
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
		
		self.tts.say(lang.OffsetChange %(self.offset))
		
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
		self.tts.say(lang.OffsetSet %(self.offset))
		
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
			self.tts.say(lang.OffsetChange %(self.offset))
		else:
			self.tts.say(lang.OffsetChangeFail)
			
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontOffset")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleOffset")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearOffset")
	
	def onFrontVolume(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		self.volume += 1
		
		self.tts.say(lang.VolumeChange %(self.volume))
		
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontVolume")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleVolume")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearVolume")
		
	def onMiddleVolume(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		self.audioDev.setOutputVolume(self.volume)
		self.beforeVolume = self.volume
		self.tts.say(lang.VolumeSet %(self.volume))
		self.audioMute = False
		
		self.close()
	
	def onRearVolume(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())
		
		if self.volume > 0:
			self.volume -= 1
			self.tts.say(lang.VolumeChange %(self.volume))
		else:
			self.tts.say(lang.VolumeChangeFail)
			
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontVolume")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleVolume")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearVolume")
	
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
			self.tts.say(lang.UnknownError)
		
		self.tts.say(lang.MainMenuChange %(self.menuLang[self.menuVal]))
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
		
		flag_Break = False
		while True:
			status = self.touch.getStatus()
			for value in status:
				if value[0] == "MiddleTactilTouched":
					if value[1]:
						time.sleep(0.001)
					else:
						flag_Break = True
			if flag_Break:
				break
		
		if self.menu[self.menuVal] == "init":
			#
			self.audio.playFile("/usr/share/naoqi/wav/fall_jpj.wav")
			self.tts.say(lang.NothingSelected)
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
			#flag_Return = True
			self.volume = self.audioDev.getOutputVolume()
			self.changeVolume()
		elif self.menu[self.menuVal] == "fastReboot":
			self.fastReboot()
		elif self.menu[self.menuVal] == "close":
			self.close()
		else:
			self.tts.say(lang.UnknownError)
		
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
		
		self.tts.say(lang.MainMenuChange %(self.menuLang[self.menuVal]))
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
			self.tts.say(lang.WiFiError)
			return
		if not self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.setCountry(wifiCountry)
			self.connectionManager.enableTethering("wifi", tetheringSSID, tetheringPassword)
			self.tts.say(lang.WifiActivated)
		else:
			self.tts.say(lang.WifiAlreadyActive)
			
	def deactivateWiFi(self):
		if self.connectionManager is None:
			self.tts.say(lang.WiFiError)
			return
		if self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.disableTethering("wifi")
			self.tts.say(lang.WifiDeactivated)
		else:
			self.tts.say(lang.WifiAlreadyInactive)
		
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
			naoName = lang.VirtualRobotName
		
		self.tts.say(lang.Name %(naoName))
		
		batteryCharge = memory.getData("Device/SubDeviceList/Battery/Charge/Sensor/Value")
		self.tts.say(lang.Battery %(batteryCharge*100))
		
		autoLifeStatus = self.autoLife.getState()
		if autoLifeStatus == "solitary":
			autoLifeStatus = lang.AutoSolitary
		elif autoLifeStatus == "interactive":
			autoLifeStatus = lang.AutoInteractive
		elif autoLifeStatus == "disabled":
			autoLifeStatus = lang.AutoDisabled
		elif autoLifeStatus == "safeguard":
			autoLifeStatus = lang.AutoSafeGuard
		self.tts.say(lang.Autonomous %(autoLifeStatus))
		
		if(self.connectionManager.getTetheringEnable("wifi")):
			self.tts.say(lang.WifiActive)
			
			if Say_SSID:
				ssid = self.connectionManager.tetheringName()
				checkSsid = ""
				if Spell_SSID:
					for char in ssid:
						try:
							int(char)
							integer = True
						except:
							integer = False
						if integer:
							checkSsid += " %s " %(char)
						else:
							if char.isupper():
								checkSsid += lang.UpperLetter %(char)
							else:
								checkSsid += lang.LowerLetter %(char)
				else:
					checkSsid = ssid
				self.tts.say(lang.WifiSSID %(checkSsid))
			
			if Say_Passowrd:
				password = self.connectionManager.tetheringPassphrase()
				checkPassword = ""
				if Spell_Password:
					for char in password:
						try:
							int(char)
							integer = True
						except:
							integer = False
						if integer:
							checkSsid += " %s " %(char)
						else:
							if char.isupper():
								checkPassword += lang.UpperLetter %(char)
							else:
								checkPassword += lang.LowerLetter %(char)
				else:
					checkPassword = password
				self.tts.say(lang.WifiPassword %(checkPassword))
		else:
			self.tts.say(lang.WifiInactive)
		
		try:
			urllib.urlopen('http://www.google.com', timeout=1)
			self.tts.say(lang.InternetOn)
		except: 
			self.tts.say(lang.InternetOff)
		
		"""
		ipv4
		state
		type
		autoconnect
		security
		strenght
		error
		"""
		
	def changeVolume(self):
		self.tts.say("Not supported yet")
		
	def autonomousLifeToggle(self):
		lifeState = self.autoLife.getState()
		if lifeState == "solitary" or lifeState == "interactive":
			self.autoLife.setState("disabled")
		elif lifeState == "safeguard":
			self.postureProxy.setMaxTryNumber(3)
			result = self.postureProxy.goToPosture("Stand", 80)
			
			if not result:
				self.tts.say(lang.Surrdender)
		else:
			self.autoLife.setState("solitary")
		
	def fastReboot(self):
		self.motion.rest()
		self.tts.say(lang.Reboot)
		proc = subprocess.Popen(["nao restart"], stdout=subprocess.PIPE)
		
	def close(self):
		global memory
		self.tts.setLanguage(self.language)
		self.menuVal = 0
		if self.audioDev.getOutputVolume() == 100:
			self.audioDev.setOutputVolume(self.beforeVolume)
		self.audioDev.muteAudioOut(self.audioMute)
		
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
		pip=config.Nao_IP,
		pport=config.Nao_Port)

	(opts, args_) = parser.parse_args()
	pip   = opts.pip
	pport = opts.pport
	
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
		CorMenu.unload()
		myBroker.shutdown()
		sys.exit(0)
	except Exception as exception:
		CorMenu.unload()
		myBroker.shutdown()
		print (exception)
		sys.exit(1)

if __name__ == "__main__":
	main()
