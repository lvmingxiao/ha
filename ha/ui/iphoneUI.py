
from jinja2 import FileSystemLoader
from ha import *

def iphoneUI(resources, templates, views):
    with resources.lock:
        widths = [[320, [60, 100, 60]], [320, [120, 72, 128]]]
        reply = templates.get_template("iphone.html").render(script="",
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            dayOfWeek=resources.getRes("theDayOfWeek"),
                            date=resources.getRes("theDate"),
                            dashResources=resources.getResList(["sunrise", "sunset"]),
                            spaControls = templates.get_template("spaWidget.html").render(templates=templates, widths=widths[1],
                                    spa=resources.getRes("spa"), spaTemp=resources.getRes("spaTemp"), spaTempTarget=resources.getRes("spaTempTarget"), nSetValues=3, views=views),
                            poolControls = templates.get_template("poolPumpWidget.html").render(templates=templates, widths=widths[1],
                                    poolPumpControl=resources.getRes("poolPump"), poolPumpFlowSensor=resources.getRes("poolPumpFlow"), nSetValues=5, views=views),
                            poolResources=resources.getResList(["valveMode", "spaBlower", "spaFill", "spaFlush", "spaDrain", "cleanSequence"]),
                            lightResources=resources.getResList(["frontLights", "backLights", "deckLights", "trashLights", "garageLights", "garageBackDoorLight",
                                                                 "poolLight", "spaLight", "sculptureLights"]),
                            shadeResources=resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"]),
                            sprinklerResources=resources.getResList(["backLawnSequence", "backBedSequence", "gardenSequence",
                                                                     "sideBedSequence", "frontLawnSequence", "frontBedSequence",
                                                                     "dailySequence", "weeklySequence"]),
                            hvacLiving = templates.get_template("hvacWidget.html").render(label="Living area",
                                    widths=widths[1],
                                    templates=templates,
                                    tempSensor=resources.getRes("diningRoomTemp"),
                                    heatTargetControl=resources.getRes("southHeatTempTarget"),
                                    coolTargetControl=resources.getRes("southCoolTempTarget"),
                                    fanControl=resources.getRes("southFan"),
                                    thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                                    views=views),
                            hvacBedrooms = templates.get_template("hvacWidget.html").render(label="Bedrooms",
                                    widths=widths[1],
                                    templates=templates,
                                    tempSensor=resources.getRes("masterBedroomTemp"),
                                    heatTargetControl=resources.getRes("northHeatTempTarget"),
                                    coolTargetControl=resources.getRes("northCoolTempTarget"),
                                    fanControl=resources.getRes("northFan"),
                                    thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                                    views=views),
                            hvacBackHouse = templates.get_template("hvacWidget.html").render(label="Back house",
                                    widths=widths[1],
                                    templates=templates,
                                    tempSensor=resources.getRes("backHouseTemp"),
                                    heatTargetControl=resources.getRes("backHeatTempTarget"),
                                    coolTargetControl=resources.getRes("backCoolTempTarget"),
                                    fanControl=resources.getRes("backFan"),
                                    thermostatUnitSensor=resources.getRes("backThermostatUnitSensor"),
                                    views=views),
                            alertResources=resources.getResList(["smsAlerts", "appAlerts", "iftttAlerts", "alertServices", "alertDoorbell", "alertSpa", "alertDoors"]),
                            powerResources=resources.getResList(["solar.inverters.stats.power", "loads.stats.power", "solar.stats.netPower",
                                                                 "solar.inverters.stats.avgVoltage",
                                                                 "solar.inverters.stats.dailyEnergy", "loads.stats.dailyEnergy", "solar.stats.netDailyEnergy",
                                                                 "solar.inverters.stats.lifetimeEnergy",
                                                                 "loads.lights.power", "loads.plugs.power", "loads.appliance1.power", "loads.appliance2.power",
                                                                 "loads.ac.power",
                                                                 "loads.cooking.power", "loads.pool.power", "loads.backhouse.power", "loads.carcharger.power",
                                                                 ]),
                            weatherResources=resources.getResList(["poolEquipTemp", "atticTemp",
                                                                   "solar.inverters.stats.avgTemp", "solar.optimizers.stats.avgTemp", "maxTemp", "minTemp",
                                                                   "dewpoint", "humidity", "barometer",
                                                                   "windSpeed", "windDir", "rainDay", "rainHour", "rainMinute",
                                                                 ]),
                            doorResources=resources.getResList(["frontDoor", "familyRoomDoor", "masterBedroomDoor",
                                                                "garageDoor", "garageBackDoor", "garageHouseDoor", "backHouseDoor",
                                                                 ]),
                            garageResources=resources.getResList(["garageTemp", "recircPump", "garageLights", "charger", "loads.carcharger.power"]),
                            fireplaceResources=resources.getResList(["fireplace", "fireplaceVideo"]),
                            holidayResources=resources.getResList(["holidayLights", "holiday", "halloween", "halloweenVideo",
                                                                    "xmasTree", "xmasTreePattern", "xmasCowTree", "xmasBackLights"]),
                            views=views)
    return reply

# iPhone 5 - 320x568
def iphone5():
    debug('debugWeb', "/iphone5", cherrypy.request.method)
    with resources.lock:
        widths = [[320, [60, 100, 60]], [320, [120, 72, 128]]]
        reply = templates.get_template("iphone5.html").render(script="",
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
                            resources=resources.getResList(["spaBlower", "porchLights",
#                                                            "xmasLights", "xmasTree",
                                                            "shade1", "shade2", "shade3", "shade4",
                                                            "backLawnSequence", "backBedSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence", "frontBedSequence"
                                                            ]),
                            views=views)
    return reply
