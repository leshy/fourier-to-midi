#!/usr/bin/python
# Code to replicate (sort of) how the epucks listen and analyse sound to aid 
# in checking the timings of the epucks sound analysis and generation
# Takes 64 samples of sound, performs an FFT, builds up the timings for 
# sounds and silences in the freq bins the epucks listen to (8,10,12,14)

import alsaaudio, time, audioop
from scipy import *
from pylab import *
import datetime

def PlotSignal(Signal,myLabel, myFig):
    figure(myFig)
    if myLabel=='Combined':
        plot(Signal, label=myLabel, ls=':', lw=4)
    else:
        plot(Signal, label=myLabel)
    #legend()
    return 'ok'
def PlotFreq(Signal,myLabel, myFig):
    figure(myFig)
    localMag=zeros(8*1024, float)
    for i in range(0, len(localMag)):            
        localIndex = int((i * (len(Signal)/2))/len(localMag))
        localMag[i] = abs(Signal[localIndex])
    if myLabel=='Combined':
        plot(localMag, label=myLabel, ls=':', lw=4)
    else:
        plot(localMag, label=myLabel)
    legend()
#        show()
    return 'ok'
def ShowPlot():
    show()
    return 'ok'
        
def UpdateSong( iSong, iState, iMilli ):
        # iSong is 0 to 3
        # iState is 0 for silence, 1 for sound
        
        if iState==1:   
                # sound heard
                if mySongs[len(mySongs)-1][iSong][0]==0:
                        # song not started yet, start song
                        mySongs[len(mySongs)-1][iSong][0]=iMilli
                        mySongState[iSong]=1
                elif mySongState[iSong]==1:
                        # sound pulse continues
                        mySongs[len(mySongs)-1][iSong][len(mySongs[len(mySongs)-1][iSong])-1]+=iMilli
                elif mySongState[iSong]==0:
                        # sound pulse ends, silence begins
                        mySongState[iSong]=1
                        mySongs[len(mySongs)-1][iSong].append(iMilli)
        elif iState==0:
                if mySongs[len(mySongs)-1][iSong][0]==0:
                        # song not started yet, do nothing
                        mySongs[len(mySongs)-1][iSong][0]==0
                elif mySongState[iSong]==1:
                        # sound pulse ends
                        mySongState[iSong]=0
                        mySongs[len(mySongs)-1][iSong].append(iMilli)
                elif mySongState[iSong]==0:
                        #silence continues
                        mySongs[len(mySongs)-1][iSong][len(mySongs[len(mySongs)-1][iSong])-1]+=iMilli
                
def PrintSongs():
        for iLoop1 in range(0, 4):
                print "Accent",  iLoop1
                for iLoop2 in range(len(mySongs)):                      
                        print mySongs[iLoop2][iLoop1]
                        
def UpdateHeardFiles():
        for iLoop1 in range(0, 4):
                s=""
                print SongCount, iLoop1, 
                for iLoop2 in range(len(mySongs[SongCount][iLoop1])):
                        print iLoop2, 
                        s += str(mySongs[SongCount][iLoop1][iLoop2]) + ","
                        print mySongs[SongCount][iLoop1][iLoop2], 
                print
                s += "\n"
                fSongsHeard[iLoop1].write(s)
                
                
mySamples = zeros(64)
myBigSamples = zeros(50000)
myBigSamplePos=0
myFFT = zeros(64)
myFFTAbs = zeros(16)
mySongs = [[[0], [0], [0], [0]]]
mySongState = [0, 0, 0, 0]
myBins = [8, 10, 12, 14]
SingingStarted=False
SilenceTime=0
SongOver=False
SilCount=0
SongCount=0
FreqFileName = "res/freqs" + str(SongCount) + ".csv"
SamplesFileName = "res/samples" + str(SongCount) + ".csv"
fFreqs = open(FreqFileName, 'w')
fSamples = open(SamplesFileName, 'w')
fSongsHeard = []
fSongsHeard.append(open('res/heard0.csv', 'w'))
fSongsHeard.append(open('res/heard1.csv', 'w'))
fSongsHeard.append(open('res/heard2.csv', 'w'))
fSongsHeard.append(open('res/heard3.csv', 'w'))



