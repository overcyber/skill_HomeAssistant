import sqlite3
from pathlib import Path

from core.device.model.Device import Device
from core.device.model.DeviceAbility import DeviceAbility


class HAlightSensor(Device):
	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAlightSensor',
			'perLocationLimit'      : 0,
			'totalDeviceLimit'      : 0,
			'allowLocationLinks'    : False,
			'allowHeartbeatOverride': False,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		super().__init__(data)
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'


	def getDeviceIcon(self) -> Path:
		if not self.uid:
			return Path(f'{self._imagePath}Lights/HAlightSensor.png')

		if not self.connected:
			return Path(f'{self._imagePath}Lights/haLightSensorOff.png')

		return Path(f'{self._imagePath}Lights/haLightSensorOn.png')


	def toggle(self, device: Device):
		# todo add light sensor trigger
		pass
