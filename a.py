#!/usr/bin/python
## This is an example of a simple sound capture script.
##
## The script opens an ALSA pcm for sound capture. Set
## various attributes of the capture, and reads in a loop,
## Then prints the volume.
##
## To test it out, run it and shout at your microphone:

import alsaaudio, time, audioop, scipy, visual
import numpy as np

slen = 160

class Visualiser:
    def __init__(self):
        self.step = 1
        self.maxlen = (slen / 2) / self.step
        self.g = visual.display(width=600, height=200,center=(slen/4,30,0))
        #        self.curve = visual.curve( x=arange(slen / 2), color=color.red, display=self.g, radius=0.1)
        self.curves = []

    def display(self,data):

        
        dominant = reduce ( lambda y, x: x if x[1] > y[1] else y  ,zip(range(len(data)),data),[0,0])
        if(dominant[1] < 7):
           dominant = False
        else:
           dominant = dominant[0]
           print dominant

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

# Open the device in nonblocking capture mode. The last argument could
# just as well have been zero for blocking mode. Then we could have
# left out the sleep call in the bottom of the loop
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)

# Set attributes: Mono, 8000 Hz, 16 bit little endian samples
inp.setchannels(1)
inp.setrate(8000)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

# The period size controls the internal number of frames per period.
# The significance of this parameter is documented in the ALSA api.
# For our purposes, it is suficcient to know that reads from the device
# will return this many frames. Each frame being 2 bytes long.
# This means that the reads below will return either 320 bytes of data
# or 0 bytes of data. The latter is possible because we are in nonblocking
# mode.
inp.setperiodsize(160)

while True:
    # Read data from device
    l,data = inp.read()
    if l > 0:
        #print l, len(data)
        # Return the maximum of the absolute value of all samples in a fragment.
        #print audioop.max(data,2)

        samples = scipy.zeros(slen)
        fft = scipy.zeros(slen)

        for i in range(0, slen):
            samples[i]=audioop.getsample(data, 2, i)

        fft=np.fft.ifftshift(scipy.fft(samples))
        fft = fft[160/2:]
        fft = np.abs(fft)
        fft *= 0.00005
        #fft *= 30.0/fft.max()
        #print fft
        v.display(fft)
    time.sleep(.01)
