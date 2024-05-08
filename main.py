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
from ctrlxdatalayer.variant import Result
from pylogix import PLC
import logging
import logging.handlers
import typing
from pycomm3 import LogixDriver
from app.helper.ctrlx_datalayer_helper import get_provider
from app.ab_util import myLogger, addData
from app.pycomm3.sorter import tagSorter


def loadConfig() -> typing.Tuple[str,str,object]:
    """
    Loads config file and sets logging path depending on environment
        :param void:
        :return configPath: = path to configuration file 
        :return logPath: = path to log file
        :return configData: = parsed JSON of config file
    """
    snap_path = os.getenv('SNAP')
    print(snap_path)
    if snap_path is None:
        configPath = "./DEV/config.json"
        logPath = "./DEV/info.log"
    else:
        configPath = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/config.json"
        logPath = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/info.log"

    # Configure the logger for easier analysis
    logging.basicConfig(filename = logPath, filemode = 'w', format='%(asctime)s:%(msecs)d, %(name)s, %(levelname)s, %(message)s', datefmt= '%H:%M:%S', level=logging.DEBUG) 
    
    myLogger("cltrX File Path: " + str(snap_path), logging.INFO, source=__name__) 

    # Get the time the files was modified
    fileTime = os.stat(configPath).st_mtime
    myLogger("Config modified at UNIX TIME " + str(fileTime), logging.INFO)

    # Read config.json
    try:
        with open(configPath) as jsonConfig:
            configData = json.load(jsonConfig)
            myLogger("Config data: " + str(configData), logging.INFO)
    except Exception as e:
        myLogger("Failed to read config.json. Exception: "  + repr(e), logging.ERROR, source=__name__)
    return configPath,logPath,configData

# Load global configuration data
configPath,logPath,configData = loadConfig()

# Define global variables
AB_NODE_LIST = []
SORTED_TAGS = []
PLC_LIST = []
EIP_CLIENT_LIST = []

def sortAndProvideTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _plc:PLC, _EIP_client:LogixDriver, _tags:list):
    """
    Sorts and provides given tags as nodes to ctrlX datalayer provider
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _plc: = PyLogix PLC
        :param _EIP_client: = LogixDriver
        :param _tags: = list of tags to sort and provide
    """
    try:
        for tag in _tags:
            # Sort sub-tags to determine paths and add all tags to provider node list
            sortedTags = tagSorter(tag)    
            for sortedTag in sortedTags:
                AB_NODE_LIST.append(addData(sortedTag, _ctrlxDatalayerProvider, _plc, _EIP_client))
    except Exception as e:
        myLogger("Failed to sort and provide tags for device: " + _plc.IPAddress + ". Exception: " + repr(e), logging.ERROR, source=__name__)

def provideAllScopeTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _plc:PLC, _EIP_client:LogixDriver, _scope:object, _controller: bool):
    """
    Provides all program tags to the ctrlX datalayer provider
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _plc: = PyLogix PLC
        :param _EIP_client: = LogixDriver
        :param _scope: = PLC program or controller object from config.json
        :param _controller: = Boolean flag to indicate controller scope (TRUE = controller scope)
    """
    try:
        if(_controller):
            tags = _EIP_client.get_tag_list()
        else:            
            tags = _EIP_client.get_tag_list(_scope['name'])
        # Tag list here is all top level tags of the program
        sortAndProvideTags(_ctrlxDatalayerProvider, _plc, _EIP_client, tags)
    except Exception as e:
        myLogger("Scope tags for: " + _scope['name'] + "of device: " + _plc.IPAddress + " could not be loaded. Exception: " + repr(e), logging.ERROR, source=__name__)

def provideSpecifiedScopeTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _plc:PLC, _EIP_client:LogixDriver, _scope:object, _controller:bool):
    """
    Provides specified program tags to the ctrlX datalayer provider
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _plc: = PyLogix PLC
        :param _EIP_client: = LogixDriver
        :param _scope: = PLC program or controller object from config.json
        :param _controller: = Boolean flag to indicate controller scope (TRUE = controller scope)
    """
    try:
        # Loop through each tag in the config.json program tags array
        locatedTags = []
        for tag in _scope['tags']:
            # Format tag path based on controller or program tag type
            if not _controller: 
                tag = "Program:" + _scope['name'] + "." + tag
                _EIP_client.get_tag_list(_scope['name']) # Need to cache tag list for get_tag_info()
            else:
                tag = tag
                t = _EIP_client.get_tag_list() # Need to cache tag list for get_tag_info()
            # Get specified tag info from the EIP client
            locatedTag = _EIP_client.get_tag_info(tag)
            # Add tag info to located tags array
            locatedTags.append(locatedTag)
        # Sort and provide all located tags
        sortAndProvideTags(_ctrlxDatalayerProvider, _plc, _EIP_client,locatedTags)
            
    except Exception as e:
        myLogger("Specified program tags for: " + _scope['name'] + " of device: " + _plc.IPAddress + " could not be loaded. Exception: " + repr(e), logging.ERROR, source=__name__)

def provideAllDeviceTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _plc:PLC, _EIP_client:LogixDriver):

    """
    Provides all device tags to ctrlx datalayer provider and adds PLC and EIP client to global list          
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _plc: = PyLogix PLC
        :param _EIP_client: = LogixDriver
    """
    try:
        tags = _EIP_client.get_tag_list('*')
        sortAndProvideTags(_ctrlxDatalayerProvider,_plc,_EIP_client,tags)
    except Exception as e:
        myLogger("Device tags of device: " + _plc.IPAddress + " could not be loaded. Exception: " + repr(e), logging.ERROR, source=__name__)

def createPLCAndConnectEIPClient(_ipAddress:str) -> typing.Tuple[PLC,LogixDriver]:
    """
    Creates a new PyLogix PLC and opens an EIP connection at the specified IP address        
        :param _ipAddress: = IP address of Logix PLC
        :return plc: = PyLogix PLC
        :return EIP_client: = LogixDriver
    """
    try:
        plc = PLC()
        plc.IPAddress = _ipAddress
        EIP_client = LogixDriver(plc.IPAddress)
        EIP_client.open()
        print("Opening EIP client for: " + EIP_client.info['name'] + " at: " + plc.IPAddress)
        PLC_LIST.append(plc)
        EIP_CLIENT_LIST.append(EIP_client)
        return plc, EIP_client
    except Exception as e:
        myLogger("Failed to open EIP client for: " + EIP_client.info['name'] + " at: " + plc.IPAddress + ". Exception: " + repr(e), logging.ERROR, source=__name__)
    
def localExecution(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider):
    """
    Handles program execution outside of the snap context            
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """
    print("Running local...")
    try:
        # -------------------------- OPTION 1: NO AUTOSCAN ------------------------------
        if configData['scan'] != "true":
            # Loop through each controller defined in config.json
            for controller in configData['controllers']:              
                # Establish EIP client connection to each controller
                plc, EIP_client = createPLCAndConnectEIPClient(controller['ip']) 
                # If tag list exists at controller level, provide specified tags
                if "tags" in controller:
                    provideSpecifiedScopeTags(_ctrlxDatalayerProvider ,plc, EIP_client, controller, True)
                # If no tag list exists at controller level, provide all controller scoped tags
                else:
                    provideAllScopeTags(_ctrlxDatalayerProvider ,plc, EIP_client, controller, True)
                # Loop through each program in the controller programs array
                for program in controller['programs']:
                    # If a tag list exists in the program, provide specified tags
                    if "tags" in program:
                        provideSpecifiedScopeTags(_ctrlxDatalayerProvider ,plc, EIP_client, program, False)                         
                    # If no tag list exists in the program, provide all program scoped tags
                    else:
                        provideAllScopeTags(_ctrlxDatalayerProvider, plc, EIP_client, program)
        # ---------------------------- OPTION 2: AUTOSCAN -------------------------------
        else:
            t = 6
    except Exception as e:
         myLogger("Local execution failure: " + repr(e), logging.ERROR, source=__name__)
        
def runApp(_ctrlxDatalayerProvider):
    snap_path = os.getenv('SNAP')

    # This top level plc is only used for network discovery
    with PLC() as plc:
        devices = plc.Discover() # Scan EIP network to discover devices
        for device in devices.Value: 
            message = 'Found Device: ' + device.IPAddress + '  Product Code: ' + device.ProductName + " " + str(device.ProductCode) + '  Vendor/Device ID:' + device.Vendor + " " + str(device.DeviceID) + '  Revision/Serial:' + device.Revision + " " + device.SerialNumber
            myLogger(message, logging.INFO, source=__name__)
# -----------------------------EMBEDDED EXECUTION ---------------------------------------------------------------------- 
    if snap_path is not None: # This means the app is deployed on a target
        # Check configuration for autoscan enable
        myLogger("Autoscan Setting = " + configData['scan'], logging.INFO, source=__name__)
