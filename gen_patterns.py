#!/usr/bin/env python3

import sys

rom = open('RoadFighter.rom', 'rb').read()

def get_byte(memory_address):
    return rom[memory_address - 0x4000]

def get_word(memory_address):
    return\
    (
        rom[memory_address - 0x4000]
        |
        (rom[memory_address - 0x4000 + 1] << 8)
    )



color_table_base_address = 0x0000
pattern_table_base_address = 0x2000

## Sorted by DE, because that is the order is which the patterns appear 
## in the ROM.
patterns =\
(
    {
        'VRAM_src_location': 0x4776,	## DE = 0x478A
	'VRAM_dst_location': 0x4479,	## HL = 0x2080
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x48C9,	## DE = 0x490F
        'VRAM_dst_location': 0x48CC,	## HL = 0x2200
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x49B1,	## DE = 0x4A25
        'VRAM_dst_location': 0x49B4,	## HL = 0x2600
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x68AA,	## DE = 0x5DEC
        'VRAM_dst_location': 0x68AD,	## HL = 0x2200
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x68B3,	## DE = 0x5F25
        'VRAM_dst_location': 0x68B6,	## HL = 0x0200
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x68BF,	## DE = 0x5FEC
        'VRAM_dst_location': 0x68BC,	## HL = 0x2680
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x68E5,	## DE = 0x5FF7
        'VRAM_dst_location': 0x68E2,	## HL = 0x26C8
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x690B,	## DE = 0x6008
        'VRAM_dst_location': 0x6908,	## HL = 0x2748
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x68C8,	## DE = 0x601D
        'VRAM_dst_location': 0x68C5,	## HL = 0x0680
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x68DC,	## DE = 0x601F
        'VRAM_dst_location': 0x68D9,	## HL = 0x06A8
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Seen at both 0x68EE and 0x6902',
        'VRAM_src_location': 0x68EE,	## DE = 0x6022
        'VRAM_dst_location': 0x68EB,	## HL = 0x06C8
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Seen at both 0x68EE and 0x6902',
        'VRAM_src_location': 0x6902,	## DE = 0x6022
        'VRAM_dst_location': 0x68FF,	## HL = 0x0708
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x6914,	## DE = 0x602D-0x603D
        'VRAM_dst_location': 0x6911,	## HL = 0x0748 (chars 0xE9-0xF3)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x6928,	## DE = 0x6031-0x603D
        'VRAM_dst_location': 0x6925,	## HL = 0x0798 (chars 0xF3-0xFA)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 1 specific patterns',
        'VRAM_src_location': 0x6A51,	## DE = 0x603E-0x61C7
        'VRAM_dst_location': 0x6A40,	## HL = 0x2400 (chars 0x80-0xBD)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 1 specific colors',
        'VRAM_src_location': 0x6A53,	## DE = 0x61C8-0x6278
        'VRAM_dst_location': 0x6A4B,	## HL = 0x0400 (chars 0x80-0xBD)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 2 specific patterns',
        'VRAM_src_location': 0x6A55,	## DE = 0x6279-0x63AB
        'VRAM_dst_location': 0x6A40,	## HL = 0x2400 (chars 0x80-0xB0)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 2 specific colors',
        'VRAM_src_location': 0x6A57,	## DE = 0x6431-0x64C9
        'VRAM_dst_location': 0x6A4B,	## HL = 0x0400 (chars 0x80-0xC8)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Seen at both 0x698C and 0x6995',
        'VRAM_src_location': 0x698C,	## DE = 0x63AC-0x6430
        'VRAM_dst_location': 0x698F,	## HL = 0x2588 (chars 0xB1-0xC8)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Seen at both 0x698C and 0x6995',
        'VRAM_src_location': 0x6995,	## DE = 0x63AC-0x6430
        'VRAM_dst_location': 0x6998,	## HL = 0x2400 (chars 0x80-0x97)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 3 specific patterns',
        'VRAM_src_location': 0x6A59,	## DE = 0x64CA-0x65D6
        'VRAM_dst_location': 0x6A40,	## HL = 0x2400 (chars 0x80-0xAB)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 3 specific colors',
        'VRAM_src_location': 0x6A5B,	## DE = 0x65D7-0x6644
        'VRAM_dst_location': 0x6A4B,	## HL = 0x0400 (chars 0x80-0xAB)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x69B2,	## DE = 0x6645-0x6696
        'VRAM_dst_location': 0x69B5,	## HL = 0x2400 (chars 0x80-0x8C)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 4+5 specific patterns, and 0x69B2',
        'VRAM_src_location': 0x6A5D,	## DE = 0x6645-0x6696, same as stage 5
        'VRAM_dst_location': 0x6A40,	## HL = 0x2400 (chars 0x80-0x8C)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 4+5 specific patterns, and 0x69B2',
        'VRAM_src_location': 0x6A61,	## DE = 0x6645-0x6696, same as stage 4
        'VRAM_dst_location': 0x6A40,	## HL = 0x2400 (chars 0x80-0x8C)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x69D8,	## DE = 0x6697-0x6736
        'VRAM_dst_location': 0x69DB,	## HL = 0x24D0 (chars 0x9A-0xB0)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Seen at both 0x69C6 and 0x69CF',
        'VRAM_src_location': 0x69C6,	## DE = 0x6737-0x675D
        'VRAM_dst_location': 0x69C9,	## HL = 0x0400 (chars 0x80-0x8C)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Seen at both 0x69C6 and 0x69CF',
        'VRAM_src_location': 0x69CF,	## DE = 0x6737-0x675D
        'VRAM_dst_location': 0x69D2,	## HL = 0x0468 (chars 0x8D-0x99)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x69E1,	## DE = 0x675E-0x67C1
        'VRAM_dst_location': 0x69E4,	## HL = 0x03D0 (chars 0x9A-0xB0)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x69A9,	## DE = 0x67C2-0x67D4
        'VRAM_dst_location': 0x69AC,	## HL = 0x0588 (chars 0xB1-0xC8)
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 6 specific patterns',
        'VRAM_src_location': 0x6A65,	## DE = 0x67D5-0x6884
        'VRAM_dst_location': 0x6A40,	## HL = 0x2400 (chars 0x80-0x98)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'description': 'Stage 6 specific colors',
        'VRAM_src_location': 0x6A67,	## DE = 0x6885-0x68A9
        'VRAM_dst_location': 0x6A4B,	## HL = 0x0400 (chars 0x80-0x98)
        'VRAM_src_offset': 0,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x744F,		## DE = 0x74BC
        'VRAM_dst_location': 0x744C,		## HL = 0x2400
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
    {
        'VRAM_src_location': 0x7458,		## DE = 0x7638
        'VRAM_dst_location': 0x7455,		## HL = 0x0400
        'VRAM_src_offset': 1,
        'VRAM_dst_offset': 1,
    },
)

color_pattern_data_pointers =\
[
    (get_word(0x6902+1), get_word(0x68FF+1)),
    (get_word(0x6928+1), get_word(0x6925+1)),
    (get_word(0x69A9+1), get_word(0x69AC+1)),
    (get_word(0x69C6+1), get_word(0x69C9+1)),
    (get_word(0x69CF+1), get_word(0x69D2+1)),
    (get_word(0x69E1+1), get_word(0x69E4+1)),
    ## Stages
        (get_word(0x6A51+0*4+2), get_word(0x6A4B+1)),	## Stage 1
        (get_word(0x6A51+1*4+2), get_word(0x6A4B+1)),	## Stage 2
        (get_word(0x6A51+2*4+2), get_word(0x6A4B+1)),	## Stage 3
        (get_word(0x6A51+3*4+2), get_word(0x6A4B+1)),	## Stage 4
        (get_word(0x6A51+4*4+2), get_word(0x6A4B+1)),	## Stage 5
        (get_word(0x6A51+5*4+2), get_word(0x6A4B+1)),	## Stage 6
    (get_word(0x7458+1), get_word(0x7455+1)),
]



'''Implements Road Fighter routine 0x4611.'''
def print_text_or_color_pattern_data_pointer(pattern_data_pointer):
    (addr, dest) = pattern_data_pointer
    
    ## Seen 0x6200 at 0x46cc. 0x6200 is outside VRAM. BIOS call SETWRT 
    ## uses mask 0x3FFFF. Do the same.
    dest &= 0x3FFF
    
    is_text = dest >= 0x2000
    vram_offset = pattern_table_base_address if is_text else color_table_base_address
    
    def decode_data_byte_as_pattern(byte):
        items = []
        for i in range(8):
            items += 'x' if byte & (1 << (7-i)) else '.'
        decoded = ' '.join(items)
        return decoded
    
    
    
    def decode_data_byte_as_color(byte):
        colornum2name =\
        {
            0x0: 'transparent',
            0x1: 'black',
            0x2: 'medium green',
            0x3: 'light green',
            0x4: 'dark blue',
            0x5: 'light blue',
            0x6: 'dark red',
            0x7: 'cyan',
            0x8: 'medium red',
            0x9: 'light red',
            0xA: 'dark yellow',
            0xB: 'light yellow',
            0xC: 'dark green',
            0xD: 'magenta',
            0xE: 'gray',
            0xF: 'white',
        }
        
        hi_nybble = byte >> 4
        lo_nybble = byte & 0x0F
        
        decoded = ''
        decoded += f'0x{hi_nybble:x}={colornum2name[hi_nybble]:12s}'
        decoded += ', '
        decoded += f'0x{lo_nybble:x}={colornum2name[lo_nybble]:12s}'
        
        return decoded
    decode_fun = decode_data_byte_as_pattern if is_text else decode_data_byte_as_color
    
    data_lines_generated = 0
    while True:
        prefix_template = '\tdefb 0x{:02X}\t\t;{:04x}'
        
        opcode = get_byte(addr)
        prefix = prefix_template.format(opcode, addr)
        addr += 1
        
        if opcode == 0x00:
            print(f'{prefix} END. Start was at 0x{pattern_data_pointer[0]:04X}.')
            return
        
        if opcode <= 0x7F:
            num_copy = opcode
            #print(f'{prefix} Copy next byte 0x{num_copy:02X} times.')
            data_byte = get_byte(addr)
            decoded = decode_fun(data_byte)
            
            for n in range(num_copy):
                if n == 0:
                    opcode_addr = addr - 1
                    prefix = '\tdefb 0x{:02X}, 0x{:02X}\t\t;{:04x}'.format(opcode, data_byte, opcode_addr)
                else:
                    prefix = '\t\t\t\t;{:04x}'.format(addr)
                
                suffix = ''
                if data_lines_generated % 8 == 0:
                    char_num = ((dest - vram_offset) + data_lines_generated) // 8
                    suffix = f' Character 0x{char_num:02x}.'
                print(f'{prefix} {decoded}   {n + 1:02x}{suffix}')
                
                data_lines_generated += 1
                if data_lines_generated % 8 == 0:
                    print()
            
            addr += 1
            
            
            continue
        
        
        
        if opcode == 0x80:
            new_vram_address = get_word(addr)
            addr += 2
            print(f'{prefix} HL = 0x{new_vram_address:04X}')
            raise NotImplementedError
            continue
        
        
        
        if opcode >= 0x81:
            num_copy = opcode & 0x7f
            #print(f'{prefix} Copy next 0x{num_copy:02X} bytes.')
            
            for n in range(num_copy):
                data_byte = get_byte(addr)
                if n == 0:
                    opcode_addr = addr - 1
                    prefix = '\tdefb 0x{:02X}, 0x{:02X}\t\t;{:04x}'.format(opcode, data_byte, opcode_addr)
                else:
                    prefix = prefix_template.format(data_byte, addr)
                
                if addr == 0x5f24:
                    print(f'{prefix} FORCED END, DUE TO SUSPECTED BUG (0x5F06 should be 0x9D instead of 0xBD.')
                    return
		
                addr += 1
                
                suffix = ''
                if data_lines_generated % 8 == 0:
                    char_num = ((dest - vram_offset) + data_lines_generated) // 8
                    suffix = f' Character 0x{char_num:02x}.'
                decoded = decode_fun(data_byte)
                print(f'{prefix} {decoded}   {n + 1:02x}{suffix:s}')
                
                data_lines_generated += 1
                if data_lines_generated % 8 == 0:
                    print()
                
            continue

def print_color_pattern_data_pointers(color_pattern_data_pointers):
    for addr in color_pattern_data_pointers:
        ## Why +1? Since the first byte is for the opcode (LD).
        DE = get_word(addr[0]+1)
        HL = get_word(addr[1]+1)
        print(f"; Compressed color data, seen at 0x{addr[0]:04X}.")
        print_text_or_color_pattern_data_pointer(addr, is_text=False)

def print_text_pattern_data_pointers(text_pattern_data_pointers):
    for VRAM in text_pattern_data_pointers:
        DE = get_word(VRAM['VRAM_src_location'] + VRAM['VRAM_src_offset'])
        HL = get_word(VRAM['VRAM_dst_location'] + VRAM['VRAM_dst_offset'])
        print(f"; Compressed pattern data, seen at 0x{VRAM['VRAM_src_location']:04X}.")
        if 'description' in VRAM:
            print(f"; ")
            print(f"; {VRAM['description']}")
        print_text_or_color_pattern_data_pointer((DE, HL), is_text=True)

def print_patterns(patterns):
    for VRAM in patterns:
        DE = get_word(VRAM['VRAM_src_location'] + VRAM['VRAM_src_offset'])
        HL = get_word(VRAM['VRAM_dst_location'] + VRAM['VRAM_dst_offset'])
        is_text = HL >= 0x2000

        print(f"; Compressed {'pattern' if is_text else 'color'} data, seen at 0x{VRAM['VRAM_src_location']:04X}.")
        if 'description' in VRAM:
            print(f"; ")
            print(f"; {VRAM['description']}")
        print_text_or_color_pattern_data_pointer((DE, HL))




if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_patterns(patterns)
    else:
        wanted = int(sys.argv[1], base=0)
        for pattern in patterns:
            if wanted in (
                pattern['VRAM_src_location'],
                get_word(pattern['VRAM_src_location'] + pattern['VRAM_src_offset'])
            ):
                print_patterns((pattern, ))
