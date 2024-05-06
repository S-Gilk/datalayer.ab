#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2021-2022 Bosch Rexroth AG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import sys
import time
import json
import ctrlxdatalayer
from ctrlxdatalayer.variant import Variant, Result
from pylogix import PLC
import logging
import logging.handlers
from pycomm3 import LogixDriver
from helper.ctrlx_datalayer_helper import get_provider
from app.ab_util import myLogger, addData#, tagSorter
from app.pycomm3.getTags import tagSorter
import pprint
#from cysystemd import journal

def runApp(provider):
    # Path to compiled files

    snap_path = os.getenv('SNAP')
    if snap_path is None:
        config = "./DEV/config.json"
    else:
        config = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/config.json"

    #Get the time the files was modified
    fileTime = os.stat(config).st_mtime
    myLogger("Config modified at UNIX TIME " + str(fileTime), logging.INFO)
    with open(config) as jsonConfig:
        configdata = json.load(jsonConfig)
        myLogger("Config data: " + str(configdata), logging.INFO)
        
    #Define the master list of data
    abProviderList = []
    with PLC() as comm:
        devices = comm.Discover() #find all of the rockwell devices
        for device in devices.Value: 
            #for each device, print what was found
            message = 'Found Device: ' + device.IPAddress + '  Product Code: ' + device.ProductName + " " + str(device.ProductCode) + '  Vendor/Device ID:' + device.Vendor + " " + str(device.DeviceID) + '  Revision/Serial:' + device.Revision + " " + device.SerialNumber
            myLogger(message, logging.INFO, source=__name__)
    if snap_path is not None: #this means the app is deployed on a target
        #start the process of checking for the variables
        myLogger("Autoscan Setting = " + configdata['scan'], logging.INFO, source=__name__)        
        if configdata['scan'] != "true":
            #if the auto scan is not true then load controllers from file
            if "controllers" in configdata:
                applications = configdata['controllers']
                for application in applications:
                    myLogger('Loading configuration for ' + application, logging.INFO, source=__name__)
                    comm = PLC()
                    comm.IPAddress = application["ip"]
                    myLogger("Adding controller at " + application["ip"], logging.INFO, source=__name__)
                    try:
                        with LogixDriver(device.IPAddress) as controller:
                            if "programs" in application:
                                for programs in application["programs"]:
                                    #cycle through the programs in the application
                                    for program in programs.keys():
                                        if "tags" in programs[program]:
                                            for tag in programs[program]["tags"]:
                                                #cycle through the tags in the configuration file
                                                if program != "controller": 
                                                    tag = "Program:" + program + "." + tag
                                                else:
                                                    tag = tag
                                                print('Adding Tag: ' + tag)
                                                sortedTags = tagSorter(controller.get_tag_info(tag))        
                                                for sortedTag in sortedTags:
                                                    abProviderList.append(addData(sortedTag, provider, comm, controller))
                                        else:       
                                            #if the tags are not explicit in the file 
                                            if program != "controller": 
                                                tagPath = "Program:" + program
                                            else:
                                                tagPath = ""
                                            tags = controller.get_tag_list(tagPath) 
                                            for tag in tags:
                                                if tag['tag_name'].find("Program:.") != -1:
                                                    tag['tag_name'] = tag['tag_name'].split(".")[1]
                                                sortedTags = tagSorter(tag)        
                                                for sortedTag in sortedTags:
                                                    abProviderList.append(addData(sortedTag, provider, comm, controller))                                                      
                            else:
                                tags = controller.get_tag_list('*')
                                for tag in tags:
                                    #pass each tag to the tag sorter which returns 
                                    sortedTags = tagSorter(tag)       
                                    #pprint.pprint(sortedTags)
                                    for sortedTag in sortedTags:
                                        abProviderList.append(addData(sortedTag, provider, comm, controller))
                            return abProviderList, comm, controller
                    except:
                        myLogger("Controller at " + comm.IPAddress + " could not be loaded.", logging.ERROR, source=__name__) 
                        return None, None, None  
            else:
                #if no devices were configured in the file, return empty and log the exception
                myLogger('No devices configured in the configuration data.', logging.ERROR, source=__name__)
                return None, None, None    
            
        elif devices.Value != []:
            print("adding auto-scanned devices")
            for device in devices.Value:
                comm = PLC()
                comm.IPAddress = device.IPAddress
                try:
                    with LogixDriver(device.IPAddress) as controller:
                        tags = controller.get_tag_list('*')
                        for t in tags:
                            sortedTags = tagSorter(t)   
                            #pprint.pprint(sortedTags)     
                            for sortedTag in sortedTags:
                                abProviderList.append(addData(sortedTag, provider, comm, controller))
                        return abProviderList, comm, controller
                except:
                    myLogger("Controller at " + comm.IPAddress + " could not be loaded.", logging.ERROR, source=__name__)
                    return None, None, None
                                  
        else:
            print('No devices found on startup')  
    else: #use a defined PLC IP for debug and testing
        comm = PLC()
        comm.IPAddress = "192.168.2.90"
        print("running local")
        try:        
            with LogixDriver("192.168.2.90") as controller:
                #tags = controller.get_tag_list('TestProgram')
                tags = controller.get_tag_list("Program:TestProgram")
                print(controller.info)
                #for t in tags:
                    #agList.append(tagSorter(t['tag_name'], t['tag_name'], t))
                    #sortedTags = tagSorter(t['tag_name'], t['tag_name'], t)  
                #sortedTags = tagSorter(t)  
                #tag = 'Program:TestProgram.arReal100'

                #tags = controller.get_tag_list('*')
                for tag in tags:    
                    #sortedTags = tagSorter(controller.get_tag_info(tag))    
                    sortedTags = tagSorter(controller.get_tag_info(tag["tag_name"]))    
                    #pprint.pprint(sortedTags)
                    for sortedTag in sortedTags:
                        abProviderList.append(addData(sortedTag, provider, comm, controller))
                return abProviderList, comm, controller          
        except:
            myLogger("Controller at " + comm.IPAddress + " could not be loaded.", logging.ERROR, source=__name__)
            return None, None, None
                  
