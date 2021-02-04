import sqlite3

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility


class HAlight(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAlight',
			'perLocationLimit'      : 0,
			'totalDeviceLimit'      : 0,
			'allowLocationLinks'    : False,
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
		self.logDebug(f'Currently there\'s no toggle event available for this light controller')
		return super().onUIClick()
