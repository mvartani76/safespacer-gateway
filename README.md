# safespacer-gateway
Gateway code for interfacing with safespacer tags via safespacer s-bridge.
## topics
This code sends two MQTT messages with the following topics

### ss/ss_alerts
This is the topic for messages sent after the safe spacer tag has interacted with the s-bridge gateway and has data on it to send.

**Data Sent:**
```
tag1
tag2
minDistance
alertTime
currentTime
duration
tag1_battery_lvl
S-Bridge
RPi-GW
CustomerID
sw_version
```
### ss/sb_ping
This is the topic for messages sent every ```PINGTIMERTHRESH``` seconds from the Raspberry Pi that provides status that it is still running

**Data sent:**
```
time
S-Bridge
RPi-GW
CustomerID
sw_version
```
### ss/set_params/\<hostname\>
This is the topic for sending parameters to update on the remote device.

```
{
  "CUSTOMERID": "<string>",
  "TAGDISTANCETHRESH": "<Integer>",
  "SLEEPTIME": "<Integer>",
  "PINGTIMERTHRESH": "<Integer>"
}
```
*\<hostname\>* is the hostname for the device that is to be programmed. Still TBD on sending command to all devices.

NOTE: The key values need to be exact as these are the values used in the .env file. They will not update the algorithm if not correct but will add additional values to the .env file.

## Other Items
### Code Execution
The code can be run by initiating the following command
```python3 sbridge_gateway.py```
### Environment Variables
The parameters for the code are located in an environment file (.env). The required parameters in this file are:
```
HOST = <String> - AWS Endpoint.
ROOTPATH = <String> - Full filename and path for location of root certificate file.
CERTIFICATEPATH = <String> - Full filename and path for location of AWS certificate file (.cert.pem).
PRIVATEKEYPATH = <String> - Full filename and path for location of AWS private key (.private.key).
ALERTTOPIC = <String> - AWS Alert Topic - This is the message sent when there is a tag nearby the S-bridge with data on it to upload.
PINGTOPIC = <String> - AWS Ping Topic - This is the message sent to provide status information that the gateway is still alive.
PINGTIMERTHRESH = <Integer> - Time (in seconds) for how often the gateway should send a ping message.
TAGDISTANCETHRESH = <Integer> - Distance (in centimeters) for how close the tags need to be to connect to S-Bridge.
SLEEPTIME = <Float> - Time (in seconds) for how long code sleeps after executing serial write commands.
CLIENTID = <String> - Client ID for AWS IoT.
CUSTOMERID = <String> - Customer identifier for sorting data in database.
```

### Systemd service file
This code can be initiated in a service file with the following settings.<br>
Location for service file: /etc/systemd/system<br>
Service File Name: safespacer.service<br>

```
[Unit]
Description=Safe Spacer Gateway Service
After=multi-user.target

[Service]
Type=simple
WorkingDirectory=/home/pi/Documents/safespacer-gateway/
ExecStart=/usr/bin/python3.7 /home/pi/Documents/safespacer-gateway/sbridge_gateway.py
User=pi
Restart=always
RestartSec=30
StartLimitInterval=350
StartLimitBurst=10

[Install]
WantedBy=multi-user.target
```
