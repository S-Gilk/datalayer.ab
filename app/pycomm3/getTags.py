from pycomm3 import LogixDriver
import pprint


def tagSorter(dataLayerPath, controllerPath, tag):
    tagList = []
    if 'dimensions' in tag:
        print(dataLayerPath)
        print("tag type: " + tag['tag_type'])
        print("dimensions: " + str(tag['dimensions']))
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
                       tagList.append(tagSorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute]))
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
                print(tag['data_type']['attributes'])
                for attribute in tag['data_type']['attributes']:
                    print(attribute)
                    tagList.append(tagSorter(dataLayerPath + "/" + attribute, controllerPath + "." + attribute, tag['data_type']['internal_tags'][attribute])) 
            elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)            
                    
    elif 'array' in tag:
        print(dataLayerPath)  
        print("tag type: " + tag['tag_type'])   
        print("dimensions: " + str(tag['array']))   
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
                       tagList.append(tagSorter(dataLayerPath + "/" + str(index) + '/' + attribute, controllerPath + "[" + str(index) + '].' + attribute, tag['data_type']['internal_tags'][attribute]))
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
                print(tag['data_type']['attributes'])
                for attribute in tag['data_type']['attributes']:
                    print(attribute)
                    tagList.append(tagSorter(dataLayerPath + "/" + attribute,  controllerPath + '.' + attribute, tag['data_type']['internal_tags'][attribute]))
            elif tag_type == 'struct' and tag['data_type_name'] == 'STRING':
                    dataType = 'STRING'
                    abTagTuple = (dataLayerPath, controllerPath, dataType)
                    tagList.append(abTagTuple)                     
    if 'bit' in tag:
        print(dataLayerPath)  
        print("tag type: " + tag['tag_type'])   
        print("dimensions: BOOL") 
        tag_type = tag['tag_type']               
        if tag_type == 'atomic':
                dataType = tag['data_type']
                abTagTuple = (dataLayerPath, controllerPath, dataType)
                tagList.append(abTagTuple)
    return tagList
    
with LogixDriver('192.168.1.90') as plc:
    tag_List = plc.get_tag_list("TestProgram")
    tagList = []
    #print(plc.tags.keys())
    #print(plc.info)
    File_object = open("DEV/tagList.csv", "w+")
    for t in tag_List:
        tagList.append(tagSorter(t['tag_name'], t['tag_name'], t))
    fileString = pprint.pformat(tagList)
    #print(fileString)
    File_object.write(fileString)
    File_object.close()
        #index = t['tag_name'].find("Program:")
        #print(index)
        
        #if t["tag_type"] == "struct": 
        #    print(t["tag_type"])
    #    name = t["tag_name"].split(".")
    #    for n in name:  
    #        print(n) 
        #application = name[1].split(".")
        #for a in application:
        #    print(a)
        #value = (plc.read(t["tag_name"]))
        #print(value[1])
        #print(plc.read(t["tag_name"]))
        #if t["dim"] != 0: 
        #    print(t["dimensions"][0])



def find_attributes():
    with LogixDriver('192.168.1.90') as plc:
        ...  # do nothing, we're just letting the plc initialize the tag list
        tag_List = plc.get_tag_list()
        
        print(tag_List)

