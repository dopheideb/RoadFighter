import string

## We inherit from the 'bytes' object, since the 'bytes' object does not 
## support item assignment, which is what we want here: the ROM mustn't 
## be altered, only examined.
## 
## We also inherit from the bytes object since that object is fully 
## featured, with slicing etc.


class ROM(bytes):
	def __new__(cls, file):
		with open(file, 'rb') as f:
			data = f.read()
		return super(ROM, cls).__new__(cls, data)

	def __init__(self, file):
		pass
	
	def hexdump(self, offset: int, length: int) -> str:
		retval = ''
		i = (offset // 16) * 16
		mod16 = 0
		while True:
			## Always write at least one offset.
			if mod16 == 0:
				retval += f"{i:08x} "
				printable = ''
				spaces = ''
			elif mod16 == 8:
				retval += ' '
			
			if i >= offset + length:
				spaces += ''.join(['   '] * (16 - mod16))
				if mod16 < 8:
					spaces += ' '
				retval += spaces + '  |' + printable + '|\n'
				break
			
			if i < offset:
				retval += ' ..'
				spaces += ' '
			else:
				val = self[i]
				retval += f" {val:02x}"
				
				if val >= 0x20 and val <= 0x7E:
					printable += chr(val)
				else:
					printable += '.'
			
			i += 1
			mod16 += 1
			if mod16 == 16:
				retval += spaces + '  |' + printable + '|\n'
				mod16 = 0
		return retval
	
	def get_byte(self, address):
		return self[address.rom_address()]
	
	def get_bytes(self, address, num):
		lst = []
		for n in range(num):
			lst.append(self.get_byte(address))
			address += 1
		return lst
	
	def get_word(self, address):
		return\
			 self.get_byte(address)\
			+\
			(self.get_byte(address + 1) << 8)
	
	def get_words(self, address, num):
		lst = []
		for n in range(num):
			lst.append(self.get_word(address))
			address += 2
		return lst
