import threading
import json
import requests

from datetime import datetime
from dateutil import tz
import pytz

from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler
from requests import get
from core.util.model.TelemetryType import TelemetryType
from core.commons import constants


class HomeAssistant(AliceSkill):
	"""
	Author: Lazza
	Description: Connect alice to your home assistant
	"""
	DATABASE = {
		'HomeAssistant': [
			'id integer PRIMARY KEY',
			'entityName TEXT NOT NULL',
			'friendlyName TEXT NOT NULL',
			'deviceState TEXT ',
			'ipAddress TEXT',
			'deviceGroup TEXT',
			'deviceType TEXT',
			'uID TEXT'
		]
	}


	# todo Add Ipaddress's
	# todo add further sensor support ?
	# todo double check code is Pshyco friendly/compatible
	def __init__(self):
		self._broadcastFlag = threading.Event()
		self._newSynonymList = list()
		self._friendlyName = ""
		self._deviceState = ""
		self._entireSensorlist = list()
		self._switchAndGroupList = list()
		self._dbSensorList = list()
		self._grouplist = list()
		self._action = ""
		self._entity = ""
		self._setup: bool = False
		self._sunState = tuple
		self._triggerType = ""

		super().__init__(databaseSchema=self.DATABASE)


	############################### INTENT HANDLERS #############################

	# Alice speaks what Devices she knows about
	@IntentHandler('WhatHomeAssistantDevices')
	def sayListOfDevices(self, session: DialogSession):
		currentFriendlyNameList = self.listOfFriendlyNames()
		activeFriendlyName = list()
		for name in currentFriendlyNameList:
			activeFriendlyName.append(name[0])

		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='sayListOfDevices', replace=[activeFriendlyName]),
			siteId=session.siteId
		)


	# Used for picking required data from incoming JSON (used in two places)
	def sortThroughJson(self, item):

		if 'device_class' in item["attributes"]:
			sensorType: str = item["attributes"]["device_class"]
			sensorFriendlyName: str = item["attributes"]["friendly_name"]
			sensorFriendlyName = sensorFriendlyName.lower()
			sensorEntity: str = item["entity_id"]
			sensorValue: str = item["state"]

			dbSensorList = [sensorFriendlyName, sensorEntity, sensorValue, sensorType]
			self._dbSensorList.append(dbSensorList)
		try:
			if 'DewPoint' in item["attributes"]["friendly_name"]:
				sensorType: str = 'dewpoint'
				sensorFriendlyName: str = item["attributes"]["friendly_name"]
				sensorFriendlyName = sensorFriendlyName.lower()
				sensorEntity: str = item["entity_id"]
				sensorValue: str = item["state"]

				dbSensorList = [sensorFriendlyName, sensorEntity, sensorValue, sensorType]
				self._dbSensorList.append(dbSensorList)
			if 'Gas' in item["attributes"]["friendly_name"]:
				sensorType: str = 'gas'
				sensorFriendlyName: str = item["attributes"]["friendly_name"]
				sensorFriendlyName = sensorFriendlyName.lower()
				sensorEntity: str = item["entity_id"]
				sensorValue = item["state"]

				dbSensorList = [sensorFriendlyName, sensorEntity, sensorValue, sensorType]
				self._dbSensorList.append(dbSensorList)

			if 'switch.' in item["entity_id"] or 'group.' in item["entity_id"] and item["entity_id"] not in self._switchAndGroupList:
				if 'switch.' in item["entity_id"]:
					switchFriendlyname: str = item["attributes"]["friendly_name"]
					switchFriendlyname = switchFriendlyname.lower()
					switchList = [item["entity_id"], switchFriendlyname, item['state']]
					self._switchAndGroupList.append(switchList)
				else:
					groupFriendlyname: str = item["attributes"]["friendly_name"]
					groupFriendlyname = groupFriendlyname.lower()
					groupList = [item["entity_id"], groupFriendlyname]
					self._grouplist.append(groupList)


		except Exception:
			pass


	@IntentHandler('AddHomeAssistantDevices')
	def addHomeAssistantDevices(self, session: DialogSession):
		if not self.checkConnection():  # If not connected to HA, say so and stop
			self.sayConnectionOffline(session)
			return

		# connect to the HomeAssistant API/States to retrieve entity names and values
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()

		if self.getConfig('DebugMode'):
			self.logDebug(f'********* COPY THE FOLLOWING JSON PAYLOAD **********')
			self.logDebug(f'')
			self.logDebug(f'{data}')
			self.logDebug(f'')
			self.logInfo(f' You\'ll probably need to be in manual start mode to copy the above debug message ')
			self.logDebug(f'')

		# delete and existing values in DB so we can update with a fresh list of Devices
		self.deleteAliceHADatabaseEntries()
		if '1.0.0-b1' in constants.VERSION:
			self.deleteAliceHADatabaseEntriesB1()
		else:
			self.deleteHomeAssistantDBEntries()

		# Loop through the incoming json payload to grab data that we need
		for item in data:
			if isinstance(item, dict):
				self.sortThroughJson(item=item)

		# Split above and below into other methods to reduce complexity complaint from sonar
		self.processHADataRetrieval()
		# write friendly names to dialogTemplate as synonyms
		self.addSynonyms()

		self._setup = True
		if self._switchAndGroupList:
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='addHomeAssistantDevices'),
				siteId=session.siteId
			)
			self.ThreadManager.doLater(
				interval=10,
				func=self.sayNumberOfDeviceViaThread
			)
		else:
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='addHomeAssistantDevicesError'),
				siteId=session.siteId
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
			uid = session.slotRawValue('switchNames')

			tempSwitchId = self.getDatabaseEntityID(uid=uid)
			self._entity = tempSwitchId['entityName']

		if self._action and self._entity:
			header, url = self.retrieveAuthHeader(urlPath='services/switch/', urlAction=self._action)

			jsonData = {"entity_id": self._entity}
			requests.request("POST", url=url, headers=header, json=jsonData)

			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='homeAssistantSwitchDevice', replace=[self._action]),
				siteId=session.siteId
			)


	# Get the state of a single device
	@IntentHandler('HomeAssistantState')
	def getDeviceState(self, session: DialogSession):
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		if 'DeviceState' in session.slots:
			entityName = self.getDatabaseEntityID(uid=session.slotRawValue("DeviceState"))

			# get info from HomeAssitant
			header, url = self.retrieveAuthHeader(urlPath='states/', urlAction=entityName["entityName"])
			stateResponce = requests.get(url=url, headers=header)
			# print(stateResponce.text) disable me at line 215-ish
			data = stateResponce.json()

			entityID = data['entity_id']
			entityState = data['state']
			# add the device state to the database
			self.updateSwitchValueInDB(key=entityID, value=entityState, uid=session.slotRawValue("DeviceState"))
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='getActiveDeviceState', replace=[session.slotRawValue("DeviceState"), entityState]),
				siteId=session.siteId
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

			if isinstance(item, dict) and 'friendly_name' in item["attributes"] and 'Sun' in item["attributes"]['friendly_name']:
				if self.getConfig('DebugMode'):
					self.logDebug(f'************* SUN DEBUG LOG ***********')
					self.logDebug(f'')
					self.logDebug(f'The sun JSON is ==> {item}')
					self.logDebug(f'')

				try:
					self._sunState = item["attributes"]['friendly_name'], item["attributes"]['next_dawn'], item["attributes"]['next_dusk'], item["attributes"]['next_rising'], item["attributes"]['next_setting'], item['state']
				except Exception as e:
					self.logDebug(f'Error getting full sun attributes from Home Assistant: {e}')
					return

		request = session.slotRawValue('sunState')
		if 'position' in request:
			horizon = self._sunState[5].replace("_", " the ")
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='sayHorizon', replace=[horizon]),
				siteId=session.siteId
			)

		elif 'dusk' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[2])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = 'Next dusk will be on'
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)

		elif 'sunrise' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[3])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = 'The next sunrise will be on'
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)

		elif 'dawn' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[1])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = 'The next dawn will be on'
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)

		elif 'sunset' in request:
			dateObj = self.makeDateObjFromString(sunState=self._sunState[4])
			result, hours, minutes = self.standard_date(dateObj)

			if result:
				stateType = 'The sun will go down on'
				self.saysunState(session=session, state=stateType, result=result, hours=hours, minutes=minutes)


	##################### POST AND GET HANDLERS ##############################


	def updateDBStates(self):
		"""Update entity states from a 5 min timer"""
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()

		# Loop through the incoming json payload to grab data that we need
		for item in data:

			if isinstance(item, dict):
				self.sortThroughJson(item=item)

		for switchItem, uid, state in self._switchAndGroupList:
			if self.getConfig('DebugMode'):
				self.logDebug(f'********* updateDBStates code **********')
				self.logDebug(f'')
				self.logDebug(f'I\'m updating {switchItem} with state {state}')
				self.logDebug(f'')

			# Locate entity in HA database and update it's state
			if self.getDatabaseEntityID(uid=uid):
				self.updateSwitchValueInDB(key=switchItem, value=state)

		for sensorName, entity, state, haClass in self._dbSensorList:

			if self.getConfig('DebugMode'):
				self.logDebug(f'')
				self.logDebug(f'i\'m updating the sensor {sensorName} with state {state}')

			# Locate sensor in the database and update it's value
			if self.getDatabaseEntityID(uid=sensorName):
				self.updateSwitchValueInDB(key=entity, value=state, uid=sensorName)


	def retrieveAuthHeader(self, urlPath: str, urlAction: str = None):
		"""
		Sets up and returns the Request Header file and url

		:param urlPath - sets the path such as services/Switch/
		:param urlAction - sets the action such as turn_on or turn_off

		EG: useage - header, url = self.requestAuthHeader(urlPath='services/switch/', urlAction=self._action)
		:returns: header and url
		"""

		header = {"Authorization": f'Bearer {self.getConfig("HAaccessToken")}', "content-type": "application/json", }

		if urlAction:
			url = f'{self.getConfig("HAIpAddress")}{urlPath}{urlAction}'
		else:  # else is used for checking HA connection and boot up
			url = f'{self.getConfig("HAIpAddress")}{urlPath}'

		return header, url


	def checkConnection(self) -> bool:
		try:
			header, url = self.retrieveAuthHeader(' ', ' ')
			response = get(self.getConfig('HAIpAddress'), headers=header)
			if '{"message": "API running."}' in response.text:
				return True
			else:
				self.logWarning(f'It seems HomeAssistant is currently not connected ')
				return False
		except Exception as e:
			self.logWarning(f'HomeAssistant connection failed with an error: {e}')
			return False


	########################## DATABASE ITEMS ####################################


	def AddToAliceDB(self, uID: str):
		"""Add devices to Alices Devicemanager-Devices table.
		If location not known, create and store devices in a StoreRoom"""

		locationID = self.LocationManager.getLocation(location='StoreRoom')
		locationID = locationID.id
		if '1.0.0-b1' in constants.VERSION:
			values = {'typeID': 3, 'uid': uID, 'locationID': locationID,  'name': self.name, 'display': "{'x': '10', 'y': '10', 'rotation': 0, 'width': 45, 'height': 45}"}
		else:
			values = {'typeID': 3, 'uid': uID, 'locationID': locationID, 'display': "{'x': '10', 'y': '10', 'rotation': 0, 'width': 45, 'height': 45}", 'skillName': self.name}
		self.DatabaseManager.insert(tableName=self.DeviceManager.DB_DEVICE, values=values, callerName=self.DeviceManager.name)


	def addEntityToDatabase(self, entityName: str, friendlyName: str, deviceState: str = None, ipAddress: str = None, deviceGroup: str = None, deviceType: str = None, uID: str = None):
		# adds sensor data to the HomeAssistant database
		# noinspection SqlResolve
		self.databaseInsert(
			tableName='HomeAssistant',
			query='INSERT INTO :__table__ (entityName, friendlyName, deviceState, ipAddress, deviceGroup, deviceType, uID) VALUES (:entityName, :friendlyName, :deviceState, :ipAddress, :deviceGroup, :deviceType, :uID)',
			values={
				'entityName'  : entityName,
				'friendlyName': friendlyName,
				'deviceState' : deviceState,
				'ipAddress'   : ipAddress,
				'deviceGroup' : deviceGroup,
				'deviceType'  : deviceType,
				'uID'         : uID
			}
		)


	# noinspection SqlResolve
	def deleteAliceHADatabaseEntries(self):
		""""
		 Deletes values from Alice's devices table if name value is HomeAssistant

		"""
		self.DatabaseManager.delete(
			tableName=self.DeviceManager.DB_DEVICE,
			query='DELETE FROM :__table__ WHERE skillName = "HomeAssistant" ',
			callerName=self.DeviceManager.name
		)

	#1.0.0-b1 compatibility
	def deleteAliceHADatabaseEntriesB1(self):
		""""
		 Deletes values from Alice's devices table if name value is HomeAssistant and user on b1

		"""
		self.DatabaseManager.delete(
			tableName=self.DeviceManager.DB_DEVICE,
			query='DELETE FROM :__table__ WHERE name = "HomeAssistant" ',
			callerName=self.DeviceManager.name
		)


	def deleteHomeAssistantDBEntries(self):
		""" Deletes the entire database table from the Homeassistant Table"""
		self.DatabaseManager.delete(
			tableName='HomeAssistant',
			query='DELETE FROM :__table__ ',
			callerName=self.name
		)


	# noinspection SqlResolve
	def getDatabaseEntityID(self, uid):
		"""Get entityName where uid is the same as requested"""

		# returns SensorId for all listings of a uid
		return self.databaseFetch(
			tableName='HomeAssistant',
			query='SELECT entityName FROM :__table__ WHERE uID = :uid ',
			method='one',
			values={
				'uid': uid
			}
		)


	# noinspection SqlResolve
	def getSwitchValueFromDB(self, uid, key):
		""" returns the state of the entityName

		:params uid = Device identification
		:params key = the entities name IE - switch.kitchen_light"""

		return self.databaseFetch(
			tableName='HomeAssistant',
			query='SELECT entityName FROM :__table__ WHERE uID = :uid and entityName = :key ',
			method='one',
			values={
				'uid': uid,
				'key': key
			}
		)


	# noinspection SqlResolve
	def listOfFriendlyNames(self):
		"""Returns a list of known friendly names that are switchable devices"""

		return self.databaseFetch(
			tableName='HomeAssistant',
			query='SELECT friendlyName FROM :__table__  WHERE deviceGroup != "sensor" ',
			method='all'
		)


	# noinspection SqlResolve
	def getSensorValues(self):
		"""Returns a list of known sensors"""

		return self.databaseFetch(
			tableName='HomeAssistant',
			query='SELECT * FROM :__table__  WHERE deviceGroup == "sensor" ',
			method='all'
		)


	# noinspection SqlResolve
	def rowOfRequestedDevice(self, friendlyName: str):
		"""Returns the row for the selected friendlyname

		:params friendlyName is for example kitchen light"""

		return self.databaseFetch(
			tableName='HomeAssistant',
			query='SELECT * FROM :__table__ WHERE friendlyName = :friendlyName ',
			values={'friendlyName': friendlyName},
			method='all'
		)


	# noinspection SqlResolve
	def updateSwitchValueInDB(self, key: str, value: str, uid: str = None):
		"""Updates the state of the switch in the selected row of database
		:params key = entityName
		:params uid = entity unique ID
		:params value is the new state of the switch"""

		self.DatabaseManager.update(
			tableName='HomeAssistant',
			callerName=self.name,
			query='UPDATE :__table__ SET deviceState = :value WHERE uID = :uid and entityName = :key',
			values={
				'value': value,
				'key'  : key,
				'uid'  : uid
			}
		)


	# Future enhancement
	# noinspection SqlResolve
	def updateDeviceIPInfo(self, ip: str, uid: str):
		"""updates the device with it's Ip address"""

		self.DatabaseManager.update(
			tableName='HomeAssistant',
			callerName=self.name,
			query='UPDATE :__table__ SET ipAddress = :ip WHERE uID = :uid ',
			values={
				'ip' : ip,
				'uid': uid
			}
		)


	################# General Methods ###################


	def sayNumberOfDeviceViaThread(self):
		currentFriendlyNameList = self.listOfFriendlyNames()
		activeFriendlyName = list()
		for name in currentFriendlyNameList:
			activeFriendlyName.append(name[0])
		listLength = len(activeFriendlyName)
		self.say(
			text=self.randomTalk(text='saynumberOfDevices', replace=[listLength]),
			siteId=self.getAliceConfig('deviceName')
		)


	def sayConnectionOffline(self, session: DialogSession):
		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='sayConnectionOffline'),
			siteId=session.siteId
		)


	def onFiveMinute(self):
		if not self.checkConnection():
			return

		self.updateDBStates()
		sensorDBrows = self.getSensorValues()

		for sensor in sensorDBrows:
			if not 'unavailable' in sensor['deviceState'] and not 'unknown' in sensor['deviceState']:

				newPayload = dict()
				siteID: str = sensor["uID"]
				siteIDlist = siteID.split()

				siteID = siteIDlist[0]
				# clean up siteID and make it all lowercase so less errors when using text widget
				siteID.replace(" ", "").lower()

				if 'temperature' in sensor["deviceType"]:
					newPayload['TEMPERATURE'] = sensor['deviceState']
				if 'humidity' in sensor["deviceType"]:
					newPayload['HUMIDITY'] = sensor['deviceState']
				if 'pressure' in sensor["deviceType"]:
					newPayload['PRESSURE'] = sensor['deviceState']
				if 'gas' in sensor["deviceType"]:
					newPayload['GAS'] = sensor['deviceState']
				if 'dewpoint' in sensor["deviceType"]:
					newPayload['DEWPOINT'] = sensor['deviceState']

				if self.getConfig('DebugMode'):
					self.logDebug(f'*************** OnFiveMinute Timer code ***********')
					self.logDebug(f'')
					self.logDebug(f'upDateDBStates Method = "deviceType" is {sensor["deviceType"]} ')
					self.logDebug(f'')

				if newPayload:
					try:
						self.sendToTelemetry(newPayload=newPayload, siteId=siteID)
					except Exception as e:
						self.logWarning(f'There was a error logging data for sensor {siteID} as : {e}')


	# add friendlyNames to dialog template as a list of synonyms
	def addSynonyms(self) -> bool:
		"""Add synonyms to the existing dialogTemplate file for the skill"""

		file = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')
		if not file:
			return False
		friendlylist = self.listOfFriendlyNames()

		# using this duplicate var to capture things like sonoff 4 channel pro or multi button devices
		duplicate = ''

		for mylist in friendlylist:
			if mylist[0] not in duplicate:
				self._newSynonymList.append(mylist[0])
			duplicate = mylist

		data = json.loads(file.read_text())

		if 'slotTypes' not in data:
			return False

		for i, friendlyname in enumerate(data['slotTypes'][0]['values']):

			data['slotTypes'][i]['values'][i]['synonyms'] = self._newSynonymList
			file.write_text(json.dumps(data, ensure_ascii=False, indent=4))
		return True


	def processHADataRetrieval(self):
		# extra method to reduce complexity value of addHomeAssistantDevices()
		# clean up any duplicates in the list
		duplicateList = set(tuple(x) for x in self._switchAndGroupList)

		finalList = [list(x) for x in duplicateList]

		duplicateGroupList = set(tuple(x) for x in self._grouplist)
		finalGroupList = [list(x) for x in duplicateGroupList]

		# process group entities
		for group, value in finalGroupList:
			self.addEntityToDatabase(entityName=group, friendlyName=value, uID=value, deviceGroup='group')

		# process Switch entities
		for switchItem in finalList:
			self.addEntityToDatabase(entityName=switchItem[0], friendlyName=switchItem[1], deviceState=switchItem[2], uID=switchItem[1], deviceGroup='switch')

			self.AddToAliceDB(switchItem[1])
		# friendlyNameList.append(switchItem[1])

		# Process Sensor entities
		for sensorItem in self._dbSensorList:
			self.addEntityToDatabase(entityName=sensorItem[1], friendlyName=sensorItem[0], uID=sensorItem[0], deviceState=sensorItem[2], deviceGroup='sensor', deviceType=sensorItem[3])


	def sendToTelemetry(self, newPayload: dict, siteId: str):

		for item in newPayload.items():
			teleType: str = item[0]
			teleType = teleType.upper()

			if self.getConfig('DebugMode'):
				self.logDebug(f'*************** Send to Telemetry code ***************')
				self.logDebug(f'')
				self.logDebug(f'The {teleType} reading for the {siteId} is {item[1]} ')  # uncomment me to see incoming temperature payload
				self.logDebug(f'')
			try:
				if 'TEMPERATURE' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.TEMPERATURE, value=item[1], service=self.name, siteId=siteId)
				elif 'HUMIDITY' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.HUMIDITY, value=item[1], service=self.name, siteId=siteId)
				elif 'DEWPOINT' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.DEWPOINT, value=item[1], service=self.name, siteId=siteId)
				elif 'PRESSURE' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.PRESSURE, value=item[1], service=self.name, siteId=siteId)
				elif 'GAS' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.GAS, value=item[1], service=self.name, siteId=siteId)
				elif 'AIR_QUALITY' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.AIR_QUALITY, value=item[1], service=self.name, siteId=siteId)
				elif 'UV_INDEX' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.UV_INDEX, value=item[1], service=self.name, siteId=siteId)
				elif 'NOISE' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.NOISE, value=item[1], service=self.name, siteId=siteId)
				elif 'CO2' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.CO2, value=item[1], service=self.name, siteId=siteId)
				elif 'RAIN' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.RAIN, value=item[1], service=self.name, siteId=siteId)
				elif 'SUM_RAIN_1' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.SUM_RAIN_1, value=item[1], service=self.name, siteId=siteId)
				elif 'SUM_RAIN_24' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.SUM_RAIN_24, value=item[1], service=self.name, siteId=siteId)
				elif 'WIND_STRENGTH' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.WIND_STRENGTH, value=item[1], service=self.name, siteId=siteId)
				elif 'WIND_ANGLE' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.WIND_ANGLE, value=item[1], service=self.name, siteId=siteId)
				elif 'GUST_STREGTH' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.GUST_STRENGTH, value=item[1], service=self.name, siteId=siteId)
				elif 'GUST_ANGLE' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.GUST_ANGLE, value=item[1], service=self.name, siteId=siteId)
				elif 'Illuminance' in teleType:
					self.TelemetryManager.storeData(ttype=TelemetryType.LIGHT, value=item[1], service=self.name, siteId=siteId)

			except Exception as e:
				self.logInfo(f'An exception occured adding {teleType} reading: {e}')


	def onBooted(self) -> bool:

		if 'http://localhost:8123/api/' in self.getConfig("HAIpAddress"):
			self.logWarning(f'You need to update the HAIpAddress in Homeassistant Skill ==> settings')
			self.say(
				text=self.randomTalk(text='sayConfigureMe'),
				siteId=self.getAliceConfig('deviceName')
			)
			return False
		else:
			try:
				header, url = self.retrieveAuthHeader('na', 'na')
				response = get(self.getConfig('HAIpAddress'), headers=header)

				if self.getConfig('DebugMode'):
					self.logDebug(f'*************** OnBooted code ***********')
					self.logDebug(f'')
					self.logDebug(f'{response.text} - onBooted connection code')
					self.logDebug(f' The header is {header} ')
					self.logDebug(f'The Url is {url} (note: nana on the end is ignored in this instance)')
					self.logDebug(f'')

				if '{"message": "API running."}' in response.text:
					self.logInfo(f'HomeAssistant Connected')
					return True

				else:
					self.logWarning(f'Issue connecting to HomeAssistant : {response.text}')

					return False

			except Exception as e:
				self.logWarning(f'HomeAssistant failed to start. Double check your settings in the skill {e}')
				return False


	@property
	def broadcastFlag(self) -> threading.Event:
		return self._broadcastFlag


	@staticmethod
	def makeDateObjFromString(sunState: str):
		"""Takes HA's UTC string and turns it to a datetime object"""

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


	def saysunState(self, session, state: str, result, hours, minutes):
		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='saySunState', replace=[state, result, hours, minutes]),
			siteId=session.siteId
		)


	########################## TELEMTRY PROCESSING #############################

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
		if '1.0.0-b1' in constants.VERSION:
			self.logDebug(f'Sorry but Telemetry High/Low reports only available on version 1.0.0-b2 or greater')
			return
		trigger = kwargs['trigger']
		value = kwargs['value']
		threshold = kwargs['threshold']
		area = kwargs['area']

		if 'upperThreshold' in trigger:
			trigger = 'high'
		else:
			trigger = 'low'

		if not 'freezing' in self._triggerType:
			self.say(
				text=f'ATTENTION. Your {self._triggerType} readings have exceeded the {trigger} limit of {threshold} with a reading of {value}',
				siteId=self.getAliceConfig('deviceName')
			)
		else:
			self.say(
				text=self.randomTalk(text='sayTelemetryFreezeAlert', replace=[area, value]),
				siteId=self.getAliceConfig('deviceName')
			)
