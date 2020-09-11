import sqlite3

from core.device.model.Device import Device
from core.device.model.DeviceType import DeviceType


class HaSensor(DeviceType):

	def __init__(self, data: sqlite3.Row):
		super().__init__(data, devSettings=self.DEV_SETTINGS, locSettings=self.LOC_SETTINGS, heartbeatRate=500)


	def getDeviceIcon(self, device: Device) -> str:
		if not device.uid:
			return 'HaSensor.png'
		if not device.connected:
			return 'hot.png'
		return 'connectedTemp.png'


	def toggle(self, device: Device):
		#todo probably report the temperature here one day
		pass

