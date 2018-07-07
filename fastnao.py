#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.9'

print("""
FastNAO v%s started!
Author: %s
License: %s
"""%(__version__,__author__,__license__))

confVer = 0.3

try:
	import config
	if config.Config_Version != confVer:
		print("Configuration file not valid. Please update it.")
		sys.exit(1)
except ImportError:
	print("Configuration file not found.")

try:
	lang = __import__("%s-lang" %(config.Language))
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

if lang.Config_Version != confVer:
	print("Language file not valid. Please update it.")
	sys.exit(1)

import sys
import time
import subprocess
import socket

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

def checkInternet(host=config.Internet_Check_IP, port=config.Internet_Check_Port, timeout=config.Internet_Check_TimeOut):
	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except:
		return False

class FastNaoModule(ALModule):

	class Menu:
		_menu = {
			"init":lang.NothingSelected,
			"disconnect":lang.Disconnect,
			"activateWiFi":lang.WiFiOn,
			"deactivateWiFi":lang.WiFiOff,
			"autonomousLifeToggle":lang.AutoLifeToggle,
			"changeOffsetFromFloor":lang.ChangeOffsetFloor,
			"changeVolume":lang.ChangeVolume,
			"status":lang.Status,
			"fastReboot":lang.FastReboot,
			"close":lang.Close,
		}
		_menukeys = list(_menu.keys())
		_menuVal = 0
		_menuLen = len(_menu)
		_menuSelected = False

		def __init__(self, name):
			self._name = name

		def getActionKey(self):
			return self._menukeys[self._menuVal]

		def incrementAction(self):
			if self._menuVal >= self._menuLen:
				self._menuVal = 1
				return False
			else:
				self._menuVal += 1
				return True

		def decrementAction(self):
			if self._menuVal <= 1:
				self._menuVal = self._menuLen -1
				return False
			else:
				self._menuVal -= 1
				return True

		def getActionLang(self):
			return self._menu[self._menuKeys[self._menuVal]]

		def reset(self):
			self._menuVal = 0
			self._menuSelected = False

		def getName(self):
			return self._name

		def setName(self, name):
			self._name = name

		def setSelected(self):
			self._menuSelected = self._menukeys[self._menuVal]

		def getSelectedKey(self):
			return self._menuSelected

		def getSelectedLang(self):
			if self._menuSelected:
				return self._menu[self._menuSelected]
			else:
				self._menu["init"]

	class Volume:

		def __init__(self, name, module, defalutDifference = 10):
			self._name = name
			self._difference = defalutDifference
			self._module = module
			self.setDefaultVolume()

		def setDefaultVolume(self):
			self._defaultVolume = self._module.getOutputVolume()
			self._defaultMuted = self._module.isAudioOutMuted()
			self._volume = self._defaultVolume
			self._muted = self._defaultMuted

		def volumeOn(self, value=100):
			self.setDefaultVolume()
			self._module.muteAudioOut(False)
			self._module.setOutputVolume(value)

		def volumeOff(self):
			self.setDefaultVolume()
			self._module.muteAudioOut(True)

		def volumeReset(self):
			self._module.muteAudioOut(self._defaultMuted)
			self._module.setOutputVolume(self._defaultVolume)

		def incrementVolume(self, value=self._difference):
			if self._volume < 100-value:
				self._volume += value
			else:
				self._volume = 100

		def getVolume(self):
			return self._volume

		def setVolume(self):
			self._module.muteAudioOut(False)
			self._module.setOutputVolume(self._volume)

		def decrementVolume(self, value=self._difference):
			if self._volume > 0+value:
				self._volume -= value
			else:
				self._volume = 0

		def getName(self):
			return self._name

		def setName(self, name):
			self._name = name

	class RobotOffsetFromFloor:

		def __init__(self, name, module, defalutDifference = 1):
			self._name = name
			self._difference = defalutDifference
			self._module = module
			self.setDefaultOffset()

		def setDefaultOffset():
			self._defaultOffsetFromFloor = self._module.getRobotOffsetFromFloor()
			self._offsetFromFloor = self._defaultOffsetFromFloor

		def resetOffset(self):
			self._module.setRobotOffsetFromFloor(self._defaultOffsetFromFloor)

		def incrementOffset(self, value=self._difference):
			self._offsetFromFloor += value

		def decrementOffset(self, value=self._difference):
			if self._offsetFromFloor > 0+value:
				self._offsetFromFloor -= value
			else:
				self._offsetFromFloor = 0

		def setOffset(self):
			self._module.setRobotOffsetFromFloor(self._offsetFromFloor)

		def getOffset(self):
			return self._offsetFromFloor

		def getName(self):
			return self._name

		def setName(self, name):
			self._name = name

	def __init__(self, name):
		ALModule.__init__(self, name)

		self.isFastNaoRunning = False

		warnLevel = 0

		try:
			self.motion = ALProxy("ALMotion")
		except:
			self.logger.warn("ALMotion is not available")
			self.motion = None
			warnLevel = 1

		try:
			self.autoLife = ALProxy("ALAutonomousLife")
		except:
			self.logger.warn("ALAutonomousLife is not available")
			self.autoLife = None
			warnLevel = 1

		try:
			self.tts = ALProxy("ALTextToSpeech")
		except:
			self.logger.warn("ALTextToSpeech is not available")
			self.tts = None
			warnLevel = 2

		try:
			self.sys = ALProxy("ALSystem")
		except:
			self.logger.warn("ALSystem is not available")
			self.sys = None
			warnLevel = 1

		try:
			self.touch = ALProxy("ALTouch")
		except:
			self.logger.warn("ALTouch is not available")
			self.touch = None
			warnLevel = 1

		try:
			self.connectionManager = ALProxy("ALConnectionManager", \
				config.Nao_IP, config.Nao_Port)
		except:
			self.logger.warn("ALConnectionManager is not available")
			self.connectionManager = None
			warnLevel = 1

		try:
			self.postureProxy = ALProxy("ALRobotPosture")
		except:
			self.logger.warn("ALRobotPosture is not available")
			self.postureProxy = None
			warnLevel = 1

		try:
			self.audio = ALProxy("ALAudioPlayer")
		except:
			self.logger.warn("ALAudioPlayer is not avaiable")
			self.audio = None
			warnLevel = 1

		try:
			self.audioDev = ALProxy("ALAudioDevice")
		except:
			self.logger.warn("ALAudioDevice is not avaiable")
			self.audioDev = None
			warnLevel = 1

		try:
			self.notification = ALProxy("ALNotificationManager")
		except:
			self.logger.warn("ALNotificationManager is not avaiable")
			self.notification = None
			warnLevel = 1

		if lang.LanguageName not in self.tts.getAvailableLanguages():
			self.logger.error("Language not installed on Nao, please install it.")
			sys.exit(1)

		if warnLevel == 1:
			self.tts.say(lang.FailedEnabling)
		if warnLevel > 0:
			sys.exit(1)
		else:
			self.tts.say(lang.Enabled)

		self._menu = Menu(name)
		self._volume = Volume(name, self.audioDev, config.Volume_Difference)
		self._offset = RobotOffsetFromFloor(name, self.autoLife, config.Offset_From_Floor_Difference)

		global memory
		memory = ALProxy("ALMemory")

		memory.declareEvent("KillFastNAO")

		memory.subscribeToEvent("KillFastNAO",
			self.getName(),
			"unload")

		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")

	def checkDisk(self):
		disk = self.sys.diskFree(False)
		if disk < 10:
			self.notification.add(lang.DiskFull)
		return

	def disconnect(self):
		""" Disconnect Choregraphe forcedly """
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
		"""  """
		if self.isFastNaoRunning:
			self.stop()
		else:
			self.startMenu()

	def startMenu(self):
		self.isFastNaoRunning = True
		self._volume.volumeOn()

		self.language = self.tts.getLanguage()
		self.tts.setLanguage(lang.LanguageName)

		self.audio.playFile("/usr/share/naoqi/wav/bip_gentle.wav")
		if config.Intro:
			self.tts.say(lang.Welcome1)
			self.tts.say(lang.Welcome2)

	def onFrontHead(self, *_args):
		global memory
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())

		if not self._menu.getSelectedKey():
			self._menu.incrementAction()
			self.tts.say(lang.MainMenuChange %(self._menu.getActionLang())
		elif self._menu.getSelectedKey() == "changeOffsetFromFloor":
			self._offset.incrementOffset()
			self.tts.say(lang.OffsetChange %(self._offset.getOffset()))
		elif self._menu.getSelectedKey() == "changeVolume":
			self._volume.incrementVolume()
			self.tts.say(lang.VolumeChange %(self._volume.getVolume()))
		else:
			pass

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

		if not self._menu.getSelectedKey():
			self._menu.setSelected()
			self._actionChooser()
		elif self._menu.getSelectedKey() == "changeOffsetFromFloor":
			self._offset.setOffset()
			self.tts.say(lang.OffsetSet %(self._offset.getOffset()))
			self.stop()
		elif self._menu.getSelectedKey() == "changeVolume":
			self._volume.setVolume()
			self.tts.say(lang.VolumeSet %(self._volume.getVolume()))
			self.stop()
		else:
			pass

		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")

	def onRearHead(self, *_args):
		memory.unsubscribeToEvent("MiddleTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("FrontTactilTouched",
			self.getName())
		memory.unsubscribeToEvent("RearTactilTouched",
			self.getName())

		if not self._menu.getSelectedKey():
			self._menu.decrementAction()
			self.tts.say(lang.MainMenuChange %(self._menu.getActionLang())
		elif self._menu.getSelectedKey() == "changeOffsetFromFloor":
			self._offset.decrementOffset()
			self.tts.say(lang.OffsetChange %(self._offset.getOffset()))
		elif self._menu.getSelectedKey() == "changeVolume":
			self._volume.decrementVolume()
			self.tts.say(lang.VolumeChange %(self._volume.getVolume()))
		else:
			pass
		memory.subscribeToEvent("FrontTactilTouched",
			self.getName(),
			"onFrontHead")
		memory.subscribeToEvent("MiddleTactilTouched",
			self.getName(),
			"onMiddleHead")
		memory.subscribeToEvent("RearTactilTouched",
			self.getName(),
			"onRearHead")

	def _actionChooser(self):

		flag_Loop = True
		while flag_Loop:
			status = self.touch.getStatus()
			for value in status:
				if value[0] == "MiddleTactilTouched":
					if value[1]:
						time.sleep(0.001)
					else:
						flag_Loop = False

		key = self._menu.getSelectedKey()
		if key == "init":
			self.audio.playFile("/usr/share/naoqi/wav/fall_jpj.wav")
			self.tts.say(lang.NothingSelected)
			self.stop()
		elif key == "disconnect":
			self.disconnect()
			self.stop()
		elif key == "activateWiFi":
			self.activateWiFi()
			self.stop()
		elif key == "deactivateWiFi":
			self.deactivateWiFi()
			self.stop()
		elif key == "status":
			self.status()
			self.stop()
		elif key == "autonomousLifeToggle":
			self.autonomousLifeToggle()
			self.stop()
		elif key == "changeOffsetFromFloor":
			self._offset.resetOffset()
		elif key == "changeVolume":
			self._volume.setDefaultVolume()
		elif key == "fastReboot":
			self.fastReboot()
		elif key == "close":
			self.stop()
		else:
			self.tts.say(lang.UnknownError)

	def activateWiFi(self):
		if self.connectionManager is None:
			self.tts.say(lang.WiFiError)
			return
		if not self.connectionManager.getTetheringEnable("wifi"):
			self.connectionManager.setCountry(wifiCountry)
			self.connectionManager.enableTethering("wifi", tetheringSSID, \
				tetheringPassword)
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

		if checkInternet():
			self.tts.say(lang.InternetOn)
		else:
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
		self.unload()
		proc = subprocess.Popen(["nao restart"], stdout=subprocess.PIPE)
		sys.exit(0)

	def stop(self):
		self.isFastNaoRunning = False
		self.audio.stopAll()
		self.tts.stopAll()
		self.postureProxy.stopMove()
		self.tts.setLanguage(self.language)
		self._menu.reset()
		self._offset.resetOffset()
		self._volume.volumeReset()

	def unload(self):
		self.stop()

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

		sys.exit(0)

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

	global FastNAO
	FastNAO = FastNaoModule("FastNAO")

	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print "Interrupted by user, shutting down..."
		FastNAO.unload()
		myBroker.shutdown()
		sys.exit(0)
	except Exception as exception:
		FastNAO.unload()
		myBroker.shutdown()
		print (exception)
		sys.exit(1)

if __name__ == "__main__":
	main()
