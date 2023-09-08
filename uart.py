import serial
delimiter = "$"
port = "/dev/ttyAMA0"
baudrate = 115200

class Uart():
	uart = serial.Serial(port, baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
	def __init__(self):
		print("Initialized Uart")

	def send(self, value):
		message = value + delimiter
		self.uart.write(message.encode())

	def close(self):
		self.uart.close()
