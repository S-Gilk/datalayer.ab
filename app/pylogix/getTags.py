from pylogix import PLC

with PLC() as comm:
    comm.IPAddress = '192.168.1.90'
    tags = comm.GetTagList('Program:TestProgram.TestRecipe')
    
    for t in tags.Value:
        print(t.TagName, t.DataType)