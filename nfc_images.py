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
dirpath = 'C:\\'
existing = os.listdir(callpath)

running = False

checkTime = None

def parse_file_name(file):
	sp = file.split("_")
	lt = localtime()
	tz = ''
	
	if lt.tm_isdst == 0:
		tz = 'EST'
	else:
		tz = 'EDT'
	
	return sp[0]+" at "+sp[2]+" "+tz+" on "+sp[1]+". "

def makeimg(wav):
	global callpath
	global imgpath

	fs, frames = wavfile.read(os.path.join(callpath, wav))
	
	pylab.ion()

	# generate specgram
	pylab.figure(1)
	
	# generate specgram
	pylab.specgram(
		frames,
		NFFT=256, 
		Fs=22050, 
		detrend=pylab.detrend_none,
		window=numpy.hamming(256),
		noverlap=192,
		cmap=pylab.get_cmap('Greys'))
	
	x_width = len(frames)/fs
	
	pylab.ylim([0,11025])
	pylab.xlim([0,round(x_width,3)-0.006])
	
	img_path = os.path.join(imgpath, wav.replace(".wav",".png"))

	pylab.savefig(img_path)
	
	return img_path

def callme():
	global existing
	global checkTime
	global callpath
	
	print 'Looking for new noises.'

	checkTime = threading.Timer(15.0, callme)
	checkTime.start()

	if (len(existing) != len(os.listdir(callpath))):
		print 'New noises!'
		
		checkTime.cancel()
		
		acton = set(os.listdir(callpath)) - set(existing)
		
		#make images
		for f in acton:
			img_path = makeimg(f)
		
		existing = os.listdir(callpath)
		
		print 'Waiting 15 seconds'
		checkTime = threading.Timer(15.0, callme)
		checkTime.start()

def start_tseep_offline():
	global dirpath
	global existing
	global running
	
	print 'Start tseep offline.'
	
	running = True
	
	for filename in os.listdir('C:\\'):
		if filename.startswith("stop"):
			os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, "go.txt"))
			
	os.startfile(r"C:\My Recordings\Tseep-r.exe")
	os.startfile(r"C:\My Recordings\Thrush-r.exe")
	
	existing = os.listdir(callpath)
	
	callme()
		
def stop_tseep():
	global dirpath
	global existing
	global checkTime
	
	print "Stop tseep."
	
	for filename in os.listdir('C:\\'):
	    if filename.startswith("go"):
	        os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, "stop.txt"))
		
	if checkTime != None:
		checkTime.cancel()
		checkTime = None
	
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
	ri.horizon = '-6'
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
	
	next_set_time_tt = utc_to_local(next_set_time).timetuple()
	next_rise_time_tt = utc_to_local(next_rise_time).timetuple()
	prev_set_time_tt = utc_to_local(prev_set_time).timetuple()
	prev_rise_time_tt = utc_to_local(prev_rise_time).timetuple()
	
	if running:	
		if (prev_rise_time_tt.tm_yday > prev_set_time_tt.tm_yday) & \
		(next_rise_time_tt.tm_yday > next_set_time_tt.tm_yday) & \
		(now >= prev_rise_time) & \
		(now <= next_set_time):
			stop_tseep()
			running = False
	else:
		if (utc_to_local(prev_set_time).day == utc_to_local(now).day) & \
		(now >= prev_set_time) & \
		(now <= next_rise_time):
			start_tseep_offline()

def check_time():
	threading.Timer(60.0, check_time).start()
	
	check_running()

check_time()