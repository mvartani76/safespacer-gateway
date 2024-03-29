from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import argparse
import ReadLine
import serial
import time
import sys
import json
import os
import socket
import dateutil.parser as dp
import dotenv
from dotenv import load_dotenv
dotenv.load_dotenv()

SERIALPORT = "/dev/ttyUSB0"
BAUDRATE = 921600

CODE_VERSION = 0.26

# initialize debug time variables
readRemoteTime = 0
remoteConnectTime = 0
readBattLvlTime = 0
readFilesTime = 0
readFileDataTime = 0
removeFileTime = 0
disconnectTime = 0
totalTime = 0


# AWS IoT Code
# General message notification callback
def customOnMessage(message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")
	json_payload = json.loads(message.payload)
	print(json_payload)
	for key, value in json_payload.items():
		print(key)
		os.environ[key] = value
		dotenv.set_key(".env",key,os.environ[key])
		params[key] = value


# Param Set Suback callback
def paramSetSubackCallback(mid, data):
    print("Received SUBACK packet id: ")
    print(mid)
    print("Granted QoS: ")
    print(data)
    print("++++++++++++++\n\n")


# Puback callback
def customPubackCallback(mid):
    print("Received PUBACK packet id: ")
    print(mid)
    print("++++++++++++++\n\n")


# Create Params Dict to store parameter values
# Use default values just in case
params = {"SLEEPTIME":0.5, "LONGSLEEPTIME":2.0, "TAGDISTANCETHRESH":1500, "PINGTIMERTHRESH":900}

# Read in command-line parameters from .env file
host = os.getenv("HOST")
rootCAPath = os.getenv("ROOTPATH")
certificatePath = os.getenv("CERTIFICATEPATH")
privateKeyPath = os.getenv("PRIVATEKEYPATH")
params["PINGTIMERTHRESH"] = int(os.getenv("PINGTIMERTHRESH"))
useWebsocket = False
clientId = socket.gethostname()
customerID = os.getenv("CUSTOMERID")
alertTopic = os.getenv("ALERTTOPIC")
pingTopic = os.getenv("PINGTOPIC")

# MQTT message for sending parameter updates is <general_param_topic>/<hostname>
# this way it will only update the specific device -- will need to think about how to update all devices
paramSetTopic = os.getenv("PARAMSETTOPIC") + "/" + str(clientId)
params["TAGDISTANCETHRESH"] = int(os.getenv("TAGDISTANCETHRESH"))
params["SLEEPTIME"]  = float(os.getenv("SLEEPTIME"))
params["LONGSLEEPTIME"] = float(os.getenv("LONGSLEEPTIME"))

print(paramSetTopic)

#if args.useWebsocket and args.certificatePath and args.privateKeyPath:
#    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
#    exit(2)

#if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
#    parser.error("Missing credentials for authentication.")
#    exit(2)

# Port defaults
#if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
#    port = 443
#if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.ERROR)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
myAWSIoTMQTTClient.onMessage = customOnMessage

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
# Note that we are not putting a message callback here. We are using the general message notification callback.
myAWSIoTMQTTClient.subscribeAsync(paramSetTopic, 1, ackCallback=paramSetSubackCallback)
time.sleep(2)

# End of AWS IoT Code

ser = serial.Serial(SERIALPORT, baudrate = BAUDRATE, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, write_timeout=1)
time.sleep(float(params["SLEEPTIME"]))

print("Starting up Safe Spacer Serial Monitor...")
print(ser)
connected = False
commandToSend = "remote list\r\n"

print(ser.is_open)
ser.flush()

print("Sending command to turn off colors...")
ser.write("cli colors -s off\n".encode())
time.sleep(float(params["SLEEPTIME"]))
ser.flushInput()
print("Sending command to turn off echo...")
ser.write("cli echo -s off\n".encode())
time.sleep(float(params["SLEEPTIME"]))
ser.flushInput()

# check to see if the sbridge is connected to a tag
# and if it is, disconnect
print("Ping the device to see what the S-bridge is connected to...")
ser.write("device ping\n".encode())
time.sleep(float(params["SLEEPTIME"]))

readOut = ""
while ser.inWaiting() != 0:
	readOut = ser.readline().decode() + readOut
	time.sleep(float(params["SLEEPTIME"]))

print(float(params["SLEEPTIME"]))

splitout = readOut.split()
print(splitout)
tmp = str(splitout[0])
tmp = tmp[0:2]

# disconnect from tag if connected to a safe spacer tag
# need to flush any data from the ping message I think?
if tmp == "ss":
	print("S-bridge currently connected to tag. Need to disconnect...")
	ser.write("remote disconnect\r\n".encode())
	time.sleep(float(params["SLEEPTIME"]))
	ser.flushInput()

# get the s-bridge ID
print("Checking the S-Bridge ID (EUI)...")
ser.write("device info\n".encode())
time.sleep(float(params["SLEEPTIME"]))

readOut = ""
while ser.inWaiting() != 0:
	readOut = ser.readline().decode() + readOut
	time.sleep(float(params["SLEEPTIME"]))

splitout = readOut.split()
print(splitout)
# the EUI is the element 2 in the splitout array
sbridgeID = splitout[2]

# initialize ping timer to current time
currentPingTime = int(time.time())
previousPingTime = currentPingTime

while True:
	totalStartTime = time.time()
	ser.flushInput()
	time.sleep(float(params["SLEEPTIME"]))

	readRemoteStartTime = time.time()
	ser.write(commandToSend.encode())
	time.sleep(float(params["SLEEPTIME"]))

	print ("Attempt to Read remote list...")
	readOut = [chr(c) for c in ser.read(ser.in_waiting)]
	strOut = "".join(readOut)
	readOut = strOut

	readRemoteTime = round(time.time() - readRemoteStartTime, 3)
#	print("readRemoteTime = " + str(readRemoteTime))

	splitout = readOut.split()

	# if length of splitout = 0, there is an error so should flush data and restart loop
	if len(splitout) < 1:
		print("Length of splitout < 1, something not right...")
		numtTagsFound = -1
		ser.flushInput()
		time.sleep(float(params["SLEEPTIME"]))
		ser.close()
		time.sleep(float(params["LONGSLEEPTIME"]))
		ser = serial.Serial(SERIALPORT, baudrate = BAUDRATE, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, write_timeout=1)
		time.sleep(float(params["SLEEPTIME"]))

		# Send error message to AWS
		jobj = {
			"time": str(int(time.time())),
			"error": "LSPL<1",
			"S-Bridge": sbridgeID,
			"RPi-GW": clientId,
			"CustomerID": customerID,
			"sw_version": CODE_VERSION
			}
		jsonOutput = json.dumps(jobj)
		myAWSIoTMQTTClient.publishAsync(pingTopic, jsonOutput, 1, ackCallback=customPubackCallback)

	else:
		# Check to make sure that numTagsFound is an integer value
		try:
			#numTagsFound = int(splitout[len(splitout)-1])
			numTagsFound = int(splitout[0])
		except ValueError:
			print("NumTagsFound not an integer...")
			numTagsFound = -1
			ser.flushInput()
			time.sleep(float(params["SLEEPTIME"]))
			ser.close()
			time.sleep(float(params["LONGSLEEPTIME"]))
			ser = serial.Serial(SERIALPORT, baudrate = BAUDRATE, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, write_timeout=1)
			time.sleep(float(params["SLEEPTIME"]))

			# Send error message to AWS
			jobj = {
				"time": str(int(time.time())),
				"error": "NUMTAGSNOTINT",
				"S-Bridge": sbridgeID,
				"RPi-GW": clientId,
				"CustomerID": customerID,
				"sw_version": CODE_VERSION
				}
			jsonOutput = json.dumps(jobj)
			myAWSIoTMQTTClient.publishAsync(pingTopic, jsonOutput, 1, ackCallback=customPubackCallback)


	# Only attempt to connect to tags if we have found some so if
	# there are no tags found, go back to the beginning of loop (or sleep)
	if (numTagsFound < 1):
		print("No tags found...")
	else:
		tagsNum = []
		tagsDist = []
		# loop through the number of tags in the list
		for i in range(int(numTagsFound)):
			tagsNum.append(splitout[2*i+1])
			tagsDist.append(splitout[2*i+2])

		for i in range(int(numTagsFound)):
			ser.flushInput()
			# check to see if the tag is within tagDistanceThresh
			if (int(tagsDist[i]) <= int(params["TAGDISTANCETHRESH"])):
				print("remote connect " + tagsNum[i])
				remoteConnectStartTime = time.time()
				# connect to the tag
				ser.write(("remote connect " + str(tagsNum[i]) + "\r").encode())
				#time.sleep(float(params["SLEEPTIME"]))
				# observed that this nees to be a little longer to make sure the following commands are sent
				# to the tags so we need to be sure the tag is connected before sending the next commands
				time.sleep(0.75)

				readOut = [chr(c) for c in ser.read(ser.in_waiting)]
				strOut = "".join(readOut)
				splitout = strOut.split()
				print("array after remote connect... " + str(splitout))
				ser.flushOutput()
				time.sleep(float(params["SLEEPTIME"]))

				remoteConnectTime = round(time.time() - remoteConnectStartTime, 3)
#				print("remoteConnectTime = " + str(remoteConnectTime))
				# make sure echo and color is off on tags

				print("turning off tag colors...")
				ser.write("cli colors -s off\r\n".encode())
				time.sleep(float(params["SLEEPTIME"]))

				readOut = [chr(c) for c in ser.read(ser.in_waiting)]
				strOut = "".join(readOut)
				readOut = strOut
				print("array after cli colors..." + str(readOut))

				print("turning off tag echo...")
				ser.write("cli echo -s off\r\n".encode())
				time.sleep(float(params["SLEEPTIME"]))

				readOut = [chr(c) for c in ser.read(ser.in_waiting)]
				strOut = "".join(readOut)
				readOut = strOut
				print(readOut)
				print("array after cli echo..." + str(readOut))

				# set the tags date/time
				named_tuple = time.localtime()
				time_string = time.strftime("%Y-%m%dT%H:%M:%S",named_tuple)
				#print("setting time: " + time_string)
				ser.write(("device datetime -s " + time_string + "\r\n").encode())
				time.sleep(float(params["SLEEPTIME"]))
				#print("enabling contact tracing")
				ser.write("contact log -s on\r".encode())
				time.sleep(float(params["SLEEPTIME"]))
				#print("flushing input...")
				ser.flushInput()
				time.sleep(float(params["SLEEPTIME"]))

				# get the battery information
				print("obtaining battery level")
				readBattLvlStartTime = time.time()
				ser.write("device battery_state\r\n".encode())
				time.sleep(float(params["SLEEPTIME"]))

				readOut = [chr(c) for c in ser.read(ser.in_waiting)]
				strOut = "".join(readOut)
				readOut = strOut

				readBattLvlTime = round(time.time() - readBattLvlStartTime, 3)
				print("readBattLvlTime = " + str(readBattLvlTime))
				#print("Read all battery data...")
				# will probably need to do some error checking on the data
				batt_splitout = readOut.split()
				#print(batt_splitout)
				# battery % is 4th item in array (base 0) if 'device' is the first element
				# sometimes we read 'level' as the first item which means 'device' is missing
				# in this case, the battery % is stored in the second item base 0
				if (batt_splitout[0] == "device"):
					battery_level = batt_splitout[3]
				else:
					battery_level = batt_splitout[1]
				print("battery level = " + str(battery_level))
				# list the files available
				#print("listing the files available on tag")
				readFilesStartTime = time.time()
				time.sleep(float(params["SLEEPTIME"]))
				ser.write("fs ls /logs\r\n".encode())
				time.sleep(float(params["SLEEPTIME"]))

				readOut = [chr(c) for c in ser.read(ser.in_waiting)]
				strOut = "".join(readOut)
				readOut = strOut

				readFilesTime = round(time.time() - readFilesStartTime, 3)
				print("readFilesTime = " + str(readFilesTime))
				#print("Read all fs ls data...")
				splitout = readOut.split()
				print(splitout)
				# if no files are on the tag, we should only read data for the following
				# . DIR
				# .. DIR
				# ss$
				# so if the length of splitout <=5, then there is no data on the tag to read

				if len(splitout) <= 5:
					print("No data on the tag to read...")
				else:
					# assume that the first 4 values of splitout are:
					# 'DIR', '.', 'DIR', '..'
					print("Data on the tag to read...")
					# assume that the file name data will be from locations 2 to length-5 in base 0
					print("length of filename splitout = " + str((len(splitout))))
					fileNameArray = []
					# zero out # of files found on tag
					numFiles = 0
					for j in range(len(splitout)-5):
						print("j="+str(j)+" len="+str(len(splitout)))
						splt_str = str(splitout[4+j])
						print(splt_str)
						# check if string is a filename by looking at extension
						if (splt_str.endswith(".txt")):
							print("Found a .txt file.")
							# increment number of files found on tag
							numFiles = numFiles + 1
							ser.flushInput()
							ser.flushOutput()
							fileNameArray.append(splt_str)
							fn_t = splt_str[0:len(splt_str)-4]+".000Z"
							# convert the ISO 8601 time to unix
							parsed_t = dp.parse(fn_t)
							t_in_sec = parsed_t.timestamp()
							readFileDataStartTime = time.time()
							ser.write(("fs read /logs/" + str(splt_str) + " -f ascii\r\n").encode())
							time.sleep(float(params["SLEEPTIME"]))
							readOut = ""

							readOut = [chr(c) for c in ser.read(ser.in_waiting)]
							strOut = "".join(readOut)
							readOut = strOut
							readFileDataTime = round(time.time() - readFileDataStartTime, 3)
							print("readFileDataTime = " + str(readFileDataTime))
							splitoutData = readOut.split()
							print(splitoutData)
							# splitoutData should look like this
							# ['File', 'size:', <size>, <data>, 'ss:$']
							# ['File', 'size:', '19', '0001f82,67,5184,74', 'ss:~$']
							#
							# Observed that sometimes the previous command is in the array so we need to ignore
							# ['fs', 'read', '/logs/2021-03-15T03:07:13.txt', '-f', 'ascii', 'File', 'size:', '18', '0001f82,114,21,43', 'ss:~$']
							#
							# Look in the array for the 'File' element and use that as an offset
							offset = splitoutData.index('File')
							alertData = splitoutData[3+offset]
							print(alertData)
							splitAlert = alertData.split(',')
							print(splitAlert)
							alertTime = int(splitAlert[2]) + int(t_in_sec)
							currentTime = int(time.time())

							# remove file from device since we have just sent it to AWS
							#print("Removing " + str(splt_str))
							removeFileStartTime = time.time()
							ser.write(("fs rm logs/" + str(splt_str) +"\r\n").encode())
							time.sleep(float(params["SLEEPTIME"]))

							readOut = [chr(c) for c in ser.read(ser.in_waiting)]
							ser.flushInput()
							removeFileTime = round(time.time() - removeFileStartTime, 3)
							print("removeFileTime = " + str(removeFileTime))

							# totalTime here is not actually the total time but everything minus the disconnect
							# but we want to capture some itme information when sending AWS message
							totalTime = round(time.time() - totalStartTime, 3)

							jobj = {
								"tag1": tagsNum[i],
								"tag2": splitAlert[0],
								"minDistance": splitAlert[1],
								"alertTime": str(alertTime),
								"currentTime": str(currentTime),
								"duration": splitAlert[3],
								"tag1_battery_lvl": battery_level,
								"S-Bridge": sbridgeID,
								"RPi-GW": clientId,
								"CustomerID": customerID,
								"sw_version": CODE_VERSION,
								"time": str(int(time.time())),
								"readremotetime": str(readRemoteTime),
								"remoteconnecttime": str(remoteConnectTime),
								"readbattlvltime": str(readBattLvlTime),
								"readfilestime": str(readFilesTime),
								"readfiledatatime": str(readFileDataTime),
								"removefiletime": str(removeFileTime),
								"disconnecttime": str(disconnectTime),
								"totaltime": str(totalTime),
								"fileNum": str(numFiles)
								}
							jsonOutput = json.dumps(jobj)
							myAWSIoTMQTTClient.publishAsync(alertTopic, jsonOutput, 1, ackCallback=customPubackCallback)

					print(fileNameArray)
				# need to disconnect from the device
				print("Disconnect from tag")
				disconnectStartTime = time.time()
				ser.write("remote disconnect\r\n".encode())
				time.sleep(float(params["SLEEPTIME"]))
				disconnectTime = round(time.time() - disconnectStartTime, 3)
				print("disconnectTime = " + str(disconnectTime))
				totalTime = round(time.time() - totalStartTime, 3)
			else:
				print("No tags found within threshold distance.")
				totalTime = round(time.time() - totalStartTime, 3)
#	print ("Restart")
	ser.flush() #flush the buffer
	totalTime = round(time.time() - totalStartTime, 3)
	print("totalTime = " + str(totalTime))

	# Check against time threshold to send gateway ping
	# if the difference in time is > pingTimerThresh, send the ping message
	# and set the current and previous times equal to each other
#	print("Time difference = " + str(currentPingTime - previousPingTime))
	if (currentPingTime - previousPingTime) > int(params["PINGTIMERTHRESH"]):
		previousPingTime = currentPingTime
		jobj = {
			"time": str(int(time.time())),
			"readremotetime": str(readRemoteTime),
			"remoteconnecttime": str(remoteConnectTime),
			"readbattlvltime": str(readBattLvlTime),
			"readfilestime": str(readFilesTime),
			"readfiledatatime": str(readFileDataTime),
			"removefiletime": str(removeFileTime),
			"disconnecttime": str(disconnectTime),
			"totaltime": str(totalTime),
			"S-Bridge": sbridgeID,
			"RPi-GW": clientId,
			"CustomerID": customerID,
			"sw_version": CODE_VERSION
			}
		jsonOutput = json.dumps(jobj)
		myAWSIoTMQTTClient.publishAsync(pingTopic, jsonOutput, 1, ackCallback=customPubackCallback)
	else:
		currentPingTime = int(time.time())
