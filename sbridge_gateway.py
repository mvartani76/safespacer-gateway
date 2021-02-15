import serial
import time
import sys

SERIALPORT = "/dev/ttyUSB0"
BAUDRATE = 921600

#ser = serial.Serial(SERIALPORT, BAUDRATE)
#ser.bytesize = serial.EIGHTBITS
#ser.parity = serial.PARITY_NONE
#ser.stopbits = serial.STOPBITS_ONE
#ser.timeout = 2
#ser.writeTimeout = 2

ser = serial.Serial(SERIALPORT, baudrate = BAUDRATE, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
time.sleep(0.1)

print("Starting up Safe Spacer Serial Monitor...")
print(ser)
connected = False
commandToSend = "remote list\r\n"

print(ser.is_open)
ser.flush()

print("Sending command to turn off colors...")
ser.write("cli colors -s off\n")
time.sleep(1)
ser.flushInput()
print("Sending command to turn off echo...")
ser.write("cli echo -s off\n")
time.sleep(1)
ser.flushInput()

while True:
	ser.flushInput()
	time.sleep(1)
	print ("Writing: ",  commandToSend)
	ser.write(commandToSend)
	time.sleep(1)

	print ("Attempt to Read remote list")
	readOut = ""
	while ser.inWaiting() != 0:
		print(ser.inWaiting())
		readOut = ser.readline() + readOut
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
			ser.write("remote connect " + str(tagsNum[i]) + "\r\n")
			time.sleep(1)
			readOut = ""
			print(ser.inWaiting())
			readOut = ser.readline() + readOut
			while (ser.inWaiting() != 0):
				print(ser.inWaiting())
				readOut = ser.readline() + readOut
				time.sleep(1)
				print("Reading RC: ", readOut)

			# make sure echo and color is off on tags
			ser.write("cli echo -s off\r\n")
			time.sleep(1)
			ser.write("cli colors -s off\r\n")
			time.sleep(1)
			# set the tags date/time
			named_tuple = time.localtime()
			time_string = time.strftime("%Y-%m%dT%H:%M:%S",named_tuple)
			print("setting time: " + time_string)
			ser.write("device datetime -s " + time_string + "\r\n")
			time.sleep(1)
			print("enabling contact tracing")
			ser.write("contact log -s on\r\n")
			time.sleep(1)
			print("flushing input...")
			ser.flushInput()
			time.sleep(1)
			# list the files available
			print("listing the files available on tag")
			ser.write("fs ls /logs\r\n")
			time.sleep(1)
			print("Reading log data...")
			readOut = ""
			while (ser.inWaiting() != 0):
				print(ser.inWaiting())
				readOut = ser.readline() + readOut
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


			# need to disconnect from the device
			print("Disconnect from tag")
			ser.write("remote disconnect\r\n")
			time.sleep(1)

	print ("Restart")
	ser.flush() #flush the buffer
