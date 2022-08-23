## SetUp Steps --- In Home Assistant: ---

1. Create a long life token from your user profile screen. (Copy it and store it safely for now as you'll 
only get once chance to copy it)
2. Add the following to your Home Assistant configuration.yaml file

api;

&nbsp;&nbsp;&nbsp; http://your-HomeassistantIP:port/api/

#### Example:

api:

&nbsp;&nbsp;&nbsp; http://192.168.4.1:8123/api/

#### NOTE: 
*the /api/ not just /api*

while in there, check if you have in your Home Assistant yaml

- default_config:

or 
- sun:

Add either of those to your Home Assistant configuration.yaml, if you'd like Alice to tell you about sun events

- Now restart Home Assistant and carry on with the below Alice setup

## SetUp Steps --- In Alice: ----

1. Go to the Alice web ui
2. Click into Skills
3. Install the HomeAssistant skill
4. Once installed, Go to the HomeAssistant skill and click on -&gt; Settings
5. In "HAaccessToken" field, add your copied long life token
6. In "HAIpAddress" field, add your HomeAssistant IP address - make sure you append /api/
 
#### Example http://192.168.4.1:8123/api/

7. Restart Alice


#### SIDE NOTE:
For now all devices captured by Alice from HA will get installed in one location
- You may want to at some stage, go to "My Home" in the web Ui and move each device to an appropriate location. To keep
  a tidy house keeps Alice happy :)

Once alice restarts you can then ask her :

- "Hey Snips/Alice"
- "Setup home assistant skill" 
or
- "configure the home assistant skill"

You really only need to ask that once. By asking that she will


1. Get the list of device entities from Home Assistant
2. Write them to Alices devices Database
3. Takes all the friendly names and automatically writes them to dialogTemplate file

Once setup is completed (takes 30 seconds or so) and **you restart alice** again for training.

You should be able to ask 

- "Hey Alice/Snips"
- "Turn off / on the entity Friendly name"

#### Example: turn off the bathroom light

- "Hey Alice/Snips"
- "What's the state of the pool pump"

### Usage:

Some examples of what to say

*For initial set up* 

- "Add my home assistant devices"
or
- "Configure the home assistant skill"

*General usage*

- Turn on the Bedroom light
- Turn off the Bathroom light
- Close the bedroom blinds 
- Open the garage door
- What's the state of the garage door
- What home assistant devices do you know
- Tell me what my home assistant devices are please
- What can you turn on or off
- When is sunrise
- When is sunset
- What position is the sun
- How long until dusk
- What's the ip of the kitchen light
- Change the bedroom light to blue
- set the kitchen light to 50 percent brightness


### Configuration Tips -- Manually setting up sensors

Currently, the sensors from HA that will get captured are "

*sensor.sensor_name* and *binary_sensor.sensor_name* devices

EG: "sensor.inside_temperature".

To be captured however they must have a "device_class" attribute assigned to them.

HA will tend to automatically do this for you in some cases. Especially if you're running HASS.IO and the MQTT Addon and
Tasmota firmware on your devices. However, you may find that currently not all sensors are being captured.

There's potentially at least two common reasons for this

1. Currently only sensors that have a function in the HA skill are concentrated on. This will change as the 
skill progresses. Devices that have a device_class of , temperature, humidity, gas, illuminance, pressure, dewpoint,
battery, power, current, voltage, motion are used and can be reported on by Alice.

**NOTE**: HA skill may collect other sensor's above what i've listed. So if you notice some sensors
added to Home Assistant that don't display a Icon, Please let lazza in discord
know about these sensors and i'll add that support.
 

2. You've manually configured a MQTT device in the yaml but have not added a "device_class" attribute 



If manually creating sensors in your home assistant configuration.yaml be sure to add a "device_class" such as the below
example and Alice should pick up on that the next time you ask Alice to
"configure the home Assistant skill " and then retrain her.

#### Example configuration.yaml entry
```

sensor:

     - platform: mqtt

       name: "Inside Temperature"

       state_topic: "your sensor state topic here"

       unit_of_measurement: "°C"

       device_class: temperature

     - platform: mqtt

       name: "inside Humidity"

       state_topic: "your sensor state topic here"

       unit_of_measurement: "%"

       device_class: humidity

     - platform: mqtt

       name: "inside Pressure"

       state_topic: "your sensor state topic here"

       unit_of_measurement: "mb"
```

For available device classes, have a look here <a href="https://www.home-assistant.io/integrations/sensor/" target="_blank">Sensors</a>
and here 
<a href="https://www.home-assistant.io/integrations/binary_sensor/" target="_blank">Binary sensors</a>

#### Note:
state_topic will of course be the topic of your mqtt device :)

### Accessing sensor data that Alice captures but currently does nothing with

So let's say for example you know Alice is capturing your outside motion sensor and storing that data in the
HomeAsistant database, and you want to use that value in your own skill to do something.

