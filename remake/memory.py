from typing import Final

#BYTE: Final[int] = 1
#WORD: Final[int] = 2
class Memory:
	def __init__(self, rom: bytes, bios=None) -> None:
		self._bios = bios
		self._rom = rom
		self._ram = bytearray(0x2000)

	def __getitem__(self, key: int|slice) -> bytes | bytearray:
		if isinstance(key, int):
			(mem, offset) = self.unmap(address=key)
			return mem[offset]

		if isinstance(key, slice):
			(mem,      offset_start) = self.unmap(address=key.start)
			(mem_stop, offset_stop)  = self.unmap(address=key.stop)

			if mem is not mem_stop:
				raise IndexError('Mixing RAM and ROM in a slice is not supported.')

			mem_slice = slice(
				offset_start,
				offset_stop,
				key.step
			)
			return mem[mem_slice]

		raise ValueError("Only int and slice are supported arguments.")

	def __setitem__(self, key: int|slice, val) -> None:
		if isinstance(key, int):
			(mem, offset) = self.unmap(address=key)
			mem[offset] = val
			return

		if isinstance(key, slice):
			(mem,      offset_start) = self.unmap(address=key.start)
			(mem_stop, offset_stop)  = self.unmap(address=key.stop)
			if mem is not self._ram:
				raise ValueError("Can't write to ROM.")

			mem_slice = slice(
				offset_start,
				offset_stop,
				key.step
			)
			mem[mem_slice] = val
			return

		raise NotImplementedError

	##
	## Byte
	##
	def get_byte(self, offset: int) -> int:
		'''
		Return a byte from memory as int.

		If you need bytes type, just slice the object.
		'''
		return self[offset]

	def set_byte(self, offset: int, value: int) -> int:
		'''
		Adjust a byte in memory.

		Note: using the [] operator is a more readable way to 
		change a byte.
		'''
		self[offset] = value



	##
	## Char
	##
	def get_char(self, offset: int) -> str:
		'''
		Return a byte from memory as (1 character) str. This is 
		a convenience member, without a setter equivalent.
		'''
		byte = self.get_byte(offset=offset)
		return chr(byte)


	## Word
	def get_word(self, offset: int) -> int:
		'''
		Return a word (=2 bytes) from memory as int. A 'word' in 
		Z80 is read litte endian. So if you read memory b'\dead', 
		you will get integer 0xADDE (44510).
		
		If you need bytes type, just slice the object.
		'''
		lo_byte = self[offset+0]
		hi_byte = self[offset+1]
		return (hi_byte << 8) | lo_byte

	def set_word(self, offset: int, value: int) -> None:
		'''
		Write a little endian word to memory at specified offset.
		'''
		if value < 0 or value > 0xFFFF:
			raise ValueError("Value must be a 16 bit unsigned int value.")

		lo_byte = value & 0xFF
		hi_byte = value >> 8

		## Perhaps we are being paranoid, but splitting we 
		## handle the case of writing to memory mapped I/O, say 
		## to 0xFFFE, as 0xFFFF is not RAM but the subslot 
		## select register.
		(mem_lo_byte, offset_lo_byte) = self.unmap(address=offset+0)
		(mem_hi_byte, offset_hi_byte) = self.unmap(address=offset+1)

		mem_lo_byte[offset_lo_byte] = lo_byte
		mem_hi_byte[offset_hi_byte] = hi_byte

	def unmap(self, address: int) -> tuple:
		'''
		Unmap an offset, returning the actual memory object and 
		the actual offset for said object.

		What does 'unmap' mean here? Reading/writing to memory 
		mapped I/O means that the Z80 has to read/write from 
		BIOS/ROM/RAM/etc, depending on the address. I.e. 
		0x0000-0x3FFF is (almost) always BIOS, 0xE000-0xFFFF is 
		RAM (except for some bytes), and 0x4000-0x5FFF may be 
		mapped to page 0 of the ROM.

		In the latter case, unmap() returns the (whole) ROM 
		object and the address inside the ROM, and memory 
		0x4000-0x5FFF is mapped to addresses 0x0000-0x1FFFF.
		'''
		if address < 0x4000:
			return (self._bios, address)

		if address >= 0xE000:
			return (self._ram, address - 0xE000)

		## FIXME: no support for pages (memory mapper).
		return (self._rom, address - 0x4000)



if __name__ == '__main__':
	import rom

	rf_rom = rom.ROM(file='./RoadFighter.rom')
	mem = Memory(rom=rf_rom)

	## Test the cartridge header in various ways.
	assert  'A' == mem.get_char(offset=0x4000)
	assert b'A' == mem[0x4000:0x4001]
	assert ord('B') == mem.get_byte(offset=0x4001)
	assert 0x4241 == mem.get_word(offset=0x4000)
	assert b'AB' == mem[0x4000:0x4002]

	## Write and read a byte via [] operator.
	mem[0xE000] = ord('C')
	assert mem[0xE000] == ord('C')

	## Test if writing to BIOS is disallowed.
	try:
		mem[0x0000] = 42
	except TypeError as e:
		## If BIOS ROM is not specified, it is None, and trying 
		## to assign to None leads to a TypeError.
		pass
	else:
		raise AssertionError("Shouldn't be able to write to BIOS.")

	## Test if writing to ROM is disallowed.
	try:
		mem[0x4000] = 42
	except TypeError as e:
		pass
	else:
		raise AssertionError("Shouldn't be able to write to ROM.")

	## Write and read a word via [] operator.
	mem[0xE000:0xE002] = bytes('CD', 'utf-8')
	assert b'CD' == mem[0xE000:0xE002]

	## Write and read a word set_word() and get_word().
	mem.set_word(offset=0xE002, value=0x4546)
	assert 0x4546 == mem.get_word(offset=0xE002)
