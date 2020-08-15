import threading
import re
import json
import requests

from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler
from requests import get
from core.util.model.TelemetryType import TelemetryType


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


	# todo Add Ipaddress
	# todo add further sensor support ?
	def __init__(self):
		self._entityId = list()
		self._broadcastFlag = threading.Event()
		self._newSynonymList = list()
		self._friendlyName = ""
		self._deviceState = ""
		self._entireList = list()
		self._entireSensorlist = list()
		self._dbSensorList = list()
		self._grouplist = list()
		self._action = ""
		self._entity = ""
		self._setup: bool = False

		super().__init__(databaseSchema=self.DATABASE)


	############################### INTENT HANDLERS #############################


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


	@IntentHandler('AddHomeAssistantDevices')
	def addHomeAssistantDevices(self, session: DialogSession):
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		# connect to the HomeAssistant API/States to retrieve entity names and values
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()
		if self.getConfig('DebugMode'):
			self.logDebug(f'{data}')
			print("")
			self.logInfo(f' You\'ll probably need to be in manual start mode to copy the above debug message - code triggered around line 80')
			print("")
		# delete and existing values in DB so we can update with a fresh list of Devices
		self.deleteAliceHADatabaseEntries()
		self.deleteHomeAssistantDBEntries()

		# Loop through the incoming json payload to grab data that we need
		for item in data:
			if isinstance(item, dict):
				if 'device_class' in item["attributes"]:
					sensorType = item["attributes"]["device_class"]
					sensorFriendlyName = item["attributes"]["friendly_name"]
					sensorentity = item["entity_id"]
					sensorValue = item["state"]

					dbSensorList = [sensorFriendlyName, sensorentity, sensorValue, sensorType]
					self._dbSensorList.append(dbSensorList)

				if 'entity_id' in item["attributes"]:

					entitiesInDictionaryList: list = item["attributes"]["entity_id"]
					listOfEntitiesToStore = entitiesInDictionaryList

					self._deviceState = item['state']

					grouplist = item['entity_id']

					if grouplist and 'switch.' in entitiesInDictionaryList:  # NOSONAR
						listOfEntitiesToStore.append(grouplist)

					self._entityId = listOfEntitiesToStore
					self._friendlyName = item["attributes"]["friendly_name"]

				for i in self._entityId:
					if 'switch.' in i:
						newfriendlyname = re.sub('switch.', '', i)
						newfriendlyname = re.sub('_', ' ', newfriendlyname)
						currentlist = [i, newfriendlyname, self._deviceState]
						self._entireList.append(currentlist)
					if 'group.' in i:
						groupFriendlyName = re.sub('group.', '', i)
						groupFriendlyName = re.sub('_', ' ', groupFriendlyName)
						grouplist = [i, groupFriendlyName]
						self._grouplist.append(grouplist)

		self.processHADataRetrieval()
		self.addSynomyns()
		self._setup = True
		if self._entireList:
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


	@IntentHandler('HomeAssistantAction')
	def homeAssistantSwitchDevice(self, session: DialogSession):
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		if 'on' in session.slotRawValue('OnOrOff') or 'open' in session.slotRawValue('OnOrOff'):
			self._action = "turn_on"
		elif 'off' in session.slotRawValue('OnOrOff') or 'close' in session.slotRawValue('OnOrOff'):
			self._action = "turn_off"

		if session.slotValue('switchNames'):
			uid = session.slotRawValue('switchNames')

			tempSwitchId = self.getDatabaseEntityID(uid=uid)
			self._entity = tempSwitchId['entityName']

		if self._action and self._entity:
			header, url = self.retrieveAuthHeader(urlPath='services/switch/', urlAction=self._action)

			jsonData = {"entity_id": self._entity}
			responce = requests.request("POST", url=url, headers=header, json=jsonData)
			if '200' in responce.text:
				self.endDialog(
					sessionId=session.sessionId,
					text=self.randomTalk(text='homeAssistantSwitchDevice', replace=[self._action]),
					siteId=session.siteId
				)
			else:
				self.logWarning(f' Switching that Device encountered a error')


	@IntentHandler('HomeAssistantState')
	def getDeviceState(self, session: DialogSession):
		if not self.checkConnection():
			self.sayConnectionOffline(session)
			return

		if 'sun' in session.slotRawValue('DeviceState') or 'sunrise' in session.slotRawValue('DeviceState') or 'sunset' in session.slotRawValue('DeviceState'):
			self.endDialog(
				sessionId=session.sessionId,
				text=self.randomTalk(text='getDeviceStateError'),
				siteId=session.siteId
			)
			return
		if 'DeviceState' in session.slots:
			entityName = self.getDatabaseEntityID(uid=session.slotRawValue("DeviceState"))

			# get info from HomeAssitant
			header, url = self.retrieveAuthHeader(urlPath='states/', urlAction=entityName["entityName"])
			stateResponce = requests.get(url=url, headers=header)
			# print(stateResponce.text) disable me at line 179-ish
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


	##################### POST AND GET HANDLERS ##############################


	def updateDBStates(self):
		"""Update entity states from a 5 min timer"""
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()

		# Loop through the incoming json payload to grab data that we need
		for item in data:
			if isinstance(item, dict):
				if 'device_class' in item["attributes"]:
					sensorFriendlyName = item["attributes"]["friendly_name"]
					sensorentity = item["entity_id"]
					sensorValue = item["state"]
					sensorType = item["attributes"]["device_class"]
					dbSensorList = [sensorFriendlyName, sensorentity, sensorValue, sensorType]

					self._dbSensorList.append(dbSensorList)

				if 'entity_id' in item["attributes"]:

					entitiesInDictionaryList: list = item["attributes"]["entity_id"]
					listOfEntitiesToStore = entitiesInDictionaryList
					self._deviceState = item['state']

					self._entityId = listOfEntitiesToStore

				for i in self._entityId:
					if 'switch.' in i:
						uid = re.sub('switch.', '', i)
						uid = re.sub('_', ' ', uid)
						currentlist = [i, uid, self._deviceState]
						self._entireList.append(currentlist)

		duplicateList = set(tuple(x) for x in self._entireList)
		finalList = [list(x) for x in duplicateList]

		for switchItem, uid, state in finalList:
			if self.getDatabaseEntityID(uid=uid):
				self.updateSwitchValueInDB(key=switchItem, value=state)

		for sensorName, entity, state, haClass in self._dbSensorList:

			if self.getDatabaseEntityID(uid=sensorName):
				self.updateSwitchValueInDB(key=sensorName, value=state)


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
		else:
			url = f'{self.getConfig("HAIpAddress")}{urlPath}'

		return header, url


	def checkConnection(self) -> bool:
		try:
			header, url = self.retrieveAuthHeader('na', 'na')
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

		values = {'typeID': 3, 'uid': uID, 'locationID': locationID, 'name': uID, 'display': "{'x': '10', 'y': '10', 'rotation': 0, 'width': 45, 'height': 45}"}
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
		self.DatabaseManager.delete(
			tableName=self.DeviceManager.DB_DEVICE,
			query='DELETE FROM :__table__ WHERE name IS NOT NULL ',
			callerName=self.DeviceManager.name
		)


	def deleteHomeAssistantDBEntries(self):
		self.DatabaseManager.delete(
			tableName='HomeAssistant',
			query='DELETE FROM :__table__ ',
			callerName=self.name
		)


	# noinspection SqlResolve
	def getDatabaseEntityID(self, uid):
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
		"""Returns a list of known friendly names"""
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
			text=self.randomTalk(text='sayListOfDevices', replace=[listLength]),
			siteId=self.getAliceConfig('deviceName')
		)


	def sayConnectionOffline(self, session: DialogSession):
		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='sayConnectionOffline'),
			siteId=session.siteId
		)


	def onFiveMinute(self):
		# "BME680":{"Temperature":25.0,"Humidity":62.7,"DewPoint":17.4,"Pressure":1016.1,"Gas":125.75},"PressureUnit":"hPa","TempUnit":"C"}}
		if not self.checkConnection():
			return

		self.updateDBStates()
		sensorDBrows = self.getSensorValues()
		for sensor in sensorDBrows:
			if not 'unavailable' in sensor['deviceState'] and not 'unknown' in sensor['deviceState']:
				if self.getConfig('DebugMode'):
					self.logDebug(f'device type in upDateDBStates is {sensor["deviceType"]} code triggered around line 499')
				newPayload = dict()
				siteID: str = sensor["uID"]
				siteIDlist = siteID.split()
				siteID = siteIDlist[0]
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

				if newPayload:
					try:
						self.sendToTelemetry(newPayload=newPayload, siteId=siteID)
					except Exception as e:
						self.logWarning(f'There was a error logging data for sensor {siteID} as : {e}')


	# add friendlyNames to dialog template as a list of synonyms
	def addSynomyns(self) -> bool:
		"""Add synonyms to the existing dialogTemplate file for the skill"""

		file = self.getResource(f'dialogTemplate/{self.activeLanguage()}.json')
		if not file:
			return False
		friendlylist = self.listOfFriendlyNames()

		# using duplicate var to capture things like sonoff 4 channel pro or multi button devices
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
		# method to reduce complexity value of addHomeAssistantDevices()
		# clean up any duplicates in the list
		duplicateList = set(tuple(x) for x in self._entireList)
		finalList = [list(x) for x in duplicateList]
		duplicateGroupList = set(tuple(x) for x in self._grouplist)
		finalGroupList = [list(x) for x in duplicateGroupList]
		# process group entities
		for group, value in finalGroupList:
			self.addEntityToDatabase(entityName=group, friendlyName=value, uID=value, deviceGroup='group')
		friendlyNameList = list()
		# process Switch entities
		for switchItem in finalList:
			self.addEntityToDatabase(entityName=switchItem[0], friendlyName=switchItem[1], deviceState=switchItem[2], uID=switchItem[1], deviceGroup='switch')

			self.AddToAliceDB(switchItem[1])
			friendlyNameList.append(switchItem[1])

		# Process Sensor entities
		for sensorItem in self._dbSensorList:
			self.addEntityToDatabase(entityName=sensorItem[1], friendlyName=sensorItem[0], uID=sensorItem[0], deviceState=sensorItem[2], deviceGroup='sensor', deviceType=sensorItem[3])


	def sendToTelemetry(self, newPayload: dict, siteId: str):

		for item in newPayload.items():
			teleType: str = item[0]
			teleType = teleType.upper()

			if self.getConfig('DebugMode'):
				self.logDebug(f'The {teleType} reading for the {siteId} is {item[1]} (code triggered line 580 ish)')  # uncomment me to see incoming temperature payload
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
				self.logInfo(f'A exception occured adding {teleType} reading: {e}')


	def onBooted(self) -> bool:

		if 'http://localhost:8123/api/' in self.getConfig("HAIpAddress"):
			self.logWarning(f'You need to update the HAIpAddress in Homeassistant Skill ==> settings')
			return False
		else:
			try:
				header, url = self.retrieveAuthHeader('na', 'na')
				response = get(self.getConfig('HAIpAddress'), headers=header)
				if self.getConfig('DebugMode'):
					self.logDebug(f'{response.text} - onBooted connection code')
					self.logDebug(f' The header is {header} ')
					self.logDebug(f'The Url is {url} ')
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
