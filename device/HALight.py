import sqlite3

from core.device.model.Device import Device
from core.device.model.DeviceType import DeviceType


class HALight(DeviceType):

	def __init__(self, data: sqlite3.Row):
		super().__init__(data, devSettings=self.DEV_SETTINGS, locSettings=self.LOC_SETTINGS, heartbeatRate=500, internalOnly=True)



	def getDeviceIcon(self, device: Device) -> str:

		if not device.id:
			return 'HaLight.png'
		if not device.connected or not device.getCustomValue('state'):
			return 'HaLight_Offline.png'
		if 'on' in device.getCustomValue('state'):
			return 'HaLight_On.png'
		elif 'off' in device.getCustomValue('state'):
			return 'HaLight_Off.png'
		else:
			return 'HaLight_Offline.png'


	def toggle(self, device: Device):
		self.logDebug(f'Currently there\'s no toggle event available for this light controller' )

