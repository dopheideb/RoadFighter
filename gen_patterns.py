#!/usr/bin/env python3

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

text_pattern_data_pointers =\
[
    (get_word(0x4776+1), get_word(0x4779+1)),		## 0x478A
    #(get_word(0x48C9+1), get_word(0x48CC+1)),
    #(get_word(0x49B1+1), get_word(0x49B4+1)),
    #(get_word(0x68AA+1), get_word(0x68AD+1)),
    #(get_word(0x68BF+1), get_word(0x68BC+1)),
    #(get_word(0x68DC+1), get_word(0x68D9+1)),
    #(get_word(0x68E5+1), get_word(0x68E2+1)),
    #(get_word(0x690B+1), get_word(0x6908+1)),
    #(get_word(0x698C+1), get_word(0x698F+1)),
    #(get_word(0x6995+1), get_word(0x6998+1)),
    #(get_word(0x69B2+1), get_word(0x69B5+1)),
    #(get_word(0x69D8+1), get_word(0x69DB+1)),
    ## Stages
        #(get_word(0x6A51+0*4), get_word(0x6A40+1)),	## Stage 1
        #(get_word(0x6A51+1*4), get_word(0x6A40+1)),	## Stage 2
        #(get_word(0x6A51+2*4), get_word(0x6A40+1)),	## Stage 3
        #(get_word(0x6A51+3*4), get_word(0x6A40+1)),	## Stage 4
        #(get_word(0x6A51+4*4), get_word(0x6A40+1)),	## Stage 5
        #(get_word(0x6A51+5*4), get_word(0x6A40+1)),	## Stage 6
    #(get_word(0x744F+1), get_word(0x744C+1)),
]

color_pattern_data_pointers =\
[
    (get_word(0x68B3+1), get_word(0x68B6+1)),
    (get_word(0x68C8+1), get_word(0x68C5+1)),
    (get_word(0x68DC+1), get_word(0x68D9+1)),
    (get_word(0x68EE+1), get_word(0x68EB+1)),
    (get_word(0x6902+1), get_word(0x68FF+1)),
    (get_word(0x6914+1), get_word(0x6911+1)),
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
def print_text_or_color_pattern_data_pointer(pattern_data_pointer, is_text):
    (addr, dest) = pattern_data_pointer
    dest &= 0x3FFF	## Seen 0x6200 at 0x46cc
    
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
        
        hi_nybble = byte >> 8
        lo_nybble = byte & 0x0F
        
        decoded = ''
        decoded += f'0x{hi_nybble:x}={colornum2name[hi_nybble]:12s}'
        decoded += ', '
        decoded += f'0x{lo_nybble:x}={colornum2name[lo_nybble]:12s}'
        
        return decoded
    decode_fun = decode_data_byte_as_pattern if is_text else decode_data_byte_as_color
    
    print(f"; {'Patterns' if is_text else 'Colors'}, seen at 0x{pattern_data_pointer[0]:04x}.")
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
            print(f'{prefix} Copy next byte 0x{num_copy:02X} times.')
            data_byte = get_byte(addr)
            decoded = decode_fun(data_byte)
            
            for n in range(num_copy):
                if n == 0:
                    prefix = prefix_template.format(data_byte, addr)
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
            print(f'{prefix} Copy next 0x{num_copy:02X} bytes.')
            
            for n in range(num_copy):
                data_byte = get_byte(addr)
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
        print_text_or_color_pattern_data_pointer(addr, is_text=False)

def print_text_pattern_data_pointers(text_pattern_data_pointers):
    for addr in text_pattern_data_pointers:
        print_text_or_color_pattern_data_pointer(addr, is_text=True)




if __name__ == '__main__':
    print_text_pattern_data_pointers(text_pattern_data_pointers)
    #print_color_pattern_data_pointers(color_pattern_data_pointers)
