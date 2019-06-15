#!/usr/bin/env python3
import os
import sys
import runpy
from intelhex import IntelHex
#import lz4.frame
import subprocess
import shutil

def get_section_from_elf(elf,section_name):
    objdump = shutil.which('objdump')
    cmd = [ objdump,elf,'-h','--section='+section_name]
    out=""
    res=subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
    out = res.stdout
    fields = out.splitlines()[5].split()
    size=int("0x"+fields[2].decode("utf-8") ,0)
    run=int("0x"+fields[3].decode("utf-8") ,0)
    load=int("0x"+fields[4].decode("utf-8") ,0)
    return {'load':load,'run':run,'size':size}

def bytes_length(x):
    return (x.bit_length() + 7) // 8


if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.realpath(__file__))
    lz4 = os.path.join(script_directory,'lz4')
    if not os.path.isfile(lz4):
        lz4 = shutil.which('lz4')
        assert(lz4 is not None)

    if (len(sys.argv) > 3) | (len(sys.argv) < 3) :
        print("ERROR: incorrect arguments")
        print("Usage:")
        print("prep.py <ihex> <metainfo>")
        exit()

    ihexf = sys.argv[1]
    metainfof = sys.argv[2]

    ih = IntelHex()
    ihgu = IntelHex()
    ih.loadhex(ihexf)
    all_sections = ih.segments()
    print("input hex file sections:")
    for sec in all_sections:
        print("0x%08X 0x%08X"%(sec[0],sec[1]-1))

    file_globals = runpy.run_path(metainfof,init_globals={'prep_path':os.path.dirname(script_directory)})
    comp_storage_start=file_globals["comp_storage"]['start']
    comp_storage_end=file_globals["comp_storage"]['end']
    map_load_size=file_globals["map_load_size"]
    map_run_size=file_globals["map_run_size"]
    grow_up=file_globals["grow_up"]
    comp_sections=file_globals["comp_sections"]
    
    def get_file_global(name,default_value=None):
        if name in file_globals:
            out=file_globals[name]
        else:
            out=default_value
        return out
        
    linear_mode=get_file_global("linear_mode",True)
    start_at_end=get_file_global("start_at_end",False)
    use_seg_as_linear=get_file_global("use_seg_as_linear",False)
    
    print("%d sections to compress"%len(comp_sections))
    for sec in comp_sections:
        print("load: 0x%08X -> 0x%08X, run: 0x%08X -> 0x%08X, size: 0x%X"%(sec['load'],sec['load']+sec['size']-1,sec['run'],sec['run']+sec['size']-1,sec['size']))
    mapsize = (map_load_size+map_run_size)*len(comp_sections)
    map_storage=comp_storage_start
    comp_storage=comp_storage_start+mapsize

    #compress the sections
    for sec in comp_sections:
        #write the start address in the map LUT
        start_offset_bytes = (comp_storage-comp_storage_start).to_bytes(8,byteorder='little')
        for i in range(0,map_load_size):
            ihgu[map_storage] = start_offset_bytes[i]
            map_storage+=1
    
        run_bytes = sec['run'].to_bytes(8,byteorder='little')
        for i in range(0,map_run_size):
            ihgu[map_storage] = run_bytes[i]
            map_storage+=1

        data = ih[sec['load']:sec['load']+sec['size']]
        ba = bytearray()
        for bi in range(sec['load'],sec['load']+sec['size']):
            ba.append(ih[bi])
        newfile=open('lz4_input.bin','wb')
        newfile.write(ba)
        newfile.close()
        cmd = [ lz4,'-9','-l','-f','lz4_input.bin','lz4_output.bin']
        subprocess.run(cmd,check=True)
        size=0
        with open('lz4_output.bin', "rb") as f:
            #skip the frame descriptor
            frame_descriptor = f.read(4)
            byte = f.read(1)
            while byte:
                ihgu[comp_storage] = int.from_bytes( byte, byteorder='little', signed=False )
                comp_storage+=1
                size+=1
                byte = f.read(1)
        sec['comp_size']=size

    if comp_storage>comp_storage_end:
        print("ERROR: compressed storage overflow by %d"%(comp_storage - comp_storage_end))
        exit(1)
    else:
        used = comp_storage - comp_storage_start
        free = comp_storage_end+1-comp_storage
        print("0x%08x bytes used in compressed storage"%(used))
        print("0x%08x bytes free in compressed storage"%(free))

    comp_storage_pad=0
    if grow_up:
        #just rename ihex object
        iho = ihgu
    else:
        #reverse compressed area storage
        iho = IntelHex()
        map_storage=comp_storage_end+1
        #if 0!=(free%16):
        #    comp_storage_pad = free%16
        #    free-=comp_storage_pad
        comp_storage=comp_storage_start+free
        if 0!=(comp_storage%16):
            #add padding data
            for i in range(comp_storage-(comp_storage%16),comp_storage):
                iho[i]=0x55

        #move the compressed data up
        print("copy 0x%X bytes from 0x%08X to 0x%08X"%(used,comp_storage_start+mapsize,comp_storage_start+free))
        for i in range(0,used):
            iho[comp_storage_start+free+i] = ihgu[comp_storage_start+mapsize+i]
        #rebuild map
        for sec in comp_sections:
            sec['load']=comp_storage
            #write the start offset in the map LUT
            map_storage-=map_load_size+map_run_size
            start_offset_bytes = (comp_storage-comp_storage_start).to_bytes(8,byteorder='little')
            for i in range(0,map_load_size):
                iho[map_storage] = start_offset_bytes[i]
                map_storage+=1

            run_bytes = sec['run'].to_bytes(8,byteorder='little')
            for i in range(0,map_run_size):
                iho[map_storage] = run_bytes[i]
                map_storage+=1
            map_storage-=map_load_size+map_run_size
            comp_storage+=sec['comp_size']
            #print("0x%x"%comp_storage)
            #print("0x%x"%map_storage)
        assert(map_storage==comp_storage+comp_storage_pad)

    #create a list of start address of the sections which have been compressed
    print("compressed sections load addresses:")
    comp_sections_start=[]
    for sec in comp_sections:
        print("0x%08X"%sec['load'])
        comp_sections_start.append(sec['load'])

    #copy all regular sections
    for sec in all_sections:
        if (sec[1]<comp_storage_start) or (sec[0]>comp_storage_end):
            for i in range(sec[0],sec[1]):
                iho[i]=ih[i]

    #copy start address
    #print("start address: ",ih.start_addr)
    iho.start_addr = ih.start_addr
    
    if not linear_mode or start_at_end or use_seg_as_linear:
        #need custom version of intelhex, get it here: https://github.com/sebastien-riou/intelhex
        iho.write_hex_file(ihexf+".lz4l.ihex",linear_mode=linear_mode,start_at_end=start_at_end,use_seg_as_linear=use_seg_as_linear)
    else:
        iho.write_hex_file(ihexf+".lz4l.ihex")
