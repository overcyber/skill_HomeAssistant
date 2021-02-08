import sqlite3

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


	def getDeviceIcon(self) -> Path:

		if self.getParam(key='state') == "on":
			return Path(f'{self._imagePath}Lights/lightOn.png')

		elif self.getParam(key='state') == "off":
			return Path(f'{self._imagePath}Lights/lightOff.png')

		else:
			return Path(f'{self._imagePath}Lights/lightOff.png')


	def onUIClick(self):
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
		return super().onUIClick()

	def updateStateOfDeviceInHA(self):
		""" Sends uid to HomeAssistant skill which then sends the command over
			API to HomeAssistant to turn on or off the device
		"""
		haClass = HomeAssistant()
		haClass.deviceClicked(uid=self.uid)
