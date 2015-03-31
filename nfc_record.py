#program to tweet nfcs
from __future__ import division
import os
import admin
import threading
import twitter
import config
import numpy
import matplotlib
matplotlib.use('Agg')
import pylab
import soundcloud
import ephem
import calendar
import threading
import time
import requests
from datetime import datetime, timedelta
from scipy.io import wavfile
from matplotlib import cm
from time import localtime
import wave
import pyaudio
from sys import byteorder
from array import array
from struct import pack

#dependencies
#pywin32
#numpy
#scipy
#python-twitter
#matplotlib
#six
#python-dateutil
#pyparsing
#soundcloud
#PyEphem

if not admin.isUserAdmin():
        admin.runAsAdmin()

callpath = 'C:\\temp\\calls'
imgpath = 'C:\\temp\\imgs'
recordpath = 'C:\\temp\\recordings'
dirpath = 'C:\\'
existing = os.listdir(callpath)

running = False
internet_up = False

api = ""
scclient = ""
timer15 = 0
tweets = 0
checkTime = None
waitTime = None

def parse_file_name(file):
	sp = file.split("_")
	lt = localtime()
	tz = ''
	
	if lt.tm_isdst == 0:
		tz = 'EST'
	else:
		tz = 'EDT'
	
	return sp[0]+" at "+sp[2]+" "+tz+" on "+sp[1]+". "
		
def record_audio():
	global recordpath
	
	CHUNK_SIZE = 1024
	FORMAT = pyaudio.paInt16
	RATE = 44100
	
	p = pyaudio.PyAudio()
	stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK_SIZE)

	r = array('h')
	
	now = datetime.utcnow()
	fmt = "%Y%m%d"
	
	day = datetime.utcnow().strftime("%Y%m%d")
	
	while running:
		snd_data = array('h', stream.read(CHUNK_SIZE))
		if byteorder == 'big':
			snd_data.byteswap()
		r.extend(snd_data)
		
		sample_width = p.get_sample_size(FORMAT)
		data = pack('<' + ('h'*len(r)), *r)
		
		wf = wave.open(os.path.join(recordpath, day + 'full.wav'), 'wb')
		wf.setnchannels(1)
		wf.setsampwidth(sample_width)
		wf.setframerate(RATE)
		wf.writeframes(data)
		
		wf.writeframes(data)
		
	wf.close()

def start():
	global dirpath
	global running
	
	print 'Start recording.'
	
	running = True
	
	#start recording
	record_audio()
		
def stop():
	global dirpath
	
	print "Stop recording."
	
def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)
	
def check_running():
	global running
	
	print "Checking running status."
	
	now = datetime.utcnow()

	ri = ephem.Observer()
	ri.lat = '41.38'
	ri.lon = '-71.61'
	ri.elev = 10
	ri.pressure = 0
	ri.horizon = '-18'
	ri.date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
	
	previous_set = ri.previous_setting(ephem.Sun(), use_center=True)
	next_rise = ri.next_rising(ephem.Sun(), use_center=True)
	previous_rise = ri.previous_rising(ephem.Sun(), use_center=True)
	next_set = ri.next_setting(ephem.Sun(), use_center=True)

	fmt = "%Y/%m/%d %H:%M:%S"

	next_set_time = datetime.strptime(str(next_set), fmt)
	next_rise_time = datetime.strptime(str(next_rise), fmt)
	prev_set_time = datetime.strptime(str(previous_set), fmt)
	prev_rise_time = datetime.strptime(str(previous_rise), fmt)
	
	if running:	
		if (utc_to_local(prev_rise_time).day > utc_to_local(prev_set_time).day) & \
		(utc_to_local(next_rise_time).day > utc_to_local(next_set_time).day) & \
		(now >= prev_rise_time) & \
		(now <= next_set_time):
			stop()
			running = False
	else:
		if (utc_to_local(prev_set_time).day == utc_to_local(now).day) & \
		(now >= prev_set_time) & \
		(now <= next_rise_time):
			start()

def check_time():
	threading.Timer(60.0, check_time).start()
	
	check_running()

check_time()
start()