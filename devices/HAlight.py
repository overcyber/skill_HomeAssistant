import sqlite3
from typing import Optional

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility
from skills.HomeAssistant.HomeAssistant import HomeAssistant


class HAlight(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAlight',
			'perLocationLimit'      : 0,
			'totalDeviceLimit'      : 0,
			'allowLocationLinks'    : True,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		super().__init__(data)
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'


	def getDeviceIcon(self, path: Optional[Path] = None) -> Path:

		if self.getParam(key='state') == 'on':
			icon = Path(f'{self._imagePath}Lights/lightOn.png')
		else:
			icon = Path(f'{self._imagePath}Lights/lightOff.png')

		return super().getDeviceIcon(icon)


	def onUIClick(self):
		if self.getParam(key='state') == "on":
			self.updateParam(key='state', value='off')
			self.updateStateOfDeviceInHA()

		elif self.getParam(key='state') == "off":
			self.updateParam(key='state', value='on')
			self.updateStateOfDeviceInHA()

		else:
			self.logInfo(f"Sorry but that light is currently not available")

		return super().onUIClick()

	def updateStateOfDeviceInHA(self):
		""" Sends uid to HomeAssistant skill which then sends the command over
			API to HomeAssistant to turn on or off the device
		"""
		haClass = HomeAssistant()
		haClass.deviceClicked(uid=self.uid)
