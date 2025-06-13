import numpy as np
import pygame
from typing import Self, Any, List, Union

import sys
np.set_printoptions(threshold=sys.maxsize)



class TMS9918A:
	## Define 1 RGB value to be interpreted as transparent. The 
	## actual values are not important. Use surface.set_key(0) to 
	## map color index 0 to transparent.
	transparent_color = (42,42,42)

	palette_msx1 = (
		transparent_color,	##  0. Transparent
		(  0,   0,   0),	##  1. Black
		( 33, 200,  66),	##  2. Medium green
		( 94, 220, 120),	##  3. Light green
		( 84,  85, 237),	##  4. Dark blue
		(125, 118, 252),	##  5. Light blue
		(212,  82,  77),	##  6. Dark red
		( 66, 235, 245),	##  7. Cyan
		(252,  85,  84),	##  8. Medium red
		(255, 121, 120),	##  9. Light red
		(212, 193,  84),	## 10. Dark yellow
		(230, 206, 128),	## 11. Light yellow
		( 33, 176,  59),	## 12. Dark green
		(201,  91, 186),	## 13. Magenta
		(204, 204, 204),	## 14. Gray
		(255, 255, 255),	## 15. White
	)

	def __init__(self) -> None:
		self._palette = TMS9918A.palette_msx1

		## The screen is 32x24 character. Each character is 8x8.
		self.width  = 32 * 8
		self.height = 24 * 8

		self.clear()

	def clear(self: Self) -> None:
		## The names used are taken from the TMS9918 
		## documentation. Please don't complain.
		## 
		## Because we want to allow low-level operations, just 
		## mimic VRAM and use a 1D array.
		self._vram = np.zeros(16 * 1024, dtype=np.uint8)

		## 8 write-only registers and 1 status register
		self._register = np.zeros(8+1, dtype=np.uint8)
		self._register[0] = 0x02		## M3
		self._register[1] = 0xE2		## BL|IE0|SI
		self._register[2] = 0x0E		## 0x3800 (name table)
		self._register[3] = 0x7F		## 0x0000 (color table)
		self._register[4] = 0x07		## 0x2000 (pattern table)
		self._register[5] = 0x76		## 0x3B00 (sprite attribute table)
		self._register[6] = 0x03		## 0x1800 (sprite pattern (generator) table)
		self._register[7] = 0xE0		## Foreground: gray, background: transparent

	def RDVRM(self: Self, address: int) -> int:
		return self._vram[address]

	def read_vram(self: Self, start: int, num: int) -> np.ndarray[Any, np.dtype[np.uint8]]:
		stop = start + num
		return self._vram[start:stop]

	def write_vram(self: Self, start: int, data: np.ndarray | list[int]) -> None:
		num = len(data)
		self._vram[start:start+num] = data

	def get_colored_character_2D(self: Self, index: int, band=0) -> np.ndarray:
		char_index = 256 * band + index
		return self.get_colored_characters()[char_index]

	def get_colored_characters(self: Self) -> np.ndarray:
		## Note: numpy is slow if we use it for indexing only 
		## and do de math in Python. numpy is bloody fast if we 
		## let numpy do the calculation and make just a few 
		## numpy calls.
		## 
		## I.e,: __vectorize__ our calculations. Old slow code 
		## took 0.117 seconds (!) to generate a mere 768 
		## character, while the following is done in a blink of 
		## an eye.
		patterns = self.get_pgt()
		colors   = self.get_pct()
		fg_colors = colors >> 4		## No masking necessary, since type is np.uint8
		bg_colors = colors & 0xF

		bit_pattern = np.unpackbits(patterns)
		characters = np.where(bit_pattern, np.repeat(fg_colors, 8), np.repeat(bg_colors, 8))
		return characters
	def get_colored_characters_3D(self: Self) -> np.ndarray:
		return self.get_colored_characters().reshape((768, 8, 8))

	def get_colored_character_ansi_utf8(self: Self, num: int) -> List[List[str]]:
		character = []
		vdp_character = self.get_colored_character_2D(num)
		for row in vdp_character:
			ch_row = []
			for color_id in row:
				(r, g, b) = self._palette[color_id]
				ch_row.append(f"\033[38;2;{r};{g};{b}m\u2588\u2588")
			character.append(ch_row)
		return character

	def get_palette(self: Self) -> tuple:
		return self._palette


	##
	## Color
	##
	def get_pct(self: Self) -> np.ndarray:
		start = self.color_table_base_address
		num   = 8 * 3 * 256
		return self.read_vram(start=start, num=num)

	def get_color(self: Self, index: int, band: int=0) -> np.ndarray:
		return self.get_pattern_color(index=index, band=band)
	def get_pattern_color(self: Self, index: int, band: int=0) -> np.ndarray:
		## Every color pattern is 8 bytes.
		elem_size = 8
		band_offset = elem_size * 256 * band
		start = self.color_table_base_address\
			+ band_offset + elem_size * index
		return self.read_vram(start=start, num=8)

	def set_colors(self: Self, index: int, colors: np.ndarray, band: int=0) -> None:
		self.set_pattern_colors(colors=colors, index=index, band=band)
	def set_pattern_colors(self: Self, colors: np.ndarray, index: int, band: int=0) -> None:
		'''
		Set the colors for the pattern with index 'index'.

		The pattern_colors must be an numpy array of size 64, 
		and of type numpy.uint8.

		Each pattern is made up of 8 scanlines of 8 pixels. Each 
		scanline can use 2 colors. Each color is a 4-bit color 
		ID, so 2 colors are 8-bit (i.e. byte/np.uint8).

		Example:
			pattern_colors = numpy.array([0xF1, 0x1F] * 4, dtype=numpy.uint8)

			The scanlines alternate between black+white and 
			white+black.
		'''

		## Every color pattern is 8 bytes.
		elem_size = 8
		band_offset = elem_size * 256 * band
		start = self.color_table_base_address\
			+ band_offset + elem_size * index
		self.write_vram(start=start, data=colors)

	##
	## Name
	##
	def set_names(self: Self, names: np.ndarray, index: int, band: int=0) -> None:
		band_offset = 256 * band
		start = self.name_table_base_address + band_offset + index
		end   = start + len(names)
		self._vram[start:end] = names

	##
	## Pattern
	##
	def get_pattern(self: Self, index: int, band: int=0) -> np.ndarray:
		elem_size = 8
		band_offset = 256 * band
		start = self.pattern_generator_base_address + elem_size * (band_offset + index)
		return self.read_vram(start=start, num=8)

	def get_pattern_2D(self: Self, index: int) -> np.ndarray:
		return np.unpackbits(self.get_pattern(index)).reshape(8, 8)

	def set_pattern(self: Self, pattern: np.ndarray, index: int, band: int=0) -> None:
		return self.set_patterns(patterns=pattern, index=index, band=band)

	def set_patterns(self: Self, patterns: np.ndarray | list[int], index: int, band: int=0) -> None:
		## Every pattern is 8 bytes.
		band_offset = 8 * 256 * band
		start = self.pattern_generator_base_address + band_offset + 8 * index
		self.write_vram(start, patterns)



	def get_pgt(self) -> np.ndarray:
		num_patterns_per_band = 256
		num_bands = 3
		elem_size = 8
		num = elem_size * num_bands * num_patterns_per_band
		start = self.pattern_generator_base_address
		return self.read_vram(start=start, num=num)

	def get_pnt(self) -> np.ndarray:
		start = self.name_table_base_address
		end   = start + 3 * 256
		return self._vram[start:end]

	def make_framebuffer(self: Self, pnt: None|np.ndarray=None) -> np.ndarray:
		if pnt is None:
			pnt = self.get_pnt()
		## The PNT must be 768 element long. Enlarge/shrink.
		pnt.resize(768)

		## Use the pattern name table to know which patterns are 
		## needed and where they are needed. Same for the colors.
		patterns = self.get_pgt().reshape(768, 8)[pnt]
		colors   = self.get_pct().reshape(768, 8)[pnt]

		## Every pattern bit represent a single pixel, 
		## split/unpack every byte into 8 bits.
		fg_bg_pattern = np.unpackbits(patterns)

		## Every color byte consists of 2 nybbles: the high 
		## nybble is the foreground color palette index, the low 
		## nybble is the background color palette index.
		bg_colors = colors & 0x0F
		fg_colors = colors >> 4

		characters = np.where(
			fg_bg_pattern,
			np.repeat(fg_colors, 8),
			np.repeat(bg_colors, 8)
		)
		if not hasattr(self, 'framebuffer_mapping'):
			## Character 0: bytes 0..63
			## Character 1: bytes 64..128
			## Character 2: bytes 128..192
			indices = np.arange(256 * 192, dtype=np.uint16)

			## But the character need to be mapped to the 
			## framebuffer order:
			##
			##   ch00_00..ch00_07, ch01_00..ch01_07, .. ch31_00, ch31_07,
			##   ...
			##   ch00_56..ch07_63, ch01_56..ch01_63, .. ch31_56, ch31_63,
			##   ch32_00..ch32_07, ch33_00..ch33_07, .. ch63_00..ch63_07,
			##   ...
			##   ch32_56..ch32_63, ch33_56..ch33_63, .. ch63_56..ch63_63,
			##   ...

			## Cut into 24 rows. Each row consists of 32 
			## character, Each character is 8 scanlines of 
			## each 8 pixels. Hence: the reshape to (24, 32, 
			## 8, 8).
			##
			## Dimension 0: row
			## Dimension 1: column
			## Dimension 2: scanline
			## Dimension 3: pixel
			## 
			## indices_as_2D_characters[0][ 0] is character 0 as 8x8.
			## indices_as_2D_characters[0][ 1] is character 1 as 8x8.
			## indices_as_2D_characters[0][31] is character 31 as 8x8.
			## indices_as_2D_characters[1][ 0] is character 32 as 8x8.
			## indices_as_2D_characters[r][ c] is character 32*r+c as 8x8.
			indices_as_2D_characters = indices.reshape(24, 32, 8, 8)

			## indices_as_2D_characters[n] has all the right 
			## characters, but its element needs to be 
			## arranged differently: We must have the first 
			## scan line from the first element, the first 
			## scan line from the second element, etc. We 
			## just need to swap scanline (dimension 2) with 
			## the column (dimension 1).
			screen_characters = indices_as_2D_characters.swapaxes(2, 1)

			## Make it 1D again, and cache the outcome.
			self.map_characters2framebuffer = screen_characters.ravel()
		return characters[self.map_characters2framebuffer]

	def make_surface(self: Self, pnt: np.ndarray|None=None):
		framebuffer = self.make_framebuffer(pnt)

		depth = 8
		surface = pygame.Surface((256, 192), depth=8)
		surface.set_palette(TMS9918A.palette_msx1)
		surface.set_colorkey(0)
		pygame.pixelcopy.array_to_surface(
			surface,
			framebuffer.reshape(192,256).swapaxes(0,1)
		)
		return surface



	##
	## Registers: named bits
	##
	@property
	def M1(self: Self): return (self.reg1 & 0x10) >> 4
	@property
	def M2(self: Self): return (self.reg1 & 0x08) >> 3
	@property
	def M3(self: Self): return (self.reg0 & 0x02) >> 1
	##
	## Registers: register 0 (mode register)
	##
	@property
	def reg0(self: Self) -> int: return self._register[0]
	@reg0.setter
	def reg0(self: Self, value: int) -> None: self._register[0] = value

	##
	## Registers: register 1 (mode register)
	##
	@property
	def reg1(self: Self) -> int: return self._register[1]
	@reg1.setter
	def reg1(self: Self, value: int) -> None: self._register[1] = value

	##
	## Registers: register 2 (name table)
	##
	@property
	def reg2(self: Self) -> int: return self._register[2]
	@reg2.setter
	def reg2(self: Self, value: int) -> None: self._register[2] = value
	@property
	def name_table_base_address(self: Self) -> int:
		return 0x400 * (self.reg2 & 0x0F)

	##
	## Registers: register 3 (color table)
	##
	@property
	def reg3(self: Self) -> int: return self._register[3]
	@reg3.setter
	def reg3(self: Self, value: int) -> None: self._register[3] = value
	@property
	def color_table_base_address(self: Self) -> int:
		if self.M1 == 0 and self.M2 == 0 and self.M3 == 1:
			## Graphics II mode
			return 0x2000 * ((self.reg3 & 0x80) >> 7)
		return 0x40 * self.reg3

	##
	## Registers: register 4 (pattern table)
	##
	@property
	def reg4(self: Self) -> int: return self._register[4]
	@reg4.setter
	def reg4(self: Self, value: int) -> None: self._register[4] = value
	@property
	def pattern_generator_base_address(self: Self) -> int:
		if self.M1 == 0 and self.M2 == 0 and self.M3 == 1:
			## Graphics II mode
			return 0x2000 * ((self.reg4 & 7) >> 2)
		return 0x800 * (self.reg4 & 0x07)
	@property
	def pattern_table_base_address(self: Self) -> int:
		return self.pattern_generator_base_address

	##
	## Registers: register 5 (sprite attribute table)
	##
	@property
	def reg5(self: Self) -> int: return self._register[5]
	@reg5.setter
	def reg5(self: Self, value: int) -> None: self._register[5] = value
	@property
	def sprite_attribute_table_base_address(self: Self) -> int:
		return 0x80 * (self._register[5] & 0x7F)

	##
	## Registers: register 6 (sprite pattern table)
	##
	@property
	def reg6(self: Self) -> int: return self._register[6]
	@reg6.setter
	def reg6(self: Self, value: int) -> None: self._register[6] = value
	@property
	def sprite_pattern_table_base_address(self) -> int:
		return 0x800 * (self._register[6] & 0x03)

	@property
	def reg7(self: Self) -> int: return self._register[7]
	@reg7.setter
	def reg7(self: Self, value: int) -> None: self._register[7] = value
	@property
	def color_register(self: Self) -> int: return self.reg7
	@color_register.setter
	def color_register(self: Self, value: int) -> None: self.reg7 = value