All current device states that Alice knows about (from HA skill) are stored in the database. However, every 5 minutes
they are also written to a file in the skills' directory called "currentStateOfDevices.json"

This will allow you to grab the state of all devices via your own skill or perhaps via the "file in" node of Node red,
without the need to extract it from the database directly.

### Creating Extra intents on the fly

There are things in HA that don't get reported on by the API. Such as the RMpro for RF signals that you might use to do
certain things like turn on a tv, or tune tv stations rather than using your tv remote. In that situation and many
others Alice can create a "trigger" keyword that you use for what ever purpose you like.

For the below explanation and example let's assume we have a Node Red flow in HA that sends an RF command to the TV when
we send that flow a trigger of "tv on"

In Alice via the HA skill you can create an intent on the fly and assign it the slot value "tv on"
Ask Alice -->> "update home assistant dialogue" or "add more home assistant dialogue"

Then follow her prompts, she will ask you for the intent to use, in which case you could reply with
"turn the tv on"
She will then ask you to pick a slot value from that intent, so say "tv on" and then say yes when prompted

She will then ask if you want to add synonyms. We could now say "television on" and say yes when prompted. Then add
another synonym when prompted if you like. Otherwise, when you say "no" to adding another synonym She will then write to
you dialogTemplate folder the appropriate utterances and slot details.

Restart, and she will go into training.

When she's trained, now ask her " turn the tv on"
She will then send a MQTT message on the topic "ProjectAlice/HomeAssistant" with a payload of "tv on"

In Home Assistant.... you can now use something like Node Red and a "MQTT node" that goes into a "switch node"
Configure the MQTT node to connect to Alices MQTT broker IP and listen to the topic of "ProjectAlice/HomeAssistant"

Then when Alice sends a message on the topic "ProjectAlice/HomeAssistant" you should see the payload of "tv on"
You can then send that payload to the switch node and finally to the appropriate flow to allow the RF code to be
triggered which should hopefully then .... turn the "tv on" :).

Obviously this is just one simple example. Let your mind be creative, and you could think up multiple things to do

Basically Alice is just going to send a keyword that you can intercept and trigger a Node Red flow to do what ever you
want it to.

## Ignore device discovery 

Let's say you want to use the Phillips Hue skill for example rather than HA skill to control those devices. You can skip adding those devices 
to the HA skill by adding a custom attribute to that device in Home assistant and Alice will skip adding it.

To do that:

- Go to HomeAssistant.
- Go to the "configuration" menu
- Click into "customizations"
- Select the device you want to ignore from the drop down list
- Choose "pick an attribute to override" and select "other"
- For attribute name type in "AliceIgnore" (case-sensitive)
- For attribute value type in "True"

In the future if you want to allow Alice to add that device, change True to False and then reconfigure alice with a "
configure home assistant skill". This is also handy if alice keeps adding a 
pointless device to your My home screen. You can delete it from my home but it will return
next time you configure HA skill. So in this case add the AliceIgnore steps above for that device in Home Assistant.


## Icons - and what they are

Icon - Description - state(where applicable):

- Battery - battery icon for device_class battery and device_class power

- Green circle with a tick - Input_boolean, state= on

- Red circle with Black X - Input_boolean, state = off

- Green On button - switch.entity - state = on

- Red Off button - switch.entity - state = off

- Green Toggle switch - group.entity - state = on

- Red toggle switch - Group.entity - state = off

- yellow light bulb - light.entity

- co2 sensor - device_ class = gas

- humidity sensor - device_class humidity 

- thermometer - device class temperature

- motion sensor - sensor with man under it - device_class motion

- dewpoint sensor

- pressure gauge - device_class pressure

- sensor with light bulb = device_class illuminance

- voltage sign - device_class voltage

- electrical sparks - device_class current

**Icons that will change based on high alert signal from telemetry:**

- Gas (co2)
- humidity
- temperature

## Debug Control

In the skill settings you have a couple of options for monitoring debug info.

1. ViewJsonPayload - This will write your incomming data from HA into a file found in
your skill directory. Handy for seeing what comes from your HA and diagnosing why some things might not get captured
   
2. debugMode - This will print debug information to your syslog. Good for seeing what is happening behind
   the scenes in regards too HA skill doing stuff
   
NOTE on #2: debug mode prints alot of syslog debug messages (must also have debug mode enabled in alice admin)
However, to personalise that a litle there is also a debugControl.json file found in your
skill directory.

By default, those values are set to true so that all debug messages are displayed
Set to false in order to stop a specific type of debug message from displaying

EG: "header" : false, won't display the header debug message you get on boot up but will display the others

Some debug messages don't have this control such as synonym creation. This is ok as it only happens when you add 
devices anyway so won't be a regular event


## Adding and displaying water tank levels

The HA skill now comes with the ability to display tank levels of what ever you have set up.
This has been based on, and tested on, using digital non contact level "sensors" configured with Tasmota sending MQTT
payload to Home Assistant (search google for non contact water level sensors) . If you're using float "switches" you may have to do some tweaking in HA so that they become a 
sensor.sensorname_tank1 device rather than a switch.switchname_tank1 device and of course follow the below setup guide. 

