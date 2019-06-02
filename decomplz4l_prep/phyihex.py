#!/usr/bin/env python3
import os
import sys
from intelhex import IntelHex

def bytes_length(x):
    return (x.bit_length() + 7) // 8

if (1==(len(sys.argv)%2 ) | (len(sys.argv) < 4)):
    print("ERROR: incorrect arguments")
    print("phyihex.py: format an ihex to match exactly physical memory map (pad with 0xFF)")
    print("Usage:")
    print("phyihex.py <ihex> <start> <end> [<start> <end>]*")
    exit()

ihexf = sys.argv[1]
sections=[]
for i in range(2,len(sys.argv),2):
    start=int(sys.argv[i],0)
    end=int(sys.argv[i+1],0)
    sections.append([start,end+1])

ih = IntelHex()
iho = IntelHex()
ih.loadhex(ihexf)
all_sections = ih.segments()
print("input hex file sections:")
for sec in all_sections:
    print("0x%08X 0x%08X"%(sec[0],sec[1]-1))

#copy all regular sections
for sec in sections:
    for i in range(sec[0],sec[1]):
        iho[i]=ih[i]

iho.write_hex_file(ihexf+".phy.ihex")

all_sections = iho.segments()
print("output hex file sections:")
for sec in all_sections:
    print("0x%08X 0x%08X"%(sec[0],sec[1]-1))
