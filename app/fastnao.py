#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
#  ______        _   _   _          ____
# |  ____|      | | | \ | |   /\   / __ \
# | |__ __ _ ___| |_|  \| |  /  \ | |  | |
# |  __/ _` / __| __| . ` | / /\ \| |  | |
# | | | (_| \__ \ |_| |\  |/ ____ \ |__| |
# |_|  \__,_|___/\__|_| \_/_/    \_\____/

__author__ = 'Fabrimat'
__license__ = 'Apache License 2.0'
__version__ = '0.10.4'

print("""
FastNAO v%s started!
Author: %s
License: %s
"""%(__version__,__author__,__license__))

confVer = "0.3.5"

import sys
import time
import subprocess
import socket
import os
import json
import urllib2

try:
	from inc import config
	if config.Config_Version != confVer:
		print("Configuration file not valid. Please update it.")
		sys.exit(1)
except ImportError:
	print("Configuration file not found.")
	sys.exit(1)

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
scriptDir = os.path.dirname(os.path.realpath(__file__)) + "/"
FastNAO = None
lang = None
newVersionFound = False

def checkInternet(host=config.Internet_Check_IP, port=config.Internet_Check_Port, timeout=config.Internet_Check_TimeOut):
	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except:
		return False

def checkNewVersion():
	if(config.Check_New_Version == True and checkInternet()):
		try:
			j = urllib2.urlopen("http://www.fabrimat.me/api/fastnao/release.php")
		except:
			return False
		j_obj = json.load(j)
		if(j_obj['tag_name'] != 'v' + __version__):
			if(j_obj['prerelease'] == "true"):
				if(config.Allow_PreReleases == True):
					return j_obj['html_url']
			else:
				return j_obj['html_url']
	return False

class Menu:
	global lang

	indexValue = 3

	def __init__(self, name):
		self._menu = {
			"00.init":lang.NothingSelected,
		}

		if(config.Disconnect_Module):
			self._menu.update({"01.disconnect":lang.Disconnect})
		if(config.WiFi_On_Module):
			self._menu.update({"02.activateWiFi":lang.WiFiOn})
		if(config.WiFi_Off_Module):
			self._menu.update({"03.deactivateWiFi":lang.WiFiOff})
		if(config.AutonomousLife_Module):
			self._menu.update({"04.autonomousLifeToggle":lang.AutoLifeToggle})
		if(config.OffsetFromFloor_Module):
			self._menu.update({"05.changeOffsetFromFloor":lang.ChangeOffsetFloor})
		if(config.Volume_Module):
			self._menu.update({"06.changeVolume":lang.ChangeVolume})
		if(config.Status_Module):
			self._menu.update({"07.status":lang.Status})
		#if(config.Reboot_Module):
		#	self._menu.update({"08.fastReboot":lang.FastReboot})

		self._menu.update({"99.close":lang.Close})

		self._menuKeys = sorted(self._menu.iterkeys())
		self._menuVal = 0
		self._menuLen = len(self._menu)
		self._menuSelected = False
		self._name = name

	def getActionKey(self):
		return self._menuKeys[self._menuVal][self.indexValue:]

	def incrementAction(self):
		if self._menuVal >= self._menuLen-1:
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
		self._menuSelected = self._menuKeys[self._menuVal]

	def getSelectedKey(self):
		if (self._menuSelected == False):
			return self._menuSelected
		return self._menuSelected[self.indexValue:]

	def getSelectedLang(self):
		if self._menuSelected:
			return self._menu[self._menuSelected]
		else:
			self._menu["init"]

