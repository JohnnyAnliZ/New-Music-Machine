from cmu_graphics import *
import math         
import wave
import numpy as np
import numpy
import winsound
from scipy.io.wavfile import read
from scipy.io.wavfile import write
import csv 

class UserPreset:
    def __init__(self,number,app):
        self.number = number
        self.slotList=None
        self.startingPointList=[0 for _ in range(len(app.sampleList))]
        self.lengthList = [100 for _ in range(len(app.sampleList))]
        self.volumeList = [0 for _ in range(len(app.sampleList))]
        self.attackList = [0 for _ in range(len(app.sampleList))]
        self.decayList = [100 for _ in range(len(app.sampleList))]
        self.speedList=[100 for _ in range(len(app.sampleList))]
        self.lowPassList=[20000 for _ in range(len(app.sampleList))]
        self.loopList = [0 for _ in range(len(app.sampleList))]
    def __repr__(self):
        return f"UserPreset{self.number}"
    def __hash__(self):
        return hash(str(self))
    def saveTo(self,app):
        #saving the current slot information as sample ids in a list
        self.slotList = [sampleSetToNumIdSet(app.slotList[i].sampleSet) for i in range(len(app.slotList))]
        for i in range(len(app.sampleList)):
            self.startingPointList[i]=app.sampleList[i].glbStartingPoint
            self.lengthList[i]=app.sampleList[i].glbLength
            self.volumeList[i] = app.sampleList[i].glbVolume
            self.attackList[i] = app.sampleList[i].glbAttack
            self.decayList[i] = app.sampleList[i].glbDecay
            self.speedList[i]=app.sampleList[i].glbSpeed
            self.lowPassList[i]= app.sampleList[i].glbLowPass
            self.loopList[i]= app.sampleList[i].glbLoop
        userPresetsFields = ["num"]+["slotList"]
        app.userPresets=[[u.number]+[u.slotList] for u in app.presetsList]
        userPresetsRows = app.userPresets
        parametersFields = ["sample"]+[k.name for k in app.knobList]
        parametersRows = [[s.id]+[s.glbStartingPoint,s.glbLength,
                                  s.glbVolume,s.glbLowPass,
                                  s.glbAttack,s.glbDecay,
                                  s.glbSpeed,s.glbLoop] for s in app.sampleList]
        with open("userPresets.csv","w") as f:
            write = csv.writer(f)

            write.writerow(userPresetsFields)
            write.writerows(userPresetsRows)
        with open(f"parameters slot{self.number}.csv","w") as f:
            write = csv.writer(f)

            write.writerow(parametersFields)
            write.writerows(parametersRows) 

    def getColor(self):
        if self.slotList == None:
            return "pink"
        else:
            return "beige"
        ###TO do 
    def export(self,app,repititions):
        pass

class Sample:
    def __init__(self,id,url):
        self.id = id
        self.url = url
        self.urlList = [url for i in range(16)]
        self.glbStartingPoint = 0
        self.glbLength = 100
        self.glbVolume = 0
        self.glbLowPass = 20000
        self.glbDecay = 1000
        self.glbAttack=0
        self.glbSpeed= 100
        self.glbLoop=0
        self.glbUrl=url
    def __repr__(self):
        return f"Sample {self.id}"
    def __hash__(self):
        return hash(str(self))
    def __eq__(self, other):
        return self.id == other.id 
    def globalListenAndRender(self):
        wf=wave.open(self.url,mode="rb")
        frames =wf.getnframes()
        audio = wf.readframes(frames)
        audio_as_np_int16=numpy.frombuffer(audio,dtype =numpy.int16)
        #Signal processing chain
        choppedArray = choppingSample(audio_as_np_int16,
                       self.glbStartingPoint,
                       self.glbLength)
        stretchedArray = pitch(choppedArray,self.glbSpeed)
        filteredArray = lowPassFilter(stretchedArray,self.glbLowPass)
        loopedArray = loop(filteredArray, self.glbLoop)
        envelopedArray = envelope(loopedArray,self.glbAttack,self.glbDecay)
        finalArray = volumeControl(envelopedArray,self.glbVolume)
        newUrl = f"{self.url}(Processed).wav"
        write(newUrl,44100,finalArray)
        self.urlList = [newUrl for i in range(16)]
        self.glbUrl = newUrl
        winsound.PlaySound(None,0)
        winsound.PlaySound(newUrl,winsound.SND_ASYNC)

