import sqlite3

from core.device.model.Device import Device
from core.device.model.DeviceType import DeviceType
from core.util.model.TelemetryType import TelemetryType
from skills.HomeAssistant.HomeAssistant import HomeAssistant

class HALightSensor(DeviceType):

	def __init__(self, data: sqlite3.Row):
		super().__init__(data, devSettings=self.DEV_SETTINGS, locSettings=self.LOC_SETTINGS, heartbeatRate=500)



	def getDeviceIcon(self, device: Device) -> str:
		#if not device.uid:
		#	return 'haLightSensor.png'
		if not device.connected:
			return 'haLightSensorOff.png'
		return 'haLightSensorOn.png'


	def toggle(self, device: Device):
		#todo add light sensor trigger
		pass
