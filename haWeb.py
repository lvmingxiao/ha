import os
import cherrypy
import json
import threading
import time
import copy
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.restCache import *
from ha.timeInterface import *
from haWebViews import *

buttons = [] #"index", "solar", "lights", "pool", "spa", "sprinklers", "doors"]

stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

class WebRoot(object):
    def __init__(self, resources, env, cache):
        self.resources = resources
        self.env = env
        self.cache = cache
        self.lastStates = {}
    
    # Everything    
    @cherrypy.expose
    def index(self, action=None, resource=None):
        debug('debugWeb', "/", "get", action, resource)
        with resourceLock:
            reply = self.env.get_template("default.html").render(title="4319 Shadyglade", script="", 
                                groups=[[group, self.resources.getGroup(group)] for group in ["Time", "Temperature", "Pool", "Lights", "Doors", "Water", "Solar", "Power", "Cameras", "Tasks"]],
                                views=views,
                                buttons=buttons)
        return reply

    # iPad - 1024x768   
    @cherrypy.expose
    def ipad(self, action=None, resource=None):
        debug('debugWeb', "/ipad", "get", action, resource)
        with resourceLock:
            reply = self.env.get_template("ipad.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                day=self.resources["theDay"],
                                temp=self.resources["deckTemp"],
                                groups=[["Pool", self.resources.getResList(["poolTemp", "spa1"])], 
                                      ["Lights", self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight"])], 
                                      ["Shades", self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                                      ["Sprinklers", self.resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"])]
                                      ],
                                views=views,
                                buttons=buttons)
        return reply

    # iPhone 5 - 320x568    
    @cherrypy.expose
    def iphone5(self, action=None, resource=None):
        debug('debugWeb', "/iphone5", "get", action, resource)
        with resourceLock:
            reply = self.env.get_template("iphone5.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                temp=self.resources["deckTemp"],
                                resources=self.resources.getResList(["spa1", "frontLights", "backLights", "allShades", "shade1", "shade2", "shade3", "shade4", "backLawn", "backBeds", "garden", "sideBeds", "frontLawn"]),
                                views=views,
                                buttons=buttons)
        return reply

    # iPhone 3GS - 320x480    
    @cherrypy.expose
    def iphone3gs(self, action=None, resource=None):
        debug('debugWeb', "/iphone3gs", "get", action, resource)
        with resourceLock:
            reply = self.env.get_template("iphone3gs.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                day=self.resources["theDay"],
                                temp=self.resources["deckTemp"],
                                resources=self.resources.getResList(["frontLights", "backLights", "bedroomLight", "recircPump", "garageBackDoor"]),
                                views=views,
                                buttons=buttons)
        return reply

    # Solar    
    @cherrypy.expose
    def solar(self):
        return self.env.get_template("group.html").render(title="Solar", css="solar.css", 
                            resources=self.resources.getResList(["currentPower", "todaysEnergy", "lifetimeEnergy"]), 
                            views=views,
                            buttons=buttons)

    # Lights    
    @cherrypy.expose
    def lights(self, action=None, resource=None, link=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Lights", css="lights.css", 
                            resources=self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight", "xmasLights"]), 
                            views=views,
                            buttons=buttons)

    # Pool    
    @cherrypy.expose
    def pool(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Pool", css="pool.css", 
                            resources=self.resources.getResList(["poolTemp", "cleanMode", "poolPump", "poolCleaner", "poolLight", "spaLight"]), 
                            views=views,
                            buttons=buttons)

    # Spa    
    @cherrypy.expose
    def spa(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Spa", css="spa.css", 
                            resources=self.resources.getResList(["poolTemp", "spaTemp", "spaWarmup", "spaReady", "spaShutdown", "spaBlower", "poolLight", "spaLight"]), 
                            views=views,
                            buttons=buttons)

    # Sprinklers    
    @cherrypy.expose
    def sprinklers(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Sprinklers", css="sprinklers.css", 
                            resources=self.resources.getResList(["frontLawnSequence", "gardenSequence", "backLawnSequence", "sideBedSequence"]), 
                            views=views,
                            buttons=buttons)

    # Doors    
    @cherrypy.expose
    def doors(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Doors", css="doors.css", 
                            resources=self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"]), 
                            views=views,
                            buttons=buttons)

    # Return the value of a resource attribute
    @cherrypy.expose
    def value(self, resource=None, attr=None):
        try:
            if resource:
                if attr:
                    return self.resources[resource].__getattribute__(attr).__str__()
                else:
                    return self.resources[resource].dict().__str__()
        except:
            return "Error"        

    # Update the states of all resources
    @cherrypy.expose
    def state(self, _=None):
        debug('debugWebUpdate', "state", cherrypy.request.remote.ip)
        return self.updateStates(self.resources["states"].getState())
        
    # Update the states of resources that have changed
    @cherrypy.expose
    def stateChange(self, _=None):
        debug('debugWebUpdate', "stateChange", cherrypy.request.remote.ip)
        debug('debugInterrupt', "update", "event wait")
        stateChangeEvent.wait()
        debug('debugInterrupt', "update", "event clear")
        stateChangeEvent.clear()
        return self.updateStates(self.resources["states"].getStateChange())

    # return the json to update the states of the specified collection of sensors
    def updateStates(self, resourceStates):
        staticTypes = ["time", "ampm", "date"]          # types whose class does not depend on their value
        tempTypes = ["tempF", "tempC", "spaTemp"]       # temperatures
        updates = {"cacheTime": self.cache.cacheTime}
        for resource in resourceStates.keys():
            try:
                resState = self.resources[resource].getViewState(views)
                resClass = self.resources[resource].type
                if resClass in tempTypes:
                    updates[resource] = ("temp", resState, tempColor(resState))
                else:
                    if resClass not in staticTypes:
                        resClass += "_"+resState
                    updates[resource] = (resClass, resState, "")
            except:
                pass
        debug('debugWebUpdate', "states", len(updates))
        return json.dumps(updates)
        
    # Submit    
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", "post", action, resource)
        self.resources[resource].setViewState(action, views)
        reply = ""
        return reply

if __name__ == "__main__":
    # resources
    resources = HACollection("resources")

    # time resources
    timeInterface = TimeInterface("time")
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %B %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # start the cache to listen for services on other servers
    restCache = RestCache("restCache", resources, socket.gethostname()+":"+str(webRestPort), stateChangeEvent, resourceLock)
    restCache.start()
    
    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    globalConfig = {
        'server.socket_port': webPort,
        'server.socket_host': "0.0.0.0",
        }
    appConfig = {
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "css",
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "js",
        },
        '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(baseDir, "static/favicon.ico"),
        },
    }    
    cherrypy.config.update(globalConfig)
    root = WebRoot(resources, Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates'))), restCache)
    cherrypy.tree.mount(root, "/", appConfig)
    if not webLogging:
        access_log = cherrypy.log.access_log
        for handler in tuple(access_log.handlers):
            access_log.removeHandler(handler)
    cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.engine.autoreload.unsubscribe()
    cherrypy.engine.start()

    # start the REST server for this service
    restServer = RestServer(resources, port=webRestPort, event=stateChangeEvent)
    restServer.start()

