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
			'allowLocationLinks'    : False,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'
		super().__init__(data)


	def getDeviceIcon(self) -> Path:
		if not self.connected:
			return Path(f"{self._imagePath}Switches/switch_offline.png")

		if self.getParam(key='state') == 'on':
			return Path(f"{self._imagePath}Switches/switch_on.png")

		elif self.getParam(key='state') == 'off':
			return Path(f"{self._imagePath}Switches/switch_off.png")

		else:
			return Path(f"{self._imagePath}Switches/HAswitch.png")


	def onUIClick(self):

		if self.getParam(key='state') == "on":
			self.updateParams(key='state', value='off')
			self.updateStateOfDevice()
			return

		if self.getParam(key='state') == "off":
			self.updateParams(key='state', value='on')
			self.updateStateOfDevice()
			return

		if self.getParam(key='state') == "unavailable":
			self.logInfo(f"Sorry but device is currently unavailable. Is it connected ? connected to network ?")


	def updateStateOfDevice(self):
		haClass = HomeAssistant()
		haClass.deviceClicked(uid=self.uid)
