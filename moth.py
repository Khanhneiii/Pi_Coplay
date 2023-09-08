import subprocess
import asyncio
import serial
import re
import json
import time
from time import sleep 
import websocket
import threading
import io
from gstreamer import GStreamer
from uart import Uart
from sys import getsizeof
PUB_SUCCESS = "PUB_SUCCESS"
PUB_FAILED = "PUB_FAILED"
PUB_WS_FAILED = "PUB_WS_FAILED"
PUB_CAMERA_FAILED = "PUB_CAMERA_FAILED"
LED_READY = "LED_READY"
LED_PUB = "LED_PUB"

class Moth():
	url = None
	def __init__(self, uart):
		self.gst = GStreamer()
		self.now = time.time()
		self.websocket = None
		self.uart = uart
		self.sendThreadOn = False
		self.connectThread	= None
		self.sendThread	= None

	# Try Moth Connect
	def start(self):
		try:
			if(self.connectThread):
				self.close()
				self.connectThread = None
			self.connectThread = threading.Thread(target=self.connect)
			self.connectThread.start()
		except Exception as e:
			print(f"start Error: {e}")

	# Try Connect Websocket 
	def connect(self):
		try:
			print(f"Connect websocket:{self.url}")
			# websocket.enableTrace(True)
			self.websocket = websocket.WebSocketApp(self.url,
									on_open=self.on_open,
									on_message=self.on_message,
									on_error=self.on_error,
									on_close=self.on_close)
			self.websocket.run_forever(reconnect=5)
		except Exception as e:
			print(f"connect Error: {e}")

	def on_open(self, ws):
		print("Opened connection")
		print(f"self:{self}")
		self.uart.send(PUB_SUCCESS)
		if(self.sendThread):
			# self.sendThread.stop()
			print("send thread stop")
			self.sendThreadOn = False
			self.sendThread = None
		self.sendThreadOn = True
		self.sendThread = threading.Thread(target=self.send)
		self.sendThread.start()

	def on_message(self, ws, message):	
		print(f"received message:{message}")
		try:
			if("ping" in message):
				print(message)
			else:
				jsonObject = json.loads(message)
				if("type" in jsonObject):
					type = jsonObject.get("type")
					print(f"type:{type}")
					if(type == "control"):
						direction = jsonObject.get("direction")
						print(f"direction:{direction}")
						if(direction):
							upper = direction.upper()
							self.uart.send(upper)
						else:
							print(f"empty direction")
						nows = jsonObject.get("time")
						if nows:
							print("Control Time : ", int(1000*(time.time() - float(nows))), "ms")
					else:
						print(f"empty type")

		except json.JSONDecodeError as e:
			print(f"JSON Error: {e}")
		except Exception as e:
			print(f"unknown Error: {e}")

	def on_error(self, ws, error):
		print(error)
		self.sendThreadOn = False
		self.uart.send(PUB_FAILED)

	def on_close(self, ws, close_status_code, close_msg):
		print(f"close_status_code:{close_status_code}")
		self.sendThreadOn = False

	# Send encoded video frame to websocket
	def send(self):
		print("Send encoded video frame begin")
		if(self.websocket):
			self.websocket.send(self.gst.mime)
		while self.sendThreadOn:
			image = self.gst.get_video_frame()
			if image:
				# now = time.time()
				self.websocket.send(image, opcode=websocket.ABNF.OPCODE_BINARY)
				# print(int(1000*(time.time()-now)), "ms")
			else:
				self.uart.send(PUB_CAMERA_FAILED)
		print("Send encoded video frame end")

	# Close WebSocket 
	def close(self):
		if(self.websocket):
			self.websocket.close(status=1002)
			self.websocket = None
			print("close websocket")

	def change_pipeline(self, info):
		self.gst.change_pipeline(info)

	
