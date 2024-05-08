import pprint
 

def Sorter(dataLayerPath, controllerPath, tag):    
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
                for attribute in tag['data_type']['attributes']:
                    tagTupleList = Sorter(dataLayerPath + "/" + attribute, controllerPath + "." + attribute, tag['data_type']['internal_tags'][attribute])
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
                for attribute in tag['data_type']['attributes']:
                    tagTupleList = Sorter(dataLayerPath + "/" + attribute,  controllerPath + '.' + attribute, tag['data_type']['internal_tags'][attribute])
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

# Wrapper for Sorter function which writes out tag list to csv
def tagSorter(tag):
    abList = Sorter(tag['tag_name'], tag['tag_name'], tag)    
    File_object = open("DEV/tagList.csv", "w+")
    fileString = pprint.pformat(abList)
    File_object.write(fileString)
    File_object.close()
    return abList

