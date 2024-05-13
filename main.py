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
from app.ab_util import myLogger, addData, addDataBulk, writeSortedTagsToCSV

class Controller():
    plc:PLC
    EIP_client:LogixDriver
    ip:str
    name:str
    STANDARD_NODES:list
    PRIORITY_NODES:list

    def __init__(self, _ipAddress, _name):
        self.ip = _ipAddress
        self.name = _name
        self.plc = PLC(self.ip)
        self.EIP_client = LogixDriver(self.ip)
        self.STANDARD_NODES = []
        self.PRIORITY_NODES = []
        self.PRIORITY_TAG_NAMES = []
        self.PRIORITY_TAG_TYPES = []
        self.PRIORITY_TAG_LIST = []
        CONTROLLER_LIST.append(self)
        self.connect()

    def __del__(self):
        self.disconnect()
        for node in self.STANDARD_NODES:
            node.unregister_node()
        for node in self.PRIORITY_NODES:
            node.unregister_node()
        CONTROLLER_LIST.remove(self)
    
    def getPLC(self):
        return self.plc
    
    def connect(self):
        self.EIP_client.open()
    
    def disconnect(self):
        self.EIP_client.close()
        self.plc.Close()    

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
CONTROLLER_LIST: typing.List[Controller] = []

def sortAndProvideTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _controller:Controller, _tags:list, _priorityTags:bool):
    """
    Sorts and provides given tags as nodes to ctrlX datalayer provider
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _controller: = Controller object containing PLC and EIP client
        :param _tags: = list of tags to sort and provide
        :param _priorityTags: = boolean flag to indicate tags should be added to bulk read node list (TRUE = include in bulk read node list)
    """
    try:
        for tag in _tags:
            # if(_priorityTags):               
            #     _controller.PRIORITY_TAGS.append(tag)
            # Sort sub-tags to determine paths and add all tags to provider node list
            sortedTags = writeSortedTagsToCSV(tag, tagListPath)  
            # Add tags to respective node lists
            index = 0
            for sortedTag in sortedTags:
                if not _priorityTags:
                    _controller.STANDARD_NODES.append(addData(sortedTag, _ctrlxDatalayerProvider, _controller))
                if _priorityTags:
                    _controller.PRIORITY_NODES.append(addDataBulk(sortedTag, _ctrlxDatalayerProvider, _controller, _controller.PRIORITY_TAG_LIST,index))
                    _controller.PRIORITY_TAG_NAMES.append(sortedTag[1])
                    _controller.PRIORITY_TAG_TYPES.append(sortedTag[2])
                    index += 1
    except Exception as e:
        myLogger("Failed to sort and provide tags for device: " + _controller.ip + ". Exception: " + repr(e), logging.ERROR, source=__name__)

def provideAllScopeTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _controller:Controller, _config:object, _controllerScope: bool, _priorityTags: bool):
    """
    Provides all program tags to the ctrlX datalayer provider
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _controller: = Controller object containing PLC and EIP client
        :param _config: = PLC program or controller config object from config.json
        :param _controllerScope: = Boolean flag to indicate controller scope (TRUE = controller scope)
        :param _priorityTags: = boolean flag to indicate tags should be added to bulk read node list (TRUE = include in bulk read node list)
    """
    try:
        if _controllerScope:
            tags = _controller.EIP_client.get_tag_list()
        else:            
            tags = _controller.EIP_client.get_tag_list(_config['name'])
        # Tag list here is all top level tags of the program
        sortAndProvideTags(_ctrlxDatalayerProvider, _controller, tags, _priorityTags)
    except Exception as e:
        myLogger("Scope tags for: " + _config['name'] + "of device: " + _controller.ip + " could not be loaded. Exception: " + repr(e), logging.ERROR, source=__name__)

def provideSpecifiedScopeTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _controller:Controller, _config:object, _controllerScope:bool, _priorityTags: bool):
    """
    Provides specified program tags to the ctrlX datalayer provider
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _controller: = Controller object containing PLC and EIP client
        :param _config: = PLC program or controller config object from config.json
        :param _controllerScope: = Boolean flag to indicate controller scope (TRUE = controller scope)
        :param _priorityTags: = boolean flag to indicate tags should be added to bulk read node list (TRUE = include in bulk read node list)
    """
    try:
        # Loop through each tag in the config.json program tags array
        locatedTags = []
        if not _controllerScope:
            tagList = _controller.EIP_client.get_tag_list(_config['name']) # Need to cache tag list for get_tag_info()
        else:
            tagList = _controller.EIP_client.get_tag_list() # Need to cache tag list for get_tag_info()
        for tag in _config['tags']:
            # Format tag path based on controller or program tag type
            if not _controllerScope: 
                tag = "Program:" + _config['name'] + "." + tag
            else:
                tag = tag
            # Get specified tag info from the EIP client
            locatedTag = _controller.EIP_client.get_tag_info(tag)
            # Add tag info to located tags array
            locatedTags.append(locatedTag)
        # Sort and provide all located tags
        sortAndProvideTags(_ctrlxDatalayerProvider, _controller,locatedTags,_priorityTags)
            
    except Exception as e:
        myLogger("Specified program tags for: " + _config['name'] + " of device: " + _controller.ip + " could not be loaded. Exception: " + repr(e), logging.ERROR, source=__name__)

