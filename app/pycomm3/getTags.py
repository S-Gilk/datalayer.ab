from pycomm3 import LogixDriver
import pprint
 

def Sorter(dataLayerPath, controllerPath, tag):    
    tagList = []
    if 'dimensions' in tag:
        #print(dataLayerPath)
        #print("tag type: " + tag['tag_type'])
        #print("dimensions: " + str(tag['dimensions']))
        tag_type = tag['tag_type']
        index = 1
        if tag["dimensions"][0] != 0:
            for x in range(tag["dimensions"][0]):
                if tag_type == 'atomic':
                    dataType = tag['data_type']
                    abTagTuple = (dataLayerPath + '/' + str(index), controllerPath + '[' + str(index) + ']', dataType)
                    tagList.append(abTagTuple)
                elif tag_type == 'struct' and tag['data_type_name'] != 'STRING':
                    for attribute in tag['data_type']['attributes']:
                        #tagList.append(Sorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute]))
                        tagTupleList = Sorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute])
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
                #print(tag['data_type']['attributes'])
                for attribute in tag['data_type']['attributes']:
                    #print(attribute)
                    #tagList.append(Sorter(dataLayerPath + "/" + attribute, controllerPath + "." + attribute, tag['data_type']['internal_tags'][attribute])) 
                    tagTupleList = Sorter(dataLayerPath + "/" + attribute, controllerPath + "." + attribute, tag['data_type']['internal_tags'][attribute])
                    for tagTuple in tagTupleList:
                        tagList.append(tagTuple)
            elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)            
                    
    elif 'array' in tag:
        #print(dataLayerPath)  
        #print("tag type: " + tag['tag_type'])   
        #print("dimensions: " + str(tag['array']))   
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
                        #tagList.append(Sorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute]))
                        tagTupleList = Sorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute])
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
                #print(tag['data_type']['attributes'])
                for attribute in tag['data_type']['attributes']:
                    #print(attribute)
                    tagTupleList = Sorter(dataLayerPath + "/" + attribute,  controllerPath + '.' + attribute, tag['data_type']['internal_tags'][attribute])
                    for tagTuple in tagTupleList:
                        tagList.append(tagTuple)
            elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)                     
    if 'bit' in tag:
        #print(dataLayerPath)  
        #print("tag type: " + tag['tag_type'])   
        #print("dimensions: BOOL") 
        tag_type = tag['tag_type']               
        if tag_type == 'atomic':
                dataType = tag['data_type']
                abTagTuple = (dataLayerPath, controllerPath, dataType)
                tagList.append(abTagTuple)
    return tagList

def tagSorter(tag):
    abList = Sorter(tag['tag_name'], tag['tag_name'], tag)    
    File_object = open("DEV/tagList.csv", "w+")
    fileString = pprint.pformat(abList)
    File_object.write(fileString)
    File_object.close()
    return abList

#with LogixDriver('192.168.2.90') as plc:
#    tag_List = plc.get_tag_list("TestProgram")
#    tagList = []
#    File_object = open("DEV/tagList.csv", "w+")
#    for t in tag_List:
#        tagList.append(tagSorter(t))
#    fileString = pprint.pformat(tagList)
#   File_object.write(fileString)
#    File_object.close()


def find_attributes():
    with LogixDriver('192.168.1.90') as plc:
        ...  # do nothing, we're just letting the plc initialize the tag list
        tag_List = plc.get_tag_list()
        
        print(tag_List)

