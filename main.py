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
from helper.ctrlx_datalayer_helper import get_provider
from app.ab_util import myLogger, addData, writeSortedTagsToCSV

def loadConfig() -> typing.Tuple[str,str,str,object]:
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
        tagPath = "./DEV/tagList.csv"
    else:
        configPath = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/config.json"
        logPath = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/info.log"
        tagPath = "/var/snap/rexroth-solutions/common/solutions/activeConfiguration/AllenBradley/tagList.csv"

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
            # Set log level based on configured value
            if(configData["LOG LEVEL"]):
                            logLevel = configData["LOG LEVEL"]
                            logging.getLogger().setLevel(logging.getLevelName(logLevel))
            myLogger("Config data: " + str(configData), logging.INFO)
    except Exception as e:
        myLogger("Failed to read config.json. Exception: "  + repr(e), logging.ERROR, source=__name__)
    return configPath,logPath,tagPath,configData

# Load global configuration data
configPath,logPath,tagListPath,configData = loadConfig()

# Define global variables
AB_NODE_LIST = []
AB_BULK_READ_NODE_LIST = []
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
            sortedTags = writeSortedTagsToCSV(tag, tagListPath)    
            for sortedTag in sortedTags:
                AB_NODE_LIST.append(addData(sortedTag, _ctrlxDatalayerProvider, _plc, _EIP_client))
    except Exception as e:
        myLogger("Failed to sort and provide tags for device: " + _plc.IPAddress + ". Exception: " + repr(e), logging.ERROR, source=__name__)

def provideAllScopeTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _plc:PLC, _EIP_client:LogixDriver, _scope:object, _controller: bool, _priorityTags: bool):
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

def provideSpecifiedScopeTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _plc:PLC, _EIP_client:LogixDriver, _scope:object, _controller:bool, _priorityTags: bool):
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
                tagList = _EIP_client.get_tag_list(_scope['name']) # Need to cache tag list for get_tag_info()
            else:
                tag = tag
                tagList = _EIP_client.get_tag_list() # Need to cache tag list for get_tag_info()
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
        myLogger("Failed to open EIP client at: " + plc.IPAddress + ". Exception: " + repr(e), logging.ERROR, source=__name__)

def provideNodesByConfig(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _configTagType:str):
    """
    Provides standard nodes to the ctrlX datalayer as described in config.json       
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """
    # Check configured tag type
    if _configTagType == 'standard tags':
        priorityTags = False
    elif _configTagType == 'priority tags':
        priorityTags = True
    else:
        myLogger("Unknown tag type in config.json. Must be 'standard tags' or 'priority tags'", logging.ERROR, source=__name__)
        return

    # Loop through each controller defined in config.json
    for controller in configData[_configTagType]['controllers']:              
        # Establish EIP client connection to each controller
        plc, EIP_client = createPLCAndConnectEIPClient(controller['ip']) 
        # If tag list exists at controller level, provide specified tags
        if "tags" in controller:
            provideSpecifiedScopeTags(_ctrlxDatalayerProvider ,plc, EIP_client, controller, True, priorityTags)
        # If no tag list exists at controller level, provide all controller scoped tags
        else:
            provideAllScopeTags(_ctrlxDatalayerProvider ,plc, EIP_client, controller, True, priorityTags)
        # Loop through each program in the controller programs array
        for program in controller['programs']:
            # If a tag list exists in the program, provide specified tags
            if "tags" in program:
                provideSpecifiedScopeTags(_ctrlxDatalayerProvider ,plc, EIP_client, program, False, priorityTags)                         
            # If no tag list exists in the program, provide all program scoped tags
            else:
                provideAllScopeTags(_ctrlxDatalayerProvider, plc, EIP_client, program, False, priorityTags)

def providePriorityNodesByConfig(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider):
    """
    Provides priority nodes to the ctrlX datalayer as described in config.json       
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """ 
    # Loop through each controller defined in config.json
    for controller in configData['priority tags']['controllers']:              
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
                provideAllScopeTags(_ctrlxDatalayerProvider, plc, EIP_client, program, False)

