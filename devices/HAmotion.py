import sqlite3

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility


class HAmotion(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAmotion',
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
		if self.connected:
			return Path(f'{self._imagePath}GeneralSensors/HAmotion.png')

		return Path(f'{self._imagePath}HAsensorOffline.png')


	def onUIClick(self):
		location = self.LocationManager.getLocationName(self.parentLocation)

		answer = f"The {location} motion sensor currently reads {self.getParam('state')}"
		self.MqttManager.say(text=answer)