class Slot:
    def __init__(self,sequenceNumber,sampleSet):
        self.sequenceNumber= sequenceNumber 
        self.sampleSet=sampleSet
    def __repr__(self):
        return (f"slot {self.sequenceNumber}") 
    def __hash__(self):
        return hash(str(self))
    def __eq__(self, other):
        return (type(self)==type(other)) and (
            self.sequenceNumber == other.sequenceNumber)
    def addSample(self,other):
        if isinstance(other,Sample):
            self.sampleSet.add(other)
    def addSampleById(self,app,id):
        if isinstance(id,int):
            self.sampleSet.add(app.sampleList[id-1])
    def removeSample(self,other):
        if isinstance(other,Sample):
            self.sampleSet.remove(other)
    def clearSamplesOnSlot(self):
        self.sampleSet = set()

class Knob:

    def __init__(self,cx,cy,parameterValue,name,unit):
        self.cx =cx
        self.cy=cy
        self.parameterValue=parameterValue
        self.name=name
        self.unit = unit
    def __repr__(self):
        return self.name
    def __eq__(self,other):
        if isinstance(other,Knob):
            return self.name == other.name
        else:
            return False
    def __hash__(self):
        return hash(str(self))
    def draw(self,app):
        cx=self.cx
        cy=self.cy
        drawCircle(cx,cy,app.width/35,fill='orange',opacity = 70)
        drawLabel(self.name,cx,cy-app.height*0.08,size = 10,fill ='brown')
        drawLabel(f"{self.parameterValue}{self.unit}",cx,cy)

#MVC
def onAppStart(app):
    restartApp(app)

def restartApp(app):
    #default settings
        #overlap or not 
    app.mutedSamplesSet = set()
    app.overlap = False
        #bpm stuff
    app.bpmKnobAdjusting = False
    app.bpm = 90    
    app.stepsPerSecond =6
    #stock samples, all the audio samples below are created by me 
    url1 = "DRUM SAMPLE.wav"
    url2 = "halved.wav"  
    url3 = "hi hat sample.wav"
    url4 = "kick sample.wav"
    url5 = "acoustic Guitar Sample.wav"
    url6 = "toms Sample.wav"
    url7 = "PureHihat.wav"
    url8 = "guitarFeedBack.wav"
    app.sampleList=[Sample(1,url1),Sample(2,url2),Sample(3,url3),Sample(4,url4),
                    Sample(5,url5),Sample(6,url6),Sample(7,url7),Sample(8,url8)]
    app.presetsList=[UserPreset(i,app) for i in range(1,17)]
    app.slotList = [Slot(i+1,set()) for i in range(16)]
    app.currentSample = app.sampleList[0]
    app.currentSampleIndex = 0
    app.positionList=[i for i in range(16)]
    app.currentIndex = 0
    app.leftover = np.zeros(1,dtype = numpy.int16)
    #knobList   
    app.knobList = ([Knob(800*0.6,app.height*0.4,
        app.currentSample.glbStartingPoint,"StartingPoint","ms"),
                    Knob(800*0.68,app.height*0.40,
         app.currentSample.glbLength,"Length","%"),
                    Knob(800*0.76,app.height*0.4,
        app.currentSample.glbVolume,"Volume","dB"),
                    Knob(800*0.76,app.height*0.65,
        app.currentSample.glbLowPass,"Hi-cut","Hz"),
                    Knob(800*0.84,app.height*0.4,
        app.currentSample.glbAttack,"Attack","dB"),
                    Knob(800*0.92,app.height*0.4,
        app.currentSample.glbDecay,"Decay","ms"),
                    Knob(800*0.6,app.height*0.65,
        app.currentSample.glbSpeed,"Speed","%"),
                    Knob(800*0.92,app.height*0.65,
        app.currentSample.glbLoop,"Loop","times") ])
    app.currentKnobAdjusted = None
    app.currentKnobPositionAnchor = None
    app.currentKnobValueAnchor = None
    #write default parameter csv files

    # parametersFields = ["sample"]+[k.name for k in app.knobList]
    # parametersRows = [[s.id]+[s.glbStartingPoint,s.glbLength,
    #                         s.glbVolume,s.glbLowPass,
    #                         s.glbAttack,s.glbDecay,
    #                         s.glbSpeed,s.glbLoop] for s in app.sampleList]
    # for i in range(1,17):
    #     with open(f"parameters slot{i}.csv","w") as f:
    #             write = csv.writer(f)

    #             write.writerow(parametersFields)
    #             write.writerows(parametersRows) 


    # Update presets based on csv files in the folder

    with open("userPresets.csv",mode = "r") as file:
        csvTable = csv.reader(file)
        for line in csvTable:
            currentSlotNum = "notDigit"
            if line!=[]:
                currentSlotNum =line[0] 
                currentListStr=line[1].replace("set()","{}")
                currentList=[]
                for member in currentListStr[2:-2].split("}, {"):
                    if member == "":
                        currentList.append(set())
                    else:
                        numSet=set()
                        for num in member.split(", "):
                            if num.isdigit():
                                numSet.add(int(num))
                        currentList.append(numSet)
                if currentSlotNum.isdigit() and currentList != "":
                    currentSlotNum=int(currentSlotNum)
                    app.presetsList[currentSlotNum-1].slotList=currentList
            if isinstance(currentSlotNum,int):
                with open(f"parameters slot{currentSlotNum}.csv",mode = "r") as file:
                    paramTable = csv.reader(file)
                    spList=[]
                    lList=[]
                    vlmList=[]
                    lpssList = []
                    dcList = []
                    atckList = []
                    spdList = []
                    lpList = []
                    for line in paramTable:
                        if line !=[] and line[1]!="StartingPoint" and line[1]!="":
                            spList.append(int(line[1]))
                            lList.append(int(line[2]))
                            vlmList.append(float(line[3]))
                            lpssList.append(int(line[4]))
                            atckList.append(float(line[5]))
                            dcList.append(int(line[6]))
                            spdList.append(int(line[7]))
                            lpList.append(int(line[8]))

                    app.presetsList[currentSlotNum-1].startingPointList = spList
                    app.presetsList[currentSlotNum-1].lengthList = lList
                    app.presetsList[currentSlotNum-1].volumeList = vlmList
                    app.presetsList[currentSlotNum-1].lowPassList = lpssList
                    app.presetsList[currentSlotNum-1].decayList = dcList
                    app.presetsList[currentSlotNum-1].attackList= atckList
                    app.presetsList[currentSlotNum-1].speedList= spdList
                    app.presetsList[currentSlotNum-1].loopList= lpList
                    
                    
    #Userpreset 2d list
    app.userPresets=[[u.number]+[u.slotList] for u in app.presetsList]
    #app width and height, knobs position
    app.width =800
    app.length = 400
    app.bpmKnobX = 400
    app.bpmKnobY = 200
    app.flashingColor = "gold"
    app.flashingColorToggle = False
        #playback stuff
    app.currentPos = 0
    app.mode = "edit"
    # audio editting parameters 
    #TO DO
    app.lengthParameterList= None

