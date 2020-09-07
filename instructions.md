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
For now all switches captured by Alice from HA will get installed in one location
- You may want to at some stage go to "My Home" in the web Ui 
and move each switch to a appropriate location. To keep a tidy house keeps Alice happy :)

Once alice restarts you can then ask her :
<ul>
<li>"Hey Snips/Alice"</li>
<li>"Setup home assistant skill" </li>
or
<li>"configure the home assistant skill"</li>
</ul>
You really only need to ask that once. By asking that she will

<ol>
<li>Get the list of switch entities from Home assistant</li>
<li>Write them to Alices new HomeAssistant Database</li>
<li>Add those devices to Alice's Database ( so they show in My home and are Alice acknowledable)</li>
<li>Takes all the friendly names and automatically writes them to dialogTemplate file</li>
</ol>
Once setup is completed (takes 30 seconds or so) and <strong>you restart alice</strong> again for training.

You should be able to ask 

- "Hey Alice/Snips"
- "Turn off / on the "entity Friendly name"

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
</ul>

<span style="color: #ff0000;">Configuration Tips</span> #####<span style="color: #0000ff;"></strong> Manually setting up sensors</span></strong> #####

Currently the sensors from HA that will get captured are "<i>sensor.sensor_name"</i> and 
<i>binary_sensor.sensor_name</i> devices 

EG: "sensor.inside_temperature".

To be captured however they must have a "device_class" attribute assigned to them.

HA will tend to automatically do this for you in some cases. Especially if your running HASS.IO and the MQTT Addon and 
Tasmota firmware on your devices. However you may find that currently not all sensors are being captured.

<span style="color: #ff6600;">There's potentially at least two common reasons for this</span> 
<ol>
<li> Currently only sensors that have a function in the HA skill are concentrated on. This will change as the 
skill progresses. Devices such as, temperature, humidity, gas, illuminance, pressure and dewpoint are used 
and can be reported on by Alice.

Sensors such as motion sensor's, battery sensors etc "might" also get captured, however they have no 
function in Alice currently. Please see example configurations further down these instructions </li>

<li> You've manually configured a MQTT device in the yaml but have not added a "device_class" attribute </li>
</ol>


If manually creating sensors in your home assistant configuration.yaml be sure to add a "device_class" such as 
the below example and Alice should pick up on that the next time you ask Alice to
"configure the home Assistant skill " and then re train her.

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

So lets say for example you know Alice is capturing your outside motion sensor and storing that data in the 
HomeAsistant database. You want to use that value in your own skill to do something.

You can access that value by importing the HomeAssistant Class, 
create a instance of HomeAssistant and use the get.SensorValues() function:

<span style="color: #00ff00;">Example:</span>

```

from skills.HomeAssistant import HomeAssistant

   @staticmethod

    def getHomeAssitantSensorData():
	
		haClass = HomeAssistant.HomeAssistant()
	
		knownSensors = haClass.getSensorValues
	
		if knownSensors:
	
			return knownSensors

```

You'll then want to iterate over the result to find the sensor data you're specifically after.

<span style="color: #ff0000;">Creating Extra intents on the fly</span> #####

There are things in HA that dont get reported on by the API. Such as the RMpro for RF signals that you might use to 
do certain things like turn on a tv, or tune tv stations rather than using your tv remote. In that situation and many
 others Alice can create a "trigger" keyword that you use for what ever prupose you like.
 
For the below explanation and example let's assume we have a Node Red flow in HA that sends a RF command to the TV
when we send that flow a trigger of "turn on"

In Alice via the HA skill you can create an intent on the fly and assign it the slot value "turn on"
Ask Alice "add a home assistant intent"

Then follow her prompts, she will ask you for the intent to use, in which case you could reply with
"turn the tv on"
She will then ask you to pick a slot value from that intent, so say "tv on" and then say yes when prompted

She will then ask if you want to add synonyms. We could now say "television on" and say yes when prompted. 
Then add another synonym when prompted if you like. Otherwise when you say "no" to adding another synonym
She will then write to you dialogTemplate folder the appropriate utterances and slot details.

Restart and she will go into training.

Once trained now ask her " turn the tv on"
She will then send a MQTT message on the topic "ProjectAlice/HomeAssistant" with a payload of "tv on"

IN Home Assistant you can now perhaps use Node Red and a MQTT node into a switch node and listen to the topic of 
"ProjectAlice/HomeAssistant" with the payload of "tv on" and trigger a appropriate Node Red flow to handle
sending the RF code to the TV.

Obviously this is just one simple example. Let your mind be creative and you could think up multiple things to do

Basically Alice is just going to send a keyword that you can intercept and trigger a Node Red flow to do what ever
you want it to.

