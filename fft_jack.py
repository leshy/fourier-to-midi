#!/usr/bin/python
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm for sound capture. Set
## various attributes of the capture, and reads in a loop,
## Then prints the volume.
##
## To test it out, run it and shout at your microphone:

import alsaaudio, time, audioop, scipy, visual, math
import numpy as np
import alsaseq
import jack

alsaseq.client( 'test', 1, 2, False )

rate = 8000
slen = 160

freqs = np.fft.fftfreq(slen,1.0 / rate)
freqs = freqs[:len(freqs) / 2]

def miditof(x):
    return (440 / 32) * (2 ^ ((x - 9) / 12));

def ftomidi(f):
    return int((math.log(f / (440 / 32),2) * 12) + 9)

def PlayNote(num):
    alsaseq.output( [6, 0, 0, 253, (0, 0), (129, 0), (131, 0), (0, num, 127, 0, 0)] )

class Visualiser:
    def __init__(self):
        self.step = 1
        self.maxlen = (slen / 2) / self.step
        self.g = visual.display(width=600, height=200,center=(slen/4,30,0))
        self.curves = []

    def display(self,data):
        #dominant = reduce(lambda y,x: x if x[1] > y[1] else y, zip(range(len(data)), data), [0,0])
        #if (dominant[1] > 10 and dominant[0] != 0.0):
        #    freq = freqs[dominant[0]]
        #    print freq,
        #    note = ftomidi(freq)
        #    print note
        #    PlayNote(note)
        #    dominant = dominant[0]
        #else:
        #    dominant = False

        if (len(self.curves) > self.maxlen):
            todel = self.curves.pop()
            todel.visible = False
            del todel

        for oldcurve in self.curves:
            for point in range(len(oldcurve.pos)):
                oldcurve.pos[point][2] -= self.step

        y = []
        for point in data:
            y.append(point)
            y.append(point)

        curve = visual.curve(color=visual.color.white, display=self.g, radius=0)

        for point in zip(range(len(data)),data):
            r = g = b = 1
            curve.append(pos=(point[0],point[1] * 10,0), color=(r,g,b))
        self.curves.insert(0,curve)

#out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK)
#out.setchannels(1)
#out.setrate(rate)
#out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
#out.setperiodsize(slen)
#inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)

jack.attach("captest")
jack.register_port("in_1", jack.IsInput)
#jack.register_port("in_2", jack.IsInput)
jack.register_port("out_1", jack.IsOutput)
#jack.register_port("out_2", jack.IsOutput)

jack.activate()

jack.connect("system:capture_1", "captest:in_1")
jack.connect("system:capture_2", "captest:in_1")
jack.connect("captest:out_1", "system:playback_1")
jack.connect("captest:out_1", "system:playback_2")

buffer_size = jack.get_buffer_size()
sample_rate = float(jack.get_sample_rate())

print "Buffer Size:", buffer_size, "Sample Rate:", sample_rate

sec = 0.1

#capture = scipy.zeros((2,int(Sr*sec)), 'f')
input = scipy.zeros((1,buffer_size), 'f')
output = scipy.zeros((1,buffer_size), 'f')

def parse(data):
    fftsize = 10
    fft = scipy.zeros(fftsize)
    fft = scipy.fft(data,fftsize)
    fft = fft[:len(fft) / 2]
    fft = abs(fft)
    fft *= 0.05
    v.display(fft)

while True:
    i = 0
    capture = scipy.zeros((1,int(sample_rate*sec)), 'f')

    while i < capture.shape[1] - buffer_size:
        try:
            jack.process(output, capture[:,i:i+buffer_size])
            i += buffer_size
        except jack.InputSyncError:
            print "Input Sync"
            pass
        except jack.OutputSyncError:
            print "Output Sync"
            pass
        
        #    print len(capture[0])
    parse(capture[0])


jack.deactivate()
jack.detach()


#inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE)
#inp.setchannels(1)
#inp.setrate(rate)
#inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
#inp.setperiodsize(slen)

#while True:
    # Read data from device
    #    l,data = inp.read()
    #if l > 0:
    #    parse(data)
    #time.sleep(.01)
