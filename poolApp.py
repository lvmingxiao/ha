spaTempTargetDefault = 100
spaNotifyMsg = "Spa is ready"
notifyFromNumber = ""
spaReadyNotifyNumbers = []
spaReadyNotifyApp = ""

import threading
import time
import json
from ha import *
from ha.interfaces.serialInterface import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.pentairInterface import *
from ha.interfaces.powerInterface import *
from ha.interfaces.ads1015Interface import *
from ha.interfaces.analogTempInterface import *
from ha.interfaces.valveInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.timeInterface import *
from ha.controls.tempControl import *
from ha.controls.poolControls import *
from ha.rest.restServer import *

serialConfig = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    nullInterface = Interface("nullInterface", Interface("None"))
    serialInterface = SerialInterface("serialInterface", device=pentairDevice, config=serialConfig, event=stateChangeEvent)
    i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    gpioInterface0 = GPIOInterface("gpioInterface0", i2cInterface, addr=0x20, bank=0, inOut=0x00)
    gpioInterface1 = GPIOInterface("gpioInterface1", i2cInterface, addr=0x20, bank=1, inOut=0x00)
    pentairInterface = PentairInterface("pentairInterface", serialInterface)
    powerInterface = PowerInterface("powerInterface", Interface("None"), event=stateChangeEvent)
    ads1015Interface = ADS1015Interface("ads1015Interface", addr=0x48)
    analogTempInterface = AnalogTempInterface("analogTempInterface", ads1015Interface)
    valveInterface = ValveInterface("valveInterface", gpioInterface1)
    timeInterface = TimeInterface("timeInterface")
    configInterface = FileInterface("configInterface", fileName=stateDir+"pool.state", event=stateChangeEvent)
    
    # persistent config data
    spaTempTarget = Control("spaTempTarget", configInterface, "spaTempTarget", group="Pool", label="Spa temp set", type="tempFControl")
    
    # Lights
    poolLight = Control("poolLight", gpioInterface0, 2, type="light", group="Lights", label="Pool light")
    spaLight = Control("spaLight", gpioInterface0, 3, type="light", group="Lights", label="Spa light")
    poolLights = ControlGroup("poolLights", [poolLight, spaLight], type="light", group="Lights", label="Pool and spa")

    # Temperature
    waterTemp = Sensor("waterTemp", analogTempInterface, 0, "Temperature",label="Water temp", type="tempF")
    poolTemp = Sensor("poolTemp", analogTempInterface, 0, "Temperature",label="Pool temp", type="tempF")
    spaTemp = Sensor("spaTemp", analogTempInterface, 0, "Temperature",label="Spa temp", type="tempF")
    poolEquipTemp = Sensor("poolEquipTemp", analogTempInterface, 1, "Temperature",label="Pool equipment temp", type="tempF")

    # Pool
    poolPump = Control("poolPump", pentairInterface, 0, group="Pool", label="Pump", type="pump")
    poolCleaner = Control("poolCleaner", gpioInterface0, 0, group="Pool", label="Polaris", type="cleaner")
    intakeValve = Control("intakeValve", valveInterface, 0, group="Pool", label="Intake valve", type="poolValve")
    returnValve = Control("returnValve", valveInterface, 1, group="Pool", label="Return valve", type="poolValve")
    valveMode = ControlGroup("valveMode", [intakeValve, returnValve], stateList=[[0, 1, 1, 0], [0, 1, 0, 1]], stateMode=True, 
                             type="valveMode", group="Pool", label="Valve mode")
    spaFill = ControlGroup("spaFill", [intakeValve, returnValve, poolPump], stateList=[[0, 0], [0, 1], [0, 4]], stateMode=True, group="Pool", label="Spa fill")
    spaFlush = ControlGroup("spaFlush", [intakeValve, returnValve, poolPump], stateList=[[0, 0], [0, 1], [0, 3]], stateMode=True, group="Pool", label="Spa flush")
    spaDrain = ControlGroup("spaDrain", [intakeValve, returnValve, poolPump], stateList=[[0, 1], [0, 0], [0, 4]], stateMode=True, group="Pool", label="Spa drain")
    poolClean = ControlGroup("poolClean", [poolCleaner, poolPump], stateList=[[0, 1], [0, 3]], stateMode=True, group="Pool", label="Pool clean")
    poolHeater = Control("poolHeater", gpioInterface1, 2, group="Pool", label="Pool heater")
    heaterControl = TempControl("heaterControl", nullInterface, poolHeater, spaTemp, spaTempTarget, group="Pool", label="Heater control", type="tempControl")
    spaBlower = Control("spaBlower", gpioInterface0, 1, group="Pool", label="Blower")
    
    poolPumpSpeed = Sensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed")
    poolPumpFlow = Sensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow")

    # Spa
    sunUp = Sensor("sunUp", timeInterface, "sunUp")
    # spa light control that will only turn on if the sun is down
    spaLightNight = DependentControl("spaLightNight", nullInterface, spaLight, [(sunUp, 0)])
    spa = SpaControl("spa", nullInterface, valveMode, poolPump, heaterControl, spaLightNight, waterTemp, group="Pool", label="Spa", type="spa")
    # spa light control that will only turn on if the sun is down and the spa is on
    spaLightNightSpa = DependentControl("spaLightNightSpa", nullInterface, spaLightNight, [(spa, 1)])
    
    filterSequence = Sequence("filterSequence", [Cycle(poolPump, duration=39600, startState=1),  # filter 11 hr
                                              ], group="Pool", label="Filter daily")
    cleanSequence = Sequence("cleanSequence", [Cycle(poolClean, duration=3600, startState=1), 
                                              ], group="Pool", label="Clean 1 hr")
    flushSequence = Sequence("flushSequence", [Cycle(spaFlush, duration=900, startState=1), 
                                              ], group="Pool", label="Flush spa 15 min")

    # Power
    poolPumpPower = Sensor("poolPumpPower", pentairInterface, 2, type="power", group="Power", label="Pool pump")
    poolCleanerPower = Sensor("poolCleanerPower", powerInterface, poolCleaner, type="power", group="Power", label="Pool cleaner")
    spaBlowerPower = Sensor("spaBlowerPower", powerInterface, spaBlower, type="power", group="Power", label="Spa blower")
    poolLightPower = Sensor("poolLightPower", powerInterface, poolLight, type="power", group="Power", label="Pool light")
    spaLightPower = Sensor("spaLightPower", powerInterface, spaLight, type="power", group="Power", label="Spa light")

    # Schedules
    sundaySpaOnTask = Task("sundaySpaOnTask", SchedTime(year=[2016], month=[8], day=[14], hour=[16], minute=[30]), spa, 1)
    sundaySpaOffTask = Task("sundaySpaOffTask", SchedTime(year=[2016], month=[8], day=[14], hour=[18], minute=[30]), spa, 0)
    poolFilterTask = Task("poolFilterTask", SchedTime(hour=[21], minute=[0]), filterSequence, 1)
    poolCleanerTask = Task("poolCleanerTask", SchedTime(hour=[8], minute=[1]), cleanSequence, 1)
    flushSpaTask = Task("flushSpaTask", SchedTime(hour=[9], minute=[2]), flushSequence, 1)
    spaLightOnSunsetTask = Task("spaLightOnSunsetTask", SchedTime(event="sunset"), spaLightNightSpa, 1)
    schedule = Schedule("schedule", [sundaySpaOnTask, sundaySpaOffTask, poolFilterTask, poolCleanerTask, flushSpaTask, spaLightOnSunsetTask])

    # Resources
    resources = Collection("resources", [poolLight, spaLight, poolLights,
                                        waterTemp, poolTemp, spaTemp, poolEquipTemp, 
                                        poolPump, poolCleaner, poolClean, intakeValve, returnValve, 
                                        valveMode, spaFill, spaFlush, spaDrain, poolHeater, spaBlower, 
                                        poolPumpSpeed, poolPumpFlow,
                                        spa, spaTempTarget, heaterControl,
                                        filterSequence, cleanSequence, flushSequence,
                                        poolPumpPower, poolCleanerPower, spaBlowerPower, poolLightPower, spaLightPower,
                                        ])
    restServer = RestServer(resources, event=stateChangeEvent, label="Pool")

    # Start interfaces
    configInterface.start()
    if not spaTempTarget.getState():
        spaTempTarget.setState(spaTempTargetDefault)
    gpioInterface0.start()
    gpioInterface1.start()
    pentairInterface.start()
    schedule.start()
    restServer.start()

