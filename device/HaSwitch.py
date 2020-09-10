import sqlite3

from core.device.model.Device import Device
from core.device.model.DeviceType import DeviceType
from skills.HomeAssistant.HomeAssistant import HomeAssistant

class HaSwitch(DeviceType):

	def __init__(self, data: sqlite3.Row):
		super().__init__(data, devSettings=self.DEV_SETTINGS, locSettings=self.LOC_SETTINGS, heartbeatRate=500)


	def getDeviceIcon(self, device: Device) -> str:

		haClass = HomeAssistant()
		deviceState = haClass.getHeatbeatDeviceRow(uid=device.uid)

		if not device.id:
			return 'HaSwitch.png'
		if not device.connected:
			return 'switch_offline.png'

		if 'on' in deviceState['deviceState']:
			return 'switch_on.png'
		if 'off' in deviceState['deviceState']:
			return 'switch_off.png'


	def toggle(self, device: Device):
		print(f'you just clicked on {device.uid}')
		haClass = HomeAssistant()
		haClass.deviceClicked(device.uid)

