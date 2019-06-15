#!/usr/bin/env python3
import os
import sys
from intelhex import IntelHex

def bytes_length(x):
    return (x.bit_length() + 7) // 8

if (len(sys.argv) < 2):
    print("ERROR: incorrect arguments")
    print("ihex2ascii.py: convert an ihex to human readable memory image")
    print("Usage:")
    print("ihex2ascii.py <ihex>")
    exit()

ihexf = sys.argv[1]

ih = IntelHex()
ih.loadhex(ihexf)
all_sections = ih.segments()
low_addr=all_sections[0][0]
high_addr=all_sections[0][1]
print("input hex file sections:")
for sec in all_sections:
    print("0x%08X 0x%08X"%(sec[0],sec[1]-1))
    low_addr=min(low_addr,sec[0])
    high_addr=max(high_addr,sec[1])

print("low_addr =0x%x"%low_addr)
print("high_addr=0x%x"%high_addr)
size=high_addr-low_addr
if size>1024*1024:
    print("image is larger than 1MB, give up")
    exit(-1)
    
#copy all regular sections
print("%08X: "%(low_addr),end="")
for i in range(low_addr,high_addr):
    print("%02X "%ih[i],end="")
    if 15==(i%16):
        print("")
        print("%08X: "%(i+1),end="")

print("\nstart address: ",ih.start_addr)
