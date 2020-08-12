# HomeAssistant

[![Continous Integration](https://gitlab.com/project-alice-assistant/skills/skill_HomeAssistant/badges/master/pipeline.svg)](https://gitlab.com/project-alice-assistant/skills/skill_HomeAssistant/pipelines/latest) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=project-alice-assistant_skill_HomeAssistant&metric=alert_status)](https://sonarcloud.io/dashboard?id=project-alice-assistant_skill_HomeAssistant)

Connect alice to your home assistant

- Author: Lazza
- Maintainers: 
- Alice minimum Version: 1.0.0-b1
- Languages:
    en

**What this does :**

This skill allows you to connect your exisiting Home Assistant to Alice so you can turn on or off switches
It does this through using the RESTful API.

**What this skill will control**

You will be able to control an entity in HomeAssistant that is a existing switch.*entityName* in HA
*It will not listen to sensors or binary sensors at this stage.*
If you're wanting to get sensor data such as temperature sensors please consider flashing your sensor with 
the Tasmota skill and also installing the telemetry skill to store the data. That way Alice can respond with
 enviroment readings

"group.*entityName*" are also captured with this skill so you can "turn off kitchen lights" or smiliar
commands that control groups of switch.<entityName> devices. 

*Pre Req's* -
This skill uses HA friendly names to trigger commands. So if your friendly names in tasmota for example are "gardenlights"
then i suggest you fine tune that a little to read "garden lights" ( two words with no strange charactors). That way 
"turn off the garden lights" is more natural than " turn off gardenlights" which only sounds natural when drunk :)

**SetUp**
In Home Assistant:
1. create a long life token from your user profile screen. (Copy it and store it safe for now, you'll only get one chance to copy it)
2. Add the following to your configuration screen
  - api:
     - *your HomeassistantIP:port*/api/
    
**Example:**
- api:
  - http://192.168.4.1:8123/api/

**In Alice:**

1. Go to the Alice web ui
2. Click into Skills
3. Go to the HomeAssistant skill and click on -> Settings
4. In "HAaccessToken" field add your copied long life token
5. In "HAIpAddress" field add your HomeAssistant IP address (make sure you append /api to the address)
    - Example 192.168.4.1:8123/api
6. SIDE NOTE: For now all switches captured by Alice from HA will get installed in one location / room 
-  You will have to later go to "My Home" in the web Ui and move each switch to a appropriate room not critical
for now but, to keep a tidy house keeps Alice happy :)

7.Restart Alice and ask her to :
- "Hey Snips/Alice"
- "connect HomeAssistant"

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
- whats the state of the pool pump

**Possible Future additions**
- Add sun events like sunrise and sunset times
- Capture sensor and binary sensor data
- Tell you the IP of a requested device
