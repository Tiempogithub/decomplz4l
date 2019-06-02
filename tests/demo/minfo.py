#!/usr/bin/env python3
import sys
sys.path.append(prep_path)
from decomplz4l_prep import get_section_from_elf
import os

#comp_storage: where we store the compressed data
#the compressed area starts or end with a mapping table
#it indicates the start address of the compressed data for each section
comp_storage={'start':0x02000000,'end':0x02000FFF}

#grow_up:
#- if true comp_storage is used from start address and up, compressed area starts with map
#- if false comp_storage is used from end and down, compressed area ends with map, map is reversed
grow_up=False

#map_load_size: size in bytes of the load addresses in the mapping table
map_load_size=2
#map_run_size: size in bytes of the run addresses in the mapping table
map_run_size=2

#list of sections to compress
#load: the original load region in the input ihex file, typically it is not in the actual physical memory map
#run: the location at run time
#size: the uncompressed size
comp_sections=[]

script_directory = os.path.dirname(os.path.realpath(__file__))
filepath = os.path.join(script_directory,'demo.elf')

comp_sections.append(get_section_from_elf(filepath,'.memory'))
comp_sections.append(get_section_from_elf(filepath,'.rodata'))
comp_sections.append(get_section_from_elf(filepath,'.data'))