def main():
    snap_path = os.getenv('SNAP')
    print(snap_path)
    if snap_path is None:
        config = "./DEV/config.json"
        logPath = "./DEV/info.log"
    else:
        myLogger("cltrX File Path: " + str(snap_path), logging.INFO, source=__name__)
        config = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/config.json"
        logPath = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/info.log"

    #configure the logger for easier analysis
    logging.basicConfig(filename = logPath, filemode = 'w', format='%(asctime)s:%(msecs)d, %(name)s, %(levelname)s, %(message)s', datefmt= '%H:%M:%S', level=logging.DEBUG)  
    
    #logger = logging.getLogger()
    #logger.setLevel(logging.DEBUG)
    #logger.addHandler(journal.JournalLogHandler())

    #logger = logging.getLogger(__name__)
    #logger.setLevel(logging.DEBUG)
    #handler = logging.handlers.RotatingFileHandler(logPath, maxBytes=1*1024*1024, backupCount=2)
    #handler.setLevel(logging.DEBUG)
    #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #handler.setFormatter(formatter)
    # add the handler to the logger
    #logger.addHandler(handler)
    
    myLogger('#######################################################################', logging.DEBUG, source=__name__)
    myLogger('#######################################################################', logging.DEBUG, source=__name__)
    myLogger('#######################################################################', logging.DEBUG, source=__name__)
    myLogger('Initializing application', logging.INFO)   

    with ctrlxdatalayer.system.System("") as datalayer_system:
        datalayer_system.start(False)

        # ip="10.0.2.2", ssl_port=8443: ctrlX virtual with port forwarding and default port mapping
        provider, connection_string = get_provider(datalayer_system)
        if provider is None:
            myLogger("Connecting to " + connection_string + " failed.", logging.ERROR, source=__name__)
            sys.exit(1)

        with provider:  # provider.close() is called automatically when leaving with... block

            result = provider.start()
            if result != Result.OK:
                myLogger("ERROR Starting Data Layer Provider failed with:" + str(result), logging.ERROR, source=__name__)
                return

            #Start the applicaiton             
            abProviderList, comm, controller = runApp(provider)
            #pprint.print(abProviderList)
            #Get the time the files was modified
            fileTime =  os.stat(config).st_mtime
            if abProviderList is not None and comm is not None and controller is not None:       
                myLogger('INFO Running endless loop...', logging.INFO, source=__name__)
                while provider.is_connected():
                    if (fileTime == os.stat(config).st_mtime):
                        time.sleep(1.0)  # Seconds
                    else:
                        fileTime == os.stat(config).st_mtime
                        myLogger('"ERROR Data Layer Provider is disconnected', logging.ERROR, source=__name__)
                        for node in abProviderList:
                            node.unregister_node()
                            del node
                        comm.Close()
                        controller.close(0)
                        abProviderList, comm, controller = runApp(provider)
            else: 
                myLogger("Improperly configured application, see application log.", logging.ERROR, source=__name__)            

            myLogger('Stopping Data Layer provider', logging.INFO, source=__name__)
            result = provider.stop()
            myLogger('Data Layer Stopped with result: ' + str(result), logging.INFO, source=__name__)

        # Attention: Doesn't return if any provider or client instance is still running
        stop_ok = datalayer_system.stop(False)
        myLogger('System Stop: ' + str(stop_ok), logging.INFO, source=__name__)


if __name__ == '__main__':
    main()