Perhaps you have a 
- Fish tank you want to monitor the level of ?
- or maybe you live remotely and want to check on rainwater tank levels ?
- or perhaps you have a boat or a caravan and want to monitor fresh or grey water tanks or even fuel tanks?

The possibilities could be many. The HA skill will now display in "my home" those tank levels in four different version.

1. 4 different levels , for those that have 4 sensors on the water tank.
	- Full
	- 75 % full
	- 50 % full
	- 25 % full
	- Empty (When all sensors are "off")
	
2. 3 Different levels
	- Full
	- 2/3rds Full
	- 1/3rd Full
	- Empty (When all sensors are "off")
	
3. 2 different levels
	- High
	- Low
	- Empty ( When both sensors read "off")
	
4. 1 level
	- High
	- Empty ( When the high level trigger is "off")

Tank Level setup

For the tank level gauges to work in "My Home" there are a few setup steps to take. Because the icons have the ability to be 
customised, that means there are a few specific steps to get them to display correctly.

- In HA the name of the device should be called whatever you want but with a tank number on the end of it.

### Example is,
"sensor.Fresh_Water_Tank_1" and "sensor.Fresh_Water_Tank_2"
  
Reason being is... The code will then detect if you have more than 1 fresh_Water_Tank (in this example) and display the
appropriate icon IE: Fresh water Tank 1 or Fresh Water Tank 2. Leaving the number off won't hurt but will just 
always display the tank 1 image

### NOTE:
tank2 icons have only been done for fourLevelTank devices (refer devices/img/TankLevel/FourLevels).
If you need more tank icons or more icons for other tankLevel devices
please edit the provided svg files and create as many more png files as required (following the existing naming format)

- Once the device has been added to HA, edit the customize.yaml file in home assistant and add the following attribute
	- Attribute name -> HaDeviceType
	- Attribute Value -> tankLevel4
	
Change out the value tankLevel4 with tankLevel3 or tankLevel2 or tankLevel1 depending on how many sensors you have on that tank

### NOTE:
Attribute name and value are case-sensitive so add them exactly as per above example. Without adding this attribute
HA skill WILL NOT pick up on it being a tank level and therefore will not display in My Home.

- The json payload that alice expects from a tankLevel device is in the following format (example is for a 3 level tank)

```{"Switch1": "ON", "Switch2": "OFF", "Switch3": "OFF", "Time": "2021-03-02T10:31:58"}```

You can achieve this easily by using a similar configuration in your configuration.yaml file in HA as per below.
### NOTE:
The "time" key is ignored and not important
```
sensor:
  - platform: mqtt
    name: Fresh Water Tank 1
    state_topic: "FreshWaterTank1/tele/SENSOR"
    value_template: "{{ value_json | tojson }}"
    json_attributes_topic: "FreshWaterTank1/tele/HASS_STATE"
    json_attributes_template: "{{ value_json | tojson }}"
```
Obviously adjust your topics and name to suit your set up.

In ```ProjectAlice/skills/HomeAssistant/devices/img/svgFiles```
There are the actual svg files used for creating the icons. 
Feel free to modify the svg files as required then save them as png files
to suit your needs EG: maybe you want to change the colors ? change the tank name etc

IMPORTANT: The downside to displaying specific images is you'll need to manually rename the image files to suit.
here's the steps involved.

Let's assume you have named your "rain water tank sensors" as sensor.Rain_Water_Tank_1 for this example and it
has 4 sensors on it. Therefore you have made the attribute as per above as tankLevel4.

1. Go to ```ProjectAlice/skills/HomeAssistant/devices/img/svgFiles```
2. Modify the FourLevelTankTemplate.svg file as you please
3. When finished editing you will save it in ```ProjectAlice/skills/HomeAssistant/devices/img/TankLevel/FourLevels/``` as a .png file following the below steps
4. For this example save the file as rainwatertank-1-xxx.png
5. Example : rainwatertank-1-Full.png
    (the -1- part denotes the tank number, if you had a second rainwater tank it would be 
    rainwatertank-2-Full.png) Note the lowercase name with no spaces. For a four level sensor you will also be doing the same for 
   - a Empty.png image
   - a 25.png image (denoting 25% full)
   - a 50.png image (denoting 50% full)
   - a 75.png image (denoting 75% full)
   
The syntax is... devices displayname (in lowercase with no spaces) - tanknumber - theLevel.png
By following the above steps... once you "configure home assistant skill" Alice should
hopefully display tank level icons in your "my home" on the web UI. 

#### You could also then consider writing your own skills to do something with those tank levels.

### Example
- "Hey Alice"  "how full is my rain water tank ?"
- on the hour, have alice check tank levels and have her report the fish are dying cause there's no water left :)
- Have alice turn a pump on when a tank reaches a certain level and off again when full
etc.
  

