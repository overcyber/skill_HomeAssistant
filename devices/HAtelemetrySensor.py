import sqlite3
import json

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
		super().__init__(data)
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'
		self._telemetrySetpointPath = Path(f"{str(Path.home())}/ProjectAlice/skills/Telemetry/config.json")

		self._telemetryUnits = {
			'airquality'   : '%',
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


	def getDeviceIcon(self) -> Path:
		telemetryConfig = self.telemetrySetPoints()
		# haDeviceType: str = self.getParam("haDeviceType")

		# Change icon depending on telemetry config setPoints
		iconState = self.highOrLowIconAlert(telemetrySetPoint=telemetryConfig)
		print(f"icon state {iconState}")
		return iconState


	def onUIClick(self):
		location = self.LocationManager.getLocationName(self.parentLocation)
		answer = f"The {location} {self.getParam('haDeviceType')} is {self.getParam('state')} {self._telemetryUnits.get(self.getParam('haDeviceType').lower())}"
		self.MqttManager.say(text=answer)
		return super().onUIClick()


	def telemetrySetPoints(self):
		if self._telemetrySetpointPath.exists():
			telemetrySetpoint = json.loads(self._telemetrySetpointPath.read_text())
			return telemetrySetpoint


	def highOrLowIconAlert(self, telemetrySetPoint: dict):
		alertHigh = f'{str(self.getParam("haDeviceType")).capitalize()}AlertHigh'
		alertLow = f'{str(self.getParam("haDeviceType")).capitalize()}AlertLow'

		# If Telemetry Alerts have both low and high alerts, do this
		if alertHigh in telemetrySetPoint.keys() and alertLow in telemetrySetPoint.keys():
			if self.connected and float(self.getParam("state")) >= telemetrySetPoint[alertHigh]:
				return self.returnHigh(alert=alertHigh, telemetrySetPoint=telemetrySetPoint)

			elif self.connected and float(self.getParam("state")) <= telemetrySetPoint[alertLow]:
				return self.returnLow(alert=alertLow, telemetrySetPoint=telemetrySetPoint)

		# If Telemetry Alerts only have High alerts do this
		elif alertHigh in telemetrySetPoint.keys() \
				and not alertLow in telemetrySetPoint.keys() \
				and self.connected and float(self.getParam("state")) >= telemetrySetPoint[alertHigh]:
			print(f"state is high")
			return self.returnHigh(alert=alertHigh, telemetrySetPoint=telemetrySetPoint)

		# if any of the above fails return the devices standard icon
		return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}.png')


	# Return the path of the high alert icon
	def returnHigh(self, alert: str, telemetrySetPoint) -> Path:
		if self.connected and float(self.getParam("state")) >= telemetrySetPoint[alert]:
			return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}High.gif')


	# Return the path of the low alert icon
	def returnLow(self, alert: str, telemetrySetPoint) -> Path:
		if self.connected and float(self.getParam("state")) >= telemetrySetPoint[alert]:
			return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}Low.png')
