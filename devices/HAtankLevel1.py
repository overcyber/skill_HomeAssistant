import sqlite3

from core.device.model.Device import Device
from pathlib import Path
from core.device.model.DeviceAbility import DeviceAbility
import json

class HAtankLevel1(Device):
	"""
	This device is used for displaying water level sensors on My home. It has 1 level of monitoring + empty
	1. Full
	2. Empty


	For now... for this to work the user must add attributes in the customize.yaml of HA with the following
	attribute
	- key = haDeviceType
	- value = tankLevel1
	as there is no device_class that matches water level sensors in HA. So adding that attribute will allow the
	 skill to capture that device

	There is a svg file here "devices/img/svgFiles/OneLevelTankTemplate.svg" that can
	be modified to refelct your own tank names/ colors etc. modify it then replace the apporpriate
	png file in "devices/img/TankLevel/TwoLevels"

	The incoming payload / state from HA needs to be in json format such as
	"{"Switch1": "ON", "Time": "2021-03-02T10:31:58"}"

	To add multiple tanks, In HA make sure the name of the additional device (tank) ends in a numeric value.
	EG: sensor.fresh_water_tank_1 and sensor.fresh_water_tank_2
	By doing so the code will display the appropriate png file.
	EG: OneLevelTank1-Full.png or OneLevelTank2-Full.png etc.
	"""

	@classmethod
	def getDeviceTypeDefinition(cls) -> dict:
		return {
			'deviceTypeName'        : 'HAtankLevel1',
			'perLocationLimit'      : 0,
			'totalDeviceLimit'      : 0,
			'allowLocationLinks'    : True,
			'allowHeartbeatOverride': True,
			'heartbeatRate'         : 320,
			'abilities'             : [DeviceAbility.NONE]
		}


	def __init__(self, data: sqlite3.Row):
		self._imagePath = f'{self.Commons.rootDir()}/skills/HomeAssistant/devices/img/TankLevel/OneLevel/'
		super().__init__(data)


	def getDeviceIcon(self) -> Path:
		levelStates = json.loads(self.getParam('state'))

		if levelStates['Switch1'] == "ON":
			fullPath = self.checkPathExists(image='High.png')
			return fullPath

		fullPath = self.checkPathExists(image='Empty.png')
		return fullPath


	def onUIClick(self):
		levelStates = json.loads(self.getParam('state'))
		level = "is not full yet"
		if levelStates['Switch1'] == "ON":
			level = "is Full"

		answer = f"The {self.displayName} {level}"
		self.MqttManager.say(text=answer)
		return super().onUIClick()

	def tankNumberCheck(self):
		tankNum: str = self.getParam('entityName')[-1]
		condensedDisplayName = self.displayName.replace(" ", "")

		if tankNum.isnumeric() and int(tankNum) > 1:
			return tankNum, condensedDisplayName
		else:
			tankNum = "1"
			return tankNum, condensedDisplayName

	def checkPathExists(self, image):
		tankNum, condensedDisplayName = self.tankNumberCheck()
		requestedFile = Path(f"{self._imagePath}{condensedDisplayName}-{tankNum}-{image}")
		if requestedFile.exists():
			return requestedFile
		elif Path(f"{self._imagePath}OneLevelTank{tankNum}-{image}").exists():
			return Path(f"{self._imagePath}OneLevelTank{tankNum}-{image}")
		else:
			return Path(f"{self._imagePath}OneLevelTank1-{image}")
