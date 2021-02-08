<span style="color: #ff0000;"><strong>SetUp Steps </span><span style="color: #0000ff;">--- In Home Assistant: ---</strong></span>
<ol>
<li>Create a long life token from your user profile screen. (Copy it and store it safely for now as you'll 
only get once chance to copy it)</li>
<li>Add the following to your Home Assistant configuration.yaml file</li>
</ol>
api;

&nbsp;&nbsp;&nbsp; http://your-HomeassistantIP:port/api/

<span style="color: #00ff00;">Example:</span>

api:

&nbsp;&nbsp;&nbsp; http://192.168.4.1:8123/api/

<span style="color: #ffff00;">NOTE</span> the /api/ not just /api

while in there, check if you have in your Home Assistant yaml
<ul>
<li>default_config:

or </li>
<li>sun:</li>
</ul>
Add either of those to your Home Assistant configuration.yaml, if you'd like Alice to tell you about sun events

- Now restart Home Assistant and carry on with the below Alice setup

<span style="color: #ff0000;"><strong>SetUp Steps </span><span style="color: #0000ff;">--- In Alice: ----</strong></span>
<ol>
<li>Go to the Alice web ui</li>
<li>Click into Skills</li>
<li>Install the HomeAssistant skill</li>
<li>Once installed, Go to the HomeAssistant skill and click on -&gt; Settings</li>
<li>In "HAaccessToken" field, add your copied long life token</li>
<li>In "HAIpAddress" field, add your HomeAssistant IP address - make sure you append /api/
 
<span style="color: #00ff00;">Example</span> http://192.168.4.1:8123/api/</li>
<li>Restart Alice</li>
</ol>

<span style="color: #ffff00;">SIDE NOTE:</span>
For now all devices captured by Alice from HA will get installed in one location
- You may want to at some stage, go to "My Home" in the web Ui and move each device to an appropriate location. To keep
  a tidy house keeps Alice happy :)

Once alice restarts you can then ask her :
<ul>
<li>"Hey Snips/Alice"</li>
<li>"Setup home assistant skill" </li>
or
<li>"configure the home assistant skill"</li>
</ul>
You really only need to ask that once. By asking that she will

<ol>
<li>Get the list of device entities from Home Assistant</li>
<li>Write them to Alices devices Database</li>
<li>Takes all the friendly names and automatically writes them to dialogTemplate file</li>
</ol>
Once setup is completed (takes 30 seconds or so) and <strong>you restart alice</strong> again for training.

You should be able to ask 

- "Hey Alice/Snips"
- "Turn off / on the entity Friendly name"

<span style="color: #00ff00;">Example:</span> turn off the bathroom light

- "Hey Alice/Snips"
- "What's the state of the pool pump"

<span style="color: #ff6600;">Usage:</span>

Some examples of what to say

<em>For initial set up</em> 

- "Add my home assistant devices"
or
- "Configure the home assistant skill"

<em>General usage</em>
<ul>
<li>Turn on the Bedroom light</li>
<li>Turn off the Bathroom light</li>
<li>Close the bedroom blinds</li>
<li>Open the garage door</li>
<li>What's the state of the garage door</li>
<li>What home assistant devices do you know</li>
<li>Tell me what my home assistant devices are please</li>
<li>What can you turn on or off</li>
<li>When is sunrise</li>
<li>When is sunset</li>
<li>What position is the sun</li>
<li>How long until dusk</li>
<li>What's the ip of the kitchen light</li>
<li>Change the bedroom light to blue</li>
<li>set the kitchen light to 50 percent brightness</li>
</ul>

<span style="color: #ff0000;">Configuration Tips</span> #####<span style="color: #0000ff;"></strong> Manually setting up
sensors</span></strong> #####

Currently, the sensors from HA that will get captured are "<i>sensor.sensor_name"</i> and
<i>binary_sensor.sensor_name</i> devices

EG: "sensor.inside_temperature".

To be captured however they must have a "device_class" attribute assigned to them.

HA will tend to automatically do this for you in some cases. Especially if you're running HASS.IO and the MQTT Addon and
Tasmota firmware on your devices. However, you may find that currently not all sensors are being captured.

<span style="color: #ff6600;">There's potentially at least two common reasons for this</span>
<ol>
<li> Currently only sensors that have a function in the HA skill are concentrated on. This will change as the 
skill progresses. Devices that have a device_class of , temperature, humidity, gas, illuminance, pressure, dewpoint,
battery, power, current, voltage, motion are used and can be reported on by Alice.

NOTE: HA skill may collect other sensor's above what i've listed. So if you notice some sensors
added to Home Assistant that don't display a Icon, Please let lazza in discord
know about these sensors and i'll add that support.
 </li>

<li> You've manually configured a MQTT device in the yaml but have not added a "device_class" attribute </li>
</ol>


If manually creating sensors in your home assistant configuration.yaml be sure to add a "device_class" such as the below
example and Alice should pick up on that the next time you ask Alice to
"configure the home Assistant skill " and then retrain her.

<span style="color: #00ff00;">Example configuration.yaml entry</span>
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
and here <a href="https://www.home-assistant.io/integrations/binary_sensor/"target="_blank">Binary sensors</a>

<span style="color: #ffff00;">Note:</span> state_topic will of course be the topic of your mqtt device :)

<span style="color: #ff6600;">Accessing sensor data that Alice captures but currently does nothing with</span>

So let's say for example you know Alice is capturing your outside motion sensor and storing that data in the
HomeAsistant database, and you want to use that value in your own skill to do something.

All current device states that Alice knows about (from HA skill) are stored in the database. However, every 5 minutes
they are also written to a file in the skills' directory called "currentStateOfDevices.json"

This will allow you to grab the state of all devices via your own skill or perhaps via the "file in" node of Node red,
without the need to extract it from the database directly.

<span style="color: #ff0000;">Creating Extra intents on the fly</span> #####

There are things in HA that don't get reported on by the API. Such as the RMpro for RF signals that you might use to do
certain things like turn on a tv, or tune tv stations rather than using your tv remote. In that situation and many
others Alice can create a "trigger" keyword that you use for what ever prupose you like.

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

<span style="color: #ff0000;"><strong>Ignore device discovery</strong></span> 

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


<span style="color: #ff0000;"><strong>Icons - and what they are</strong></span>

Icon - Description - state(where aplicable):

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

<span style="color: #ff0000;">Debug Control</span>

In the skill settings you have a couple of options for monitoring debug info.

1. ViewJsonPayload - This will write your incomming data from HA into a file found in
your skill directory. Handy for seeing what comes from your HA and diagnosing why some things might not get captured
   
2. debugMode - This will print debug information to your syslog. Good for seeing what is happening behind
   the scenes in regards too HA skill doing stuff
   
3. debugIcon - If his option is enabled it will display debug information as to why a icon may not be displaying
please turn this on and send the results to the dev if requested.
   
NOTE on #2: debug mode prints alot of syslog debug messages (must also have debug mode enabled in alice admin)
However, to personalise that a litle there is also a debugControl.json file found in your
skill directory.

By default, those values are set to true so that all debug messages are displayed
Set to false in order to stop a specific type of debug message from displaying

EG: "header" : false, won't display the header debug message you get on boot up but will display the others

Some debug messages don't have this control such as synonym creation. This is ok as it only happens when you add 
devices anyway so won't be a regular event
