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
	print ("Writing: ",  commandToSend)
	ser.write(commandToSend)
	time.sleep(1)
	while True:
		try:
			print ("Attempt to Read")
			while ser.inWaiting() != 0:
				print(ser.inWaiting())
			#readOut = ser.readline(ser.inWaiting())
			#time.sleep(2)
			#while (ser.inWaiting()==0):
			#	pass
				readOut = ser.readline()
				time.sleep(1)
				print ("Reading: ", readOut) 
				time.sleep(2)
			print("read all data")
			break
        	except:
			#ser.close()
            		sys.exit(0)
    	print ("Restart")
    	ser.flush() #flush the buffer
