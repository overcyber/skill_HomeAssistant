import sqlite3

from core.device.model.Device import Device
from core.device.model.DeviceType import DeviceType
from skills.HomeAssistant.HomeAssistant import HomeAssistant
from core.commons import constants

class HaSwitch(DeviceType):

	def __init__(self, data: sqlite3.Row):
		super().__init__(data, devSettings=self.DEV_SETTINGS, locSettings=self.LOC_SETTINGS, heartbeatRate=500)

	def getDeviceIcon(self, device: Device) -> str:

		if not device.id:
			return 'HaSwitch.png'
		if not device.connected or not device.getCustomValue('state'):
			return 'switch_offline.png'

		if 'on' in device.getCustomValue('state'):
			return 'switch_on.png'
		elif 'off' in device.getCustomValue('state'):
			return 'switch_off.png'
		else:
			return 'switch_offline.png'


	def toggle(self, device: Device):
		if 'on' in device.getCustomValue('state'):
			device.setCustomValue('state', 'off')
			self.MqttManager.publish(constants.TOPIC_DEVICE_UPDATED, payload={'id': device.id, 'type': 'status'})

			haClass = HomeAssistant()
			haClass.deviceClicked(uid=device.uid, customValue=device.getCustomValue('state'))
			return

		if 'off' in device.getCustomValue('state'):
			device.setCustomValue('state', 'on')
			self.MqttManager.publish(constants.TOPIC_DEVICE_UPDATED, payload={'id': device.id, 'type': 'status'})

			haClass = HomeAssistant()
			haClass.deviceClicked(uid=device.uid, customValue=device.getCustomValue('state'))