class Volume:
	def __init__(self, name, module, defaultDifference = 10):
		self._name = name
		self._difference = defaultDifference
		self._module = module
		self.setDefaultVolume()

	def setDefaultVolume(self):
		self._defaultVolume = self._module.getOutputVolume()
		self._defaultMuted = self._module.isAudioOutMuted()
		self._volume = self._defaultVolume
		self._muted = self._defaultMuted

	def setDefaultVolumeRunTime(self, volume):
		self._defaultVolume = volume
		self._volume = volume
		if (volume > 0):
			self._defaultMuted = False
			self._muted = False
		else:
			self._defaultMuted = True
			self._muted = True

	def volumeOn(self, value=config.Default_Volume):
		self.setDefaultVolume()
		self._module.muteAudioOut(False)
		self._module.setOutputVolume(value)

	def volumeOff(self):
		self.setDefaultVolume()
		self._module.muteAudioOut(True)

	def volumeReset(self):
		self._module.muteAudioOut(self._defaultMuted)
		self._module.setOutputVolume(self._defaultVolume)

	def incrementVolume(self, value=None):
		if(value == None):
			value=self._difference
		if self._volume < 100-value:
			self._volume += value
		else:
			self._volume = 100
		self._module.setOutputVolume(self._volume)
		self.setDefaultVolumeRunTime(self._volume)

	def getVolume(self):
		return self._volume

	def setVolume(self):
		self._module.muteAudioOut(False)
		self._module.setOutputVolume(self._volume)
		self.setDefaultVolumeRunTime(self._volume)

	def decrementVolume(self, value=None):
		if(value == None):
			value=self._difference
		if self._volume > 0+value:
			self._volume -= value
		else:
			self._volume = 0
		self._module.setOutputVolume(self._volume)
		self.setDefaultVolumeRunTime(self._volume)

	def getName(self):
		return self._name

	def setName(self, name):
		self._name = name

class RobotOffsetFromFloor:
	def __init__(self, name, module, defaultDifference = 1):
		self._name = name
		self._difference = defaultDifference
		self._module = module
		self.setDefaultOffset()

	def setDefaultOffset(self):
		self._defaultOffsetFromFloor = self._module.getRobotOffsetFromFloor()
		self._offsetFromFloor = self._defaultOffsetFromFloor

	def resetOffset(self):
		self._module.setRobotOffsetFromFloor(self._defaultOffsetFromFloor)

	def incrementOffset(self, value=None):
		if(value == None):
			value=self._difference
		self._offsetFromFloor += value

	def decrementOffset(self, value=None):
		if(value == None):
			value=self._difference
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

class Language:
	dir = "inc/lang/"

	def __init__(self, name, module):
		self._name = name
		self._module = module
		self.setDefaultLanguage()
		self.importLanguage()

	def supportedLanguages(self):
		locales = []
		langFiles = []

		i = 0
		for filename in os.listdir(scriptDir + self.dir):
			if filename.endswith("-lang.py"):
				(locale, file) = filename.split("-")
				try:
					langFiles.append(__import__("%s%s-lang" %(self.dir.replace("/","."),locale), fromlist=["%s-lang" %(locale)]))
					print(__import__("%s%s-lang" %(self.dir.replace("/","."),locale), fromlist=["%s-lang" %(locale)]))
				except ImportError:
					print("Error importing language file.")
				locales.append(locale)
				i+=1
		return locales, langFiles

	def importLanguage(self):
		global lang
		if config.Language == "default":
			locale = self._module.locale()
			supported = self.supportedLanguages()
			if locale in supported[0]:
				i = 0
				for langCode in supported[0]:
					if locale == langCode:
						lang = supported[1][i]
					i+=1
			else:
				try:
					lang = __import__("%sen_US-lang" %(self.dir.replace("/",".")))
				except ImportError:
					print("Error importing language file.")
					return False
		if lang.Config_Version != confVer:
			print("Language file not valid. Please report the error.")
			return False
		return True

	def setDefaultLanguage(self, defaultLang = ""):
		if (defaultLang == ""):
			defaultLang = self._module.getLanguage()
		self._defaultLanguage = defaultLang
		self._language = self._defaultLanguage

	def languageReset(self):
		self._module.setLanguage(self._defaultLanguage)

	def getlanguage(self):
		return self._language

	def setLanguage(self, language = ""):
		if (language == ""):
			global lang
			language = lang.LanguageName
		self._module.setLanguage(language)

	def getName(self):
		return self._name

	def setName(self, name):
		self._name = name

