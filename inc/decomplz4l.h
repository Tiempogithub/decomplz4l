#ifndef __DECOMPLZ4L_H__
#include <stdint.h>

//Option configuration items

#ifndef DECOMPLZ4L_CUSTOM_SIZE_T
typedef unsigned int decomplz4l_size_t;
#endif

#ifndef DECOMPLZ4L_CUSTOME_MAP_T
typedef struct decomplz4l_map_struct_t{
    unsigned int load_offset;
    unsigned int run_offset;
} decomplz4l_map_t;
#endif

#ifndef DECOMPLZ4L_COMP_BASE
#define DECOMPLZ4L_COMP_BASE 0
#endif

#ifndef DECOMPLZ4L_GROW_UP
#define DECOMPLZ4L_GROW_UP 1
#endif

#ifndef DECOMPLZ4L_COMP_SIZE
#if 0==DECOMPLZ4L_GROW_UP
    #error "DECOMPLZ4L_GROW_UP=0, DECOMPLZ4L_COMP_SIZE must be defined"
#endif
#endif

#ifndef DECOMPLZ4L_RUN_BASE
#define DECOMPLZ4L_RUN_BASE 0
#endif

#ifndef DECOMPLZ4L_CUSTOM_ERROR_HANDLER
static void decomplz4l_error_handler(void){
    while(1);
}
#endif

//functions

//decompress lz4 "legacy" format .i.e. without any optional part
//src shall not include the magic bytes
static decomplz4l_size_t decomplz4l(void*dst,const void*const src){
    const uint8_t* in=(const uint8_t*)src;
    //uint8_t* out=(uint8_t*)dst;
    // contains the latest decoded data
    uint8_t* history=(uint8_t*)dst;//TODO: replace history[pos++] with (*out++)
    // next free position in history[]
    decomplz4l_size_t  pos = 0;
    // parse all blocks until blockSize == 0
    while (1){
        // block size
        decomplz4l_size_t blockSize = (*in++);
        blockSize |= ((decomplz4l_size_t)(*in++)) <<  8;
        blockSize |= ((decomplz4l_size_t)(*in++)) << 16;
        blockSize |= ((decomplz4l_size_t)(*in++)) << 24;
        // stop after last block
        if (blockSize == 0) break;
        // decompress block
        decomplz4l_size_t blockOffset = 0;
        decomplz4l_size_t numWritten  = 0;
        while (blockOffset < blockSize){
            // get a token
            uint8_t token = (*in++);
            blockOffset++;
            // determine number of literals
            unsigned int numLiterals = token >> 4;
            if (numLiterals == 15){
                // number of literals length encoded in more than 1 byte
                uint8_t current;
                do{
                    current = (*in++);
                    numLiterals += current;
                    blockOffset++;
                } while (current == 255);
            }
            blockOffset += numLiterals;
            // fast loop
            while (numLiterals-- > 0) history[pos++] = (*in++);
            // last token has only literals
            if (blockOffset == blockSize) break;
            // match distance is encoded in two bytes (little endian)
            uint16_t delta = (*in++);
            delta |= ((uint16_t)(*in++)) << 8;
            // zero isn't allowed
            if (delta == 0) {
                //error("invalid offset");
                decomplz4l_error_handler();
            }
            blockOffset += 2;
            // match length (always >= 4, therefore length is stored minus 4)
            unsigned int matchLength = 4 + (token & 0x0F);
            if (matchLength == 4 + 0x0F) {
                uint8_t current;
                do {// match length encoded in more than 1 byte
                    current = (*in++);
                    matchLength += current;
                    blockOffset++;
                } while (current == 255);
            }
            // copy match
            decomplz4l_size_t referencePos = pos - delta;
            // read/write continuous block (no wrap-around at the end of history[])
            while (matchLength-- > 0)
            history[pos++] = history[referencePos++];
        }
        // all legacy blocks must be completely filled - except for the last one
        if (numWritten + pos < 8*1024*1024)
        break;
    }
    return pos;
    //return out-(uint8_t*)dst;
}

//load a compressed section at the correct run address
static void decomplz4l_load_section(unsigned int index){
    uint8_t*load_address = DECOMPLZ4L_COMP_BASE;
    uint8_t*run_address = DECOMPLZ4L_RUN_BASE;
    #if DECOMPLZ4L_GROW_UP
    const decomplz4l_map_t*const map = (const decomplz4l_map_t*const)(DECOMPLZ4L_COMP_BASE+index*sizeof(decomplz4l_map_t));
    #else
    const decomplz4l_map_t*const map = (const decomplz4l_map_t*const)(DECOMPLZ4L_COMP_BASE+DECOMPLZ4L_COMP_SIZE-index*sizeof(decomplz4l_map_t));
    #endif
    load_address+=map->load_offset;
    run_address+=map->run_offset;
    decomplz4l(run_address,load_address);
}
#endif
