import sqlite3
import json
from typing import Optional

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
			'allowLocationLinks'    : True,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		super().__init__(data)
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/'
		self._telemetrySetpointPath = Path(f"{str(Path.home())}/ProjectAlice/skills/Telemetry/config.json")
		self._tempUnit = self.ConfigManager.getSkillConfigByName(skillName='HomeAssistant', configName='temperatureUnits')

		self._telemetryUnits = {
			'airquality'   : '%',
			'co2'          : 'parts per million',
			'gas'          : 'parts per million',
			'gust_angle'   : '°',
			'gust_strength': 'km/h',
			'humidity'     : '%',
			'light'        : 'lux',
			'pressure'     : 'milli bars',
			'rain'         : 'milli meters',
			'temperature'  : f'°{self._tempUnit}',
			'wind_angle'   : '°',
			'wind_strength': 'km/h',
			'voltage'		: 'volts',
			'current'		: 'amps',
			'dewpoint'		: f'°{self._tempUnit}',
			'battery'		: '% charged'
		}


	def getDeviceIcon(self, path: Optional[Path] = None) -> Path:
		telemetryConfig = self.telemetrySetPoints()

	# Change icon depending on telemetry config setPoints
		icon = self.highOrLowIconAlert(telemetrySetPoint=telemetryConfig)
		return super().getDeviceIcon(icon)


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

		# FailSafe if device is a string value such as "null"
		try:
			state = float(self.getParam('state'))
		except:
			return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}.png')

		# If Telemetry Alerts have both low and high alerts, do this
		if alertHigh in telemetrySetPoint.keys() and alertLow in telemetrySetPoint.keys():
			if state >= telemetrySetPoint[alertHigh]:
				return self.returnHigh()

			elif state <= telemetrySetPoint[alertLow]:
				return self.returnLow()

		# If Telemetry Alerts only have High alerts do this
		elif alertHigh in telemetrySetPoint.keys() \
				and not alertLow in telemetrySetPoint.keys() \
				and state >= telemetrySetPoint[alertHigh]:
			return self.returnHigh()

		# if any of the above fails return the devices standard icon
		return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}.png')


	# Return the path of the high alert icon
	def returnHigh(self) -> Path:
		return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}High.png')


	# Return the path of the low alert icon
	def returnLow(self) -> Path:
		return Path(f'{self._imagePath}Telemetry/{str(self.getParam("haDeviceType")).lower()}Low.png')