def onKeyPress(app, key):
    #toggle mode
    if key == "space":
        if app.mode == "edit":
            app.mode = "live"
        elif app.mode == "live" or app.mode == "step":
            app.mode ="edit"
            app.currentPos = 0
            app.currentIndex = 0
            app.leftover = np.zeros(1,dtype=numpy.int16)
    #toggle overlap
    if key == "o":
        app.overlap = not app.overlap

    # live mode adjusting slot playback
    keyDict={"1":0,"2":1,"3":2,"4":3,"5":4,"6":5,"7":6,"8":7,
             "q":8,"w":9,"e":10,"r":11,"t":12,"y":13,"u":14,"i":15}

    if key in keyDict:
        if app.mode == "live" or app.mode =="edit":
            slotSampleToggle(app, keyDict[key])
        elif app.mode =="step":
            positionListToggle(app,keyDict[key])


    #step mode adjusting ryhthm


    # edit mode 
        # adding sound file on slot
        # changing the sample you want to edit
    if key == "down":
        if app.currentSampleIndex ==len(app.sampleList)-1:
            app.currentSampleIndex = 0
        else:
            app.currentSampleIndex += 1
        app.currentSample = app.sampleList[app.currentSampleIndex]
        app.knobList[0].parameterValue = app.currentSample.glbStartingPoint
        app.knobList[1].parameterValue = app.currentSample.glbLength
        app.knobList[2].parameterValue = app.currentSample.glbVolume
        app.knobList[3].parameterValue = app.currentSample.glbLowPass
        app.knobList[4].parameterValue = app.currentSample.glbAttack
        app.knobList[5].parameterValue = app.currentSample.glbDecay
        app.knobList[6].parameterValue = app.currentSample.glbSpeed
        app.knobList[7].parameterValue = app.currentSample.glbLoop

    if key == "up":
        if app.currentSampleIndex ==0:
            app.currentSampleIndex = len(app.sampleList)-1
        else:
            app.currentSampleIndex -= 1
        app.currentSample = app.sampleList[app.currentSampleIndex]
        app.knobList[0].parameterValue = app.currentSample.glbStartingPoint
        app.knobList[1].parameterValue = app.currentSample.glbLength
        app.knobList[2].parameterValue = app.currentSample.glbVolume
        app.knobList[3].parameterValue = app.currentSample.glbLowPass
        app.knobList[4].parameterValue = app.currentSample.glbAttack
        app.knobList[5].parameterValue = app.currentSample.glbDecay
        app.knobList[6].parameterValue = app.currentSample.glbSpeed
        app.knobList[7].parameterValue = app.currentSample.glbLoop

    if key == "s":
        if app.mode == "edit":
            app.mode = "presetSelectionSave"
        elif app.mode == "presetSelectionSave":
            app.mode = "edit"
        if app.mode =="live":
            app.mode = "step"
        elif app.mode =="step":
            app.mode = "live"
    if key == "l":
        if app.mode == "edit": 
            app.mode = "presetSelectionLoad"
        elif app.mode == "presetSelectionLoad":
            app.mode = "edit"
        
