import os
import sys
import time
import json
import ctrlxdatalayer
from ctrlxdatalayer.variant import Variant, Result
import pylogix
from pylogix import PLC
import logging
import pycomm3
from pycomm3 import LogixDriver
from helper.ctrlx_datalayer_helper import get_provider
from app.ab_provider_node import ABnode


def myLogger(message, level, source=None):
    if (level > logging.INFO): 
        print(message, flush=True)
    if (source == None):    
        logger = logging.getLogger(__name__)
    else:
        logger = logging.getLogger(source)    
    if (level == logging.INFO):
        logger.info(message)
    elif (level == logging.DEBUG):
        logger.debug(message)
    elif (level == logging.WARNING):
        logger.warning(message)
    elif (level == logging.ERROR):
        logger.error(message)

#struct sorter takes as an argument a structured variable and returns a list of variables with the entire path
def structSorter(structItems):
    abList = []
    #this outer for loop searches all of the variables in the original strucutre
    for key in structItems.keys():
        if 'array' in structItems[key]:
            #if the item is atomic (meaning it is a base type) and not an array it is added to the list
            if structItems[key]['tag_type'] == "atomic" and structItems[key]['array'] == 0:
                datalayerPath = key 
                abPath = key 
                dataType = structItems[key]['data_type']
                abTagTuple = (datalayerPath, abPath, dataType)
                abList.append(abTagTuple)    
            elif structItems[key]['tag_type'] == 'atomic' and structItems[key]['array'] != 0:
                #if the item is atomic (meaning it is a base type) and an array it is added to the list as an array
                dataType = structItems[key]['data_type']
                for x in range(structItems[key]['array']):                    
                    datalayerPath = key + "/" + str(x)
                    tagName = key + "[" + str(x) + "]"
                    abTagTuple = (datalayerPath, tagName, dataType)
                    abList.append(abTagTuple)
            elif structItems[key]['tag_type'] != 'atomic' and structItems[key]['data_type']['name'] == 'STRING':
                #check to to see if the tag is a string
                datalayerPath = key
                datatype = 'STRING' #structItems[key]['data_type_name'] 
                abTagTuple = (datalayerPath, key, datatype)
                abList.append(abTagTuple)                           
            elif structItems[key]['tag_type'] == "struct":
                #if the item is not atomic (meaning it is a structured type) then it needs to be passed to the same function recursively
                name = structItems[key]['data_type']['name'] #capture the base name of the strucute to add to the datalayer path
                sortedStruct = structSorter(structItems[key]["data_type"]["internal_tags"])
                for i in sortedStruct:
                    #updatedPath = (name + "/" + i[0], key + "." + i[1], i[2]) 
                    updatedPath = (key + "/" + i[0], key + "." + i[1], i[2]) 
                    abList.append(updatedPath) #add each object that is returned to the list that the function returns  
        #elif structItems[key]['tag_type'] != 'atomic' and  structItems[key]['data_type_name'] == 'STRING':
        elif structItems[key]['tag_type'] != 'atomic' and structItems[key]['data_type']['name'] == 'STRING':
            #check to to see if the tag is a string
            datalayerPath = key
            datatype = 'string' #structItems[key]['data_type_name'] 
            abTagTuple = (datalayerPath, key, datatype)
            abList.append(abTagTuple)                   
        elif structItems[key]['tag_type'] == "atomic":
            #if the item is atomic (meaning it is a base type) and not an array it is added to the list  
            datalayerPath = key
            dataType = structItems[key]['data_type']
            abTagTuple = (datalayerPath, key, dataType)
            abList.append(abTagTuple)
    return abList #return the list that includes the path on the AB controller and the datalayer and datatype 

def tagSorter(tag):
    abList = []
    if tag['tag_type'] == 'atomic' and tag['dim'] == 0:
        #get the base tag and add it to the master list of tags
        datalayerPath = tag["tag_name"]
        key = tag["tag_name"]
        datatype = tag['data_type']
        abTagTuple = (datalayerPath, key, datatype)
        abList.append(abTagTuple)
    elif tag['tag_type'] == 'atomic' and tag['dim'] != 0:
        #get the base tag and an array add each one to the master list of tags
        for x in range(tag["dimensions"][0]):
            datalayerPath = tag["tag_name"] + "/" + str(x)
            key =  tag['tag_name'] + "[" + str(x) + "]"
            datatype = tag['data_type']
            abTagTuple = (datalayerPath, key, datatype)  
            abList.append(abTagTuple)
    elif tag['tag_type'] != 'atomic' and tag['data_type_name'] == 'STRING':
        #check to to see if the tag is a string
        datalayerPath = tag["tag_name"]
        key = tag['tag_name']
        datatype = tag['data_type_name']
        abTagTuple = (datalayerPath, key, datatype)
        abList.append(abTagTuple)        
    elif tag['tag_type'] != 'atomic':
        #if the tag is a struct, pass it to the struct sorter
        tagName = tag['tag_name']
        newList = structSorter(tag["data_type"]["internal_tags"])
        for i in newList:
            updatedPath = (tagName + "/" + i[0], tagName + "." + i[1], i[2]) 
            abList.append(updatedPath)
    return abList      

def addData(tag, provider, connection, controller):
    corePath = tag[0]
    myLogger('adding tag: ' + tag[0], logging.INFO, source=__name__)
    if corePath.find("Program:") != -1:
        corePath = corePath.replace("Program:", "")
        pathSplit = corePath.split(".")
        abProvider = ABnode(provider, tag[1], connection, tag[2], controller.info["product_name"].replace("/", "--").replace(" ","_") + "/" + connection.IPAddress + "/" + pathSplit[0] + "/" + pathSplit[1])
    else:
        abProvider = ABnode(provider, tag[1], connection, tag[2], controller.info["product_name"].replace("/", "--").replace(" ","_") + "/" + connection.IPAddress + "/" + "ControllerTags" + "/" + tag[0])    
    abProvider.register_node()
    return abProvider