def provideNodesAutoscan(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider):
    """
    Provides all device nodes to the datalayer discovered via EIP network scan  
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """ 
    # Create a scoped scanner PLC object. This will be destroyed once tags have been added
    with PLC() as scanner:
        # Scan EIP network for devices
        devices = scanner.Discover() 
        for device in devices.Value: 
            message = 'Found Device: ' + device.IPAddress + '  Product Code: ' + device.ProductName + " " + str(device.ProductCode) + '  Vendor/Device ID:' + device.Vendor + " " + str(device.DeviceID) + '  Revision/Serial:' + device.Revision + " " + device.SerialNumber
            myLogger(message, logging.INFO, source=__name__)
            # Create PLC object and EIP client for each discovered device
            createPLCAndConnectEIPClient(device.IPAddress)
            # Provide all device tags for each discovered device
            provideAllDeviceTags(_ctrlxDatalayerProvider, device)

def providePriorityTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider):
    for controller in configData['priority tags']['controllers']:
        plcExists = False
        # Check if a PLC object already exists at the controller IP
        for plc in PLC_LIST:
            if plc.IPAddress == controller.IPAddress:
                plcExists = True
                break
        # If no PLC object exists, create a new one and connect an EIP client
        if not plcExists:
            createPLCAndConnectEIPClient(controller['ip'])
    providePriorityNodesByConfig(_ctrlxDatalayerProvider)

def localExecution(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider):
    """
    Handles program execution outside of the snap context            
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """
    print("Running local...")
    try:
        # -------------------------- OPTION 1: NO AUTOSCAN ------------------------------
        if configData['scan'] != True:
            provideNodesByConfig(_ctrlxDatalayerProvider)
            providePriorityTags(_ctrlxDatalayerProvider)
        # ---------------------------- OPTION 2: AUTOSCAN -------------------------------
        else:
            provideNodesAutoscan(_ctrlxDatalayerProvider)
    except Exception as e:
         myLogger("Local execution failure: " + repr(e), logging.ERROR, source=__name__)


def runABProvider(_ctrlxDatalayerProvider):
    """
    Executes logic to provide configured or scanned tags to the configured ctrlX OS datalayer broker        
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """
    snap_path = os.getenv('SNAP')
    # Check configuration for autoscan enable
    myLogger("Autoscan Setting = " + str(configData['scan']), logging.INFO, source=__name__)
# ---------------------------------- EMBEDDED EXECUTION ----------------------------------------------------------------
    if snap_path is not None:
        # This means the app is deployed on a target
# ----------------------------- NETWORK SCANNING IS DISABLED -----------------------------------------------------------            
        if configData['scan'] != True:
            provideNodesByConfig(_ctrlxDatalayerProvider)
            providePriorityTags(_ctrlxDatalayerProvider)
# ----------------------------- NETWORK SCANNING IS ENABLED ------------------------------------------------------------           
        else:
            provideNodesAutoscan(_ctrlxDatalayerProvider)                             
# ----------------------------- -----LOCAL EXECUTION -------------------------------------------------------------------
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
        if(configData["ctrlX provider"]["local"] != True):
            ctrlxDatalayerProvider, connection_string = get_provider(datalayer_system, 
                                                                    configData['ctrlX provider']['ip'], 
                                                                    ssl_port=configData['ctrlX provider']['port'])
        else:
            ctrlxDatalayerProvider, connection_string = get_provider(datalayer_system)

        if ctrlxDatalayerProvider is None:
            myLogger("Connecting to " + connection_string + " failed.", logging.ERROR, source=__name__)
            sys.exit(1)

        with ctrlxDatalayerProvider:  # provider.close() is called automatically when leaving with... block
            result = ctrlxDatalayerProvider.start()
            if result != Result.OK:
                myLogger("ERROR Starting Data Layer Provider failed with:" + str(result), logging.ERROR, source=__name__)
                return
            
            # START THE APPLICATION           
            runABProvider(ctrlxDatalayerProvider)

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
                        runABProvider(ctrlxDatalayerProvider)
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