class FastNaoModule(ALModule):

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
			warnLevel = 1

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



		self._language = Language(name, self.tts)
		global lang
		if lang.LanguageName not in self.tts.getAvailableLanguages():
			self.logger.error("Language not installed on Nao, please install it.")
			sys.exit(1)

		if warnLevel > 0:
			sys.exit(1)
		if not config.Silent_Bootup:
			self.tts.say(lang.Enabled)
		else:
			self.notification.add({"message": lang.Enabled, "severity": "info", "removeOnRead": True})

		self._menu = Menu(name)
		self._volume = Volume(name, self.audioDev, config.Volume_Difference)
		self._offset = RobotOffsetFromFloor(name, self.autoLife, config.Offset_From_Floor_Difference)

		if(checkNewVersion() != False):
			self.notification.add({"message": lang.NewVersion, "severity": "info", "removeOnRead": True})
		
		self.robotVersion = self.sys.systemVersion()
			
		self.checkDisk(self.robotVersion)

		global memory
		memory = ALProxy("ALMemory")

		memory.declareEvent("KillFastNAO")

		memory.subscribeToEvent("KillFastNAO",
			self.getName(),
			"unload")

		memory.subscribeToEvent("ALChestButton/TripleClickOccurred",
			self.getName(),
			"onTripleChest")

	def checkDisk(self, version):
		""" Return occupied disk percentage """
		disk = self.sys.diskFree(False)
		percent = disk[0][3][1]*100/disk[0][2][1]
		if version.startswith("2.1"):
			if percent > 90:
				self.notification.add({"message": lang.DiskFull, "severity": "warning", "removeOnRead": True})
		elif version.startswith("2.8"):
			if percent < 10:
				self.notification.add({"message": lang.DiskFull, "severity": "warning", "removeOnRead": True})
		else:
			self.logger.error("Can't get disk space. Nao version not supported!")

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
		""" Start/stop the menu """
		if self.isFastNaoRunning:
			self.stop()
		else:
			self.startMenu()

	def startMenu(self):
		self.isFastNaoRunning = True
		self._volume.volumeOn()

		self.language = self.tts.getLanguage()
		self._language.setLanguage()

		self.audio.playFile(scriptDir + "inc/wav/bip_gentle.wav")
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
			self.tts.say(lang.MainMenuChange %(self._menu.getActionLang()))
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

		shouldClose = True
		if not self._menu.getSelectedKey():
			self._menu.setSelected()
			shouldClose = self._actionChooser()
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

		if (shouldClose):
			return

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
			self.tts.say(lang.MainMenuChange %(self._menu.getActionLang()))
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
		key = self._menu.getSelectedKey()
		if key == "init":
			self.audio.playFile(scriptDir + "inc/wav/fall_jpj.wav")
			self.tts.say(lang.NothingSelected)
			self.stop()
			return
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
			self.tts.say(lang.ChooseOffset)
			return False
		elif key == "changeVolume":
			self._volume.setDefaultVolume()
			self.tts.say(lang.ChooseVolume)
			return False
		elif key == "fastReboot":
			self.fastReboot()
		elif key == "close":
			self.stop()
		else:
			self.tts.say(lang.UnknownError)

		return True

	def activateWiFi(self):
		if self.connectionManager is None:
			self.tts.say(lang.WiFiError)
			return
		if not self.connectionManager.getTetheringEnable("wifi"):
			try:
				self.connectionManager.enableTethering("wifi", config.Tethering_SSID.replace("[name]", self.sys.robotName()), config.Tethering_Password)
			except Exception as e:
				print(e)
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
		realNotVirtual = os.path.exists("/home/nao")

		if realNotVirtual:
			robotName = socket.gethostname()
			naoName = robotName
		else:
			naoName = lang.VirtualRobotName

		self.tts.say(lang.Name %(naoName))
		
		if realNotVirtual:
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

			if config.Say_SSID:
				ssid = self.connectionManager.tetheringName("wifi")
				checkSsid = ""
				if config.Spell_SSID:
					for char in ssid:
						try:
							int(char)
							integer = True
						except ValueError:
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

			if config.Say_Passowrd:
				password = self.connectionManager.tetheringPassphrase("wifi")
				checkPassword = ""
				if config.Spell_Password:
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
		self._language.languageReset()
		self._menu.reset()
		self._offset.resetOffset()
		self._volume.volumeReset()

	def unload(self):
		self.stop()
		events = ["MiddleTactilTouched","FrontTactilTouched","RearTactilTouched","ALChestButton/TripleClickOccurred"]
		for event in events:
			for sub in memory.getSubscribers(event):
				if sub == self.getName():
					memory.unsubscribeToEvent(event,
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

	update = checkNewVersion()
	if(update != False):
		print update
		time.sleep(1)

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
