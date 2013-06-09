#!/usr/bin/python
# Capture 3 seconds of stereo audio from alsa_pcm:capture_1/2; then play it back.
#
# Copyright 2003, Andrew W. Schmeder
# This source code is released under the terms of the GNU Public License.
# See LICENSE for the full text of these terms.

import Numeric
import jack
import time
from numpy.fft import rfft
from pylab import *
from numpy import *
import math

jack.attach("fftknn")

print jack.get_ports()

jack.register_port("in_1", jack.IsInput)
jack.register_port("out_1", jack.IsOutput)

jack.activate()

# jack.connect("alsa_pcm:capture_1", "fftknn:in_1")
# jack.connect("Hydrogen-1:out_L", "fftknn:in_1")
# jack.connect("pure_data_0:output0", "fftknn:in_1")
# jack.connect("sooperlooper:common_out_1", "fftknn:in_1")

print jack.get_connections("fftknn:in_1")

N = jack.get_buffer_size()
Sr = float(jack.get_sample_rate())
print "Buffer Size:", N, "Sample Rate:", Sr
# sec = 0.1

import rtmidi
midiin = rtmidi.RtMidiIn()
midiin.openVirtualPort('fftknn')
midiout = rtmidi.RtMidiOut()
midiout.openVirtualPort('fftknn')

time.sleep(1)

print "Capturing audio..."

window = 1024

# sorry, the window is at least as big as the buffer size
if window < N :
	window = N
	
if int(float(window)/float(N)) != window/N :
	print 'warning, make the window a multiple of the buffer size'

input = Numeric.zeros((1,window), 'f')
output = Numeric.zeros((1,N), 'f')

def findmax(l) :
	max = 0
	maxi = 0
	for i, c in enumerate(l) :
		# mag = math.sqrt(c.real*c.real + c.imag*c.imag)
		if c > max :
			max = c
			maxi = i
	return max, maxi

import operator
def findmin(l, comp = operator.lt) :
	min = 999999
	mini = 0
	for i, c in enumerate(l) :
		# mag = math.sqrt(c.real*c.real + c.imag*c.imag)
		if comp(c, min) :
			min = c
			mini = i
	return min, mini

import operator
def findminp(pairs, comp = operator.lt) :
	min = 999999
	mini = 0
	for i, c in pairs :
		# mag = math.sqrt(c.real*c.real + c.imag*c.imag)
		if comp(c, min) :
			min = c
			mini = i
	return min, mini


#pt0 = array([])
#pt0.resize(513)
#pt1 = array([])
#pt1.resize(513)
#pt2 = array([])
#pt2.resize(513)

# make this general case.
# when MIDI message commes in, assign that message to the space
# when the sound is near to that, play that same message
pts = {}
pts[0] = array([])
pts[0].resize(513)

lastnote = 0

bufnum = 0
while True :
		try:
#				for j in range(window/N-1) :
#					input[:,j*N] = input[:,(j+1)*N]
				
				jack.process(output, input[:,-N:])
				
				x = rfft(input[0]*hamming(window))
				x = array(map(lambda c : math.sqrt(c.real*c.real + c.imag*c.imag), x))
				
				dists = [(i, linalg.norm(x-pt)) for i, pt in pts.iteritems()]
				_, mini = findminp(dists)
				
#				if lastnote != mini :
				midiout.sendMessage(144, mini, 0)
				lastnote = mini
				if mini != 0 :
					# TODO: use RMS volume of input signal as value here
					midiout.sendMessage(144, mini, 120)
					print mini
					
				#dist0 = linalg.norm(x-pt0)
				#dist1 = linalg.norm(x-pt1)
				#dist2 = linalg.norm(x-pt2)
				#dists = [dist0, dist1, dist2]
				#_, mini = findmin(dists)
				
				#print mini, '\t', '\t'.join(map(str, map(int, dists)))
				#if dist1 < dist2 :
					#print '1', int(dist1), int(dist2)
				#else :
					#print '2', int(dist1), int(dist2)
				
				msg = midiin.getMessage()
				while msg != () :
					# capture
					if msg[0] == 144 and msg[1] == 36 :
						pts = {}
					if msg[0] == 144 and msg[2] != 0 :
						pts[msg[1]] = x
						print 'saved',msg[1]
					#if msg[0] == 144 and msg[1] == 60 :
						#pt1 = x
						#print 'saved #1'
					#elif msg[0] == 144 and msg[1] == 61 :
						#pt2 = x
						#print 'saved #2'
					msg = midiin.getMessage()
		except jack.InputSyncError:
				print "Input Sync"
				pass
		except jack.OutputSyncError:
				print "Output Sync"
				pass

jack.deactivate()

jack.detach()


exit()

























capture = Numeric.zeros((1,int(Sr*sec)), 'f')
input = Numeric.zeros((1,N), 'f')
output = Numeric.zeros((1,N), 'f')

i = 0
while i < capture.shape[1] - N:
		try:
				jack.process(output, capture[:,i:i+N])
				if sum(capture) > 0.1 :
					i += N
				
		except jack.InputSyncError:
				print "Input Sync"
				pass
		except jack.OutputSyncError:
				print "Output Sync"
				pass

jack.deactivate()

jack.detach()

print 'calculating'

def findi(x, val) :
	for i, xi in enumerate(x) :
		if xi == val :
			return i

#a = Numeric.zeros((capture.shape[1], 101), 'f')
#a = ndarray([], float32)
#a.resize(capture.shape[1], 101)

a0 = []
a1 = []
a2 = []
for i in range(0, capture.shape[1] - N, 100) :
	x = rfft(capture[0,i:i+N]*hamming(N))
	x = map(lambda c : math.sqrt(c.real*c.real + c.imag*c.imag), x)
	#max, maxi = findmax(x)
	#a0.append(i)
	#a2.append(maxi)
	#a1.append(max)
	for j, xj in enumerate(x) :
		if j < 100 :
			a0.append(i)
			a1.append(j)
			a2.append(xj)
	
	#x = array([i.real for i in x])
	
	#print type(array(x[0,:])), array(x[0,:]).shape
	#a[i,:] = x

print 'draw'

scatter(a0, a1, 1, a2, linewidth = 0)
show()

#print a.shape

#hist(a[10,:])
#show()

#imshow(a.transpose(), aspect='auto')
#show()
