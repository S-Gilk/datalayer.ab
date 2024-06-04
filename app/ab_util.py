import logging
import typing
import pprint
import csv
import re
from pathlib import Path
from app.ab_provider_node import ABnode,ABnodeBulk

def tagSorter(_datalayerPath:str, _controllerPath:str,_tag:object) -> typing.List:
    """
    Sorts top level tag into sub tags.
        :param _tag: = Top level tag object from EIP_client get_tag_info()
        :param _datalayerPath: = Tag path in ctrlX datalayer
        :param _controllerPath: = Tag path on AB controller
        :return tagList: = Tuple list of tags including datalayer path, controller path and type
    """   
    tagList = []

    # Search for array index in datalayer path
    res = re.findall(r'\[.*?\]', _datalayerPath)
    i = ''
    if res != []:
        i = str(res[0]).replace('[','')
        i = i.replace(']','')
        # By the time this is called, there should be only one array value in brackets
        if len(res) > 1:
            myLogger("Failed parsing assertion. Too many brackets in datalayer path.", logging.WARNING, source=__name__)
           
    # Reformat datalayer path
    _datalayerPath = _datalayerPath.replace('[', '/')
    _datalayerPath = _datalayerPath.replace(']','/')
    if _datalayerPath.endswith('/'):
        _datalayerPath = _datalayerPath.rstrip('/')

    if 'dimensions' in _tag:
        tag_type = _tag['tag_type']
        index = 0
        if _tag["dimensions"][0] != 0:
            for x in range(_tag["dimensions"][0]):
                tagSortDimensional(tagList, index, _datalayerPath, _controllerPath, _tag) 
                index = index + 1           
        else:
            tagSortNondimensional(tagList,_datalayerPath,_controllerPath,_tag)                               
    elif 'array' in _tag:      
        if i != '':            
            index = int(i)
        else:
            index = 0
        if _tag["array"] != 0:
            # If no index provided, add all array tags
            if index == 0:
                for x in range(_tag["array"]):
                    tagSortDimensional(tagList, index, _datalayerPath, _controllerPath, _tag)
                    index = index + 1
            else:
                # If an array index was provided, only add specified index tags
                tagSortDimensional(tagList,index,_datalayerPath,_controllerPath,_tag, True)
        else:
            tagSortNondimensional(tagList,_datalayerPath,_controllerPath,_tag)                  
    if 'bit' in _tag:
        tagSortBit(_tag, _datalayerPath,_controllerPath, tagList)

    return tagList

def tagSortDimensional(_tagList:list, _index:int, _datalayerPath:str, _controllerPath:str, _tag:object, _specific:bool = False):
    tag_type = _tag['tag_type']   
    if tag_type == 'atomic':
        dataType = _tag['data_type']
        if _specific:
            abTagTuple = (_datalayerPath, _controllerPath, dataType)
        else:
            abTagTuple = (_datalayerPath + '/' + str(_index), _controllerPath + '[' + str(_index) + ']' , dataType)
        _tagList.append(abTagTuple)
    elif tag_type == 'struct' and _tag['data_type_name'] != 'STRING':
        for attribute in _tag['data_type']['attributes']:
            if _specific:
                tagTupleList = tagSorter(_datalayerPath + '/' + attribute, _controllerPath + '.' + attribute, _tag['data_type']['internal_tags'][attribute])
            else:
                tagTupleList = tagSorter(_datalayerPath + "/" + str(_index) + '/' + attribute, _controllerPath + "[" + str(_index) + '].' + attribute, _tag['data_type']['internal_tags'][attribute])
            for tagTuple in tagTupleList:
                _tagList.append(tagTuple)
    elif tag_type == 'struct' and _tag['data_type_name'] == 'STRING':
        dataType = 'STRING'
        if _specific:
            abTagTuple = (_datalayerPath, _controllerPath, dataType)
        else:
            abTagTuple = (_datalayerPath + '/' + str(_index), _controllerPath + '[' + str(_index) + ']', dataType)
        _tagList.append(abTagTuple)

def tagSortNondimensional(_tagList:list, _datalayerPath:str, _controllerPath:str, _tag:object):
    tag_type = _tag['tag_type'] 
    if tag_type == 'atomic':
            dataType = _tag['data_type']
            abTagTuple = (_datalayerPath, _controllerPath, dataType)
            _tagList.append(abTagTuple)
    elif tag_type == 'struct' and _tag['data_type_name'] != 'STRING' :
        for attribute in _tag['data_type']['attributes']:
            tagTupleList = tagSorter(_datalayerPath + "/" + attribute, _controllerPath + "." + attribute, _tag['data_type']['internal_tags'][attribute])
            for tagTuple in tagTupleList:
                _tagList.append(tagTuple)
    elif tag_type == 'struct' and _tag['data_type_name'] == 'STRING':
            dataType = 'STRING'
            abTagTuple = (_datalayerPath, _controllerPath, dataType)
            _tagList.append(abTagTuple)  

def tagSortBit(_tag, _datalayerPath, _controllerPath, _tagList):
    tag_type = _tag['tag_type']               
    if tag_type == 'atomic':
        dataType = _tag['data_type']
        abTagTuple = (_datalayerPath, _controllerPath, dataType)
        _tagList.append(abTagTuple)

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
        # Replace all path array brackets [] with /
        datalayerPath = _tag[1]
        datalayerPath = datalayerPath.replace('[','/')
        datalayerPath = datalayerPath.replace(']','')
        # Replace all path attributes . with /
        datalayerPath = datalayerPath.replace('.','/')
        # If path ends in an array value, provide this to tag sorter
        if _tag[1].endswith(']'):
            start = _tag[1].rindex('[')
            end = _tag[1].rindex(']')
            arrayIndex = _tag[1][start:end+1]
            datalayerPathStart = datalayerPath.rindex('/')
            datalayerPath = datalayerPath[:datalayerPathStart] + arrayIndex

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
