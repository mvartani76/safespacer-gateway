from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import logging
import argparse

import serial
import time
import sys
import json
import os
import socket
import dateutil.parser as dp
from dotenv import load_dotenv
load_dotenv()

SERIALPORT = "/dev/ttyUSB0"
BAUDRATE = 921600

CODE_VERSION = 0.5

#ser = serial.Serial(SERIALPORT, BAUDRATE)
#ser.bytesize = serial.EIGHTBITS
#ser.parity = serial.PARITY_NONE
#ser.stopbits = serial.STOPBITS_ONE
#ser.timeout = 2
#ser.writeTimeout = 2

# AWS IoT Code
# General message notification callback
def customOnMessage(message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


# Suback callback
def customSubackCallback(mid, data):
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


# Read in command-line parameters from .env file
host = os.getenv("HOST")
rootCAPath = os.getenv("ROOTPATH")
certificatePath = os.getenv("CERTIFICATEPATH")
privateKeyPath = os.getenv("PRIVATEKEYPATH")
pingTimerThresh = int(os.getenv("PINGTIMERTHRESH"))
useWebsocket = False
#clientId = os.getenv("CLIENTID")
clientId = socket.gethostname()
customerID = os.getenv("CUSTOMERID")
print(clientId)
alertTopic = os.getenv("ALERTTOPIC")
pingTopic = os.getenv("PINGTOPIC")


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
logger.setLevel(logging.DEBUG)
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
myAWSIoTMQTTClient.subscribeAsync(alertTopic, 1, ackCallback=customSubackCallback)
time.sleep(2)

# End of AWS IoT Code

ser = serial.Serial(SERIALPORT, baudrate = BAUDRATE, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
time.sleep(0.1)

print("Starting up Safe Spacer Serial Monitor...")
print(ser)
connected = False
commandToSend = "remote list\r\n"

print(ser.is_open)
ser.flush()

print("Sending command to turn off colors...")
ser.write("cli colors -s off\n".encode())
time.sleep(1)
ser.flushInput()
print("Sending command to turn off echo...")
ser.write("cli echo -s off\n".encode())
time.sleep(1)
ser.flushInput()

# check to see if the sbridge is connected to a tag
# and if it is, disconnect
print("Ping the device to see what the S-bridge is connected to...")
ser.write("device ping\n".encode())
time.sleep(1)

readOut = ""
while ser.inWaiting() != 0:
	readOut = ser.readline().decode() + readOut
	time.sleep(1)

splitout = readOut.split()
tmp = str(splitout[0])
tmp = tmp[0:2]

# disconnect from tag if connected to a safe spacer tag
# need to flush any data from the ping message I think?
if tmp == "ss":
	print("S-bridge currently connected to tag. Need to disconnect...")
	ser.write("remote disconnect\r\n".encode())
	time.sleep(1)
	ser.flushInput()

# get the s-bridge ID
print("Checking the S-Bridge ID (EUI)...")
ser.write("device info\n".encode())
time.sleep(1)

readOut = ""
while ser.inWaiting() != 0:
	readOut = ser.readline().decode() + readOut
	time.sleep(1)

splitout = readOut.split()
print(splitout)
# the EUI is the element 2 in the splitout array
sbridgeID = splitout[2]

# initialize ping timer to current time
currentPingTime = int(time.time())
previousPingTime = currentPingTime

while True:
	ser.flushInput()
	time.sleep(1)
	print ("Writing: ",  commandToSend)
	ser.write(commandToSend.encode())
	time.sleep(1)

	print ("Attempt to Read remote list")
	readOut = ""
	while ser.inWaiting() != 0:
		print(ser.inWaiting())
		readOut = ser.readline().decode() + readOut
		# first line should return # of tags detected
		time.sleep(1)
		print ("Reading: ", readOut)

	print("read all data")
	splitout = readOut.split()
	print(splitout)
	print(len(splitout))
	numTagsFound = int(splitout[len(splitout)-1])
	print("NumTagsFound = " + str(numTagsFound))

	# Only attempt to connect to tags if we have found some so if
	# there are no tags found, go back to the beginning of loop (or sleep)
	if (numTagsFound < 1):
		print("No tags found...")
	else:
		tagsNum = []
		tagsDist = []
		# loop through the number of tags in the list
		for i in range(int(numTagsFound)):
			print(i)
			tagsNum.append(splitout[len(splitout)-2*i-3])
			tagsDist.append(splitout[len(splitout)-2*i-2])

		print("tagsNum = " + str(tagsNum))
		print("tagsDist = " + str(tagsDist))

		for i in range(int(numTagsFound)):
			print("remote connect " + tagsNum[i])
			ser.write(("remote connect " + str(tagsNum[i]) + "\r\n").encode())
			time.sleep(1)
			readOut = ""
			print(ser.inWaiting())
			readOut = ser.readline().decode() + readOut
			while (ser.inWaiting() != 0):
				print(ser.inWaiting())
				readOut = ser.readline().decode() + readOut
				time.sleep(1)
				print("Reading RC: ", readOut)

			# make sure echo and color is off on tags
			ser.write("cli echo -s off\r\n".encode())
			time.sleep(1)
			ser.write("cli colors -s off\r\n".encode())
			time.sleep(1)
			# set the tags date/time
			named_tuple = time.localtime()
			time_string = time.strftime("%Y-%m%dT%H:%M:%S",named_tuple)
			print("setting time: " + time_string)
			ser.write(("device datetime -s " + time_string + "\r\n").encode())
			time.sleep(1)
			print("enabling contact tracing")
			ser.write("contact log -s on\r\n".encode())
			time.sleep(1)
			print("flushing input...")
			ser.flushInput()
			time.sleep(1)

			# get the battery information
			print("obtaining battery level")
			ser.write("device battery_state\r\n".encode())
			time.sleep(1)
			readOut = ""
			while (ser.inWaiting() != 0):
				print(ser.inWaiting())
				readOut = ser.readline().decode() + readOut
				time.sleep(1)
				print("Reading BAT: ", readOut)

			print("Read all data...")
			# will probably need to do some error checking on the data
			batt_splitout = readOut.split()
			battery_level = batt_splitout[len(batt_splitout)-3]

			# list the files available
			print("listing the files available on tag")
			ser.write("fs ls /logs\r\n".encode())
			time.sleep(1)
			print("Reading log data...")
			readOut = ""
			while (ser.inWaiting() != 0):
				print(ser.inWaiting())
				readOut = ser.readline().decode() + readOut
				time.sleep(1)
				print("Reading FS: ", readOut)

			print("Read all data...")
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
				# assume that the last 4 values of splitout are:
				# 'DIR', '..', 'DIR', '.'
				print("Data on the tag to read...")
				# assume that the file name data will be from locations 2 to length-5 in base 0
				print("length of splitout = " + str((len(splitout))))
				fileNameArray = []
				for j in range(len(splitout)-7+1):
					print("j="+str(j)+" len="+str(len(splitout)))
					splt_str = str(splitout[2+j])
					print(splt_str)
					# check if string is a filename by looking at extension
					if (splt_str.endswith(".txt")):
						fileNameArray.append(splt_str)
						fn_t = splt_str[0:len(splt_str)-4]+".000Z"
						# convert the ISO 8601 time to unix
						parsed_t = dp.parse(fn_t)
						t_in_sec = parsed_t.timestamp()
						ser.write(("fs read /logs/" + str(splt_str) + " -f ascii\r\n").encode())
						time.sleep(1)
						readOut = ""
						while (ser.inWaiting() != 0):
							print(ser.inWaiting())
							readOut = ser.readline().decode() + readOut
							time.sleep(1)
							print("Reading read: " + str(readOut))
						splitoutData = readOut.split()
						alertData = splitoutData[1]
						splitAlert = alertData.split(',')
						print(splitAlert)
						alertTime = int(splitAlert[2]) + int(t_in_sec)
						currentTime = time.time()

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
							"sw_version": CODE_VERSION
							}
						jsonOutput = json.dumps(jobj)
						myAWSIoTMQTTClient.publishAsync(alertTopic, jsonOutput, 1, ackCallback=customPubackCallback)
				print(fileNameArray)
			# need to disconnect from the device
			print("Disconnect from tag")
			ser.write("remote disconnect\r\n".encode())
			time.sleep(1)

	print ("Restart")
	ser.flush() #flush the buffer

	# Check against time threshold to send gateway ping
	# if the difference in time is > pingTimerThresh, send the ping message
	# and set the current and previous times equal to each other
	print("Time difference = " + str(currentPingTime - previousPingTime))
	if (currentPingTime - previousPingTime) > pingTimerThresh:
		previousPingTime = currentPingTime
		jobj = {
			"time": str(time.time()),
			"S-Bridge": sbridgeID,
			"RPi-GW": clientId,
			"CustomerID": customerID,
			"sw_version": CODE_VERSION
			}
		jsonOutput = json.dumps(jobj)
		myAWSIoTMQTTClient.publishAsync(pingTopic, jsonOutput, 1, ackCallback=customPubackCallback)
	else:
		currentPingTime = int(time.time())
