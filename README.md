
# decomplz4l
Generic framework for compressed firmware on embedded devices

## Overview
This repository contains python3 scripts to compress selected sections of an
intel-hex file. The inc folder contains a c99 compliant decompressor suitable
for use on embedded devices. A look-up table allows to manage several compressed
sections (which can be overlayed or not).

### Compression method
The compression method is the [LZ4](https://lz4.github.io/lz4/) "legacy" mode, i.e. what you get with "lz4 -9 -l".
We use the "legacy" mode because it is the most suitable for decompression on
embedded devices.

### Inputs

* An intel-hex file
* A python file defining the following:
    * The compressed storage area:
        * start address
        * end address
    * List of sections to compress. For each section:
        * start address in the intel-hex file
        * start address at run time, i.e. after decompression
        * size in bytes
    * Output format:
        * Filling strategy of the compressed storage area (growing upwards or growing downwards)
        * Size of addresses in the map of the compressed area

### Output
An intel-hex file with the compressed storage area and without the selected sections

### Usage
At build time:
- Compile the entire firmware without memory size constraints. The firmware shall
already include the decompressor code and calls to it.
- Identify the code sections which need to be compressed to fit in the memory
- Place the code to compress in dedicated sections using \_\_attribute\_\_ and/or linker script magic. Store those sections in an address range which does not exist on the target device
- Compile again: you get the "input hex-file"
- Define the desired output image in a Python3 script following the template in tests/demo/minfo.py. This file extract various information from the elf file, this is not mandatory, the only thing which matters is the content of the global variables at the end of the script.   
- Run: `decomplz4l_prep/__init__.py <ihex file> <python file>`  
- Optionally you can use the script phyihex.py to create a clean output file which
fully defines the target physical memories.

At run time:
- Call decomplz4l_load_section with the index of the desired section
- Jump into the decompressed code

NOTES:
- The input intel-hex file contains the sections to compress at addresses which typically do not exist on the physical memory of the device. This does not matter because they will be removed from the final image.
- C code, linker script and Python "minfo.py" shall maintain consistency:
    - decomplz4l_size_t (C code) shall be large enough to contain the decompressed size.
    - decomplz4l_map_t.load_offset (C code) shall have the size of Python map_load_size.
    - decomplz4l_map_t.run_offset (C code) shall have the size of Python map_run_size.
    - DECOMPLZ4L_GROW_UP (C code) shall be 0 if Python grow_up is False, or 1 otherwise.
    - DECOMPLZ4L_COMP_BASE and DECOMPLZ4L_COMP_SIZE shall be consistent with Python comp_storage. linker script shall reserve the corresponding memory range.

## Installation
If you use ubuntu, you just need to call the "setup" script. For other platforms
you need to install the dependencies manually.

## Dependencies

### Python3 intelhex
On ubuntu:

    sudo -H pip3 install intelhex

### LZ4 tools
Although the main scripts are in Python3, the compression is done using native
lz4 tool. (Currently lz4 python3 bindings do not support the "legacy" format).
On ubuntu:

    sudo apt-get install liblz4-tool
