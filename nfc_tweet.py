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
from datetime import datetime, timedelta
from scipy.io import wavfile
from matplotlib import cm


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
#25 tweets per 15 minute rate limit check + rain/wind check
#verification
#code convention


if not admin.isUserAdmin():
        admin.runAsAdmin()

callpath = 'C:\\temp\\calls'
dirpath = 'C:\\'
existing = os.listdir(callpath)

running = False

def parse_file_name(file):
	sp = file.split("_")
	lt = localtime()
	tz = ''
	
	if lt.tm_isdst == 0:
		tz = 'EST'
	else:
		tz = 'EDT'
	
	return sp[0]+" at "+sp[2]+" "+tz+" on "+sp[1]+"."

def makeimg(wav):
	global callpath

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
	
	pylab.title("Tester")
	pylab.ylim([0,11025])
	pylab.xlim([0,round(x_width,3)-0.006])

	pylab.savefig(os.path.join(callpath, wav.replace(".wav",".png")))
	
	return os.path.join(callpath, wav.replace(".wav",".png"))

def upload_to_soundcloud(wav):
	print 'heading to soundcloud'
	global callpath
	global config
	global scclient
	track = scclient.post(
		'/tracks', 
		track={
			'title': 'This is a sample track',
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
		status = api.PostMedia("Test tweet with link. " + wav_path,img_path)

def callme():
	print 'calling'
	global existing
	threading.Timer(5.0, callme).start()
	print 'lists'
	
	if len(existing) != len(os.listdir(callpath)):
		print 'not equal, action'
		acton = set(os.listdir(callpath)) - set(existing)
		tweet(acton)
		existing = os.listdir(callpath)

def start_tseep():
	global dirpath
	print 'start'
	#rename file to stop.txt
	
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
	print 'stop'
	#rename file to stop.txt
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
	print 'check running'
	global running
	
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
		if (utc_to_local(prev_rise_time).day == utc_to_local(now).day) & \
		(now >= prev_rise_time) & \
		(now <= next_set_time):
			stop_tseep()
	else:
		if (utc_to_local(prev_set_time).day == utc_to_local(now).day) & \
		(now >= prev_set_time) & \
		(now <= next_rise_time):
			start_tseep()

def check_time():
	threading.Timer(60.0, check_time).start()
	
	check_running()

check_time()