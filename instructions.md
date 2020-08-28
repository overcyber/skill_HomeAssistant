<span style="color: #ff0000;"><strong>SetUp Steps </span><span style="color: #0000ff;">--- In Home Assistant: ---</strong></span>
<ol>
<li>Create a long life token from your user profile screen. (Copy it and store it <br />safely for now as you'll only get once chance to copy it)</li>
<li>Add the following to your Home Assistant configuration.yaml file</li>
</ol>
api;

&nbsp;&nbsp;&nbsp; http://your-HomeassistantIP:port/api/

<span style="color: #00ff00;">Example:</span><br />

api:<br>&nbsp;&nbsp;&nbsp; http://192.168.4.1:8123/api/<br />

<span style="color: #ffff00;">NOTE</span> the /api/ not just /api<br />

while in there check if you have in your Home Assistant yaml
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
<li>In "HAIpAddress" field, add your HomeAssistant IP address - make sure you append /api/<br /> <span style="color: #ff6600;">Example</span> http://192.168.4.1:8123/api/</li>
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
<li>Add those devices to Alice's Database ( so they show in My home and are Alice aknowledable)</li>
<li>Takes all the friendly names and automatically writes them to dialogTemplate file</li>
</ol>
Once setup is completed (takes 30 seconds or so) and <strong>you restart alice</strong> again for training.

You should be able to ask <br />

- "Hey Alice/Snips"
- "Turn off / on the "entity Friendly name"

<span style="color: #00ff00;">Example:</span> turn off the bathroom light

- "Hey Alice/Snips"
- "What's the state of the pool pump"

<span style="color: #ff6600;">Usage:</span>

Some examples of what to say

<em>For initial set up</em>
- "Add my home assistant devices"
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
