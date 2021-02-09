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

		if self.getParam(key='state') == "on":
			self.updateParams(key='state', value='off')
			self.updateStateOfDeviceInHA()

		elif self.getParam(key='state') == "off":
			self.updateParams(key='state', value='on')
			self.updateStateOfDeviceInHA()

		else:
			self.logInfo("Sorry but it appears that switch is currently unavailable")

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
