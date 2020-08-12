import threading
import re
import json
import requests

from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler
from requests import get


class HomeAssistant(AliceSkill):
	"""
	Author: LazzaAU
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
			'uID TEXT'
		]
	}

	#todo Add Ipaddress
	def __init__(self):
		self._entityId = list()
		self._broadcastFlag = threading.Event()
		self._newSynonymList = list()
		self._friendlyName = ""
		self._deviceState = ""
		self._entireList = list()
		self._grouplist = list()
		self._action = ""
		self._entity = ""
		super().__init__(databaseSchema=self.DATABASE)


	############################### INTENT HANDLERS #############################

	@IntentHandler('AddHomeAssistantDevices')
	def addHomeAssistantDevices(self, session: DialogSession):
		self.endDialog(
			sessionId=session.sessionId,
			text='Ok let\'s do this, give me a moment to sort this out for you',
			siteId=session.siteId
		)
		# connect to the HomeAssistant API/States to retrieve entity names and values
		header, url = self.retrieveAuthHeader(urlPath='states')
		data = get(url, headers=header).json()
		#print(data)
		# delete and existing values in DB so we can update with a fresh list of Devices
		self.deleteAliceHADatabaseEntries()
		self.deleteHomeAssistantDBEntries()
		# Loop through the incoming json payload to grab data that we need
		for item in data:
			if isinstance(item, dict):
				if 'entity_id' in item["attributes"]:

					entitiesInDictionaryList: list = item["attributes"]["entity_id"]
					listOfEntitiesToStore = entitiesInDictionaryList
					self._deviceState = item['state']

					grouplist = item['entity_id']
					# print(f' grouplist is {grouplist} and is associated with {entitiesInDictionaryList}')

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

		duplicateList = set(tuple(x) for x in self._entireList)
		finalList = [list(x) for x in duplicateList]
		for group, value in self._grouplist:
			self.addEntityToDatabase(entityName=group, friendlyName=value, uID=value)

		for switchItem in finalList:
			self.addEntityToDatabase(entityName=switchItem[0], friendlyName=switchItem[1], deviceState=switchItem[2], uID=switchItem[1])
			self.AddToAliceDB(switchItem[1])

		self.addSynomyns()


	@IntentHandler('HomeAssistantAction')
	def homeAssistantSwitchDevice(self, session: DialogSession):
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
			self.logInfo(str(responce))
			self.endDialog(
				sessionId=session.sessionId,
				text='No drama\'s doing that now',
				siteId=session.siteId
			)


	@IntentHandler('HomeAssistantState')
	def getDeviceState(self, session: DialogSession):
		print(f'session payload is {session.slotRawValue("DeviceState")}')
		if 'sun' in session.slotRawValue('DeviceState') or 'sunrise' in session.slotRawValue('DeviceState') or 'sunset' in session.slotRawValue('DeviceState'):
			self.endDialog(
				sessionId=session.sessionId,
				text="Sorry for teasing you but i havent got those values yet. It\'s a future enhancement",
				siteId=session.siteId
			)
			return
		if 'DeviceState' in session.slots:
			entityName = self.getDatabaseEntityID(uid=session.slotRawValue("DeviceState"))

			# get info from HomeAssitant
			header, url = self.retrieveAuthHeader(urlPath='states/', urlAction=entityName["entityName"])
			stateResponce = requests.get(url=url, headers=header)
			# print(stateResponce.text)
			data = stateResponce.json()
			entityID = data['entity_id']
			entityState = data['state']
			# add the device state to the database
			self.updateSwitchValueInDB(key=entityID, value=entityState, uid=session.slotRawValue("DeviceState"))
			self.endDialog(
				sessionId=session.sessionId,
				text=f'The {session.slotRawValue("DeviceState")} state is currently {entityState}',
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


	def onBooted(self) -> bool:
		header, url = self.retrieveAuthHeader('na', 'na')
		response = get(self.getConfig('HAIpAddress'), headers=header)
		if '{"message": "API running."}' in response.text:
			self.logInfo(f'HomeAssistant Connected')
		else:
			self.logWarning(f'Issue connecting to HoemAssistant : {response.text}')
		return True


	def AddToAliceDB(self, uID: str):
		"""Add devices to Alices Devicemanager-Devices table.
		If location not known, create and store devices in a StoreRoom"""

		locationID = self.LocationManager.getLocation(location='StoreRoom')
		locationID = locationID.id

		values = {'typeID': 3, 'uid': uID, 'locationID': locationID, 'name': uID, 'display': "{'x': '10', 'y': '10', 'rotation': 0, 'width': 45, 'height': 45}"}
		self.DatabaseManager.insert(tableName=self.DeviceManager.DB_DEVICE, values=values, callerName=self.DeviceManager.name)


	@property
	def broadcastFlag(self) -> threading.Event:
		return self._broadcastFlag


	########################## DATABASE ITEMS ####################################
	def addEntityToDatabase(self, entityName: str, friendlyName: str, deviceState: str = None, ipAddress: str = None, deviceGroup: str = None, uID: str = None):
		# adds sensor data to the HomeAssistant database
		# noinspection SqlResolve
		self.databaseInsert(
			tableName='HomeAssistant',
			query='INSERT INTO :__table__ (entityName, friendlyName, deviceState, ipAddress, deviceGroup, uID) VALUES (:entityName, :friendlyName, :deviceState, :ipAddress, :deviceGroup, :uID)',
			values={
				'entityName'  : entityName,
				'friendlyName': friendlyName,
				'deviceState' : deviceState,
				'ipAddress'   : ipAddress,
				'deviceGroup' : deviceGroup,
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
			query='SELECT friendlyName FROM :__table__ ',
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


	# self.logDebug(f'Just updated Device state for {uid} to {value} ')


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


	# self.logDebug(f'Just updated Datebase by adding a ip of {ip} ')

	################# Extra Methods ###################
	def onFiveMinute(self):
		self.updateDBStates()


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
