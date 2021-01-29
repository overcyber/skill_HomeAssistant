# HomeAssistant

[![Continous Integration](https://gitlab.com/project-alice-assistant/skills/skill_HomeAssistant/badges/master/pipeline.svg)](https://gitlab.com/project-alice-assistant/skills/skill_HomeAssistant/pipelines/latest) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=project-alice-assistant_skill_HomeAssistant&metric=alert_status)](https://sonarcloud.io/dashboard?id=project-alice-assistant_skill_HomeAssistant)

Connect alice to your home assistant

- Author: Lazza
- Maintainers: 
- Alice minimum Version: 1.0.0-b2
- Languages:
    en

**What this does :**

This skill allows you to connect your exisiting Home Assistant (HA) to Alice. You can then turn on or off switches It
does this through using the RESTful API.

**What this skill will control**

You will be able to control an entity in HomeAssistant that is an existing switch.*entityName* in HA

It also captures sensor.<entityName> devices too but currently only utilises some sensor readings like temperature,
humidity etc. It does so by sending that data to Telemetry skill. You can then ask Alice what's the inside temperature
for example.

"group.*entityName*" are also captured with this skill, so you can "turn off kitchen lights" or smiliar commands that
control groups of switch.<entityName> devices.

"light.*entityName* devices are captured, "so you can change the colour of your lights or change the brightess levels (
if your device supports this feature)

Device states get updated every 5 minutes or when you ask " what's the state of the *device name*"
It will also tell you how long until sunset, sunrise, dusk and dawn.

*Pre Req's* -
- Alice version 1.0.0-B2 onwards 
- Make sure you're running the latest version of Home Assistant ( minimum tested version is 0107.5)
- Make sure you don't uninstall the Telemetry skill (it will self install if not already)
- This skill uses HA friendly names to trigger commands. So if your friendly name, for example are "gardenlights"
  then I suggest you fine tune that in HA a little to read "garden lights" ( two words with no strange characters). That
  way "turn off the garden lights" is more natural than " turn off gardenlights" which only sounds natural when drunk :)
  For now it also assumes your temperature sensors are called something like "inside temperature", "office temperature"
  and not "BME280 in the Shed". Based on current code, The latter would mean you'd have to ask Alice " what's the BME280
  temperature ", which is not very natural either :)

**Setup instructions are viewable via the skill**

*General usage (examples)*
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
- what position is the sun
- how long until dusk


- what's the ip of the kitchen light

- add home assistant dialogue (see instructions via the skill on this)

- change bedroom light to red
- dim the kitchen light to 10 percent
- set the pool light brightness to 100 percent
