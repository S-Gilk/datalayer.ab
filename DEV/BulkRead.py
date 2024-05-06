from pylogix import PLC
from pycomm3 import LogixDriver
import json
from helper.ctrlx_datalayer_helper import get_provider
import ctrlxdatalayer
from ctrlxdatalayer.variant import Variant, Result
#import app.ab_util


#struct sorter takes as an argument a structured variable and returns a list of variables with the entire path
def structSorter_old(structItems):
    abList = []
    #this outer for loop searches all of the variables in the original strucutre
    for key in structItems.keys():
        #print(key)
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
                datatype = structItems[key]['data_type_name'] 
                abTagTuple = (datalayerPath, key, datatype)
                abList.append(abTagTuple)          
            elif structItems[key]['tag_type'] == "struct":
                #if the item is not atomic (meaning it is a structured type) then it needs to be passed to the same function recursively
                #name = structItems[key]['data_type']['name'] #capture the base name of the strucute to add to the datalayer path
                name = key #capture the base name of the strucute to add to the datalayer path
                print('\n')
                #if 'attributes' in structItems[key]['data_type']:
                print('attributes: ' + str(structItems[key]['data_type']['attributes']))
                print('\n')
                #print('sorting struct ' + str(key))
                #print('\n')
                #print('Struct: \n')
                #print(structItems[key])
                #print(structItems[key])
                #for items in 
                for items in structItems[key]['data_type']['attributes']:
                    print(items)
                    print(structItems[key])
                    name = items
                    #sortedStruct = structSorter(structItems[items]["data_type"]["internal_tags"])
                    sortedStruct = structSorter(structItems[key]["data_type"]["internal_tags"][items])
                    for i in sortedStruct:
                        updatedPath = (name + "/" + i[0], name + "." + i[1], i[2]) 
                        abList.append(updatedPath) #add each object that is returned to the list that the function returns  
        #elif structItems[key]['tag_type'] != 'atomic' and  structItems[key]['data_type_name'] == 'STRING':
        elif structItems[key]['tag_type'] != 'atomic' and structItems[key]['data_type']['name'] == 'STRING':
            #check to to see if the tag is a string
            datalayerPath = key
            datatype = structItems[key]['data_type_name'] 
            abTagTuple = (datalayerPath, key, datatype)
            abList.append(abTagTuple)                   
        elif structItems[key]['tag_type'] == "atomic":
            #if the item is atomic (meaning it is a base type) and not an array it is added to the list  
            datalayerPath = key
            dataType = structItems[key]['data_type']
            abTagTuple = (datalayerPath, key, dataType)
            abList.append(abTagTuple)
    return abList #return the list that includes the path on the AB controller and the datalayer and datatype 

#struct sorter takes as an argument a structured variable and returns a list of variables with the entire path
def structSorter(structItems):
    abList = []
  
    if 'array' in structItems:
        #if the item is atomic (meaning it is a base type) and not an array it is added to the list
        if structItems['tag_type'] == "atomic" and structItems['array'] == 0:
            datalayerPath = '' 
            abPath = '' 
            dataType = structItems['data_type']
            abTagTuple = (datalayerPath, abPath, dataType)
            abList.append(abTagTuple)    
        elif structItems['tag_type'] == 'atomic' and structItems['array'] != 0:
            print('array size: ' + str(structItems['array'])) 
            #if the item is atomic (meaning it is a base type) and an array it is added to the list as an array
            dataType = structItems['data_type']
            for x in range(structItems['array']):                    
                datalayerPath =  str(x)
                tagName =  "[" + str(x) + "]"
                abTagTuple = (datalayerPath, tagName, dataType)
                abList.append(abTagTuple)
        elif structItems['tag_type'] == 'struct' and structItems['data_type']['name'] == 'STRING':
            #check to to see if the tag is a string
            datalayerPath = '' #key
            datatype = 'STRING' #structItems[key]['data_type_name'] 
            abTagTuple = (datalayerPath, '', datatype)
            abList.append(abTagTuple)                           
        elif structItems['tag_type'] == "struct":
            for attribute in structItems["data_type"]['attributes']:
                tagName = attribute
                Path = attribute 
                newList = structSorter(structItems["data_type"]['internal_tags'][attribute])
                for i in newList:
                    if i[0] == '':
                        updatedPath = (tagName, Path, i[2]) 
                    else:
                        updatedPath = (tagName + "/" + i[0], Path + "/" + i[1], i[2]) 
                    abList.append(updatedPath)
    elif structItems['tag_type'] != 'atomic' and structItems['data_type']['name'] == 'STRING':
        #check to to see if the tag is a string
        datalayerPath = ''
        datatype = 'string' #structItems[key]['data_type_name'] 
        abTagTuple = (datalayerPath, '', datatype)
        abList.append(abTagTuple)                   
    elif structItems['tag_type'] == "atomic":
        #if the item is atomic (meaning it is a base type) and not an array it is added to the list  
        datalayerPath = ''
        dataType = structItems['data_type']
        abTagTuple = (datalayerPath, '', dataType)
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
        #print("\n tag: ")
        #print(tag)
        
        
        for attribute in tag["data_type"]['attributes']:
            #print(attribute)
            newList = structSorter(tag["data_type"]['internal_tags'][attribute])
            for i in newList:
                updatedPath = (tagName + "/" + attribute + "/" + i[0], tagName + "." + attribute + "." + i[1], i[2]) 
             #   print(updatedPath)
                abList.append(updatedPath)       
    return abList      

def printTags(tag):
    print(tag)
    #print('base tag: ' + tag['tag_name'] + " :" + tag)
    if tag['tag_type'] == 'struct':      
        for attritbute in (tag['data_type']['attributes']):
            #print(attritbute)
            print('\n' + attritbute )
            print(tag["data_type"]["internal_tags"][attritbute])
            internalTag = tag["data_type"]["internal_tags"][attritbute]
            if 'array' in internalTag:
                print(internalTag['array'])
            if internalTag['tag_type'] == 'struct':
                printTags(internalTag)
    return None

comm = PLC()
comm.IPAddress = '192.168.1.90'
abList = []
with LogixDriver('192.168.1.90') as controller:
    tags = controller.get_tag_list('TestProgram')
    
    for tag in tags: 
        #print(tag['tag_name'])
        #print(tag["data_type"]["internal_tags"])
        #print(tag)
        #print('\n')
        
        #tagSorter(tag)

        for items in tagSorter(tag):
            print(items)
        #printTags(tag)

        #if tag['tag_type'] == 'struct':
        #    for attritbute in (tag['data_type']['attributes']):
        #        print(attritbute)
        #        print(tag["data_type"]["internal_tags"][attritbute])
        
        
            #for key in tag['data_type'].keys():
            #    print(key)
        #ablistFinal = tagSorter(tag)
        #for items in ablistFinal:
            #print(items)
            #print('\n')
        
        #for key in tag.keys():
        #    tag["data_type"]["internal_tags"]
            #if tag[key]['tag_type'] == "struct":
            #    name = tag[key]['data_type']['name']
            #    print(name)