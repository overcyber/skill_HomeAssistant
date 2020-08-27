**SetUp Steps**

**---- In Home Assistant: ----**

1. Create a long life token from your user profile screen. (Copy it and store it safely for now as you'll only
 get once chance to copy it)
2. Add the following to your Home Assistant configuration.yaml file
  - api:
     - *http://your HomeassistantIP:port*/api/
 
**Example:**

- api:
  - http://192.168.4.1:8123/api/

NOTE the /api/ not just /api 

while in there check if you have in your yaml
  - default_config:
or
  - sun:

(Add either of those to your Home Assistant configuration.yaml, if you'd like Alice to tell you about sun events)

- Now restart Home Assistant and carry on with the below Alice setup

**SETUP steps via Alice**

**---- In Alice: ----**

1. Go to the Alice web ui
2. Click into Skills
3. Install the HomeAssistant skill
4. Once installed, Go to the HomeAssistant skill and click on -> Settings
5. In "HAaccessToken" field, add your copied long life token
6. In "HAIpAddress" field, add your HomeAssistant IP address (make sure you append /a
    - Example http://192.168.4.1:8123/api/
7. Restart Alice 

SIDE NOTE: For now all switches captured by Alice from HA will get installed in one l
-  You will have to later go to "My Home" in the web Ui and move each switch to a app
for now but, to keep a tidy house keeps Alice happy :)

Once alice restarts you can then ask her :
- "Hey Snips/Alice"
- "Setup home assistant skill" 

You really only need to ask that once. By asking that she will

1. Get the list of switch entities from Home assistant
2. Write them to Alices new HomeAssistant Database
3. Add those devices to Alice's Database ( so they show in My home and are Alice akno
4. Takes all the friendly names and automatically writes them to dialogTemplate file 

Once setup is completed (takes 30 seconds or so) and **you reboot alice** again for training. 
You should be able to ask 
- "Hey Alice/Snips"
- "Turn off/on the *entity Friendly name*"

EG: turn off the bathroom light
- "Hey Alice/Snips"
- What's the state of the pool pump


**Usage:**

Some examples of what to say 

*For initial set up* 
- "Add my home assistant devices"
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
- Whats the ip of the kitchen light
