import numpy as np
import pygame
from typing import Self



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
		## Because we want to allow level operations, just mimic 
		## VRAM and use a 1D array.
		self.pattern_generator_table = np.zeros([3 * 256 * 8], dtype=np.uint8)
		self.pattern_color_table     = np.zeros([3 * 256 * 8], dtype=np.uint8)
		## Character placements
		self.pattern_name_table = np.zeros(3 * 256 * 1, dtype=np.uint8)

		self.sprite_pattern_table   = np.zeros(256 * 8, dtype=np.uint8)
		self.sprite_attribute_table = np.zeros(4 * 32, dtype=np.uint8)

		self.registers = bytearray(b'\x00' * 8)

	def get_character(self, num: int):
		pattern = self.get_pattern(num)
		colors  = self.get_color(num)

		character = np.zeros((8,8), dtype=np.uint8)
		for y in range(8):
			color = (colors[y] & 0x0F, colors[y] >> 4)
			for x in range(8):
				character[y, x] = color[(pattern[y] >> (7 - x)) & 1]

		return character

	def get_characters_WORKING_BUT_UTTERLY_SLOW(self, names: list[int]):
		length = len(names)
		patterns = self.get_patterns(names)
		colors   = self.get_colors(names)

		characters = np.zeros((length, 8,8), dtype=np.uint8)
		for n in range(length):
			for y in range(8):
				color = (colors[n][y] & 0x0F, colors[n][y] >> 4)
				for x in range(8):
					characters[n, y, x] = color[(patterns[n][y] >> (7 - x)) & 1]

		return characters
	def get_characters(self, names: list[int]):
		length = len(names)
		patterns = self.get_patterns(names).reshape(-1)
		colors   = self.get_colors(names).reshape(-1)
		fg_colors = colors >> 4		## No masking necessary, since type is np.uint8
		bg_colors = colors & 0xF

		bit_pattern = np.unpackbits(patterns)
		characters = np.where(bit_pattern, np.repeat(fg_colors, 8), np.repeat(bg_colors, 8))
		return characters.reshape((length, 8, 8))

	def get_character_ansi_utf8(self, num: int) -> str:
		character = []
		vdp_character = self.get_character(num)
		for row in vdp_character:
			ch_row = []
			for color_id in row:
				(r, g, b) = self._palette[color_id]
				ch_row.append(f"\033[38;2;{r};{g};{b}m\u2588\u2588")
			character.append(ch_row)
		return character

	## No need for RGB when using 8 bit mapped colors.
	#def get_character_numpy(self, num: int):
	#	character = np.zeros([8, 8, 3], dtype=np.uint8)
	#	vdp_character = self.get_character(num)
	#	for y, row in enumerate(vdp_character):
	#		for x, color_id in enumerate(row):
	#			(r, g, b) = self._palette[color_id]
	#			character[y][x] = (r, g, b)
	#	return character

	def get_color(self: Self, num):
		return self.pattern_color_table[8 * num : 8 * (num + 1)]

	def get_colors(self: Self, ids: list[int]):
		return self.pattern_color_table.reshape(3 * 256, 8)[ids]

	def get_palette(self: Self) -> tuple:
		return self._palette
	
	def get_pattern(self: Self, num):
		return self.pattern_generator_table[8 * num : 8 * (num + 1)]

	def get_patterns(self: Self, ids: list[int]):
		return self.pattern_generator_table.reshape(3 * 256, 8)[ids]

	def make_surface(self):
		characters = self.get_characters(self.pattern_name_table)
		characters_2D = np.zeros([24 * 8, 32 * 8], dtype=np.uint8)

		for m in range(24):
			for n in range(32):
				num = m * 32 + n
				characters_2D[m*8 : (m+1)*8, n*8 : (n+1)*8] = characters[num]
		depth = 8
		surface = pygame.Surface((characters_2D.shape[1], characters_2D.shape[0]), depth=8)
		surface.set_palette(TMS9918A.palette_msx1)
		surface.fill(self.text_color & 0x0F)
		surface.set_colorkey(0)
		pygame.pixelcopy.array_to_surface(surface, characters_2D.swapaxes(0,1))
		return surface

	def set_pattern_colors(self: Self, pattern_colors: np.array, index: int, band :int=0) -> None:
		## Allow a list of patterns.
		pattern_colors_1D = np.ravel(pattern_colors)
		len = pattern_colors_1D.shape[0]

		## Every color pattern is 8 bytes.
		offset = {0: 0, 1: 8 * 256, 2: 8 * 512}[band] + index * 8
		self.pattern_color_table[offset : offset + len] =\
			pattern_colors_1D

	def set_pattern(self: Self, pattern: np.array, index, band=0):
		pt_offset = {0: 0, 1: 256, 2: 512}[band] + index * 8
		self.pattern_generator_table[pt_offset : pt_offset + 8] =\
			pattern

	def set_patterns(self: Self, patterns: np.array, index, band=0):
		## Allow a list of patterns.
		patterns_1D = np.ravel(patterns)
		len = patterns_1D.shape[0]

		## Every pattern is 8 bytes.
		pgt_offset = {0: 0, 1: 8 * 256, 2: 8 * 512}[band] + index * 8
		self.pattern_generator_table[pgt_offset : pgt_offset + len] =\
			patterns_1D

	@property
	def color_table_base_address(self) -> int:
		return 0x2000 * ((self.registers[3] & 0x80) >> 7)

	@property
	def name_table_base_address(self) -> int:
		return 0x400 * (self.registers[2] & 0x0F)

	@property
	def pattern_generator_base_address(self) -> int:
		return 0x800 * (self.registers[4] & 0x07)

	@property
	def sprite_attribute_table_base_address(self) -> int:
		return 0x80 * (self.registers[5] & 0x7F)

	@property
	def sprite_pattern_generator_base_address(self) -> int:
		return 0x800 * (self.registers[6] & 0x03)

	@property
	def text_color(self) -> int:
		return self.registers[7]



if __name__ == '__main__':
	pygame.init()
	vdp = TMS9918A()

	## Draw a ball like character.
	pattern = (0x18, 0x3C, 0x7E, 0x7E, 0x7E, 0x7E, 0x3C, 0x18)
	vdp.set_pattern(index=0, pattern=pattern)

	## Use all 15 colors.
	vdp.pattern_color_table[0] = 0x0F
	vdp.pattern_color_table[1] = 0x1E
	vdp.pattern_color_table[2] = 0x2D
	vdp.pattern_color_table[3] = 0x3C
	vdp.pattern_color_table[4] = 0x4B
	vdp.pattern_color_table[5] = 0x5A
	vdp.pattern_color_table[6] = 0x69
	vdp.pattern_color_table[7] = 0x78

	print(vdp.get_character(num=0))
	for row in vdp.get_character_ansi_utf8(num=0):
		print(''.join(row))

	vdp.pattern_name_table[0:768] = (list(range(256)) * 3)