def onMousePress(app, mouseX,mouseY):
    #bpm adjustment
    if app.mode =="edit" or app.mode == "live" or app.mode == "step":
        if distance(mouseX,mouseY,app.bpmKnobX,app.bpmKnobY)<30:
            app.bpmKnobAdjusting = True
            app.bpmKnobAnchor = mouseY
            app.bpmAnchor =app.bpm
    #putting samples on slots
    if app.mode =="edit" or app.mode == "live":
        clickedSlot=getIndexSlotClicked(mouseX)
        if clickedSlot != None and 320<mouseY<360:
            slotSampleToggle(app, clickedSlot)
        # adjusting sample editting knobs
        clickedKnobIndex= getIndexKnobClicked(app,mouseX,mouseY)
        if clickedKnobIndex != None:
            app.currentKnobAdjusted = clickedKnobIndex
            app.currentKnobPositionAnchor = mouseY
            app.currentKnobValueAnchor = app.knobList[clickedKnobIndex].parameterValue
    if app.mode == "presetSelectionSave":
        presetNumClicked = getPresetClicked(app,mouseX,mouseY)
        if presetNumClicked != None:
            app.presetsList[presetNumClicked-1].saveTo(app)
            app.mode="edit"
    if app.mode == "presetSelectionLoad":
        presetNumClicked = getPresetClicked(app,mouseX,mouseY)
        if presetNumClicked != None:
            presetClicked=app.presetsList[presetNumClicked-1]
            if presetClicked.slotList != None:
                for i in range(len(app.slotList)):
                    app.slotList[i].clearSamplesOnSlot()
                    for item in presetClicked.slotList[i]:
                        app.slotList[i].addSampleById(app,item)
                for i in range(len(app.sampleList)):
                    app.sampleList[i].glbStartingPoint=presetClicked.startingPointList[i]
                    app.sampleList[i].glbLength=presetClicked.lengthList[i]
                    app.sampleList[i].glbVolume=presetClicked.volumeList[i]
                    app.sampleList[i].glbLowPass=presetClicked.lowPassList[i]
                    app.sampleList[i].glbAttack=presetClicked.attackList[i]
                    app.sampleList[i].glbDecay=presetClicked.decayList[i]
                    app.sampleList[i].glbSpeed=presetClicked.speedList[i]
                    app.sampleList[i].glbLoop=presetClicked.loopList[i]
                for currentSample in range(len(app.sampleList)):
                    currentSample = app.sampleList[app.currentSampleIndex]
                    app.knobList[0].parameterValue = currentSample.glbStartingPoint
                    app.knobList[1].parameterValue = currentSample.glbLength
                    app.knobList[2].parameterValue = currentSample.glbVolume
                    app.knobList[3].parameterValue = currentSample.glbLowPass
                    app.knobList[4].parameterValue = currentSample.glbAttack
                    app.knobList[5].parameterValue = currentSample.glbDecay
                    app.knobList[6].parameterValue = currentSample.glbSpeed
                    app.knobList[7].parameterValue = currentSample.glbLoop
            for sample in app.sampleList:   
                sample.globalListenAndRender()
            app.mode="edit"
    # mute and unmute samples
    for i in range(1,len(app.sampleList)+1):
        centerY=i*app.height/12+app.height/15
        centerX=app.width/10
        mutedIndexSet = {sample.id for sample in app.mutedSamplesSet}
        if centerX-app.width/80<mouseX<centerX+app.width/80 and (
            centerY-app.height/40<mouseY<centerY+app.height/40):

            if i in mutedIndexSet:

                app.mutedSamplesSet.remove(app.sampleList[i-1])
            else:
                app.mutedSamplesSet.add(app.sampleList[i-1])
            