if __name__ == '__main__':
	pygame.init()
	vdp = TMS9918A()

	print(f"M1 M2 M3={vdp.M1} {vdp.M2} {vdp.M3}")
	assert vdp.M1 == 0
	assert vdp.M2 == 0
	assert vdp.M3 == 1

	print(f"reg[2] Name table : 0x{vdp.name_table_base_address:04X}")
	assert 0x3800 == vdp.name_table_base_address

	print(f"reg[3] Color table: 0x{vdp.color_table_base_address:04X}")
	assert 0x0000 == vdp.color_table_base_address

	print(f"reg[4] Pattern table: 0x{vdp.pattern_table_base_address:04X}")
	assert 0x2000 == vdp.pattern_table_base_address

	print(f"reg[5] Sprite attribute table: 0x{vdp.sprite_attribute_table_base_address:04X}")
	assert 0x3B00 == vdp.sprite_attribute_table_base_address

	print(f"reg[6] Sprite pattern table: 0x{vdp.sprite_pattern_table_base_address:04X}")
	assert 0x1800 == vdp.sprite_pattern_table_base_address

	## Draw a ball like character.
	pattern = np.array([0x18, 0x3C, 0x7E, 0x7E, 0x7E, 0x7E, 0x3C, 0x18], dtype=np.uint8)
	vdp.set_pattern(index=0, pattern=pattern)

	## Use all 15 colors.
	colors = np.array([0x0F, 0x1E, 0x2D, 0x3C, 0x4B, 0x5A, 0x69, 0x78], dtype=np.uint8)
	vdp.set_pattern_colors(index=0, colors=colors)

	print(vdp.get_pattern_2D(index=0))
	#for row in vdp.get_colored_character_ansi_utf8(num=0):
	#	print(''.join(row))

	copyright_character = np.array([0x38, 0x44, 0xBA, 0xAA, 0xB2, 0xAA, 0x44, 0x38])
	copyright_colors    = np.array([0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40])
	vdp.set_pattern(index=1, pattern=copyright_character)
	vdp.set_pattern_colors(index=1, colors=copyright_colors)

	np.set_printoptions(formatter={'int':hex})
	print(f"PGT[1]: {vdp.read_vram(start=vdp.pattern_table_base_address+8, num=8)}")
	np.set_printoptions(formatter={'int': str})
	print(vdp.get_pattern_2D(index=1))
	#for row in vdp.get_character_ansi_utf8(num=1):
	#	print(''.join(row))
	np.set_printoptions(formatter={'int':hex})
	print(vdp.get_pgt().reshape(768, 8)[[1, 0]])
	print(vdp.get_pct().reshape(768, 8)[[1, 0]])
	np.set_printoptions(formatter={'int': str})
	print(vdp.get_colored_characters()[64:128].reshape(8,8))

	pgt = vdp.get_pgt()
	pct = vdp.get_pct()
	pnt = np.zeros(4, dtype=np.uint8)
	pnt[0] = 2
	pnt[1] = 1
	pnt[2] = 0
	print(f"pnt={pnt}")
	pats = pgt.reshape(768, 8)[pnt]
	cols = pct.reshape(768, 8)[pnt]
	print(f"{pats}")
	print(f"{cols}")
	bg_colors = cols & 0x0F
	fg_colors = cols >> 4
	fg_bg_pattern = np.unpackbits(pats)
	chars = np.where(fg_bg_pattern, np.repeat(fg_colors, 8), np.repeat(bg_colors, 8))
	print(f"chars={chars}")
	#print(f"{chars.reshape(-1, 8, 8)}")