# Setup audio capture using pyAlsaaudio. Sampling rate set to same as epuck (I hope!)
# period size set to capture 64 samples
inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,alsaaudio.PCM_NONBLOCK)
inp.setchannels(1)
inp.setrate(16500)
inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
inp.setperiodsize((64*16))

time_before = datetime.datetime.now()
left_over=0

while not SongOver:
        try:
                # Read data from device
                l,data = inp.read()
                
                if l>0:
                        mySamples = zeros(64)
                        myFFT = zeros(64)
                        myFFTAbs = zeros(16)

                        # copy the samples 
                        for iLoop in range(0, 64):
                                mySamples[iLoop]=audioop.getsample(data, 2, iLoop)
                                myBigSamples[myBigSamplePos]=mySamples[iLoop]
                                myBigSamplePos += 1
                        
                        # perform fft
                        myFFT=fft(mySamples)
                        
                        s = ""
                        for iLoop in range(0,64):  
                                s += str(mySamples[iLoop])  + ","
                        #s += "\n"
                        fSamples.write(s)
                        
                        for iLoop in range(0, 16):
                                myFFTAbs[iLoop]= abs(myFFT[iLoop])
                        
                        time.sleep(.0007)
                        time_after = datetime.datetime.now()
                        time_between = time_after-time_before
                        time_in_milli = time_between.microseconds/1000
                                
                        #left_over += (time_after.microsecond - time_before.microsecond) - (((time_after.microsecond - time_before.microsecond)/1000)*1000)             
                        if left_over>=1000:
                                time_in_milli+=1
                                left_over=0
                        time_before = time_after
                        SilCount=0
                        
                        s = str(time_in_milli)  + ","
                        #for iLoop in range(len(myBins)):       
                        #       s += str(myFFTAbs[myBins[iLoop]])  + ","
                        for iLoop in range(0,16):  
                                s += str(myFFTAbs[iLoop])  + ","
                        s += "\n"
                        fFreqs.write(s)
                        
                        for iLoop in range(len(myBins)):                        
                                if myFFTAbs[myBins[iLoop]]>=100000:                             
                                        #sound heard
                                        UpdateSong(iLoop, 1,time_in_milli)
                                        SingingStarted=True
                                        SilenceTime=0
                                elif myFFTAbs[myBins[iLoop]]<100000:                            
                                        #no sound
                                        UpdateSong(iLoop, 0, time_in_milli)
                                        SilCount += 1
                        
                        if SilCount==4 and SingingStarted:
                                SilenceTime += time_in_milli
                        if SilenceTime > 2000 and SingingStarted:       
                                SingingStarted=False
                                SilenceTime=0
                                fFreqs.close()
                                fSamples.close()
                                for iLoop in range(0, 4):
                                        if mySongs[len(mySongs)-1][iLoop][0]>0:                         
                                                mySongs[len(mySongs)-1][iLoop].pop(-1)
                                                
                                UpdateHeardFiles()
                                SongCount += 1                  
                                FreqFileName = "res/freqs" + str(SongCount) + ".csv"
                                fFreqs = open(FreqFileName, 'w')
                                SamplesFileName = "res/samples" + str(SongCount) + ".csv"
                                fSamples = open(SamplesFileName, 'w')
                                mySongs.append([[0], [0], [0], [0]])

        except KeyboardInterrupt:
                SongOver=True


mySamplesForFFT = zeros(8192)
myBigFFT = zeros(8192)
for iLoop in range(0, 8192):
        mySamplesForFFT[iLoop]=myBigSamples[iLoop]
myBigFFT = fft(mySamplesForFFT)

PlotSignal(mySamplesForFFT, "samples", 0)
PlotFreq(myBigFFT, "fft", 1)

show()
#PrintSongs()
fSongsHeard[0].close();
fSongsHeard[1].close();
fSongsHeard[2].close();
fSongsHeard[3].close();