def onMouseDrag(app, mouseX, mouseY):
    if app.bpmKnobAdjusting:
        if app.bpm>30 or mouseY<app.bpmKnobAnchor:
            app.bpm = app.bpmAnchor+(app.bpmKnobAnchor-mouseY)/2
        else:
            app.bpm = 30
        app.stepsPerSecond =app.bpm/15
    #0 is the index for STARTING POINT knob
    elif app.currentKnobAdjusted == 0: 
        knob = app.knobList[0]
        wf = wave.open(app.sampleList[app.currentSampleIndex].url, mode = "rb")
        frames = wf.getnframes()
        upperBound = int(frames/44.1)
        lowerBound = 0
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #1 knob control for Length knob (1-100%)
    elif app.currentKnobAdjusted == 1: 
        knob = app.knobList[1]
        upperBound = 100
        lowerBound = 1
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #2 knob control for volume (-30dB to 6dB)
    elif app.currentKnobAdjusted == 2:
        knob = app.knobList[2]
        upperBound = 6
        lowerBound = -30
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=rounded((app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)/10)*10)/10
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #3 knob control for Hi-cut (20 to 20000 Hz)
    elif app.currentKnobAdjusted == 3:
        knob = app.knobList[3]
        upperBound = 20000
        lowerBound = 20
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)*20
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #4 knob control for Envelope attack (0 to 8 db)
    elif app.currentKnobAdjusted == 4:
        knob = app.knobList[4]
        upperBound = 8
        lowerBound = 0
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=rounded((app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)/10)*10)/10
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #5 knob control for Envelope decay (1000 to 0 ms)
    elif app.currentKnobAdjusted == 5: 
        knob = app.knobList[5]
        upperBound = 1000
        lowerBound = 0
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)*10
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #6 knob control for Envelope speed (1000 to 30 percent)
    elif app.currentKnobAdjusted == 6: 
        knob = app.knobList[6]
        upperBound = 1000
        lowerBound = 30
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound
    #7 knob control for Envelope attack (0 to 100 db)
    elif app.currentKnobAdjusted == 7:
        knob = app.knobList[7]
        upperBound = 100
        lowerBound = 0
        if (knob.parameterValue>lowerBound or app.currentKnobPositionAnchor>mouseY)  and (
            knob.parameterValue<upperBound or app.currentKnobPositionAnchor<mouseY):
            knob.parameterValue=app.currentKnobValueAnchor+(
                app.currentKnobPositionAnchor-mouseY)
        elif knob.parameterValue<lowerBound:
            knob.parameterValue = lowerBound
        elif knob.parameterValue>upperBound:
            knob.parameterValue = upperBound

def onMouseRelease(app,mouseX,mouseY):
    if app.bpmKnobAdjusting:
        app.bpmKnobAdjusting = False
    ###
    ### On mouse release, processed audio file is audited and rendered
    ###
    #0 is the index for STARTING POINT knob
    if app.currentKnobAdjusted == 0:
        knob = app.knobList[0]
        #Update the sample's gloabal starting point parameter
        app.currentSample.glbStartingPoint = knob.parameterValue

    #1 is the index for Length knob
    elif app.currentKnobAdjusted == 1:
        knob = app.knobList[1]
        app.currentSample.glbLength = knob.parameterValue

    elif app.currentKnobAdjusted == 2:
        knob = app.knobList[2]
        app.currentSample.glbVolume = knob.parameterValue
    elif app.currentKnobAdjusted == 3:
        knob = app.knobList[3]
        app.currentSample.glbLowPass = knob.parameterValue
    elif app.currentKnobAdjusted == 4:
        knob = app.knobList[4]
        app.currentSample.glbAttack = knob.parameterValue
    elif app.currentKnobAdjusted == 5:
        knob = app.knobList[5]
        app.currentSample.glbDecay = knob.parameterValue
    elif app.currentKnobAdjusted == 6:
        knob = app.knobList[6]
        app.currentSample.glbSpeed = knob.parameterValue
    elif app.currentKnobAdjusted == 7:
        knob = app.knobList[7]
        app.currentSample.glbLoop = knob.parameterValue     
    #Write in the new audio files and give user a listen
    if not app.bpmKnobAdjusting:
        app.currentSample.globalListenAndRender()
    app.currentKnobAdjusted = None
    app.currentKnobPositionAnchor = None
    app.currentKnobValueAnchor = None    

def onStep(app):
    if app.mode == "live" or app.mode == "step":
        #play the sounds on the slot
            #sum up all the samples on the spot
        sampleSet =app.slotList[app.currentPos].sampleSet - app.mutedSamplesSet
        currAudio=arraysSum(app,sampleSet)
        leftOverAudio = app.leftover
        lenLeftover = len(leftOverAudio)
        lenCurr =len(currAudio)
        lenStep = int(44100/app.stepsPerSecond) 
        

        
        if app.overlap: 
            summedAudio = sumTwoArrays(app.leftover,currAudio)
            if  sampleSet == set():
                app.leftover = leftOverAudio[lenStep:]
                finalAudio = leftOverAudio 
            #only curr go over
            if lenCurr > lenStep and lenLeftover <= lenStep:
                app.leftover = currAudio[lenStep:]
            #neither go over
            elif lenCurr<lenStep and lenLeftover<=lenStep:
                app.leftover = np.zeros(1,dtype = numpy.int16)
            #both go over
            elif lenLeftover > lenStep and lenCurr > lenStep:
                app.leftover = sumTwoArrays(currAudio[lenStep:],leftOverAudio[lenStep:])
            #only leftover go over
            elif lenCurr<=lenStep and lenLeftover>lenStep:
                app.leftover = leftOverAudio[lenStep:]
            finalAudio = summedAudio[:lenStep ]
         
        else:
            finalAudio = currAudio
        
        if (lenCurr!=1 and not app.overlap) or app.overlap:
            write(f"slot{app.currentPos+1}",44100,finalAudio)
            winsound.PlaySound(None,0)
            winsound.PlaySound(f"slot{app.currentPos+1}",winsound.SND_ASYNC)
        #moving to the next slot
        
        app.currentIndex +=1
        if app.currentIndex >= len(app.positionList):
            app.currentIndex = 0
        app.currentPos = app.positionList[app.currentIndex]
    elif app.mode == "edit":
        app.flashingColorToggle = not app.flashingColorToggle
        app.flashingColor = "gold" if app.flashingColorToggle else 'mediumSlateBlue'

