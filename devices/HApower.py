import sqlite3

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility


class HApower(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HApower',
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
		powerType = self.uid.split('_')[-1]

		if powerType == "current":
			return Path(f'{self._imagePath}GeneralSensors/HAcurrent.png')
		elif powerType == "voltage":
			return Path(f'{self._imagePath}GeneralSensors/HAvoltage.png')
		else:
			return Path(f'{self._imagePath}HAsensorOffline.png')


	def onUIClick(self):

		answer = f"The {self.displayName} has a reading of {self.getParam('state')}"
		self.MqttManager.say(text=answer)
