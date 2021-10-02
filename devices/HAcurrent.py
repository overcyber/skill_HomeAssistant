import sqlite3
from typing import Optional

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility


class HAcurrent(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAcurrent',
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
		return super().getDeviceIcon(Path(f'{self._imagePath}GeneralSensors/HAcurrent.png'))


	def onUIClick(self):

		answer = f"The {self.displayName} is drawing {self.getParam('state')} amps"
		self.MqttManager.say(text=answer)
		return super().onUIClick()
