import sqlite3

from core.device.model.Device import Device
from core.device.model.DeviceType import DeviceType
from core.util.model.TelemetryType import TelemetryType
from skills.HomeAssistant.HomeAssistant import HomeAssistant

class HaSensor(DeviceType):

	def __init__(self, data: sqlite3.Row):
		super().__init__(data, devSettings=self.DEV_SETTINGS, locSettings=self.LOC_SETTINGS, heartbeatRate=500)

		self._telemetryUnits = {
			'airQuality'   : '%',
			'co2'          : 'ppm',
			'gas'          : 'ppm',
			'gust_angle'   : '°',
			'gust_strength': 'km/h',
			'humidity'     : '%',
			'light'        : 'lux',
			'pressure'     : 'mb',
			'rain'         : 'mm',
			'temperature'  : '°C',
			'wind_angle'   : '°',
			'wind_strength': 'km/h'
		}

	def getDeviceIcon(self, device: Device) -> str:
		#if not device.uid:
		#	return 'HaSensor.png'
		if not device.connected:
			return 'hot.png'
		return 'connectedTemp.png'


	def toggle(self, device: Device):
		haClass =  HomeAssistant()
		deviceType = haClass.getHADeviceType(uID=device.uid)

		telemetryType = deviceType['deviceType']
		locations = [self.LocationManager.getLocation(locId=device.locationID)]

		self.SensorClicked(telemetryType, locations)

	def SensorClicked(self, telemetryType: str, locations: list):
		data = self.TelemetryManager.getData(ttype=TelemetryType(telemetryType), location=locations[0])

		if data and 'value' in data.keys():
			answer = f"The {locations[0].name} {telemetryType} is {data['value']} {self._telemetryUnits.get(telemetryType, '')}"
			self.MqttManager.say(text=answer)
