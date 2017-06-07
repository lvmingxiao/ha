from ha import *
from ha.notify import *

# state values

pumpLo = 1
pumpMed = 2
pumpHi = 3
pumpMax = 4

spaOff = 0
spaOn = 1
spaStarting = 2
spaWarming = 3
spaStandby = 4
spaStopping = 5

seqStop = 0
seqStart = 1
seqStopped = 0
seqRunning = 1

valvePool = 0
valveSpa = 1
valveMoving = 4

class SpaControl(Control):
    def __init__(self, name, interface, valveControl, pumpControl, heaterControl, lightControl, tempSensor, addr=None, 
            group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
        self.currentState = spaOff
        self.valveControl = valveControl
        self.pumpControl = pumpControl
        self.heaterControl = heaterControl
        self.lightControl = lightControl
        self.tempSensor = tempSensor
        self.eventThread = None
        
        # state transition sequences
        self.startupSequence = Sequence("spaStartup", 
                             [Cycle(self.valveControl, duration=0, startState=valveSpa),
                              Cycle(self.pumpControl, duration=0, startState=pumpMed, delay=30),
                              Cycle(self.heaterControl, duration=0, startState=on, delay=30)
                              ])
        self.onSequence = Sequence("spaOn", 
                             [Cycle(self.pumpControl, duration=0, startState=pumpMax),
                              Cycle(self.lightControl, duration=0, startState=on),
                              ])
        self.standbySequence = Sequence("spaStandby", 
                             [Cycle(self.pumpControl, duration=0, startState=pumpMed),
                              Cycle(self.lightControl, duration=0, startState=off),
                              ])
        self.shutdownSequence = Sequence("spaShutdown", 
                             [Cycle(self.pumpControl, duration=0, startState=pumpMed),
                              Cycle(self.heaterControl, duration=0, startState=off),
                              Cycle(self.pumpControl, duration=0, startState=off, delay=60),
                              Cycle(self.valveControl, duration=0, startState=valvePool),
                              Cycle(self.lightControl, duration=0, startState=off, delay=30)
                              ])

    def getState(self):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    # Implements the state diagram
    def setState(self, state):
        debug('debugState', self.name, "setState ", state, self.currentState)
        if state == spaOff:
            if (self.currentState == spaOn) or (self.currentState == spaStandby) or (self.currentState == spaWarming):
                self.stateTransition(spaStopping)
            elif (self.currentState == spaStarting) or (self.currentState == spaStopping) or (self.currentState == spaOff):
                debug('debugState', self.name, "setState ", "pass", state, self.currentState)
            else:
                debug('debugState', self.name, "unknown state", state, self.currentState)
        elif state == spaOn:
            if self.currentState == spaOff:
                self.stateTransition(spaStarting, spaOn)
            elif (self.currentState == spaStandby):
                self.stateTransition(spaOn)
            elif (self.currentState == spaStarting) or (self.currentState == spaStopping) or (self.currentState == spaOn) or (self.currentState == spaWarming):
                debug('debugState', self.name, "setState ", "pass", state, self.currentState)
            else:
                debug('debugState', self.name, "unknown state", state, self.currentState)
        elif state == spaStandby:
            if self.currentState == spaOff:
                self.stateTransition(spaStarting, spaOn)
            elif (self.currentState == spaOn):
                self.stateTransition(spaStandby)
            elif (self.currentState == spaStarting) or (self.currentState == spaStopping) or (self.currentState == spaStandby) or (self.currentState == spaWarming):
                debug('debugState', self.name, "setState ", "pass", state, self.currentState)
            else:
                debug('debugState', self.name, "unknown state", state, self.currentState)
        else:
            log(self.name, "unknown state", state, self.currentState)

    # Implements state transitions
    def stateTransition(self, state, endState=None):
        debug('debugState', self.name, "stateTransition ", state, endState)
        if state == spaOn:
            self.onSequence.setState(seqStart, wait=True)
        elif state == spaStandby:
            self.standbySequence.setState(seqStart, wait=True)
        elif state == spaStarting:
            self.startupSequence.setState(seqStart, wait=False)
            self.startEventThread("spaStarting", self.startupSequence.getState, seqStopped, self.spaStarted, endState)
        elif state == spaStopping:
            self.shutdownSequence.setState(seqStart, wait=False)
            self.startEventThread("spaStopping", self.shutdownSequence.getState, seqStopped, self.stateTransition, spaOff)
        self.currentState = state

    # called when startup sequence is complete
    def spaStarted(self, endState):
        debug('debugState', self.name, "spaStarted ", endState)
        self.stateTransition(spaWarming)
        self.startEventThread("spaWarming", self.tempSensor.getState, spaTempTarget, self.spaReady, endState)

    # called when target temperature is reached        
    def spaReady(self, state):
        debug('debugState', self.name, "spaReady ", state)
        self.stateTransition(state)
        smsNotify(spaReadyNotifyNumbers, spaNotifyMsg)
        iosNotify(spaReadyNotifyApp, spaNotifyMsg)

    # start an event thread
    def startEventThread(self, name, checkFunction, checkValue, actionFunction, actionValue):
        if self.eventThread:
            self.eventThread.cancel()
            self.eventThread = None
        self.eventThread = SpaEventThread(name, checkFunction, checkValue, actionFunction, actionValue)
        self.eventThread.start()
            
# A thread to wait for the state of the specified sensor to reach the specified value
# then call the specified action function with the specified action value
class SpaEventThread(threading.Thread):
    def __init__(self, name, checkFunction, checkValue, actionFunction, actionValue):
        threading.Thread.__init__(self, target=self.asyncEvent)
        self.name = name
        self.checkFunction = checkFunction
        self.checkValue = checkValue
        self.actionFunction = actionFunction
        self.actionValue = actionValue
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        
    def asyncEvent(self):
        debug('debugThread', self.name, "started")
        while self.checkFunction() != self.checkValue:
            time.sleep(1)
            if self.cancelled:
                debug('debugThread', self.name, "cancelled")
                return
        self.actionFunction(self.actionValue)
        debug('debugThread', self.name, "finished")

# spa control whose state value includes the temperature
class SpaTempControl(Control):
    def __init__(self, name, interface, spaControl, tempSensor, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
        self.spaControl = spaControl
        self.tempSensor = tempSensor

    def getState(self):
        return "%d %d"%(self.tempSensor.getState(), self.spaControl.getState())

    def setState(self, state):
        self.spaControl.setState(state)
        
