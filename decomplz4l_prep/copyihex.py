#!/usr/bin/env python3
import os
import sys
from intelhex import IntelHex

if (len(sys.argv) < 3):
    print("ERROR: incorrect arguments")
    print("copyihex.py: copy ihex")
    print("Usage:")
    print("copyihex.py <ihex> <ihex out>")
    exit()

ihexf = sys.argv[1]
ohexf = sys.argv[2]

ih = IntelHex()
iho = IntelHex()
ih.loadhex(ihexf)
all_sections = ih.segments()
print("input hex file sections:")
for sec in all_sections:
    print("0x%08X 0x%08X"%(sec[0],sec[1]-1))

#copy all regular sections
for sec in all_sections:
    for i in range(sec[0],sec[1]):
        iho[i]=ih[i]

#copy start address
#print("start address: ",ih.start_addr)
iho.start_addr = ih.start_addr
            
iho.write_hex_file(ohexf)
