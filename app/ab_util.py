import logging
import typing
import pprint
import csv
from pathlib import Path
from app.ab_provider_node import ABnode,ABnodeBulk

def tagSorter(_dataLayerPath:str, _controllerPath:str,_tag:object) -> typing.List:
    """
    Sorts top level tag into sub tags.
        :param _tag: = Top level tag object from EIP_client get_tag_info()
        :param _datalayerPath: = Tag path in ctrlX datalayer
        :param _controllerPath: = Tag path on AB controller
        :return tagList: = Tuple list of tags including datalayer path, controller path and type
    """   
    tagList = []

    # If an attribute path is provided, only add tags at specified path

    if 'dimensions' in _tag:
        tag_type = _tag['tag_type']
        index = 0
        if _tag["dimensions"][0] != 0:
            for x in range(_tag["dimensions"][0]):
                if tag_type == 'atomic':
                    dataType = _tag['data_type']
                    abTagTuple = (_dataLayerPath + '/' + str(index), _controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)
                elif tag_type == 'struct' and _tag['data_type_name'] != 'STRING':
                    for attribute in _tag['data_type']['attributes']:
                        tagTupleList = tagSorter(_dataLayerPath + "/" + str(index) + '/' + attribute, _controllerPath + "[" + str(index) + '].' + attribute, _tag['data_type']['internal_tags'][attribute])
                        for tagTuple in tagTupleList:
                            tagList.append(tagTuple)
                elif tag_type == 'struct' and _tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (_dataLayerPath + '/' + str(index), _controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)  
                index = index + 1           
        else:
            if tag_type == 'atomic':
                    dataType = _tag['data_type']
                    abTagTuple = (_dataLayerPath, _controllerPath, dataType)
                    tagList.append(abTagTuple)
            elif tag_type == 'struct' and _tag['data_type_name'] != 'STRING' :
                for attribute in _tag['data_type']['attributes']:
                    tagTupleList = tagSorter(_dataLayerPath + "/" + attribute, _controllerPath + "." + attribute, _tag['data_type']['internal_tags'][attribute])
                    for tagTuple in tagTupleList:
                        tagList.append(tagTuple)
            elif tag_type == 'struct' and _tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (_dataLayerPath, _controllerPath, dataType)
                    tagList.append(abTagTuple)            
                    
    elif 'array' in _tag: 
        tag_type = _tag['tag_type']               
        index = 0
        if _tag["array"] != 0:
            for x in range(_tag["array"]):
                if tag_type == 'atomic':
                    dataType = _tag['data_type']
                    abTagTuple = (_dataLayerPath + '/' + str(index), _controllerPath + '[' + str(index) + ']' , dataType)
                    tagList.append(abTagTuple)
                elif tag_type == 'struct' and _tag['data_type_name'] != 'STRING':
                    for attribute in _tag['data_type']['attributes']:
                        tagTupleList = tagSorter(_dataLayerPath + "/" + str(index) + '/' + attribute, _controllerPath + "[" + str(index) + '].' + attribute, _tag['data_type']['internal_tags'][attribute])
                        for tagTuple in tagTupleList:
                            tagList.append(tagTuple)
                elif tag_type == 'struct' and _tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (_dataLayerPath + '/' + str(index), _controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)         
                index = index + 1        
        else:
            if tag_type == 'atomic':
                    dataType = _tag['data_type']
                    abTagTuple = (_dataLayerPath, _controllerPath, dataType)
                    tagList.append(abTagTuple)
            elif tag_type == 'struct'and _tag['data_type_name'] != 'STRING':
                for attribute in _tag['data_type']['attributes']:
                    tagTupleList = tagSorter(_dataLayerPath + "/" + attribute,  _controllerPath + '.' + attribute, _tag['data_type']['internal_tags'][attribute])
                    for tagTuple in tagTupleList:
                        tagList.append(tagTuple)
            elif tag_type == 'struct' and _tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (_dataLayerPath, _controllerPath, dataType)
                    tagList.append(abTagTuple)                     
    if 'bit' in _tag:
        tag_type = _tag['tag_type']               
        if tag_type == 'atomic':
                dataType = _tag['data_type']
                abTagTuple = (_dataLayerPath, _controllerPath, dataType)
                tagList.append(abTagTuple)
    return tagList

def writeSortedTagsToCSV(_tag:typing.Tuple[object,str], _tagListPath:str) -> typing.List:
    """
    Wrapper for tagSorter function which writes out tag list to csv
        :param _tag: = Tuple containing top level tag object from EIP_client get_tag_info() and tag path in AB controller
        :param _tagListPath: = File path to tag list csv
        :return _EIP_client: = LogixDriver
    """
    tagObject = _tag[0]

    # If tag name exists, tag object is top level 
    if 'tag_name' in tagObject:
        abList = tagSorter(tagObject['tag_name'], tagObject['tag_name'], tagObject)
    else:
        # Need to change paths here to reflect attributes
        datalayerPath = _tag[1].replace('.','/')
        datalayerPath.replace('[', '/')
        datalayerPath.replace(']','/')
        abList = tagSorter(datalayerPath, _tag[1], tagObject)



    if(Path.exists(Path(_tagListPath))):
        File_object = open(Path(_tagListPath), "a", newline='')
    else:
        File_object = open(Path(_tagListPath), "w+", newline='')

    writer = csv.writer(File_object)
    for line in abList:
        writer.writerow(line)
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
