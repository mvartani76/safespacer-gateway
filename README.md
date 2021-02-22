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