# ---------------------------- NETWORK SCANNING IS DISABLED ------------------------------------------------------------             
        if configData['scan'] != "true":
            #if the auto scan is not true then load controllers from file
            if "controllers" in configData:
                applications = configData['controllers']
                for application in applications:
                    myLogger('Loading configuration for ' + application, logging.INFO, source=__name__)
                    plc = PLC()
                    plc.IPAddress = application["ip"]
                    myLogger("Adding controller at " + application["ip"], logging.INFO, source=__name__)
                    try:
                        with LogixDriver(device.IPAddress) as EIP_client:
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
                                                sortedTags = tagSorter(EIP_client.get_tag_info(tag))        
                                                for sortedTag in sortedTags:
                                                    AB_NODE_LIST.append(addData(sortedTag, _ctrlxDatalayerProvider, plc, EIP_client))
                                        else:       
                                            #if the tags are not explicit in the file 
                                            if program != "controller": 
                                                tagPath = "Program:" + program
                                            else:
                                                tagPath = ""
                                            tags = EIP_client.get_tag_list(tagPath) 
                                            for tag in tags:
                                                if tag['tag_name'].find("Program:.") != -1:
                                                    tag['tag_name'] = tag['tag_name'].split(".")[1]
                                                sortedTags = tagSorter(tag)        
                                                for sortedTag in sortedTags:
                                                    AB_NODE_LIST.append(addData(sortedTag, _ctrlxDatalayerProvider, plc, EIP_client))                                                      
                            else:
                                tags = EIP_client.get_tag_list('*')
                                for tag in tags:
                                    #pass each tag to the tag sorter which returns 
                                    sortedTags = tagSorter(tag)       
                                    #pprint.pprint(sortedTags)
                                    for sortedTag in sortedTags:
                                        AB_NODE_LIST.append(addData(sortedTag, _ctrlxDatalayerProvider, plc, EIP_client))
                    except:
                        myLogger("Controller at " + plc.IPAddress + " could not be loaded.", logging.ERROR, source=__name__) 
            else:
                #if no devices were configured in the file, return empty and log the exception
                myLogger('No devices configured in the configuration data.', logging.ERROR, source=__name__)
                return None, None
# ---------------------------- NETWORK SCANNING IS ENABLED AND DEVICES WERE FOUND --------------------------------------           
        elif devices.Value != []: 
            print("Adding auto-scanned device tags...")
            for device in devices.Value:
                createPLCAndConnectEIPClient(device.IPAddress)
                provideAllDeviceTags(_ctrlxDatalayerProvider, device)
# ---------------------------- NETWORK SCANNING IS ENABLED AND DEVICES WERE NOT FOUND -----------------------------------                                     
        else:
            print('No devices found on startup.') 
# -----------------------------LOCAL EXECUTION -------------------------------------------------------------------------- 
    else:
        localExecution(_ctrlxDatalayerProvider)
                  
def main():

    myLogger('#######################################################################', logging.DEBUG, source=__name__)
    myLogger('#######################################################################', logging.DEBUG, source=__name__)
    myLogger('#######################################################################', logging.DEBUG, source=__name__)
    myLogger('Initializing application', logging.INFO)   

    with ctrlxdatalayer.system.System("") as datalayer_system:
        datalayer_system.start(False)

        # CREATE DATALAYER PROVIDER
        ctrlxDatalayerProvider, connection_string = get_provider(datalayer_system, configData['ctrlX provider']['ip'], ssl_port=configData['ctrlX provider']['port'])
        if ctrlxDatalayerProvider is None:
            myLogger("Connecting to " + connection_string + " failed.", logging.ERROR, source=__name__)
            sys.exit(1)

        with ctrlxDatalayerProvider:  # provider.close() is called automatically when leaving with... block
            result = ctrlxDatalayerProvider.start()
            if result != Result.OK:
                myLogger("ERROR Starting Data Layer Provider failed with:" + str(result), logging.ERROR, source=__name__)
                return
            
            # START THE APPLICATION           
            runApp(ctrlxDatalayerProvider)

            # Get the time the files was modified
            fileTime =  os.stat(configPath).st_mtime

            # If nodes exist in node list, plc objects and EIP clients exist, keep running
            if AB_NODE_LIST is not None and PLC_LIST is not None and EIP_CLIENT_LIST is not None:       
                myLogger('INFO Running endless loop...', logging.INFO, source=__name__)
                while ctrlxDatalayerProvider.is_connected():
                    if (fileTime == os.stat(configPath).st_mtime):
                        time.sleep(1.0)  # Seconds
                    else:
                        fileTime == os.stat(configPath).st_mtime
                        myLogger('ERROR Data Layer Provider is disconnected', logging.ERROR, source=__name__)
                        # CLEANUP
                        for node in AB_NODE_LIST:
                            node.unregister_node()
                            del node
                        for client in EIP_CLIENT_LIST:
                            client.close()
                            del client
                        for plc in PLC_LIST:
                            plc.Close()
                            del plc
                        runApp(ctrlxDatalayerProvider)
            else: 
                myLogger("Improperly configured application, see application log.", logging.ERROR, source=__name__)            

            myLogger('Stopping Data Layer provider', logging.INFO, source=__name__)
            result = ctrlxDatalayerProvider.stop()
            myLogger('Data Layer Stopped with result: ' + str(result), logging.INFO, source=__name__)

        # Attention: Doesn't return if any provider or client instance is still running
        stop_ok = datalayer_system.stop(False)
        myLogger('System Stop: ' + str(stop_ok), logging.INFO, source=__name__)

if __name__ == '__main__':
    main()
