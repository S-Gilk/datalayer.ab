import logging
import typing
import pprint
from pathlib import Path
from app.ab_provider_node import ABnode,ABnodeBulk

def tagSorter(dataLayerPath, controllerPath, tag):    
    tagList = []
    if 'dimensions' in tag:
        tag_type = tag['tag_type']
        index = 0
        if tag["dimensions"][0] != 0:
            for x in range(tag["dimensions"][0]):
                if tag_type == 'atomic':
                    dataType = tag['data_type']
                    abTagTuple = (dataLayerPath + '/' + str(index), controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)
                elif tag_type == 'struct' and tag['data_type_name'] != 'STRING':
                    for attribute in tag['data_type']['attributes']:
                        tagTupleList = tagSorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute])
                        for tagTuple in tagTupleList:
                            tagList.append(tagTuple)
                elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath + '/' + str(index), controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)  
                index = index + 1           
        else:
            if tag_type == 'atomic':
                    dataType = tag['data_type']
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)
            elif tag_type == 'struct' and tag['data_type_name'] != 'STRING' :
                for attribute in tag['data_type']['attributes']:
                    tagTupleList = tagSorter(dataLayerPath + "/" + attribute, controllerPath + "." + attribute, tag['data_type']['internal_tags'][attribute])
                    for tagTuple in tagTupleList:
                        tagList.append(tagTuple)
            elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)            
                    
    elif 'array' in tag: 
        tag_type = tag['tag_type']               
        index = 1
        if tag["array"] != 0:
            for x in range(tag["array"]):
                if tag_type == 'atomic':
                    dataType = tag['data_type']
                    abTagTuple = (dataLayerPath + '/' + str(index), controllerPath + '[' + str(index) + ']' , dataType)
                    tagList.append(abTagTuple)
                elif tag_type == 'struct' and tag['data_type_name'] != 'STRING':
                    for attribute in tag['data_type']['attributes']:
                        tagTupleList = tagSorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute])
                        for tagTuple in tagTupleList:
                            tagList.append(tagTuple)
                elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath + '/' + str(index), controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)         
                index = index + 1        
        else:
            if tag_type == 'atomic':
                    dataType = tag['data_type']
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)
            elif tag_type == 'struct'and tag['data_type_name'] != 'STRING':
                for attribute in tag['data_type']['attributes']:
                    tagTupleList = tagSorter(dataLayerPath + "/" + attribute,  controllerPath + '.' + attribute, tag['data_type']['internal_tags'][attribute])
                    for tagTuple in tagTupleList:
                        tagList.append(tagTuple)
            elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)                     
    if 'bit' in tag:
        tag_type = tag['tag_type']               
        if tag_type == 'atomic':
                dataType = tag['data_type']
                abTagTuple = (dataLayerPath, controllerPath, dataType)
                tagList.append(abTagTuple)
    return tagList

def writeSortedTagsToCSV(_tag:object, _tagListPath:str) -> typing.List:
    """
    Wrapper for Sorter function which writes out tag list to csv
        :param _tag: = Tag object from EIP_client get_tag_info()
        :param _tagListPath: = File path to tag list csv
        :return _EIP_client: = LogixDriver
    """
    abList = tagSorter(_tag['tag_name'], _tag['tag_name'], _tag)  
    File_object = open(Path(_tagListPath), "w+") 
    fileString = pprint.pformat(abList)
    File_object.write(fileString)
    File_object.close()
    return abList

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

def addData(_tag, _ctrlxDatalayerProvider, _controller):
    corePath = _tag[0]
    myLogger('adding tag: ' + _tag[0], logging.INFO, source=__name__)
    if corePath.find("Program:") != -1:
        corePath = corePath.replace("Program:", "")
        pathSplit = corePath.split(".")
        ABNode = ABnode(_ctrlxDatalayerProvider,
                        _tag[1],
                        _controller.plc,
                        _tag[2],
                        _controller.EIP_client.info["product_name"].replace("/", "--").replace(" ","_") + "/" + _controller.ip + "/" + pathSplit[0] + "/" + pathSplit[1])
    else:
        ABNode = ABnode(_ctrlxDatalayerProvider,
                        _tag[1],
                        _controller.plc,
                        _tag[2],
                        _controller.EIP_client.info["product_name"].replace("/", "--").replace(" ","_") + "/" + _controller.ip + "/" + "ControllerTags" + "/" + _tag[0])    
    ABNode.register_node()
    return ABNode

def addDataBulk(_tag, _ctrlxDatalayerProvider, _controller, _tagData:list, _index):
    corePath = _tag[0]
    myLogger('adding tag: ' + _tag[0], logging.INFO, source=__name__)
    if corePath.find("Program:") != -1:
        corePath = corePath.replace("Program:", "")
        pathSplit = corePath.split(".")
        ABNode = ABnodeBulk(_ctrlxDatalayerProvider,
                        _tag[1],
                        _controller.plc,
                        _tag[2],
                        _controller.EIP_client.info["product_name"].replace("/", "--").replace(" ","_") + "/" + _controller.ip + "/" + pathSplit[0] + "/" + pathSplit[1], _tagData, _index)
    else:
        ABNode = ABnodeBulk(_ctrlxDatalayerProvider,
                        _tag[1],
                        _controller.plc,
                        _tag[2],
                        _controller.EIP_client.info["product_name"].replace("/", "--").replace(" ","_") + "/" + _controller.ip + "/" + "ControllerTags" + "/" + _tag[0], _tagData, _index)    
    ABNode.register_node()
    return ABNode