def redrawAll(app):
    #background
    drawRect(0,0,app.width,app.height,fill="ivory") 
    #credits
    drawLabel("Inspired by the KORG volca sample",app.width/6,app.height/20,fill="grey",size =15,italic=True)
    #Title
    drawLabel("New",app.width/4,app.height/4,size=50,
              bold = True, italic = True,opacity = 70,
              fill = "orange")
    drawLabel("Music",app.width/3.8,app.height/2.4,size=50,
              bold = True, italic = True,opacity = 80,
              fill = "orange")
    drawLabel("Machine",app.width/3.5,app.height/1.7,size=50,
              bold = True, italic = True,opacity = 100,
              fill = "orange")
    #bpm knob
    drawCircle(app.bpmKnobX,app.bpmKnobY,30,fill = "coral")
    drawLabel(f"bpm:{app.bpm}",app.bpmKnobX,app.bpmKnobY)
    #overlap mode display
    if app.overlap:
        drawLabel(f"Overlap:ON",app.width/2,app.height*2/3,size=15,fill="greenYellow",bold=True)
    else:
        drawLabel(f"Overlap:OFF",app.width/2,app.height*2/3,size=15,fill="tomato",bold=True)
    #slots
    for seq in range(16):
        drawRect(10+seq*50, 320, 30,40,border = "darkSeaGreen",fill = None)
        drawLabel(f"{seq+1}",25+seq*50, 340)
    drawLabel("Use '1 2 3 4 5 6 7 8 q w e r t y u i' for faster control",
              app.width/5,app.height*19/20,fill="orangeRed")
    #save to preset
    drawLabel("Press S/L", 
              app.width-app.width/7,app.height/8,size = 20,fill="orangeRed")
    drawLabel("to save/load current loop to presets", 
              app.width-app.width/7,app.height/6,fill="orangeRed")
    # overlap toggle instruction
    drawLabel("Press O", 
              app.width-app.width/2.8,app.height/8,size = 20,fill="orangeRed")
    drawLabel("to toggle overlap ON/OFF", 
              app.width-app.width/2.8,app.height/6,fill="orangeRed")
    #live mode
    
    if app.mode == "live" or app.mode == "step":
        #playback indicator
        drawRect(10+app.currentPos*50,320,30,40,fill = "orangeRed")
        #samples being played display
        for sample in app.slotList[app.currentPos].sampleSet:
            drawRect(app.width/20,
                    sample.id*app.height/12+app.height/14,
                    app.width/15,
                  app.height/20,fill = "orange",opacity = 50,align = "center")
    
    #step mode indicator
    if app.mode == "step":
        for i in app.positionList:
            drawRect(10+i*50,350,30,10,fill = "orangeRed")

    #mode display
    if app.mode == "edit":
        drawLabel("Edit", app.width/2,app.height/3, fill = 'greenYellow',bold = True,size = 20)
    elif app.mode == "live" or app.mode == "step":
        drawLabel("LIVE", app.width/2,app.height/3, fill = 'tomato',bold = True,size = 20)

    #samples display
    #edit mode 
        # curr sample slots indicator
    if app.mode == "live" or app.mode =="edit":
        for slotIndex in range(len(app.slotList)):
            if app.currentSample in app.slotList[slotIndex].sampleSet:
                drawCircle(25+slotIndex*50,320,5,fill = "orange") 
                drawRect(25+slotIndex*50,340,30,40,border = "orange",fill=None,align="center")
                
    for sampleNumber in range(1,9):
            # curr sample edited indicator
            if sampleNumber == app.currentSample.id:
                drawLabel(f"sample{sampleNumber}",
                    app.width/20,
                    sampleNumber*app.height/12+app.height/15,size=13,
                    fill = app.flashingColor)
                    
            else:
                drawLabel(f"sample{sampleNumber}",
                        app.width/20,
                        sampleNumber*app.height/12+app.height/15,size=13,
                        fill = "green")
            mutedIndexSet = {sample.id for sample in app.mutedSamplesSet} 
            if sampleNumber in mutedIndexSet:
                drawRect(app.width/10,
                    sampleNumber*app.height/12+app.height/15,
                    app.width/40,
                  app.height/20,fill = 'yellowGreen',opacity = 50,align = "center")
                drawLabel("M",app.width/10,
                    sampleNumber*app.height/12+app.height/15)
            else:
                drawRect(app.width/10,
                    sampleNumber*app.height/12+app.height/15,
                    app.width/40,
                  app.height/20,fill = 'greenYellow',align = "center")
                
    # editting knobs
    drawRect(app.width*5/9,app.height/4,app.width*0.42,app.height*1/2,
             fill = None, border="tomato")
        # drawing parameter categories
        #chopping
    drawLabel("Chop",app.width*0.59,app.height*0.28,size = 15,fill ='green')
        #dynamics
    drawLabel("Dynamics",app.width*0.78,app.height*0.28,size = 15,fill ='green')
        #pitch
    drawLabel("Pitch",app.width*0.59,app.height*0.52,size = 15,fill ='green')
        #filter
    drawLabel("Frequency",app.width*0.78,app.height*0.52,size = 15,fill ='green')
        #loop
    drawLabel("Loop",app.width*0.92,app.height*0.52,size = 15,fill ='green')
    for knob in app.knobList:
        knob.draw(app)


    #presetSelection draw a window on top
    if app.mode == "presetSelectionSave":
        drawRect(app.width/8,app.length/8,
                 app.width*6/8,app.length*6/8,
                 fill = 'khaki', border = 'seaGreen')
        drawLabel("Choose a memory slot to save to",
                  app.width/2,app.height/5,size=30,fill='seaGreen')
        for i in range(8):
            drawRect(app.width/8+app.width/16+i*app.width/12,
                     app.height/2,
                     app.width/40,app.height/20,
                     fill = app.presetsList[i].getColor())
            drawLabel(f"{i+1}",app.width/8+app.width/16+i*app.width/12+app.width/80,
                     app.height/2+app.height/40)
        for i in range(8):
            drawRect(app.width/8+app.width/16+i*app.width/12,
                     app.height*2/3,
                     app.width/40,app.length/20,
                     fill = app.presetsList[i+8].getColor())
            drawLabel(f"{i+9}",app.width/8+app.width/16+i*app.width/12+app.width/80,
                     app.height*2/3+app.height/40)

    if app.mode == "presetSelectionLoad":
        drawRect(app.width/8,app.length/8,
                 app.width*6/8,app.length*6/8,
                 fill = 'paleGreen', border = "orange")
        drawLabel("Choose a user preset to load",
                  app.width/2,app.height/5,size=30,fill ='orangeRed') 
        for i in range(8):
            drawRect(app.width/8+app.width/16+i*app.width/12,
                     app.height/2,
                     app.width/40,app.height/20,
                     fill = app.presetsList[i].getColor())
            drawLabel(f"{i+1}",app.width/8+app.width/16+i*app.width/12+app.width/80,
                     app.height/2+app.height/40)
        for i in range(8):
            drawRect(app.width/8+app.width/16+i*app.width/12,
                     app.height*2/3,
                     app.width/40,app.length/20,
                     fill = app.presetsList[i+8].getColor())
            drawLabel(f"{i+9}",app.width/8+app.width/16+i*app.width/12+app.width/80,
                     app.height*2/3+app.height/40)
       


