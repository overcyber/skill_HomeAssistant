import sqlite3
from typing import Optional

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
			'allowLocationLinks'    : True,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'
		super().__init__(data)


	def getDeviceIcon(self, path: Optional[Path] = None) -> Path:
		if self.connected:
			icon = Path(f'{self._imagePath}GeneralSensors/HAmotion.png')
		else:
			icon = Path(f'{self._imagePath}GeneralSensors/HAsensorOffline.png')

		return super().getDeviceIcon(icon)


	def onUIClick(self):
		location = self.LocationManager.getLocationName(self.parentLocation)

		answer = f"The {location} motion sensor currently reads {self.getParam('state')}"
		self.MqttManager.say(text=answer)
		return super().onUIClick()
