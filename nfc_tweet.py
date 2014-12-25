#program to tweet nfcs
import os
import admin
import threading
import twitter
import config
import numpy
import matplotlib
import pylab
import soundcloud
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

if not admin.isUserAdmin():
        admin.runAsAdmin()
        
#check to see what time it is
#if time is after astronomical twilight, start Tseep-r

#start Tseep-r
os.startfile(r"C:\My Recordings\Tseep-r.exe")
#subprocess.call(['C:\\My Recordings\\Tseep-r.exe'])

callpath = 'C:\\temp\\calls'
existing = os.listdir(callpath)

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

def makeimg(wav):
	global callpath

	fs, frames = wavfile.read(os.path.join(callpath, wav))

	# generate specgram
	pylab.specgram(
		frames,
		NFFT=256, 
		Fs=44100, 
		detrend=pylab.detrend_none,
		window=pylab.window_hanning,
		noverlap=int(44100 * 0.0025),
		cmap=cm.gray_r)

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
		

callme()

##use ravenpro to create spectrogram
##upload to soundcloud?
#if more than 10 new files within 15 seconds, shut down for an hour

#if after astronomical twilight, turn off

#stop and reset Tseep-r
#need to turn off UAC so that pop up window doesn't prevent workflow
dirpath = 'C:\\'

#rename file to stop.txt
#for filename in os.listdir('C:\\'):
#       if filename.startswith("go"):
#               print filename
#               os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, "stop.txt"))


#rename file to go.txt
#for filename in os.listdir('C:\\'):
#       if filename.startswith("stop"):
#               print filename
#               os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, "go.txt"))