def provideAllDeviceTags(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _controller:Controller):
    """
    Provides all device tags to ctrlx datalayer provider and adds PLC and EIP client to global list          
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _controller: = Controller object containing PLC and EIP client
    """
    try:
        tags = _controller.EIP_client.get_tag_list('*')
        sortAndProvideTags(_ctrlxDatalayerProvider,_controller,tags, False) # When a full device tag set is provided, tags will not be priority
    except Exception as e:
        myLogger("Device tags of device: " + _controller.ip + " could not be loaded. Exception: " + repr(e), logging.ERROR, source=__name__)

def provideNodesByConfig(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider, _configTagType:str):
    """
    Provides standard nodes to the ctrlX datalayer as described in config.json       
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
        :param _configTagType: = tag type configured in config.json (standard tags, priority tags)
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
    for controllerConfig in configData[_configTagType]['controllers']:
        # Check for existing controller at IP address
        controller = checkForExistingController(controllerConfig['ip'])
        # If a controller does not exist at the configured IP, create a new one
        if controller == None:
            controller = Controller(controllerConfig['ip'], controllerConfig['name'])          
        # If tag list exists at controller level, provide specified tags
        if "tags" in controllerConfig:
            provideSpecifiedScopeTags(_ctrlxDatalayerProvider ,controller, controllerConfig, True, priorityTags)
        # If no tag list exists at controller level, provide all controller scoped tags
        else:
            provideAllScopeTags(_ctrlxDatalayerProvider ,controller, controllerConfig, True, priorityTags)
        # Loop through each program in the controller programs array
        for programConfig in controllerConfig['programs']:
            # If a tag list exists in the program, provide specified tags
            if "tags" in programConfig:
                provideSpecifiedScopeTags(_ctrlxDatalayerProvider ,controller, programConfig, False, priorityTags)                         
            # If no tag list exists in the program, provide all program scoped tags
            else:
                provideAllScopeTags(_ctrlxDatalayerProvider,controller, programConfig, False, priorityTags)

def checkForExistingController(_ipAddress:str) -> typing.Optional[Controller]:
    """
    Checks for existing controller at IP address and returns it if found
        :param _ipAddress: = IP address of controller
        :return controller: = Existing controller object matching IP address
    """ 
    #  Check for existing controller at configured IP address     
    for existingController in CONTROLLER_LIST:
        if existingController.ip == _ipAddress:
            controller = existingController
            return controller
    return None

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
            # Provide all device tags for each discovered device
            provideAllDeviceTags(_ctrlxDatalayerProvider, device)

def localExecution(_ctrlxDatalayerProvider:ctrlxdatalayer.provider.Provider):
    """
    Handles program execution outside of the snap context            
        :param _ctrlxDatalayerProvider: = ctrlX datalayer provider
    """
    print("Running local...")
    try:
        # -------------------------- OPTION 1: NO AUTOSCAN ------------------------------
        if configData['scan'] != True:
            if "standard tags" in configData:
                provideNodesByConfig(_ctrlxDatalayerProvider, 'standard tags')
            if "priority tags" in configData:
                provideNodesByConfig(_ctrlxDatalayerProvider, 'priority tags')
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
            if "standard tags" in configData:
                provideNodesByConfig(_ctrlxDatalayerProvider, 'standard tags')
            if "priority tags" in configData:
                provideNodesByConfig(_ctrlxDatalayerProvider, 'priority tags')
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

            # Create new PLCs... _TODO WHY IS THIS NECESSARY?
            comms =[]
            i = 0
            for controller in CONTROLLER_LIST:
                comms.append(PLC(controller.ip))
                tagData = CONTROLLER_LIST[i].PRIORITY_TAG_NAMES
                tempTagList = comms[i].Read(tagData)
                for tag in tempTagList:
                    CONTROLLER_LIST[i].PRIORITY_TAG_LIST.append(tag)

            # Get the time the files was modified
            fileTime =  os.stat(configPath).st_mtime

            # If active controllers exist, keep running
            if CONTROLLER_LIST is not None:       
                myLogger('INFO Running endless loop...', logging.INFO, source=__name__)
                while ctrlxDatalayerProvider.is_connected():
                    if (fileTime == os.stat(configPath).st_mtime):
                        # Bulkread logic
                        for i in range(len(CONTROLLER_LIST)):
                            if CONTROLLER_LIST[i].PRIORITY_TAG_NAMES != None:
                                try:
                                    # Read using Pycomm3
                                    #controller.EIP_client.read(*controller.PRIORITY_TAGS)
                                    # Read using Pylogix
                                    tempTagList = comms[i].Read(CONTROLLER_LIST[i].PRIORITY_TAG_NAMES)
                                    # Copy temp tags to tag list_TODO WHY IS THIS NECESSARY?
                                    tagIndex = 0
                                    for tag in tempTagList:
                                        CONTROLLER_LIST[i].PRIORITY_TAG_LIST[tagIndex] = tag
                                        tagIndex += 1
                                except Exception as e:
                                    myLogger("Bulk read failed: " + repr(e), logging.ERROR, source=__name__)                      
                    else:
                        fileTime == os.stat(configPath).st_mtime
                        myLogger('ERROR Data Layer Provider is disconnected', logging.ERROR, source=__name__)
                        # CLEANUP
                        for controller in CONTROLLER_LIST:
                            del controller
                        for comm in comms:
                            del comm
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