#heplerFunctions:
def getIndexSlotClicked(x):
    if 10>x or x>790:
        return None
    elif (x-10)%50>30:
        return None
    else:
        return ((x-10) // 50)

def getPresetClicked(app,mouseX,mouseY):
    for i in range(8):
        if (app.width/8+app.width/16+i*app.width/12<
            mouseX<
            app.width/40+app.width/8+app.width/16+i*app.width/12) and (app.height/2
            <mouseY<app.height/2+app.height/20):
            return i+1
    for i in range(8,16):
        if (app.width/8+app.width/16+(i-8)*app.width/12<
            mouseX<
            app.width/40+app.width/8+app.width/16+(i-8)*app.width/12) and (app.height*2/3
            <mouseY< app.height*2/3 + app.height /20):
            return i+1
    
def slotSampleToggle(app, clickedSlot):
    if app.currentSample in app.slotList[clickedSlot].sampleSet:
        app.slotList[clickedSlot].removeSample(app.currentSample)
    elif app.currentSample not in app.slotList[clickedSlot].sampleSet:
        app.slotList[clickedSlot].addSample(app.currentSample)

def positionListToggle(app,num):
    if num in app.positionList and len(app.positionList)>1:
        app.positionList.remove(num)
    else:
        if num<app.positionList[-1]:
            for i in range(len(app.positionList)):
                if num<app.positionList[i]:
                    app.positionList.insert(i,num)
                    break
        else:
            app.positionList.append(num)
def distance(x1, y1, x2, y2):  
    return ((abs(x1-x2)) ** 2 + (abs(y1-y2)) ** 2)** 0.5

def arraysSum(app,samplesSet):
    sum=np.zeros(1,dtype=numpy.int16)
    if samplesSet == set():
        return sum

    for sample in samplesSet:

        wf=wave.open(sample.glbUrl,mode="rb")
        frames =wf.getnframes()
        audio = wf.readframes(frames)
        array =numpy.frombuffer(audio,dtype =numpy.int16)
        lenSum = len(sum)
        lenArray = len(array)
        if lenArray>lenSum:
            sum.resize(lenArray)
            sum  = sum +array
        else:
            newArray=np.append(array,np.zeros(lenSum-lenArray,dtype=numpy.int16))
            sum = sum +newArray
    return sum

def sumTwoArrays(a1,a2):
    len1=len(a1)
    len2=len(a2)
    if len1>len2:
        return numpy.resize(a2,len1)+a1
    else:
        return numpy.resize(a1,len2)+a2
        
def sampleSetToNumIdSet(sampleSet):
    result = set()
    for sample in sampleSet:
        result.add(sample.id)
    return result

def getIndexKnobClicked(app,mouseX,mouseY):
    for i in range(len(app.knobList)):
        knob = app.knobList[i]
        if distance(knob.cx,knob.cy,mouseX,mouseY)<23:
            return i
#audio processing functions
def choppingSample(array,startingPoint,lengthPercentage):
    startingPointInSamples= int(startingPoint*44100/1000)
    rest=array[startingPointInSamples:]
    lenRest=len(rest)
    return rest[:int(lenRest*lengthPercentage/100)]

def volumeControl(array,dB):
    newArray = array*(10**(dB/20))
    newArray =np.rint(newArray).astype(np.int16)
    return newArray

def lowPassFilter(array,f):#low pass filter using the moving average method
    #calculating the windowLength based on frequency
    # math based on https://dsp.stackexchange.com/questions/9966/what-is-the-cut-off-frequency-of-a-moving-average-filter/14648#14648
    sampleRate=44100
    normalizedF= f/sampleRate
    windowLength = int(math.sqrt(0.196202+normalizedF**2)/normalizedF)
    #performing moving average

        #efficient algorithm for moving average by StackOverflow user Alleo
        #https://stackoverflow.com/questions/13728392/moving-average-or-running-mean
    cumsum =numpy.cumsum(numpy.insert(array,0,0))
    filteredSignal = (cumsum[windowLength:]-cumsum[:-windowLength])/windowLength
    filteredSignal =np.rint(filteredSignal).astype(np.int16)
    return filteredSignal

def envelope(array,attackinDB,pointOfDecay):
    lenArray=len(array)
    
    lenArrayMs=int(lenArray/44100*1000)
    envArray= numpy.ones(lenArray,dtype=numpy.int16)
    #fixed attack at 5ms
    nAttack = 440
    nDecay= nAttack+rounded(44100*pointOfDecay/1000) if pointOfDecay<lenArrayMs else lenArray
    lenDecay = nDecay-nAttack
    lenEnd=lenArray-nDecay

    attackGain= 10**(attackinDB/20)
    if attackGain >1:
        rampUp=np.linspace(0,attackGain,nAttack)
        if len(envArray[:nAttack])==nAttack:
            envArray[:nAttack]=rampUp
    if pointOfDecay >0 and pointOfDecay<lenArrayMs:
        decayRamp = np.linspace(attackGain,1,lenDecay)  
        if len(envArray[nAttack:nDecay]) == lenDecay:
            envArray[nAttack:nDecay]= decayRamp
    if pointOfDecay >0 and pointOfDecay>=lenArrayMs:
        envArray[nDecay:]=np.full(lenEnd,0)
    resultArray = (envArray*array)[:nDecay]
    return resultArray

#interpolation method to stretch signal credits to Stack Exchange User Stefan B
#https://stackoverflow.com/questions/66934748/how-to-stretch-an-array-to-a-new-length-while-keeping-same-value-distribution
# using this method, the signal can be stretched not just by integer speed ratios
def interp1d(array, newLength):
    lenArray = len(array)
    
    if lenArray!= 0:
        newArray = np.interp(np.linspace(0, lenArray - 1, newLength), # x coordinates of new array
                    np.arange(lenArray),                      # x coordinates of the array
                    array)                                    # original array
        return newArray
    else:
        return array

def pitch(array,speed):
    lenArray= len(array)
    speed = speed/100
    newLength = int(lenArray/speed)
    newArray = interp1d(array,newLength)
    return newArray

def loop(array,nRepeats):
    result=array
    for i in range(nRepeats):
        result=np.append(result,array)
    return result

def main():
    runApp()

main() 

