#!/usr/bin/python
import time
import alsaaudio # input
import audioop, scipy, numpy, math # parsing
import visual # visualisation
import alsaseq, alsamidi # midi output

import thread

alsaseq.client( 'test', 1, 2, False )

rate = 8000
slen = 160

def miditof(x):
    return (440 / 32) * (2 ^ ((x - 9) / 12));

def ftomidi(f):
    #    return int((math.log(f / (440 / 32),2) * 12) + 9) - 14
    return int((math.log(f / (440 / 32),2) * 12) + 9) - 20

def PlayNote(note,velocity=127):
    print "playnote", note, velocity
    alsaseq.output(alsamidi.noteonevent( 0, note, velocity ))

def StopNote(note,velocity=127):
    print "stopnote", note
    alsaseq.output(alsamidi.noteoffevent( 0, note, 127 ))

class Event(object):
    pass

class Observable(object):
    def subscribe(self, name, callback):
        if not hasattr(self,'callbacks'):
            self.callbacks = {}
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



class Visualiser(Node):
    def __init__(self):
        Node.__init__(self)
        self.step = 10
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

        curve = visual.curve(color=visual.color.white, display=self.g, radius=0.3)

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
                                       yoffset=127,
                                       height=10, border=6,
                                       font='sans')
            else:
                r = g = b = point[1] / 3

            curve.append(pos=(point[0],point[1],0), color=(r,g,b))
        self.lastdominant = dominant

        self.curves.insert(0,curve)


class Fft(Node):
    def input(self,data):
        recording = data['recording']
        l = len(recording)
        samples = scipy.zeros(l / 2)
        fft = scipy.zeros(l / 2)
        for i in range(0, l / 2):
            samples[i]=audioop.getsample(recording, 2, i)

        fft = scipy.fft(samples)
        fft = fft[:len(fft) / 2]
        fft = abs(fft)
        fft *= .00005
        data['fft'] = fft
        self.output(data)


class Recorder(Node):
    def start(self):
        inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE)
        inp.setchannels(1)
        inp.setrate(rate)
        inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        inp.setperiodsize(slen)

        while True:
            a = time.time()
            l,data = inp.read() 
            if ((time.time() - a) > 0.01 and l > 0): # this is dumb. figure out how to skip
                self.output({ 'recording': data })



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
            velocity = dominant[1]
            print ('v',velocity)
            if note > 55 and velocity > 10:
                data['frequency'] = frequency
                data['note'] = note
                data['velocity'] = velocity
                data['dominantbucket'] = bucket
            #self.fire('note',note=note,bucket=bucket,frequency=frequency)
        self.output(data)


class Recording():
    def __init__(self):
        self.memory = []
        self.lastnote = None
        self.offcounter = 0

    def tick(self,note,velocity=127):
        def noteoff():
            if (self.lastnote):
                self.noteoff(self.lastnote)
                self.lastnote = None

        if (note):
            if note != self.lastnote:
                if not self.lastnote:
                    self.noteon(note,velocity)
                    self.lastnote = note
                    self.offcounter = 5
                else:
                    if abs(note - self.lastnote) > 1:
                        noteoff()
                        self.noteon(note,velocity)
                        self.lastnote = note

        else:
            if (self.offcounter < 0):
                noteoff()
            else:
                self.offcounter = self.offcounter - 1
                #print(self.offcounter)

    def tick_old(self,note,velocity=127):
        self.noteon(note,velocity)

    def empty(self):
        return not (len(self.memory) > 0)

    def noteon(self,note,velocity=50):
        if (self.empty()):
            self.starttime = time.time()
        velocity = int(velocity)
        print "noteon",note,velocity
        self.memory.insert(0,[time.time() - self.starttime, note, 0])


    def noteoff(self,note):
        if (self.empty()):
            self.starttime = time.time()
        print "noteoff",note
        self.memory.insert(0,[time.time() - self.starttime, note, -1])

    def play(self,callback):

        starttime = time.time()

        while len(self.memory):
            note = self.memory.pop()
            sleep = (starttime + note[0])  - time.time()

            if (sleep > 0):
                time.sleep(sleep / 2.0 )

            if (note[2] < 0):
                StopNote(note[1])
            else:
                PlayNote(note[1])
        callback()

class NoteRecorder(Node):
    def __init__(self):
        Node.__init__(self)
        self.startListening()


    def input(self,data):
        if (self._listening):
            self.listening(data)

    def startListening(self):
        print "Listening..."
        self._listening = True
        self.recording = Recording()

    def startPlaying(self):
        print "Playing..."
        self._listening = False
        def continueListening():
            time.sleep(1)
            self.startListening()
        self.recording.play(continueListening)

    def listening(self,data):
        if data.has_key('note'):
            self.lastnote = time.time()
            self.recording.tick(data['note'],data['velocity'])
        else:
            if (self.recording.empty()):
                self.lastnote = time.time()
            self.recording.tick(False)
            if time.time() - self.lastnote > 2:
                self.startPlaying()



# instantiate stuff
recorder = Recorder()
fft = Fft()
vis = Visualiser()
note_recogniser = NoteRecogniser()
note_recorder = NoteRecorder()

# connect stuff
recorder.addchild(fft)
fft.addchild(note_recogniser)
note_recogniser.addchild(vis)
note_recogniser.addchild(note_recorder)

# start stuff
recorder.start()
