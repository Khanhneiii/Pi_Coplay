import json
import subprocess
import asyncio
from uart import Uart
from moth import Moth
PUB_PARSING_FAILED = "PUB_PARSING_FAILED"
PUB_WIFI_SSID_FAILED = "PUB_WIFI_SSID_FAILED"
PUB_WIFI_PWD_FAILED = "PUB_WIFI_PWD_FAILED"
PUB_WS_FAILED = "PUB_WS_FAILED"
PUB_CAMERA_FAILED = "PUB_CAMERA_FAILED"
LED_READY = "LED_READY"
LED_PUB = "LED_PUB"


# Try WiFi connect
def wifi_connect(ssid, pwd):
	# Try WiFi connect by nmcli
	if(pwd == None):
		result = subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid], capture_output=True)
	else:
		result = subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', pwd], capture_output=True)
	print(f"wifi connect result:{result}")
	# Wrong WiFi SSID
	if(result.stderr.decode("ascii").find("No network with SSID") > 0):
		print("wifi ssid failed")
		# Send to microbit(wrong wifi ssid)
		uart.send(PUB_WIFI_SSID_FAILED)
	# Wrong WiFi Password
	elif(result.stderr.decode("ascii").find("security.psk") > 0):
		print("wifi password failed")
		# Send to microbit(wrong wifi password)
		uart.send(PUB_WIFI_PWD_FAILED)
	else:
		print("wifi connect successfuly")	

# Read value from microbit uart
def readUart():
	print(f"Start read uart\n")
	lineCount = 0
	index = 0
	msg = ""
	'''	
	Video publish information:
		explain: A total of 14 messages are sent from the web page.
		example:
			{"type":"metric#14   <--- 14 is total message count
			","data":{"serv
			er":{"ssid":"Te
			amGRIT","passwo
			rd":"teamgrit82
			66","host":"agi
			lertc.com","por
			t":8276,"path":
			"pang/ws/pub?ch
			annel=instant&n
			ame=kjkj&track=
			video&mode=bund
			le"},"profile":
			"RPI_BW_001"}}	
	'''
	while(True):
		c = uart.uart.readline()
		value = c.decode()
		value = value.rstrip()
		print(value)
		# '#' is message count delimiter
		lineCountDelimiterIndex = value.find('#')
		if lineCountDelimiterIndex > 0:
			splits = value.split("#")
			# '#' must has index is 0
			if index > 0:
				msg = ""
				index = 0
			value = splits[0]
			lineCount = int(splits[1])
		msg = ("%s%s") % (msg, value)
		if(lineCount - 1 > index):
			index = index + 1
			print(f"index:{index}")
		else:
			lineCount = 0
			index = 0
			print(msg)
			if(msg):
				try:
					jsonObject = json.loads(msg)
					msg = ""
					value = ""
					if("type" in jsonObject):
						type = jsonObject.get("type")
						if(type == "metric"):
							data = jsonObject.get("data")
							if(data):
								server = data.get("server")
								if(server):
									ssid = server.get("ssid")
									password = server.get("password")
									host = server.get("host")
									port = server.get("port")
									path = server.get("path")
									profile = data.get("profile")
									print(f"ssid:{ssid}, password:{password}, host:{host}, port:{port}, path:{path}, profile:{profile}")
									# Try WiFi Connect
									wifi_connect(ssid, password)
									url = f"ws://{host}:{port}/{path}"
									moth.url = url
									# Try Moth Connect
									moth.start()
									print("moth started")
								else:
									print(f"empty server")
							else:
								print(f"empty data")
						elif(type == "control"):
							direction = jsonObject.get("direction")
							print(f"direction:{direction}")
							if(direction):
								upper = direction.upper()
								uart.send(upper)
							else:
								print(f"empty direction")
						elif(type == "bitrate"):
							bitrate = jsonObject.get("value")
							print(f"bitrate:{bitrate}")
							info = {}
							info["bitrate"] = bitrate
							moth.change_pipeline(info)
						else:
							print(f"empty type")

				except json.JSONDecodeError as e:
					print(f"JSON Error: {e}")
					msg = ""
					value = ""
					uart.send(PUB_PARSING_FAILED)
				except Exception as e:
					print(f"unknown Error: {e}")
					msg = ""
					value = ""
					uart.send(PUB_PARSING_FAILED)

def main():
	global uart, moth
	try:
		# Create UART Instance
		uart = Uart()
		# Create Moth Instance with UART Instance
		moth = Moth(uart)
		# Ready for Robot: Turn on Yellow LED
		uart.send(LED_READY)
		# Read Serial Data from micro:bit
		readUart()
	except KeyboardInterrupt:
		print(f"KeyboardInterrupt")
		# Close UART Connection
		uart.close()
		asyncio.run(moth.close())

if __name__ == '__main__':
    main()
