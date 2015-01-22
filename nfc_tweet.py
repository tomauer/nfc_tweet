#program to tweet nfcs
from __future__ import division
import os
import admin
import threading
import twitter
import config
import numpy
import matplotlib
import pylab
import soundcloud
import ephem
import calendar
import threading
import time
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

##TODO
#verification
#code convention

if not admin.isUserAdmin():
        admin.runAsAdmin()

callpath = 'C:\\temp\\calls'
imgpath = 'C:\\temp\\imgs'
dirpath = 'C:\\'
existing = os.listdir(callpath)

running = False

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

def makeimg(wav):
	global callpath
	global imgpath

	fs, frames = wavfile.read(os.path.join(callpath, wav))

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

def upload_to_soundcloud(wav):
	global callpath
	global config
	global scclient
	
	track = scclient.post(
		'/tracks', 
		track={
			'title': parse_file_name(wav),
			'sharing': 'public',
			'asset_data': open(os.path.join(callpath, wav), 'rb')
			}
		)
	
	return track.permalink_url
	
def tweet(tweetset):
	global callpath
	global api
	
	for f in tweetset:
		img_path = makeimg(f)
		wav_path = upload_to_soundcloud(f)
		status = api.PostMedia(parse_file_name(f) + wav_path,img_path)

def callme():
	global existing
	global timer15
	global tweets
	global checkTime
	global waitTime
	global api
	
	print 'Looking for new noises.'
	
	if waitTime != None:
		waitTime.cancel()
		waitTime = None
	
	checkTime = threading.Timer(15.0, callme)
	checkTime.start()
	
	if timer15 == 900:
		timer15 = 0
		tweets = 0
	else:
		timer15+=15
	
	print 'Time'
	print timer15
	print 'Tweets'
	print tweets
	
	if len(existing) != len(os.listdir(callpath)):
		print 'New noises!'
		
		checkTime.cancel()
		
		acton = set(os.listdir(callpath)) - set(existing)
		
		print len(acton)
		tweet(acton)
		tweets+=len(acton)
		existing = os.listdir(callpath)
		
		
		
		if (timer15 < 900) & (tweets >= 21):
			print 'Taking a break.'
			
			status = api.PostUpdate("Taking a break. Too many birds, too much wind, too much background noise, or it's raining. Back in 15 minutes!")
			
			timer15 = 0
			tweets = 0
			
			waitTime = threading.Timer(900.0, callme)
			waitTime.start()
		else:
			checkTime = threading.Timer(15.0, callme)
			checkTime.start()

def start_tseep():
	global dirpath
	global scclient
	global api
	
	print 'Start tseep.'
	
	#auth soundcloud
	scclient = soundcloud.Client(
		client_id=config.client_id,
		client_secret=config.client_secret,
		username=config.username,
		password=config.password
	)

	#auth twitter
	api = twitter.Api(
		consumer_key=config.consumer_key, 
		consumer_secret=config.consumer_secret, 
		access_token_key=config.access_token_key, 
		access_token_secret=config.access_token_secret
	)
	
	print api.VerifyCredentials()
	
	for filename in os.listdir('C:\\'):
		if filename.startswith("stop"):
			os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, "go.txt"))
			
	os.startfile(r"C:\My Recordings\Tseep-r.exe")
	os.startfile(r"C:\My Recordings\Thrush-r.exe")
	
	callme()
			
def stop_tseep():
	global dirpath
	
	print "Stop tseep."

	for filename in os.listdir('C:\\'):
	    if filename.startswith("go"):
	        os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, "stop.txt"))
	
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
			stop_tseep()
			running = False
	else:
		if (utc_to_local(prev_set_time).day == utc_to_local(now).day) & \
		(now >= prev_set_time) & \
		(now <= next_rise_time):
			start_tseep()
			running = True

def check_time():
	threading.Timer(60.0, check_time).start()
	
	check_running()

check_time()