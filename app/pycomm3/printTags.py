import pprint
from pycomm3 import LogixDriver
from getTags import tagSorter, Sorter



with LogixDriver("192.168.2.90") as plc:

    tags = plc.get_tag_list('Program:TestProgram')
    for tag in tags:
        #pprint.pprint(tag)
        #print('\n')
        #pprint.pprint(tag['tag_name'])
        print('\n')
        pprint.pprint(plc.get_tag_info(tag['tag_name']))
        print('\n')
        #sortedTags = Sorter(tag['tag_name'], tag['tag_name'], plc.get_tag_info(tag['tag_name']))   
        #sortedTags = tagSorter(tag)   
        sortedTags = tagSorter(plc.get_tag_info(tag['tag_name']))   
        for sortedTag in sortedTags:
            pprint.pprint(sortedTag)
    #tag_list = plc.get_tag_info("Workfile.Recipe.Set[1]")
    #File_object = open("DEV/tagList.txt", "w+")
    #fileString = pprint.pformat(tag_list)
    #File_object.write(fileString)
    #File_object.close()