# HomeAssistant

[![Continous Integration](https://gitlab.com/project-alice-assistant/skills/skill_HomeAssistant/badges/master/pipeline.svg)](https://gitlab.com/project-alice-assistant/skills/skill_HomeAssistant/pipelines/latest) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=project-alice-assistant_skill_HomeAssistant&metric=alert_status)](https://sonarcloud.io/dashboard?id=project-alice-assistant_skill_HomeAssistant)

Connect alice to your home assistant

- Author: Lazza
- Maintainers: 
- Alice minimum Version: 1.0.0-b2
- Languages:
    en

**What this does :**

This skill allows you to connect your exisiting Home Assistant (HA) to Alice so you can turn on or off switches
It does this through using the RESTful API.

**What this skill will control**

You will be able to control an entity in HomeAssistant that is a existing switch.*entityName* in HA

It also captures sensor.<entityName> devices too but currently only utilises some sensor readings like temperature, 
humidity etc. It does so by sending that data to Telemetry skill so you can ask Alice what's the inside 
temperature for example. (still work in progress but the data is there)

"group.*entityName*" are also captured with this skill so you can "turn off kitchen lights" or smiliar
commands that control groups of switch.<entityName> devices. 

Device states get updated every 5 minutes or when you ask " whats the state of the *device name*"
It will also tell you how long until sunset, sunrise, dusk and dawn.

*Pre Req's* -
- Alice version 1.0.0-B2 onwards 
- Make sure you're running the latest version of Home Assistant ( minimum is version 0107.5)
- Make sure you also have installed the Telemetry skill
- This skill uses HA friendly names to trigger commands. So if your friendly name, for example are "gardenlights"
then i suggest you fine tune that in HA a little to read "garden lights" ( two words with no strange characters).
 That way "turn off the garden lights" is more natural than " turn off gardenlights" which only sounds natural
  when drunk :)
For now it also assumes your temperature sensors are called something like "inside temperature", "office temperature"
and not "BME280 in the Shed". Based on current code, The latter would mean you'd have to ask 
Alice " whats the BME280 temperature ", which is not very natural either :)


**SetUp**

**---- In Home Assistant: ----**

1. Create a long life token from your user profile screen. (Copy it and store it safe for now, you'll only get one chance to copy it)
2. Add the following to your Home Assistant configuration.yaml file
  - api:
     - *your HomeassistantIP:port*/api/
 
**Example:**
- api:
  - http://192.168.4.1:8123/api/

NOTE the /api/ not just /api 

while in there check if you have in your yaml
  - default_config:

if not either add that or add

  - :sun

(That will give you sun events in Alice if you want that feature)

- Now restart Home Assistant and carry on with the below Alice setup


**SETUP steps for Alice**

**---- In Alice: ----**

1. Go to the Alice web ui
2. Click into Skills
3. Install the HomeAssistant skill
4. Once installed, Go to the HomeAssistant skill and click on -> Settings
5. In "HAaccessToken" field, add your copied long life token
6. In "HAIpAddress" field, add your HomeAssistant IP address (make sure you append /api/ to the address)
    - Example http://192.168.4.1:8123/api/
7. Restart Alice 

SIDE NOTE: For now all switches captured by Alice from HA will get installed in one location / room 
-  You will have to later go to "My Home" in the web Ui and move each switch to a appropriate room not critical
for now but, to keep a tidy house keeps Alice happy :)

Once alice restarts you can then ask her :

- "Hey Snips/Alice"
- "setup home assistant skill" 

You really only need to ask that once. By asking that she will

1. Get the list of switch entities from Home assistant
2. Write them to Alices new HomeAssistant Database
3. Add those devices to Alice's Database ( so they show in My home and are Alice aknowledgable)
4. Takes all the friendly names and automatically writes them to dialogTemplate file as synonyms

Once setup is completed (takes 30 seconds or so) you should be able to ask 
- "Hey Alice/Snips"
- "Turn off/on the *entity Friendly name*"

EG: turn off the bathroom light

- "Hey Alice/Snips"
- what's the state of the pool pump

**Future additions**
- Capture various types of sensor data for possble use in other skills ?
- Tell you the IP of a requested device

**Usage:**
Some examples of what to say 
*for set up* 
- "Add my home assistant devices"
- "Configure the home assistant skill"

*General usage*
- Turn on the Bedroom light
- Turn off the Bathroom light
- close the bedroom blinds 
- open the garage door

- what's the state of the garage door

- "What home assistant devices do you know",
- "tell me what my home assistant devices are please",
- "what can you turn on or off"

- when is sunrise
- when is sunset
- what state is the sun
- how long until dusk

- whats the ip of the kitchen light
