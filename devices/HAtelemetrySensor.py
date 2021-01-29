import sqlite3

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility


class HAtelemetrySensor(Device):

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAtelemetrySensor',
			'perLocationLimit'      : 0,
			'totalDeviceLimit'      : 0,
			'allowLocationLinks'    : False,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'
		self._highAlert = list()
		self._lowAlert = list()

		super().__init__(data)

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


	# todo change this as this event doesnt get broadcast to this file
	def onTemperatureHighAlert(self, **kwargs):
		if "HomeAssistant" in kwargs['service']:
			areaId = self.LocationManager.getLocationByName(kwargs["area"])
			self.setAlertIcon(triggerType='temperature', value=kwargs['value'], area=areaId, high=True)


	def setAlertIcon(self, triggerType: str, value: int, area, high: bool = False, low: bool = False):
		"""
		Used for setting the device alert icon values.
		Only set either High or low to True, not both
		:param triggerType: example "temperature" or "humidity" etc.
		:param value: The device state value
		:param area: The location id of the device
		:param high: Set True if High Alert event
		:param low: set to True if its a low alaert event
		:return: adds values to a list
		"""

		if high and low:
			self.logWarning("Can't set both low and high to true")
			return

		if high:
			self._lowAlert = list()
			self._highAlert = [value, triggerType, area]
		elif low:
			self._highAlert = list()
			self._lowAlert = [value, triggerType, area]

		self.getDeviceIcon()


	def getDeviceIcon(self) -> Path:
		teleType = self.uid.split('_')[-1]

		if teleType == 'temperature':
			# todo This doesnt work Larry still has to implement it
			# CHange thermometer icon depending on temperatures from telemetry
			if self._highAlert and self.connected and self.getParam("state") >= self._highAlert[0]:
				return Path(f'{self._imagePath}Temperature/hot1.png')

			elif self._lowAlert and self.connected and self.getParam("state") <= self._lowAlert[0]:
				return Path(f'{self._imagePath}Temperature/cold1.png')

			else:
				return Path(f'{self._imagePath}Temperature/normal1.png')


		elif teleType == 'humidity':
			return Path(f'{self._imagePath}HAhumidity.png')

		elif teleType == 'gas':
			return Path(f'{self._imagePath}HAco2.png')

		elif teleType == 'pressure':
			return Path(f'{self._imagePath}HApressure.png')

		elif teleType == 'dewpoint':
			return Path(f'{self._imagePath}HAdewpoint.png')

		else:
			return Path(f'{self._imagePath}HAsensor.png')


	def onUIClick(self):
		location = self.LocationManager.getLocationName(self.parentLocation)

		answer = f"The {location} {self.uid.split('_')[-1]} is {self.getParam('state')} {self._telemetryUnits.get(self.uid.split('_')[-1], '')}"
		self.MqttManager.say(text=answer)
