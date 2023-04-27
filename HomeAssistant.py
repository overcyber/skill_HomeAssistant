import threading
import json
from typing import Dict, List
import requests
import subprocess
import uuid

from datetime import datetime
from dateutil import tz
import pytz

from core.device.model.Device import Device
from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler
from requests import get
from core.util.model.TelemetryType import TelemetryType


# noinspection PyTypeChecker,SqlWithoutWhere
class HomeAssistant(AliceSkill):
	"""
	Author: Lazza
	Description: Connect Alice to your home assistant
	"""


	# todo add further sensor support

	def __init__(self):

		self._broadcastFlag = threading.Event()
		self._switchDictionary = dict()
		self._dbSensorList = list()
		self._lightList = list()
		self._action = ""
		self._entity: Device = None
		self._sunState = tuple
		self._triggerType = ""
		self._IpList = list()
		self._configureActivated = False
		self._jsonDict = dict()
		self._newDeviceCount = 0
		self._haDevicesFromAliceDatabase = list()

		# IntentCapture Vars
		self._captureUtterances = ""
		self._captureSlotValue = ""
		self._captureSynonym = ""
		self._utteranceID = 0
		self._slotValueID = 0
		self._utteranceList = list()
		self._slotValueList = list()
		self._data = dict()
		self._finalsynonymList = list()

		super().__init__()


	############################### INTENT HANDLERS #############################

	@IntentHandler('LightControl')
	def controlLightEntities(self, session: DialogSession):
		"""
		Light entities in HA can turn on and off lights, control colour etc. This method,
		allows for that to happen.

		:param session: the incoming dialogSession
		:return:
		"""
		eventKey = ""
		eventValue = ""
		textResponce = ""
		if 'LightControllers' in session.slots:
			if 'AliceColor' in session.slots:
				eventKey = "Color_name"
				eventValue = session.slotRawValue("AliceColor")
				textResponce = "changeColor"
			elif 'dimmer' in session.slots:
				eventKey = "brightness_pct"
				eventValue = session.slotValue("dimmer")
				textResponce = "changeBrightness"

			trigger = 'turn_on'

			device = self.DeviceManager.getDeviceByName(session.slotValue('LightControllers'))

			header, url = self.retrieveAuthHeader(urlPath='services/light/', urlAction=trigger)
			jsonData = {"entity_id": f'{device.getParam("entityName")}', f'{eventKey}': f'{eventValue}'}
			requests.request("POST", url=url, headers=header, json=jsonData)

			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text=textResponce, replace=[eventValue]),
				deviceUid=session.deviceUid
			)


	# Alice speaks what Devices she knows about
	@IntentHandler('WhatHomeAssistantDevices')
	def sayListOfDevices(self, session: DialogSession):
		self.updateKnownDeviceLists()

		activeFriendlyName = list()
		for device in self._haDevicesFromAliceDatabase:
			activeFriendlyName.append(device.displayName)

		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='sayListOfDevices', replace=[activeFriendlyName]),
			deviceUid=session.deviceUid
		)


	def skipAddingSelectedDevice(self, item) -> bool:
		""" if a user has added { aliceIgnore : true} as a attribute in Home Assistant
		Then Alice will ignore that device and not add it to the database

		:param item: The current dictionary item from the incomming HA payload
		:return True: if AliceIgnore is set to true
		"""

		try:
			aliceIgnore: str = item['attributes']['AliceIgnore']
			if 'true' in aliceIgnore.lower():
				if self.getConfig('debugMode') and self.getDebugControl('skippingDevice'):
					self.logDebug(
						f"Skipping the devices {item['attributes']['friendly_name']}. AliceIgnore set to {item['attributes']['AliceIgnore']} ")
					self.logDebug("")
				return True
			else:
				return False
		except:
			return False


	# Used for picking required data from incoming JSON (used in two places)
	def sortThroughJson(self, item):
		"""
		A main method for The Skill. This method reads the incoming JSON data from HA.
		It then goes through each line and based on below code will add devices to a specific list
		depending on the type of device. These list will later get iterated over and added to Alice and
		 HA databases. Or if it's 5 minute update then this method gets used also to recreate the lists
		  with updated info and then iterated over those lists to update device states

		:param item: The current dictionary item from incoming payload
		:return: nothing , but updates entity lists
		"""

		if not self.skipAddingSelectedDevice(item):

			if 'IPAddress' in item["attributes"]:
				ipaddress: str = item["attributes"]["IPAddress"]
				deviceName: str = item["attributes"]["friendly_name"]
				editedDeviceName: str = deviceName.replace(' status', '').lower()
				iplist = [editedDeviceName, ipaddress]
				self._IpList.append(iplist)

			if 'device_class' in item["attributes"]:
				dbSensorList = [self.getFriendyNameAttributes(item=item), item["entity_id"], item["state"],
								item["attributes"]["device_class"], item["entity_id"]]

				self._dbSensorList.append(dbSensorList)

			# if a user has added the haDeviceType attribute in HA customise.yaml
			if not 'device_class' in item["attributes"] and 'HaDeviceType' in item["attributes"] and item["entity_id"].split('.')[0] == 'sensor':
				dbSensorList = [self.getFriendyNameAttributes(item=item), item["entity_id"], item["state"],
								item["attributes"]["HaDeviceType"], item["entity_id"]]
				self._dbSensorList.append(dbSensorList)
			try:

				if 'DewPoint' in item["attributes"]["friendly_name"]:
					sensorType: str = 'dewpoint'
					dbSensorList = [self.getFriendyNameAttributes(item=item), item["entity_id"], item["state"],
									sensorType, item["entity_id"]]

					self._dbSensorList.append(dbSensorList)

				if 'Gas' in item["attributes"]["friendly_name"]:
					sensorType: str = 'gas'
					dbSensorList = [self.getFriendyNameAttributes(item=item), item["entity_id"], item["state"],
									sensorType, item["entity_id"]]

					self._dbSensorList.append(dbSensorList)

				# Capture Non sensor devices
				deviceType = item["entity_id"].split('.')[0]
				deviceGroup = deviceType

				if deviceType == "input_boolean" or deviceType == "group":
					aliceType = "HAswitch"
				else:
					aliceType = f"HA{deviceType}"

				if (deviceType == "light") \
						or (deviceType == "group") \
						or (deviceType == "switch") \
						or (deviceType == "input_boolean"):
					self._switchDictionary[item["entity_id"]] = {
						"friendlyName": self.getFriendyNameAttributes(item=item),
						"state"       : item['state'],
						"deviceType"  : aliceType,
						"deviceGroup" : deviceGroup
					}

			except Exception:
				pass


	@staticmethod
	def getFriendyNameAttributes(item):
		"""
		Extract the friendly name from incoming JSON payload
		:param item: The current dictionary item from incoming payload
		:return: The devices friendly name
		"""
		friendlyName: str = item["attributes"]["friendly_name"]
		friendlyName = friendlyName.lower()
		return friendlyName


	@IntentHandler('AddHomeAssistantDevices')
	def addHomeAssistantDevices(self, session: DialogSession):
		"""
		User has requested to add home assistant devices so this method GETS the payload using
		RestAPI , then sends that data off for sorting through, then sends the results off for adding to the
		database. Then it triggers adding synonyms to the dialog file. then gives the user feedback
		:param session: DialogSession
		:return:
		"""
		if not self.checkConnection():  # If not connected to HA, say so and stop
			self.sayConnectionOffline(session)
			return

		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='addHomeAssistantDevices'),
			deviceUid=session.deviceUid
		)

		# connect to the HomeAssistant API/States to retrieve entity names and values
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()

		if self.getConfig('viewJsonPayload'):
			self.logDebug(f'!-!-!-!-!-!-!-! **INCOMING JSON PAYLOAD** !-!-!-!-!-!-!-!')
			self.logDebug(f'')
			self.logDebug(f'Incomming payload has been written to  HomeAssistant/debugInfo/jsonPayload.json ')
			file = self.getResource('debugInfo/jsonPayload.json')
			file.write_text(json.dumps(data, ensure_ascii=False, indent=4))
			self.logDebug(f'')
			self.logDebug(f'')

		# Loop through the incoming json payload to grab data that we need
		for item in data:
			if isinstance(item, dict):
				self.sortThroughJson(item=item)

		# Split above and below into other methods to reduce complexity complaint from sonar
		# todo This is a process data retrival shortcut
		self.processRetrievedHaData()

		# write friendly names to dialogTemplate as slotValues
		self.addSlotValues()

		# restore previously saved dialog template file
		self._configureActivated = True

		# update the known device.
		self.updateKnownDeviceLists()

		if self._switchDictionary:
			self.ThreadManager.doLater(
				interval=5,
				func=self.sayNumberOfDeviceViaThread
			)
		else:
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='addHomeAssistantDevicesError'),
				deviceUid=session.deviceUid
			)


	# Do the actual switching via here
	@IntentHandler('HomeAssistantAction')
	def homeAssistantSwitchDevice(self, session: DialogSession):
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		if 'on' in session.slotRawValue('OnOrOff') or 'open' in session.slotRawValue('OnOrOff'):
			self._action = "turn_on"  # Set HA compatible on command
		elif 'off' in session.slotRawValue('OnOrOff') or 'close' in session.slotRawValue('OnOrOff'):
			self._action = "turn_off"

		if session.slotValue('switchNames'):
			self._entity = self.DeviceManager.getDeviceByName(session.slotRawValue('switchNames'))
			if self.getConfig('debugMode') and self.getDebugControl('switching'):
				self.logDebug(f'!-!-!-!-!-!-!-! **SWITCHING EVENT** !-!-!-!-!-!-!-!')
				self.logDebug(f'')
				self.logDebug(f'I was requested to "{self._action}" the devices called "{self._entity.displayName}" ')

				try:
					self.logDebug(f'debugSwitchId = {self._entity.getParam("entityName")}')
				except Exception as e:
					self.logDebug(f' a error occured switching the switch : {e}')

		if self._action and self._entity.getParam('entityName'):
			header, url = self.retrieveAuthHeader(urlPath=f'services/{self._entity.getParam(key="entityGroup")}/',
												  urlAction=self._action)

			jsonData = {"entity_id": self._entity.getParam('entityName')}
			requests.request("POST", url=url, headers=header, json=jsonData)

			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='homeAssistantSwitchDevice', replace=[self._action]),
				deviceUid=session.deviceUid
			)
			self._entity = None


	# Get the state of a single devices
	@IntentHandler('HomeAssistantState')
	def getDeviceState(self, session: DialogSession):
		""" return the current state of the requested device"""
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		if 'DeviceState' in session.slots:
			device = self.DeviceManager.getDeviceByName(name=session.slotRawValue("DeviceState"))

			# get info from HomeAssitant
			header, url = self.retrieveAuthHeader(urlPath='states/', urlAction=device.getParam(key="entityName"))
			stateResponce = requests.get(url=url, headers=header)

			data = stateResponce.json()

			entityID = data['entity_id']
			entityState = data['state']
			# add the devices state to the database
			device = self.DeviceManager.getDevice(uid=entityID)
			device.updateParam(key='state', value=entityState)

			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='getActiveDeviceState',
									 replace=[session.slotRawValue("DeviceState"), entityState]),
				deviceUid=session.deviceUid
			)


	@IntentHandler('HomeAssistantSun')
	def sunData(self, session: DialogSession):
		"""Returns various states of the sun"""
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		# connect to the HomeAssistant API/States to retrieve sun values
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()

		# Loop through the incoming json payload to grab the Sun data that we need
		for item in data:

			if isinstance(item, dict) and 'friendly_name' in item["attributes"] and 'Sun' in item["attributes"][
				'friendly_name']:
				if self.getConfig('debugMode'):
					self.logDebug(f'!-!-!-!-!-!-!-! **SUN DEBUG LOG** !-!-!-!-!-!-!-!')
					self.logDebug(f'')
					self.logDebug(f'The sun JSON is ==> {item}')
					self.logDebug(f'')

				try:
					self._sunState = item["attributes"]['friendly_name'], item["attributes"]['next_dawn'], \
									 item["attributes"]['next_dusk'], item["attributes"]['next_rising'], \
									 item["attributes"]['next_setting'], item['state']
				except Exception as e:
					self.logDebug(f'Error getting full sun attributes from Home Assistant: {e}')
					return

		request = session.slotRawValue('sunState')
		if 'position' in request:
			horizon = self._sunState[5].replace("_", " the ")
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='sayHorizon', replace=[horizon]),
				deviceUid=session.deviceUid
			)

		elif 'dusk' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[2])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = self.randomTalk(text='nextSunEvent', replace=[request])
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)

		elif 'sunrise' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[3])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = self.randomTalk(text='nextSunEvent', replace=[request])
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)

		elif 'dawn' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[1])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = self.randomTalk(text='nextSunEvent', replace=[request])
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)

		elif 'sunset' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[4])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = self.randomTalk(text='nextSunEvent', replace=[request])
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)


	@IntentHandler('GetIpOfDevice')
	def returnIpAddressOfDevice(self, session: DialogSession):
		"""Tells user the ip address of the requested device (if known)"""
		device = self.DeviceManager.getDeviceByName(session.slotRawValue('switchNames'))

		if device:
			ipOfDevice = device.getParam('entityIP')

		else:
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='sayIpError', replace=[session.slotRawValue("switchNames")]),
				deviceUid=session.deviceUid
			)
			self.logWarning(
				f'Getting devices IP failed: I may not have that data available from HA  - {session.slotRawValue("switchNames")}')
			return

		if ipOfDevice:

			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='sayIpAddress', replace=[ipOfDevice]),
				deviceUid=session.deviceUid
			)
			self.logInfo(f'You can view the {session.slotRawValue("switchNames")} at ->> http://{ipOfDevice}')

		else:
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='sayIpError2', replace=[session.slotRawValue("switchNames")]),
				deviceUid=session.deviceUid
			)
			self.logWarning(f'Device name not available, HA may not of supplied that devices IP')


	# device was asked to switch from Myhome
	def deviceClicked(self, uid: str):
		"""
		User has clicked a device in My home. The uid of the device is used to grab the current
		state of the device and turn on or off the device as required. Last of all it also writes
		The device states to the file found in the skill folder.
		:param uid: The uid of the device
		:return:
		"""

		if not self.checkConnection():
			return
		device = self.DeviceManager.getDevice(uid=uid)
		if "on" in device.getParam("state") or "open" in device.getParam("state"):
			self._action = 'turn_on'
		elif "off" in device.getParam("state") or "close" in device.getParam("state"):
			self._action = 'turn_off'
		else:
			answer = f"Sorry but the {device.displayName} is currently unavailable. Is it connected to the network ?"
			self.say(
				text=answer,
				deviceUid=self.DeviceManager.getMainDevice().uid
			)
			return
		deviceType = device.getParam('entityGroup')
		header, url = self.retrieveAuthHeader(urlPath=f'services/{deviceType}/', urlAction=self._action)
		# Update json file on click via Myhome
		self._jsonDict = json.loads(str(self.getResource('currentStateOfDevices.json').read_text()))
		self._jsonDict[device.getParam('entityName')] = device.getParam("state")

		jsonData = {"entity_id": device.getParam('entityName')}
		requests.request("POST", url=url, headers=header, json=jsonData)

		self.updateDeviceStateJSONfile()


	##################### POST AND GET HANDLERS ##############################

	def getUpdatedDetails(self):
		"""
		Request the data from HA's restApi
		:return:
		"""
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()

		# Loop through the incoming json payload to grab data that we need
		self._lightList = list()
		for item in data:

			if isinstance(item, dict):
				self.sortThroughJson(item=item)

		if self.getConfig('debugMode') and self.getDebugControl('updateStates'):
			self.logDebug(f'!-!-!-!-!-!-!-! **updateDBStates code** !-!-!-!-!-!-!-!')


	def updateDBStates(self):
		"""Update entity states from a 5 min timer and on boot"""

		# use getUpdatedDetails method to reduce complexity of updateDBStates and keep sonar quiet
		self.getUpdatedDetails()
		self.updateKnownDeviceLists()

		self.updateDeviceState()

		self.updateSensors()


	def updateDeviceState(self):
		""" add updated states of switch-able devices to devices.params"""

		for device in self._haDevicesFromAliceDatabase:
			for deviceId, entityDetails in self._switchDictionary.items():
				if device.getParam('entityName') == deviceId:

					# update the state of the json states file
					self._jsonDict[deviceId] = entityDetails['state']

					if self.getConfig('debugMode') and self.getDebugControl('updateStates'):
						self.logDebug(f'')
						self.logDebug(f'I\'m updating the "{deviceId}" with state "{entityDetails["state"]}" ')

					device.updateParam(key='state', value=entityDetails['state'])
					# send HeartBeat
					if not 'unavailable' in entityDetails['state'] and entityDetails['state']:
						self.DeviceManager.onDeviceHeartbeat(uid=device.uid)



	def updateSensors(self):
		"""
		Update the values of sensors in alice database. update the JSON file for states
		in the main skill directory
		:return:
		"""
		for sensorName, entity, state, haClass, uid in self._dbSensorList:
			# Locate sensor in the database and update it's value
			for device in self._haDevicesFromAliceDatabase:
				if device.getParam('entityName') == entity:
					self._jsonDict[entity] = state
					if self.getConfig('debugMode') and self.getDebugControl('updateStates'):
						self.logDebug(f'')
						self.logDebug(f'I\'m now updating the SENSOR "{sensorName}" with the state of "{state}" ')
						self.logDebug(f'HA class is "{haClass}" ')
						self.logDebug(f'The entity ID is "{entity}"')

					device.updateParam(key='state', value=state)
					device.updateParam(key="haDeviceType", value=haClass)

					if not 'unavailable' in state and state:
						self.DeviceManager.onDeviceHeartbeat(uid=device.uid)
					else:
						self._jsonDict[entity] = state

		# reset object value to prevent multiple items each update
		self._dbSensorList = list()

		self.updateDeviceStateJSONfile()


	def retrieveAuthHeader(self, urlPath: str, urlAction: str = None):
		"""
		Sets up and returns the Request Header file and url

		:param urlPath - sets the path such as services/Switch/
		:param urlAction - sets the action such as turn_on or turn_off

		EG: usage - header, url = self.requestAuthHeader(urlPath='services/switch/', urlAction=self._action)
		:returns: header and url
		"""
		header = {"Authorization": f'Bearer {self.getConfig("haAccessToken")}', "content-type": "application/json", }

		if urlAction:
			url = f'{self.getConfig("haIpAddress")}{urlPath}{urlAction}'
		else:  # else is used for checking HA connection and boot up
			url = f'{self.getConfig("haIpAddress")}{urlPath}'

		return header, url


	def checkConnection(self) -> bool:
		"""
		Used several times through out the code to check if there is a active connection to Home Assistant
		:return: True if connected
		"""
		try:
			header, url = self.retrieveAuthHeader(' ', ' ')
			response = get(self.getConfig('haIpAddress'), headers=header)
			if 'API running.' in response.text:
				return True
			else:
				self.logWarning(f'It seems HomeAssistant is currently not connected ')
				return False
		except Exception as e:
			self.logWarning(
				f'Detected a error in HA skill, did you just add a new HA devices but not run "Configure home assistant skill" yet?: {e}')
			return False


	########################## DATABASE ITEMS ####################################

	def AddToAliceDB(self, uID: str, friendlyName: str, deviceType: str, deviceParam: dict = None):
		"""
		Add devices to Alices Devicemanager-Devices table. Create and store devices in a StoreRoom
		:param uID: The devices uid (in HA's case this is same as entity name)
		:param friendlyName: The devices friendly name
		:param deviceType: The devices Type EG: HAswitch, HAlight etc
		:param deviceParam: A user defined dictionary of values
		:return:
		"""
		# If there is no "storeroom" location, create it and store devices there.
		if not self.LocationManager.getLocationByName('StoreRoom'):
			self.LocationManager.addNewLocation({"name": "StoreRoom", "parentLocation": 0})
		# register the device type if not already existing
		if not self.DeviceManager.getDeviceType(skillName=self.name, deviceType=deviceType):
			self.DeviceManager.registerDeviceType(skillName=self.name, data={"deviceTypeName": deviceType})
		self.DeviceManager.addNewDevice(deviceType=deviceType,
										skillName=self.name,
										locationId=self.LocationManager.getLocation(locationName='StoreRoom').id,
										uid=uID,
										displaySettings={"x": "10", "y": "10", "z": 25, "w": 38, "h": 40, "r": 0},
										deviceParam=deviceParam,
										displayName=friendlyName
										)


	################# General Methods ###################
	# todo General methods shortcut

	def wipeAllHaData(self):
		# delete and existing values in DB so we can update with a fresh list of Devices
		for device in self.DeviceManager.getDevicesBySkill(skillName=self.name, connectedOnly=False):
			self.DeviceManager.deleteDevice(deviceId=device.id)

		self.logWarning(f'Just deleted your Home Assistant records.')
		self.updateConfig(key="wipeAll", value='false')



	def sayNumberOfDeviceViaThread(self):
		self.say(
			text=self.randomTalk(text='saynumberOfDevices', replace=[self._newDeviceCount, len(self._haDevicesFromAliceDatabase)]),
			deviceUid=self.DeviceManager.getMainDevice().uid
		)


	def sayConnectionOffline(self, session: DialogSession):
		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='sayConnectionOffline'),
			deviceUid=session.deviceUid
		)


	@staticmethod
	def isNumber(string) -> bool:
		try:
			float(string)
			return True
		except ValueError:
			return False


	def onFiveMinute(self):
		if not self.checkConnection():
			return
		# todo LARRY sensor shortcut
		self.updateDBStates()
		self.getTelemetryValues()


	def getTelemetryValues(self):
		"""
		Pull out telemetry sensors and send those updated states to the telemetry db
		:return:
		"""
		debugtrigger = 0

		for device in self._haDevicesFromAliceDatabase:
			state = device.getParam('state')
			if device.deviceTypeName == 'HAtelemetrySensor' and state.isnumeric() or self.isNumber(state):
				haDeviceType = device.getParam('haDeviceType')

				newPayload = dict()
				newPayload[str(haDeviceType).upper()] = state
				# self.createTelemetryPayloadBasedOnDeviceType(haDeviceType=haDeviceType, state=state, newPayload=newPayload)
				if newPayload:

					try:
						if self.getConfig('debugMode') and self.getDebugControl("telemetry") and debugtrigger == 0:
							self.logDebug("")
							self.logDebug(f'!-!-!-!-!-!-!-! **Now adding to the Telemetry DataBase** !-!-!-!-!-!-!-!')
							debugtrigger = 1

						# senddata to telemtry Database
						self.sendToTelemetry(newPayload=newPayload, device=device)

					except Exception as e:
						self.logWarning(f'There was a error logging data for sensor {device.displayName} as : {e}')
			else:
				continue


	# add friendlyNames to dialog template as a list of slotValues
	def addSlotValues(self):
		"""
		Find the slotValues to write to the existing dialogTemplate file for the skill
		"""
		file = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')
		self.updateKnownDeviceLists()
		if not file:
			return

		if self.getConfig('debugMode'):
			self.logDebug('!-!-!-!-!-!-!-! **ADDING THE SLOTVALUE** !-!-!-!-!-!-!-!')

		lightValueList: List[Dict[str, str]] = list()
		switchValueList: List[Dict[str, str]] = list()

		for device in self._haDevicesFromAliceDatabase:
			dictValue = {'value': device.displayName}
			try:
				if device.getParam('entityGroup') == 'switch' \
						or device.getParam('entityGroup') == 'group' \
						or device.getParam('entityGroup') == 'input_boolean':
					switchValueList.append(dictValue)

					if self.getConfig('debugMode'):
						self.logDebug(
							f'Adding slotValue {device.displayName}, of type "{device.getParam("entityGroup")}"')
						self.logDebug('')

				if 'light' in device.getParam('entityGroup'):
					lightValueList.append(dictValue)

					if self.getConfig('debugMode'):
						self.logDebug(
							f'Adding slot value {device.displayName}, of type "{device.getParam("entityGroup")}"')
						self.logDebug('')
			except:
				continue
		data = json.loads(file.read_text())

		self.writeSlotValues(data=data,
							 switchValueList=switchValueList,
							 lightValueList=lightValueList,
							 file=file)


	@staticmethod
	def writeSlotValues(data, switchValueList, lightValueList, file) -> bool:
		"""
		:param data: The dialog template data
		:param switchValueList: A list of switch names
		:param lightValueList: A list of Light names
		:param file: The dialog File to write data to
		:return: bool
		"""

		if 'slotTypes' not in data:
			return False

		for i, suggestedSlot in enumerate(data['slotTypes']):
			if "switchnames" in suggestedSlot['name'].lower():
				# create a dictionary and append the new slot value to original list
				data['slotTypes'][i]['values'] = switchValueList
			if "lightcontrollers" in suggestedSlot['name'].lower():
				# create a dictionary and append the new slot value to original list
				data['slotTypes'][i]['values'] = lightValueList

		file.write_text(json.dumps(data, ensure_ascii=False, indent=4))

		return True


	def processRetrievedHaData(self):

		# remove duplicate sensors
		finalSensorList = dict((x[0], x) for x in self._dbSensorList).values()

		self.updateKnownDeviceLists()

		# reset the device counter
		self._newDeviceCount = 0

		entityNames = list()

		for device in self._haDevicesFromAliceDatabase:
			entityNames.append(device.getParam('entityName'))

		# Add Switches, booleans  and group entities to the database
		self.addDevicesToDatabaseTable(aliceList=entityNames)

		# Process Sensor entities
		for sensorDevice in finalSensorList:
			newUid = str(uuid.uuid4())
			isTelemtryType = False
			try:
				if TelemetryType[str(sensorDevice[3]).upper()]:
					isTelemtryType = True
			except:
				pass

			## If the sensor matches the TelemetryType Enum list. then do this block
			if not sensorDevice[4] in entityNames and isTelemtryType:
				self._newDeviceCount += 1
				self.AddToAliceDB(
					uID=newUid,
					friendlyName=sensorDevice[0],
					deviceType="HAtelemetrySensor",
					deviceParam={"haDeviceType": str(sensorDevice[3]).upper(), "state": sensorDevice[2],
								 "entityName"  : sensorDevice[4], "entityGroup": "sensor"}
				)

			classList = ["motion", 'power', 'current', 'tanklevel4', 'tanklevel3', 'tanklevel2', 'tanklevel1']

			if not sensorDevice[4] in entityNames and str(sensorDevice[3]).lower() in classList:
				self._newDeviceCount += 1
				self.AddToAliceDB(uID=newUid,
								  friendlyName=sensorDevice[0],
								  deviceType=f"HA{sensorDevice[3]}",
								  deviceParam={
									  "haDeviceType": sensorDevice[3],
									  "state"       : sensorDevice[2],
									  "entityName"  : sensorDevice[4],
									  "entityGroup" : "sensor"
								  }
								  )

		# Process Sensor entities
		for deviceDetails in self._IpList:
			# self.updateDeviceIPInfo(ip=deviceDetails[1], nameIdentity=deviceDetails[0])
			device = self.DeviceManager.getDeviceByName(deviceDetails[0])
			if device:
				device.updateParam(key="entityIP", value=deviceDetails[1])


	def updateKnownDeviceLists(self):
		"""
		Adds alices known HA devices to a list for later reference

		Purpose : To reduce the need to read the database frequently
		:return:
		"""
		self._haDevicesFromAliceDatabase = list()
		# get all known Home Assistant devices from Alices database
		self._haDevicesFromAliceDatabase = self.DeviceManager.getDevicesBySkill(skillName=self.name,
																				connectedOnly=False)


	def addDevicesToDatabaseTable(self, aliceList: list):
		"""
		Add new devices to Alice

		:param aliceList: A list of known device entityNames from Alices database
		:return:
		"""
		for deviceId, entityDetails in self._switchDictionary.items():

			newUid = str(uuid.uuid4())

			if not deviceId in aliceList:
				self._newDeviceCount += 1
				self.AddToAliceDB(uID=newUid,
								  friendlyName=entityDetails['friendlyName'],
								  deviceType=entityDetails['deviceType'],
								  deviceParam={"entityName" : deviceId, "state": entityDetails["state"],
											   "entityGroup": entityDetails['deviceGroup']})


	def sendToTelemetry(self, newPayload: dict, device):
		"""
		Send the incoming data to the TelemtryManager for storing in Telemtry Database
		:param newPayload: A Dict containing 'deviceType' and the 'value'. EG: {"TEMPERATURE": 23.4}
		:param device: The current device
		:return:
		"""
		# create location if it doesnt exist and get the id
		locationID = self.LocationManager.getLocation(locId=device.parentLocation).id

		haTelemetryType = list(newPayload.keys())[0]

		try:
			if TelemetryType[str(haTelemetryType)]:
				self.TelemetryManager.storeData(ttype=TelemetryType[str(haTelemetryType)],
												value=newPayload[str(haTelemetryType)],
												service=self.name,
												deviceId=device.id,
												locationId=locationID)
			if self.getConfig('debugMode') and self.getDebugControl('telemetry'):
				self.logDebug(f'')
				self.logDebug(
					f'The {str(haTelemetryType)} reading for the {device.displayName} is {newPayload[str(haTelemetryType)]} ')


		except:
			pass


	def updateDeviceStateJSONfile(self):
		"""
		Write all Device states to the Json file in the skill folder.
		Purpose: So user can refrence them from Node red rather than access database
		:return: Writes a json file to the skill directory /currentStateOfDevices.json
		"""
		if self.getConfig('debugMode'):
			self.logDebug(f'Updated currentStateOfDevices.json')
		self.getResource('currentStateOfDevices.json').write_text(
			json.dumps(self._jsonDict, ensure_ascii=False, indent=4))


	################### AUTO BACKUP AND RESTORE CODE ########################

	def restoreDisplaySettings(self):
		"""
		Restore display positions of devices if lost
		:return nothing:
		"""
		#todo if option to restore backup display settings is enabled
			#and display.json exists

		#loop through devices in database and update location and display settings for each valid device name
		print("this is a todo ")
	# Make a backup directory if it doesn't exist

	def runBackup(self):
		"""
		Initialises the backup Process, Creates the Backup directory if it doesn't exist
		:return:
		"""
		if not self.getResource('Backup').exists():
			self.logInfo(f'No Home Assistant BackUp directory found, so I\'m making one')
			self.getResource("Backup").mkdir()

		self.makeDialogFileCopy()


	# Back up existing DialogTemplate file
	def makeDialogFileCopy(self):
		file = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')
		subprocess.run(['cp', file, f'{self.getResource("Backup")}/{self.activeLanguage()}.json'])
		self.logInfo(f'![green](Backing up dialog file)')


	def mergeDialogIntents(self):
		activeDialogFile = json.loads(self.getResource(f'dialogTemplate/{self.activeLanguage()}.json').read_text())
		backupDialogFile = json.loads(self.getResource(f'Backup/{self.activeLanguage()}.json').read_text())
		filePath = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')

		for i, backupItem in enumerate(backupDialogFile['intents']):
			if "userintent" in backupItem['name'].lower():
				backupUserIntents = backupItem.get('utterances', list())
				for x, activeItem in enumerate(activeDialogFile['intents']):
					if "userintent" in activeItem['name'].lower():
						activeDialogFile['intents'][x]['utterances'] = backupUserIntents
						filePath.write_text(json.dumps(activeDialogFile, ensure_ascii=False, indent=4))

		self.mergeDialogSlots()


	def mergeDialogSlots(self):
		activeDialogFile = json.loads(self.getResource(f'dialogTemplate/{self.activeLanguage()}.json').read_text())
		backupDialogFile = json.loads(self.getResource(f'Backup/{self.activeLanguage()}.json').read_text())
		filePath = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')

		for i, backupItem in enumerate(backupDialogFile['slotTypes']):
			if "haintent" in backupItem['name'].lower():
				backupUserSlots = backupItem.get('values', list())
				for x, activeItem in enumerate(activeDialogFile['slotTypes']):
					if "haintent" in activeItem['name'].lower():
						activeDialogFile['slotTypes'][x]['values'] = backupUserSlots
						filePath.write_text(json.dumps(activeDialogFile, ensure_ascii=False, indent=4))

			if not self._configureActivated:
				self.mergeSwitchAndLightDialog(backupItem=backupItem, activeDialogFile=activeDialogFile,
											   filePath=filePath)

		if self._configureActivated:
			self._configureActivated = False
			self.logInfo(f'Merged DialogTemplate files.')
			return

		self.logInfo(f'Merged DialogTemplate files. Retraining now... ')


	# Reduce Cognitive Complexity of the above method
	@staticmethod
	def mergeSwitchAndLightDialog(backupItem, activeDialogFile, filePath):
		if "switchnames" in backupItem['name'].lower():
			backupUserSlots = backupItem.get('values', list())
			for x, activeItem in enumerate(activeDialogFile['slotTypes']):
				if "switchnames" in activeItem['name'].lower():
					activeDialogFile['slotTypes'][x]['values'] = backupUserSlots
					filePath.write_text(json.dumps(activeDialogFile, ensure_ascii=False, indent=4))

		if "lightcontrollers" in backupItem['name'].lower():
			backupUserSlots = backupItem.get('values', list())
			for x, activeItem in enumerate(activeDialogFile['slotTypes']):
				if "lightcontrollers" in activeItem['name'].lower():
					activeDialogFile['slotTypes'][x]['values'] = backupUserSlots
					filePath.write_text(json.dumps(activeDialogFile, ensure_ascii=False, indent=4))


	# Merge dialogTemplate files on Update if a backup exists and restore My home display settings
	def onSkillUpdated(self, skill: str):
		if skill.lower() == self.name.lower():
			self.logInfo(f'![yellow](Now restoring {skill} backups.....)')
			dialogFile = self.getResource(f'Backup/{self.activeLanguage()}.json')

			if dialogFile.exists():
				self.mergeDialogIntents()
				self.say(
					text=self.randomTalk(text='restored')
				)
		super().onSkillUpdated(skill)


	# onStop. backup display coordinates and dialogTemplate file
	def onStop(self):
		if self.getConfig('enableBackup'):
			self.runBackup()
		super().onStop()


	def onBooted(self) -> bool:

		if 'http://localhost:8123/api/' in self.getConfig("haIpAddress"):
			self.logWarning(f'You need to update the HAIpAddress in Homeassistant Skill ==> settings')
			self.say(
				text=self.randomTalk(text='sayConfigureMe')
			)
			return False
		else:
			try:
				header, url = self.retrieveAuthHeader(' ', ' ')
				response = get(self.getConfig('haIpAddress'), headers=header)

				if self.getConfig('debugMode') and self.getDebugControl('header'):
					self.logDebug(f'!-!-!-!-!-!-!-! **OnBooted code** !-!-!-!-!-!-!-!')
					self.logDebug(f'')
					self.logDebug(f'{response.text} - onBooted connection code')
					self.logDebug(f' The header is {header} ')
					self.logDebug(f'The Url is {url} ')
					self.logDebug(f'')

				if 'API running.' in response.text:
					self.logInfo(f'HomeAssistant Connected')

					if self.getConfig('wipeAll'):
						self.logWarning('Deleting all HomeAssistant devices and starting fresh')

						self.wipeAllHaData()

					self.updateKnownDeviceLists()

					if self.noDevicePreChecks():
						return True

					#temporarily disabled, as no longer needed ?
					#if self.getConfig('debugIcon'):
					#	self.getIconDebugInfo()
					heartBeatList = self._haDevicesFromAliceDatabase

					if heartBeatList:
						self.logInfo(f'Sending Heartbeat connection requests')

						for device in heartBeatList:
							self.DeviceManager.deviceConnecting(uid=device.uid)
						self.sendHeartBeatrequest()

					# on boot update states to get My home states upto date
					if self._haDevicesFromAliceDatabase:
						self.updateDBStates()
						return True

				else:
					self.logWarning(f'Issue connecting to HomeAssistant : {response.text}')
					return False

			except Exception as e:
				self.logWarning(f'HomeAssistant encounted a issue on boot up. Exception was : {e}')
				return False
		super().onBooted()
		return True

	def noDevicePreChecks(self) -> bool:
		if not self._haDevicesFromAliceDatabase:
			self.logWarning('No devices found. let\'s see if I can fix that for you')
			self.logInfo("Looking for new Home Assistant devices")
			session: DialogSession = self.DialogManager.newSession(
				deviceUid=self.DeviceManager.getMainDevice().uid
			)
			self.addHomeAssistantDevices(session)
			self.updateKnownDeviceLists()

			if not self._haDevicesFromAliceDatabase:
				self.logInfo(f"Sorry but i simply can't find any devices.")
				return True

		return False


	def sendHeartBeatrequest(self):
		"""
		Send heartbeats every 319 seconds which is after the 5 min state updates.
		Reason = Because we check for state condition. if unavailable etc then we don't send the heartbeat
		:return:
		"""
		for device in self.DeviceManager.getDevicesBySkill(skillName=self.name, connectedOnly=False):
			if device.getParam("state") != "unavailable" and device.getParam("state"):
				# print(f"sending heartbeat to {device.displayName} - {device.getParam('state')}")
				self.DeviceManager.onDeviceHeartbeat(uid=device.uid)

		self.ThreadManager.doLater(
			interval=319,
			func=self.sendHeartBeatrequest
		)


	@property
	def broadcastFlag(self) -> threading.Event:
		return self._broadcastFlag


	@staticmethod
	def makeDateObjFromString(sunState: str):
		"""
		Takes HA's UTC string and turns it to a datetime object
		"""

		utcDatetime = datetime.strptime(sunState, "%Y-%m-%dT%H:%M:%S%z")
		utcDatetimeTimestamp = float(utcDatetime.strftime("%s"))
		localDatetimeConverted = datetime.fromtimestamp(utcDatetimeTimestamp)
		return localDatetimeConverted


	@staticmethod
	def standard_date(dt):
		"""
		Takes a naive UTC datetime stamp, Converts it to local timezone,
		Outputs time between the converted UTC date and hours and minutes until then

		   params:
                dt: the date in UTC format to convert (no TZ info).
        """

		now = datetime.now()
		usersTZ = tz.tzlocal()

		# give the naive stamp, timezone info
		utcTimeStamp = dt.replace(tzinfo=pytz.utc)

		# convert from utc to local time
		haConvertedTimestamp = utcTimeStamp.astimezone(usersTZ)
		now = now.astimezone(usersTZ)

		diff = haConvertedTimestamp - now
		timeStampFormat = '%b %d @ %I:%M%p'

		# apply formatting and obtain hours and minute output
		timeDifferenceResult = haConvertedTimestamp.strftime(timeStampFormat)
		days, seconds = diff.days, diff.seconds
		hours = days * 24 + seconds // 3600
		minutes = (seconds % 3600) // 60

		return timeDifferenceResult, hours, minutes


	def saysunState(self, session, state, result, hours, minutes):
		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='saySunState', replace=[state, result, hours, minutes]),
			deviceUid=session.deviceUid
		)


	########################## TELEMETRY PROCESSING #############################

	def onGasAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'gas'
			self.telemetryEvents(kwargs)


	def onPressureHighAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'pressure'
			self.telemetryEvents(kwargs)


	def onTemperatureHighAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'temperature'
			self.telemetryEvents(kwargs)


	def onTemperatureLowAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'Temperature'
			self.telemetryEvents(kwargs)


	def onFreezing(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'freezing'
			self.telemetryEvents(kwargs)


	def onHumidityHighAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'humidity'
			self.telemetryEvents(kwargs)


	def onHumidityLowAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'Humidity'
			self.telemetryEvents(kwargs)


	def onCOTwoAlert(self, **kwargs):
		if self.name in kwargs['service']:
			self._triggerType = 'C O 2'
			self.telemetryEvents(kwargs)


	def telemetryEvents(self, kwargs):
		if self.getConfig("silenceAlerts"):
			return
		trigger = kwargs['trigger']
		value = kwargs['value']
		threshold = kwargs['threshold']
		area = self.LocationManager.getLocationName(
			self.DeviceManager.getDevice(deviceId=kwargs['area']).parentLocation)
		if 'upperThreshold' in trigger:
			trigger = 'high'
		else:
			trigger = 'low'

		if not 'freezing' in self._triggerType:

			self.say(
				text=self.randomTalk(text='sayTelemetryAlert',
									 replace=[self._triggerType, trigger, threshold, value, area])
			)
		else:
			self.say(
				text=self.randomTalk(text='sayTelemetryFreezeAlert', replace=[area, value])
			)


	########################## INTENT CAPTURE CODE ###########################################

	@IntentHandler('UserIntent')
	def sendUserIntentToHA(self, session: DialogSession):

		if self.randomTalk(text='dummyIntent') in session.payload['input']:
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='dummyUtterance'),
				deviceUid=session.deviceUid,
			)
			return
		userSlot = session.slotValue('HAintent')

		self.MqttManager.publish(topic='ProjectAlice/HomeAssistant', payload=userSlot)

		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='homeAssistantSwitchDevice')
		)


	@IntentHandler('CreateIntent')
	def createIntentRequest(self, session: DialogSession):
		# test line
		# self.addIntentToHADialog(text='turn the tv volume up', session=session)

		self.continueDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='sayYesICanCaptureIntent'),
			intentFilter=['UserRandomAnswer'],
			currentDialogState='requestingToMakeAIntent',
			probabilityThreshold=0.1
		)


	def addIntentToHADialog(self, text: str, session):
		""" Here we capture the Users Intent and just store it for later use"""

		file = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')
		if not file:
			return False

		# Read the original JSON dialogTemplate file before it gets modified
		self._data = json.loads(file.read_text())

		# enumerate over existing intents to find the userintent that we are after
		for i, suggestedIntent in enumerate(self._data['intents']):
			if "userintent" in suggestedIntent['name'].lower():
				# get a list of exisiting utterances
				self._utteranceList = suggestedIntent.get('utterances', list())

				# check the utterance doesnt already exist
				if not text in self._utteranceList:
					# we need to add slot syntax to the Utterance so store needed values and move on
					self._captureUtterances = text
					self._utteranceID = i
					self.askSlotValue(session=session)
					return True
				else:
					self.say(
						deviceUid=session.deviceUid,
						text=self.randomTalk(text='utteranceExists'), )
					self.createIntentRequest(session)

		return False


	def askSlotValue(self, session):
		self.continueDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='askSlotValue'),
			intentFilter=['UserRandomAnswer'],
			currentDialogState='requestingSlotValue',
			probabilityThreshold=0.1

		)


	@IntentHandler(intent='UserRandomAnswer', requiredState='requestingSynonymValue')
	@IntentHandler(intent='UserRandomAnswer', requiredState='requestingSlotValue')
	@IntentHandler(intent='UserRandomAnswer', requiredState='requestingToMakeAIntent')
	def listenForAvalue(self, session):
		"""Process the users spoken input"""

		triggerType = ""
		incomingValue: str = session.payload['input']

		if 'requestingToMakeAIntent' in session.currentState:
			self._captureUtterances = incomingValue
			self.addIntentToHADialog(text=self._captureUtterances, session=session)
			return
		elif 'requestingSlotValue' in session.currentState:
			triggerType = "ConfirmSlotValue"
			self._captureSlotValue = incomingValue

		elif 'requestingSynonymValue' in session.currentState:
			triggerType = "ConfirmSynonymValue"
			self._captureSynonym = incomingValue

		if not incomingValue.lower() in self._captureUtterances.lower() and not 'ConfirmSynonymValue' in triggerType:
			self.continueDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='keywordError', replace=[self._captureUtterances]),
				intentFilter=['UserRandomAnswer'],
				currentDialogState='requestingSlotValue',
				probabilityThreshold=0.1
			)
			return

		# verify what the user's value was, to confirm alice heard it properly
		self.continueDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='repeatIncomingValue', replace=[incomingValue]),
			intentFilter=['AnswerYesOrNo'],
			currentDialogState=triggerType,

		)


	@IntentHandler(intent='AnswerYesOrNo', requiredState='requestingShouldWeAddSynonyms')
	@IntentHandler(intent='AnswerYesOrNo', requiredState='ConfirmSlotValue')
	@IntentHandler(intent='AnswerYesOrNo', requiredState='ConfirmIntent')
	@IntentHandler(intent='AnswerYesOrNo', requiredState='ConfirmSynonymValue')
	def processYesOrNoResponse(self, session):
		"""Sorts through the multiple yes or no responces and redirects accordingly"""

		# if user replies with a Yes responce do this
		if self.Commons.isYes(session):

			if 'ConfirmIntent' in session.currentState:
				self.addIntentToHADialog(session.payload['input'], session=session)

			elif 'ConfirmSlotValue' in session.currentState:
				self.addSlotValueToCapturedIntent(self._captureSlotValue, session=session)

			elif 'requestingShouldWeAddSynonyms' in session.currentState:
				self.askSynonymValue(session)

			elif 'ConfirmSynonymValue' in session.currentState:
				self.addSynonymToSlot(self._captureSynonym, session=session)

		else:
			pointer = 0
			currentState = ""
			text = ""
			if 'ConfirmIntent' in session.currentState:
				currentState = 'requestingToMakeAIntent'
				text = 'intent'
				pointer = 1
			elif 'ConfirmSlotValue' in session.currentState:
				currentState = 'requestingSlotValue'
				text = 'slot'
				pointer = 1
			elif 'ConfirmSynonymValue' in session.currentState:
				currentState = 'requestingSynonymValue'
				text = 'Synonym'
				pointer = 1

			if pointer == 1:
				self.continueDialog(
					sessionId=session.sessionId,
					text=self.randomTalk(text='userSaidNo', replace=[text]),
					intentFilter=['UserRandomAnswer'],
					currentDialogState=currentState,
					probabilityThreshold=0.1
				)

			else:
				# user is finished adding data so let's write it to file
				self.rewriteJson(session=session)


	def addSlotValueToCapturedIntent(self, text, session):
		"""Adds slot values to the JSON file"""

		for i, suggestedSlot in enumerate(self._data['slotTypes']):
			if "haintent" in suggestedSlot['name'].lower():
				# Get all the current slot values in dialogTemplate file
				slotValue = suggestedSlot.get('values', list())

				# if the slot value doesn't already exist then let's save it
				if not text in slotValue:
					# create a dictionary and append the new slot value to original list
					dictValue = {'value': text, 'synonyms': []}
					slotValue.append(dictValue)
					# save it in self._data for later usage when we need to write to file
					self._data['slotTypes'][i]['values'] = slotValue

					# Now we know theres a slot name, let's add the correct syntax to the utterance, and save it for later writing
					self._captureUtterances = self._captureUtterances.replace(self._captureSlotValue,
																			  "{" + self._captureSlotValue + ":=>HAintent}")
					self._utteranceList.append(self._captureUtterances)
					self._data['intents'][self._utteranceID]['utterances'] = self._utteranceList

					# Now lets check if the user wants to also add synonyms for that slot
					self.askToUseSynonyms(session=session, word='a')

		return False


	def addSynonymToSlot(self, text, session):
		"""Add synonyms to the current slotValue"""

		for i, haIntentSlot in enumerate(self._data['slotTypes']):
			if "haintent" in haIntentSlot['name'].lower():

				# get any current slot vales and store it in a list
				synonymItem = haIntentSlot.get('values', list())

				# let's retrieve the actual synonyms now from the various values
				for x in synonymItem:
					# Now find the right slot to use
					if self._captureSlotValue in x['value'] and not text in synonymItem:
						# retrieve current synonyms from the slot and append to a list
						self._finalsynonymList = x.get('synonyms')
						self._finalsynonymList.append(self._captureSynonym)

						x['synonyms'] = self._finalsynonymList

						# find the right index to fit the new slot
						valueIndex = next(
							(index for (index, d) in enumerate(synonymItem) if d["value"] == self._captureSlotValue),
							None)
						# store the slot list until ready to write it
						self._data['slotTypes'][i]['values'][valueIndex] = x

				# Now about to ask if the user wants to add more synonyms.
				self.askToUseSynonyms(session=session, word='another')

		return False


	def askToUseSynonyms(self, session, word: str = None):

		self.continueDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='addSyn', replace=[word]),
			intentFilter=['AnswerYesOrNo'],
			currentDialogState='requestingShouldWeAddSynonyms'
		)


	def askSynonymValue(self, session):
		word = 'synonym'
		self.continueDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='addValue', replace=[word]),
			intentFilter=['UserRandomAnswer'],
			currentDialogState='requestingSynonymValue',
			probabilityThreshold=0.0
		)


	def rewriteJson(self, session):
		file = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')
		if not file:
			return False

		file.write_text(json.dumps(self._data, ensure_ascii=False, indent=4))
		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='finishUp')
		)

	def getDebugControl(self, key: str) -> bool:
		data: dict = json.loads(str(self.getResource('debugInfo/debugControl.json').read_text()))
		return data[key]

	# No longer used, retaining the method in case of reimplimenting jan 2022
	def getIconDebugInfo(self) -> dict:
		file = self.getResource('debugInfo/iconDebug.json')
		iconInfo = dict()
		for device in self._haDevicesFromAliceDatabase:
			iconInfo[device.getParam('entityName')] = {
				"deviceId"			: device.id,
				"entityName" 		: device.getParam('entityName'),
				"entityGroup"		: device.getParam('entityGroup'),
				"haDeviceType"		: device.getParam('haDeviceType'),
				"state"				: device.getParam('state'),
				"AliceDeviceType"	: device.deviceTypeName
			}

		file.write_text(json.dumps(iconInfo, ensure_ascii=False, indent='\t'))
		self.logInfo(f"![Red](So you have missing icons and need help ??)")
		self.logInfo(f"![green](Well you now have a debug file in {file} )")
		self.logInfo(f"![yellow](Either send that file to the requesting dev or...)")
		self.logInfo(f"![yellow](Copy the formatted contents of that file and paste it to pastebin, then send the link )")
		self.logInfo(f"![yellow](Also please hover over the missing icon in my home and advise what the device name is)")
		return iconInfo
