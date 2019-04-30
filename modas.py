import datetime
import requests
import json
from random import randint
from gpiozero import MotionSensor, LED, Button
from time import sleep
from picamera import PiCamera
import time as dt
import getpass

class Modas:
	def __init__(self):
		# init PiCamera
		self.camera = PiCamera()
		#flips camera rotation upside down
		#self.camera.rotation = 180
		# set camera resolution
		self.camera.resolution = (1024, 768)
		# init green, red LEDs
		self.green = LED(24)
		self.red = LED(23)
		# init button
		self.button = Button(8)
		# init PIR
		self.pir = MotionSensor(25)
		# when button  is released, toggle system arm / disarm
		self.button.when_released = self.toggle
		
		# system is disarmed by default
		self.armed = False
		self.disarm_system()

	def init_alert(self):
		self.green.off()
		self.red.blink(on_time=.25, off_time=.25, n=None, background=True)
		print("motion detected")
		# Take photo
		self.snap_photo()
		# delay
		sleep(2)
		
	def reset(self):
		self.red.off()
		self.green.on()
		
	def toggle(self):
		self.armed = not self.armed
		if self.armed:
			self.arm_system()
		else:
			self.disarm_system()
			
	def arm_system(self):
		print("System armed in 3 seconds")
		self.red.off()
		# enable camera
		self.camera.start_preview()
		
		# 3 second delay
		self.green.blink(on_time=.25, off_time=.25, n=6, background=False)
		# enable PIR
		self.pir.when_motion = self.init_alert
		self.pir.when_no_motion = self.reset
		self.green.on()
		print("System armed")
		
	def disarm_system(self):
		# disable PIR
		self.pir.when_motion = None
		self.pir.when_no_motion = None
		# disable camera
		self.camera.stop_preview()
		self.red.on()
		self.green.off()
		print("System disarmed")
		
	def snap_photo(self):
		date_string = dt.strftime("%Y-%m-%d-%H:%M:%S")
		self.camera.annotate_text = date_string
		self.camera.capture('/home/pi/Pictures/' + date_string + '.jpg')
		#self.camera.capture('/home/pi/Pictures/image.jpg')
		# get current date / time
		t = datetime.datetime.now()
		# format date in json format for RESTful API
		t_j = "{0}-{1}-{2}".format(t.strftime("%Y"), t.strftime("%m"), t.strftime("%d"))
		t_json = "{0}-{1}-{2}T{3}:{4}:{5}".format(t.strftime("%Y"), t.strftime("%m"), t.strftime("%d"), t.strftime("%H"), t.strftime("%M"), t.strftime("%S"))

		rand = randint(1, 3)
		
		try:
			rf = open("token.json", "r")
			o=json.loads(rf.read())
			rf.close()
		except:
			pass
		url = 'https://modas-hbk.azurewebsites.net/api/event/'
		headers = { 'Authorization': 'Bearer ' + o["token"],'Content-Type': 'application/json'}
		payload = { 'timestamp': t_json, 'flagged': False, 'locationId': rand }
		print(headers)
		# post the event
		r = requests.post(url, headers=headers, data=json.dumps(payload))
		self.filename = t_j+ ".log"
		f = open(self.filename, "a")
		f.write(t_json + ", False, " + str(rand) + ", " + str(r.status_code) + "\n")
		f.close()
		print(t_json)
		
	

m = Modas()

try:
	# program loop
    while True:
        sleep(.001)
# detect Ctlr+C
except KeyboardInterrupt:
	if m.armed:
		m.disarm_system()
