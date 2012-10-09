#!/usr/bin/python

import time
import scipy, numpy, math # parsing

import visual # visualisation

import alsaseq, alsamidi # midi output

alsaseq.client( 'Note Recogniser', 0, 1, False )

rate = 8000
slen = 160


def miditof(x):
    return (440 / 32) * (2 ^ ((x - 9) / 12));

def ftomidi(f):
    return int((math.log(f / (440 / 32),2) * 12) + 9)


def PlayNote(note):
    alsaseq.output(alsamidi.noteonevent( 0, note, 127 ))


class Event(object):
    pass

class Observable(object):
    def __init__(self):
        self.callbacks = {}

    def subscribe(self, name, callback):
        if not self.callbacks.has_key(name):
            self.callbacks[name] = []

        self.callbacks[name].append(callback)

    def fire(self, name, **attrs):
        if not self.callbacks.has_key(name):
            return

        e = Event()
        e.source = self
        e.name = name
        for k, v in attrs.iteritems():
            setattr(e, k, v)

        for fn in self.callbacks[name]:
            fn(e)



class Node(Observable):
    def __init__(self):
        self.children = []

    def addchild(self,node):
        self.children.append(node)

    def output(self,data):
        map(lambda child: child.input(data), self.children)

    def input(self,data):
        self.output(data)




class NoteRecorder(Node):
    def __init__(self):
        Node.__init__(self)
        self.data = {}

    def input(self,data):
        print('in')
        if data.has_key('note'):
            print(data['note'])



class Visualiser(Node):
    def __init__(self):
        Node.__init__(self)
        self.step = 1
        self.maxlen = (slen / 2) / self.step
        self.g = visual.display(width=600, height=200,center=(slen/4,30,0))
        self.curves = []
        self.label = False
        self.lastdominant = 0

    def input(self,data):
        fft = data['fft']

        if (len(self.curves) > self.maxlen):
            todel = self.curves.pop()
            todel.visible = False
            del todel

        for oldcurve in self.curves:
            for point in range(len(oldcurve.pos)):
                oldcurve.pos[point][2] -= self.step

        y = []
        for point in fft:
            y.append(point)
            y.append(point)

        curve = visual.curve(color=visual.color.white, display=self.g, radius=0)

        if data.has_key('dominantbucket'):
            dominant = data['dominantbucket']
        else:
            dominant = False


        if (self.lastdominant != dominant and self.label):
            self.label.visible = False
            del self.label
            self.label = False

        for point in zip(range(len(fft)),fft):
            if dominant and (point[0] + 2) > dominant and (point[0] - 2) < dominant:
                r = 1
                g = 0
                b = 0

                if (self.lastdominant != dominant and dominant == point[0]):
                    self.label = visual.label(pos=(point[0],10,0),
                                       text=str(data['note']), xoffset=20,
                                       yoffset=12,
                                       height=10, border=6,
                                       font='sans')
            else:
                r = g = b = point[1] / 3

            curve.append(pos=(point[0],point[1],0), color=(r,g,b))
        self.lastdominant = dominant

        self.curves.insert(0,curve)


class NoteRecogniser(Node):
    def __init__(self):
        Node.__init__(self)

        self.freqs = numpy.fft.fftfreq(slen,1.0 / rate)
        self.freqs = self.freqs[:len(self.freqs) / 2]

    def input(self,data):
        fft = data['fft']
        dominant = reduce(lambda y,x: x if x[1] > y[1] else y, zip(range(len(fft)), fft), [0,0])
        if (dominant[1] > 10 and dominant[0] != 0.0):
            frequency = self.freqs[dominant[0]]
            note = ftomidi(frequency)
            bucket = dominant[0]

            data['frequency'] = frequency
            data['note'] = note
            data['dominantbucket'] = bucket

class Fft(Node):
    def input(self,data):
        samples = data['recording']

        fft = scipy.fft(samples)
        fft = fft[:len(fft) / 2]
        fft = abs(fft)
        fft *= .00005
        data['fft'] = fft
        self.output(data)

class AlsaRecorder(Node):

    def start(self):
        import alsaaudio, audioop

        inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE)
        inp.setchannels(1)
        inp.setrate(rate)
        inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        inp.setperiodsize(slen)

        while True:
            l,data = inp.read()
            if l > 0:
                ln = len(data)
                samples = scipy.zeros(ln / 2)
                fft = scipy.zeros(ln / 2)
                for i in range(0, ln / 2):
                    samples[i]=audioop.getsample(data, 2, i)

                self.output({ 'recording': samples, 'rate': rate, 'slen': slen })
            time.sleep(.01)


class JackRecorder(Node):
    def start(self):
        import jack

        jack.attach("NoteRecogniser Recorder")
        jack.register_port("in_1", jack.IsInput)
        jack.activate()
        try:
            jack.connect("system:capture_1", "NoteRecogniser Recorder:in_1")
            jack.connect("system:capture_2", "NoteRecogniser Recorder:in_1")
        except err:
            print ("Unable to connect to system:capture")

        buffer_size = jack.get_buffer_size()
        sample_rate = float(jack.get_sample_rate())

        print "Buffer Size:", buffer_size, "Sample Rate:", sample_rate

        output = scipy.zeros((1,buffer_size), 'f')
        while True:
            try:
                input = scipy.zeros((1,buffer_size), 'f')
                jack.process(output, input)
                #print  len(input)
                fft = numpy.fft.rfft(input[0])
                fft = map(lambda c : math.sqrt(c.real*c.real + c.imag*c.imag), fft)
                #print(len(fft))
                dominant = reduce(lambda y,x: x if x[1] > y[1] else y, zip(range(len(fft)), fft), [0,0])
                print dominant
                
            except jack.InputSyncError:
				print "Input Sync Error"
				pass

            except jack.OutputSyncError:
				print "Output Sync Error"
				pass






recorder = JackRecorder()
fft = Fft()
vis = Visualiser()
note = NoteRecogniser()
note_recorder = NoteRecorder()

recorder.addchild(fft)
fft.addchild(note)
fft.addchild(vis)
note.addchild(note_recorder)


recorder.start()
