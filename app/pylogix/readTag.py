from pylogix import PLC
from struct import pack, unpack_from, pack_into

comm = PLC()
comm.IPAddress = '192.168.1.90'
#comm.tag
tagList = ['Program:TestProgram.TestRecipe.FormatListScale[5].DATA[9]', 'Program:TestProgram.TestRecipe.RecipeNumber']
lookup = dict()
index = 0
for tag in tagList:
    lookup[tag] = index
    index = index + 1
#ret = (comm.Read('Program:TestProgram.TestRecipe.DataBOOL'))
ret = (comm.Read(tagList))

for tag in ret:
    print(tag.TagName)
    print(tag.Value)
    print(tag.Status)
#ret = (comm.Read('Workfile.Data.RecipeNumber'))
#print(ret.Value)
print(ret[lookup['Program:TestProgram.TestRecipe.RecipeNumber']].Value)

#(comm.Write('Program:MainProgram.Vars.Index_2', 25.0))
#data = unpack_from('<f', ret.Value, 4)
#print(data)
#print(ret.Value)
#buffer = bytearray(ret.Value)
#write_Data = pack_into('<f', buffer, 4, 10.0)
#print(list(buffer))

#comm.Write(ret[0], ret[1])
#print(data)
#print(list(bytes(ret)))
comm.Close()