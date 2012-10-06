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
        dominant = reduce(lambda y,x: x if x[1] > y[1] else y, zip(range(len(data)), data), [0,0])
        if (dominant[1] > 10 and dominant[0] != 0.0):
            freq = freqs[dominant[0]]
            print freq,
            note = ftomidi(freq)
            print note
            PlayNote(note)
            dominant = dominant[0]
        else:
            dominant = False

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
            if dominant and (point[0] + 2) > dominant and (point[0] - 2) < dominant:
                r = 1
                g = 0
                b = 0
            else:
                r = g = b = point[1] / 3

            curve.append(pos=(point[0],point[1],0), color=(r,g,b))
        self.curves.insert(0,curve)

v = Visualiser()

#out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK)
#out.setchannels(1)
#out.setrate(rate)
#out.setformat(alsaaudio.PCM_FORMAT_S16_LE)
#out.setperiodsize(slen)
#inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)

inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE)
inp.setchannels(1)
inp.setrate(rate)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize(slen)

def parse(data):
    l = len(data)
    samples = scipy.zeros(l / 2)
    fft = scipy.zeros(l / 2)
    for i in range(0, l / 2):
        samples[i]=audioop.getsample(data, 2, i)

    fft = scipy.fft(samples)
    fft = fft[:len(fft) / 2]
    fft = abs(fft)
    fft *= .00005
    v.display(fft)

delay = []
delaytime = 50

while True:
    # Read data from device
    l,data = inp.read()
    if l > 0:
        parse(data)
    time.sleep(.01)
