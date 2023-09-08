import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
from gi.repository import GLib
from sys import getsizeof

class GStreamer():
	def __init__(self):
		Gst.init(None)

		self.width = 640
		self.height = 480
		self.framerate = 30
		self.bitrate = 2000000
		self.h264_profile = 1
		self.h264_level = 9
		self.level = 3.1
		self.profile = "baseline"
		self.format = "NV12"
		self.framesize = {'QQVGA': [160, 120], 'QCIF': [176, 144], 'HQVGA': [240, 176], '240_240': [240, 240], 'QVGA': [320, 240], 'CIF': [400, 296], 'HVGA': [480, 320], 'VGA': [640, 480], 'SVGA': [800, 640], 'XGA': [1024, 768], 'HD': [1280, 720], 'SXGA': [1280, 1024], 'UXGA': [1600, 1200], 'FHD': [1920, 1080], 'PHD': [720, 1280], 'P3MP': [864, 1536], 'QXGA': [2048, 1536], 'QHD': [2560, 1440], 'WQXGA': [2560, 1600], 'PFHD': [1080, 1920], 'QSXGA': [2560, 1920]}

		self.mime = None
		self.pipeline_cmd = None
		self.sink = None
		self.pipeline = None

		self.pipeline_set()
		self.mime_set()
		self.play_gstreamer()

	def pipeline_set(self):
		self.pipeline_cmd = f'v4l2src device=/dev/video0 ! video/x-raw, width={self.width}, height={self.height}, framerate={self.framerate}/1, format={self.format} ! videoflip method=rotate-180 ! v4l2h264enc extra-controls="controls, video_bitrate={self.bitrate}, h264_profile={self.h264_profile}, h264_level={self.h264_level}" ! video/x-h264, level=(string){self.level}, profile=(string){self.profile} ! h264parse config-interval=1 ! queue leaky=2 ! appsink name=moth max-buffers=1 drop=true emit-signals=true sync=false'

	def mime_set(self):
		self.mime = f"video/h264;width={self.width};height={self.height};framerate={self.framerate};bitrate={self.bitrate}"

	def play_gstreamer(self):
		self.pipeline = Gst.parse_launch(self.pipeline_cmd)
		self.sink = self.pipeline.get_by_name("moth")
		self.pipeline.set_state(Gst.State.PLAYING)

	def change_pipeline(self, info):
		print(f"change pipeline info:{info}")
		try:
			for row in self.framesize:
				if("width" in info and "height" in info):
					if int(self.framesize[row][0]) == int(info['width']):
						if int(self.framesize[row][1]) == int(info['height']):
							self.width = int(info['width'])
							self.height = int(info['height'])
			if("framerate" in info):
				if int(info['framerate']) > 15 and int(info['framerate']) < 31:
					self.framerate = int(info['framerate'])
			if("bitrate" in info):
				if int(info['bitrate']) > 24999 and int(info['bitrate']) < 25000001:
					self.bitrate = int(info['bitrate'])

			self.pipeline_set()
			self.mime_set()

			self.pipeline.set_state(Gst.State.NULL)
			self.play_gstreamer()

		except Exception as e:
			print(f"Exception: {e}")

	def get_video_frame(self):
		sample = self.sink.emit("pull_sample")
		if sample is not None:
			current_buffer = sample.get_buffer()
			image = current_buffer.extract_dup(0, current_buffer.get_size())
			# print(f"image size:{getsizeof(image)}")
			return image
		else:
			return False
		