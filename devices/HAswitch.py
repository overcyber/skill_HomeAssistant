import sqlite3
from pathlib import Path
from core.device.model.Device import Device
from skills.HomeAssistant.HomeAssistant import HomeAssistant

from core.device.model.DeviceAbility import DeviceAbility


class HAswitch(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAswitch',
			'perLocationLimit'      : 0,
			'totalDeviceLimit'      : 0,
			'allowLocationLinks'    : True,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'
		super().__init__(data)


	def getDeviceIcon(self) -> Path:
		iconPath = self.selectIconBasedOnState()

		if Path(iconPath).exists():
			return iconPath

		else:
			return Path(f"{self._imagePath}Switches/HAswitch.png")


	def onUIClick(self):
		# debug helper
		if self.ConfigManager.getSkillConfigByName(skillName='HomeAssistant', configName='debugMode'):
			self.Commons.getMethodCaller(name=self.displayName, haDeviceType=self.getParam('haDeviceType'), entity=self.getParam('entityName'), entityGroup=self.getParam('entityGroup'), state=self.getParam('state') )

		if self.getParam('entityGroup') == "input_boolean":
			self.logInfo(f"Input booleans are currently not clickable. It's on the 'todo' list.")
			return super().onUIClick()

		if self.getParam(key='state') == "on":
			self.updateParams(key='state', value='off')
			self.updateStateOfDeviceInHA()

			return super().onUIClick()

		if self.getParam(key='state') == "off":
			self.updateParams(key='state', value='on')
			self.updateStateOfDeviceInHA()
			return super().onUIClick()

		if self.getParam(key='state') == "unavailable":
			self.updateStateOfDeviceInHA()
			return super().onUIClick()


	def updateStateOfDeviceInHA(self):
		""" Sends uid to HomeAssistant skill which then sends the command over
			API to HomeAssistant to turn on or off the device
		"""
		haClass = HomeAssistant()
		haClass.deviceClicked(uid=self.uid)


	def selectIconBasedOnState(self):
		return Path(
			f"{self._imagePath}Switches/{self.getParam('entityGroup')}{str(self.getParam('state')).capitalize()}.png")
