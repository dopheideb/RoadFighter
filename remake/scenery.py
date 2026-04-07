#!/usr/bin/env python3

from   konami import Konami
from   memory import Memory
import numpy as np
import pygame
import rom as _rom
from   tms9918a import TMS9918A
from   typing import Final, Self

ADDRESS: Final[dict[int]] =\
{
	'470d_location_and_pattern_names__hiscore__score':	0x470D,
	'476a_location_and_pattern_names__speed_fuel':		0x476A,
	'course_pattern_names__current_address': 0xE046,
	'course_pattern_names__upcoming_line': 0xE058,
}

class RoadFighter:
	def __init__(
			self: Self,
			memory: Memory,
			vdp: TMS9918A=TMS9918A(),
	):
		self.mem = memory
		self.konami = Konami(memory=mem, vdp=vdp)
		self.vdp = vdp

	def get_byte(self: Self, address: str|int, signed: bool=False) -> int:
		if isinstance(address, str):
			address = ADDRESS[address]
		return self.mem.get_byte(address=address)
	def get_word(self: Self, address: str|int, endianness: str='little') -> bytes:
		if isinstance(address, str):
			address = ADDRESS[address]
		return self.mem.get_word(address=address)

	def set_byte(self: Self, address: str, value: int) -> bytes:
		if isinstance(address, str):
			address = ADDRESS[address]
		return self.mem.set_byte(address, value=value)
	def set_word(self: Self, address: str, value: int) -> bytes:
		if isinstance(address, str):
			address = ADDRESS[address]
		return self.mem.set_word(address, value=value)



	def x45cf_filvrm_color_or_pattern_generator(self: Self, address: int, value: int, count: int) -> None:
		for band in range(3):
			for offset in range(count):
				self.vdp.WRTVRM(
					address=address+offset,
					byte=value,
				)
			address += 0x0800

	def x45e0_copy2VRAM_3x(self: Self, source: int, destination: int) -> None:
		print(f"source={source:04X}, destination={destination:04X}")
		for band in range(3):
			self.x4611_uncompress_to_VRAM(source, destination)
			destination += 0x0800

	def x45f0_show_phrase_set(self: Self, address: int) -> None:
		mask = 0xFF
		assert mask == self.mem.get_byte(0x45F0 + 1)
		self.x45f2_read_vram_destination_and_draw_or_hide_phrase_set(
			phrase_set_address=address,
			mask=mask,
		)

	def x45f2_read_vram_destination_and_draw_or_hide_phrase_set(
			self: Self,
			phrase_set_address: int,
			mask: int,
	) -> None:
		vram_destination_address = self.mem.get_word(phrase_set_address)
		phrase_set_address += 2
		self.x45f8_draw_or_hide_phrase_set(
			vram_destination_address=vram_destination_address,
			phrase_set_address=phrase_set_address,
			mask=mask,
		)

	def x45f8_draw_or_hide_phrase_set(
			self: Self,
			vram_destination_address: int,
			phrase_set_address: int,
			mask: int,
	) -> None:
		while True:
			value = self.mem.get_byte(phrase_set_address)
			phrase_set_address += 1

			if value == 0xFF:
				## We have reached the end of the symbol 
				## set.
				break

			if value == 0xFE:
				## We have reached the end of the 
				## current word/phrase. Continue with 
				## the next.
				self.x45f2_read_vram_destination_and_draw_or_hide_phrase_set(
					phrase_set_address=phrase_set_address,
					mask=mask,
				)
				break

			value &= mask
			self.vdp.WRTVRM(
				address=vram_destination_address,
				byte=value
			)
			vram_destination_address += 1
		pass



	def x4611_uncompress_to_VRAM(self: Self, source: int, destination: int) -> None:
		address = source
		while True:
			opcode = self.mem.get_byte(address)
			if opcode == 0x00:
				## 0x4616
				break

			if opcode <= 0x7F:
				copy_count = opcode
				address += 1

				value = self.mem.get_byte(address)
				address += 1

				for _ in range(copy_count):
					self.vdp.WRTVRM(
						address=destination,
						byte=value
					)
					destination += 1

				continue

			if opcode >= 0x81:
				copy_count = opcode & 0x7F
				address += 1

				for _ in range(copy_count):
					value = self.mem.get_byte(address=address)
					address += 1

					self.vdp.WRTVRM(
						address=destination,
						byte=value
					)
					destination += 1
				continue

			assert opcode == 0x80
			raise NotImplementedError("opcode 0x80 not yet implemented")



	def x4773_setup_solids_and_uncompress_symbols_to_VRAM_3x(self: Self) -> None:
		self.x489a_set_up_solid_color_characters_in_VRAM()

		compressed_patterns_address = self.get_word(0x4776 + 1)
		vram_destination_address    = self.get_word(0x4779 + 1)

		self.x45e0_copy2VRAM_3x(
			source=compressed_patterns_address,
			destination=vram_destination_address,
		)

		## 0x447F: Set the color of all the symbols.
		##
		## high nybble == 0xF: white
		## low  nybble == 0x0: transparent (usually means black)
		color_value = 0xF0

		## The first 16 characters are the solids. The symbols 
		## come right after the solids.
		vram_destination_address = 0x10 << 3
		assert vram_destination_address == self.mem.get_word(0x4781 + 1)

		num_patters = 44
		copy_count = num_patters * 8
		assert copy_count == self.get_word(0x4784 + 1)

		self.x45cf_filvrm_color_or_pattern_generator(
			address=vram_destination_address,
			value=color_value,
			count=copy_count,
		)



	def x489a_set_up_solid_color_characters_in_VRAM(self: Self) -> None:
		##
		## Fill the pattern generator table.
		##
		start_vram_address_solid_patterns = 0x2000
		assert start_vram_address_solid_patterns == self.get_word(0x489A + 1)

		## We need to setup 16 characters (because there are 16 
		## colors).
		num_characters = 16
		copy_count = num_characters << 3
		assert copy_count == self.get_word(0x489D + 1)

		## 0x00 means: use a single color for the whole pattern 
		## line.
		value=0x00

		## Set up
		self.x45cf_filvrm_color_or_pattern_generator(
			address=start_vram_address_solid_patterns,
			value=value,
			count=copy_count,
		)



		##
		## Fill the color generator table.
		##
		start_vram_address_solid_colors = 0x0000
		assert start_vram_address_solid_colors == self.get_word(0x48A4 + 1)

		copy_count = 8
		assert copy_count == self.mem.get_word(0x48AD + 1)

		vram_address_solid_colors = start_vram_address_solid_colors
		for color_id in range(num_characters):
			self.x45cf_filvrm_color_or_pattern_generator(
				address=vram_address_solid_colors,
				value=color_id,
				count=copy_count,
			)
			vram_address_solid_colors += 8



	def x5716_write_upcoming_coarse_line_to_ram_and_vram_coarse(self: Self) -> None:
		course_pattern_names__current_address = self.get_word('course_pattern_names__current_address')
		course_pattern_num_cols = 0x16
		assert course_pattern_num_cols == 0x10000 - self.get_word(0x5719 + 1)

		course_pattern_names__current_address -= course_pattern_num_cols

		## Wraparound if necessary.
		if course_pattern_names__current_address == 0xE170:
			course_pattern_names__current_address = 0xE380
		self.set_word('course_pattern_names__current_address', course_pattern_names__current_address)

		source_address = ADDRESS['course_pattern_names__upcoming_line']
		assert source_address == 0xE058

		ldir_count = self.get_word(0x5735 + 1)
		assert ldir_count == 0x16

		## Copy 22 bytes from 0xE058 to somewhere in 
		## [0xE186..0xE395]: copy upcoming coarse line to RAM 
		## version of the coarse names.
		for n in range(ldir_count):
			val = self.get_byte(address=source_address)
			self.set_byte(address=course_pattern_names__current_address, value=val)

			source_address += 1
			course_pattern_names__current_address += 1

		self.x573a_copy_coarse_to_VRAM()



	def x573a_copy_coarse_to_VRAM(self: Self) -> None:
		## In screen 2, the VDP has 24 rows of characters.
		num_rows = 24

		## The coarse starts at column 1 (0 based).
		VRAM_destination_address = self.get_word(0x573A + 1)
		assert VRAM_destination_address == 0x3801

		## The coarse isn't as wide as the screen. (Score and 
		## highscore are not part of the coarse columns for 
		## instance).
		num_columns = 22

		course_pattern_names__current_address = self.get_word('course_pattern_names__current_address')

		for row_num in range(num_rows):
			for col_num in range(num_columns):
				vdp.WRTVRM(
					address=VRAM_destination_address+col_num,
					byte=mem.get_byte(course_pattern_names__current_address),
				)
				course_pattern_names__current_address += 1

			assert mem.get_byte(0x5760 + 1) == 0x20
			num_characters_on_1_character_row = 0x20

			VRAM_destination_address += num_characters_on_1_character_row

			assert course_pattern_names__current_address <= 0xE396
			if course_pattern_names__current_address == 0xE396:
				course_pattern_names__current_address = 0xE186



	def x68aa_push_much_stuff_to_VRAM(self: Self) -> None:
		## Set up pattern generators [0x40..0x7B].
		compressed_patterns_address = self.get_word(0x68AA + 1)
		vram_destination_address    = self.get_word(0x68AD + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)

		## Set up color generators [0x40..0x7B].
		compressed_patterns_address = self.get_word(0x68B3 + 1)
		vram_destination_address    = self.get_word(0x68B6 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



		## Set up pattern generators [0xD0..0xD4]: track
		compressed_patterns_address = self.get_word(0x68BF + 1)
		vram_destination_address    = self.get_word(0x68BC + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)

		## Set up color generators [0xD0..0xD4]: track
		compressed_patterns_address = self.get_word(0x68C8 + 1)
		vram_destination_address    = self.get_word(0x68C5 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



		## Set up pattern generators [0xD5..0xD8]: track
		konami.mirror_VRAM_patterns_in_vertical_axis(
			source=self.mem.get_word(0x68CE + 1),
			destination=mem.get_word(0x68D1 + 1),
			num=mem.get_byte(0x68D4 + 1),
		)

		## Set up color generators [0xD5..0xD8]: track
		compressed_patterns_address = self.get_word(0x68DC + 1)
		vram_destination_address    = self.get_word(0x68D9 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



		## Set up pattern generators [0xD9..0xE0]: track
		compressed_patterns_address = self.get_word(0x68E5 + 1)
		vram_destination_address    = self.get_word(0x68E2 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)

		## Set up color generators [0xD9..0xE0]: track
		compressed_patterns_address = self.get_word(0x68EE + 1)
		vram_destination_address    = self.get_word(0x68EB + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



		## Set up pattern generators [0xE1..0xE8]: track
		konami.mirror_VRAM_patterns_in_vertical_axis(
			source=self.mem.get_word(0x68F4 + 1),
			destination=mem.get_word(0x68F7 + 1),
			num=mem.get_byte(0x68FA + 1),
		)

		## Set up color generators [0xE1..0xE8]: track
		compressed_patterns_address = self.get_word(0x6902 + 1)
		vram_destination_address    = self.get_word(0x68FF + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



		## Set up pattern generators [0xE9..0xF2]: track
		compressed_patterns_address = self.get_word(0x690B + 1)
		vram_destination_address    = self.get_word(0x6908 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)

		## Set up color generators [0xE9..0xF3]: track
		compressed_patterns_address = self.get_word(0x6914 + 1)
		vram_destination_address    = self.get_word(0x6911 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



		## Set up pattern generators [0xF3..0xF8]: track
		konami.mirror_VRAM_patterns_in_vertical_axis(
			source=self.mem.get_word(0x691A + 1),
			destination=mem.get_word(0x691D + 1),
			num=mem.get_byte(0x68FA + 1),
		)

		## Set up color generators [0xF3..0xFA]: track
		compressed_patterns_address = self.get_word(0x6928 + 1)
		vram_destination_address    = self.get_word(0x6925 + 1)
		self.x45e0_copy2VRAM_3x(source=compressed_patterns_address, destination=vram_destination_address)



if __name__ == '__main__':
	rom = _rom.ROM(file='./RoadFighter.rom')
	mem = Memory(rom)
	vdp = TMS9918A()
	konami = Konami(memory=mem, vdp=vdp)
	rf = RoadFighter(memory=mem, vdp=vdp)

	## Initialize pygame.
	pygame.init()
	pygame.display.set_caption('Road Fighter Track data')
	width = 32 * 8
	height = 24 * 8
	window = pygame.display.set_mode(
		size=(width * 2, height),
		flags=pygame.SCALED,
	)
	msx_screen_rect = ((0, 0), (width, height))
	msx_vdp_patterns_rect = ((width, 0), (width, height))

	FPS = 10
	fps_clock = pygame.time.Clock()

	all_names = np.tile(np.arange(256), 3)	## [0, ..., 255, 0, ..., 255, 0, ..., 255]
	vdp.color_register = mem.get_byte(0x49A6+1)
	assert vdp.color_register == 0xE0

	rf.x4773_setup_solids_and_uncompress_symbols_to_VRAM_3x()
	phrase_set_address = ADDRESS['470d_location_and_pattern_names__hiscore__score']
	rf.x45f0_show_phrase_set(address=phrase_set_address)
	phrase_set_address = ADDRESS['476a_location_and_pattern_names__speed_fuel']
	rf.x45f0_show_phrase_set(address=phrase_set_address)

	rf.x68aa_push_much_stuff_to_VRAM()

	stage0based = -1
	scenery_order_address = 0
	scenery_order_end_address = 0
	current_coarse_scenery_item__num_rows_left = 1
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		## Read the patterns and colors of the next stage.
		if scenery_order_address == scenery_order_end_address:
			stage0based += 1
			stage0based %= 6
			print(f"stage0based={stage0based}")

			## 0x50B9
			rf.set_word('course_pattern_names__current_address', 0xE186)

			## Shore line is in stage 2 and 5.
			shore_line_pointer = 0x7DC5

			## Stage 3 and 5 use a bit pattern to determine water/snow pattern.
			if stage0based == 2:
				water_or_snow_address = 0x7C85
			elif stage0based == 5:
				water_or_snow_address = 0x7FE4
			else:
				water_or_snow_address = 0xFFFF

			## The pointers for each stage are at 0x6A51.
			stage_address = 0x6A51 + 4 * stage0based
			compressed_patterns_address = mem.get_word(stage_address + 0)
			compressed_colors_address   = mem.get_word(stage_address + 2)

			scenery_patterns = konami.uncompress_patterns(address=compressed_patterns_address)
			scenery_patterns_index = (mem.get_word(0x6A40 + 1) - 0x2000) >> 3

			scenery_colors = konami.uncompress_patterns(address=compressed_colors_address)
			scenery_colors_index = (mem.get_word(0x6A4B + 1) - 0x0000) >> 3

			## Copy patterns and colors to VRAM.
			for band in range(3):
				vdp.set_patterns(
					patterns=scenery_patterns,
					index=scenery_patterns_index,
					band=band
				)
				vdp.set_pattern_colors(
					colors=scenery_colors,
					index=scenery_colors_index,
					band=band
				)

				## Stage 2.
				if stage0based == 1:
					extra_patterns = konami.uncompress_patterns(address=mem.get_word(address=0x698C+1))
					extra_patterns_index = (mem.get_word(address=0x698F+1) - 0x2000) >> 3
					vdp.set_patterns(
						band=band,
						patterns=extra_patterns,
						index=extra_patterns_index
					)

				## Stage 4 and 5.
				if stage0based in [3,4]:
					print(f"band={band} A: {vdp.read_vram(mem.get_word(address=0x6998+1), 8)}")
					## Patterns [0x80..0x97]
					extra_patterns = konami.uncompress_patterns(address=mem.get_word(address=0x6995+1))
					extra_patterns_index = (mem.get_word(address=0x6998+1) - 0x2000) >> 3
					vdp.set_patterns(
						band=band,
						patterns=extra_patterns,
						index=extra_patterns_index
					)
					print(f"band={band} B: {vdp.read_vram(mem.get_word(address=0x6998+1), 8)}")

					## Patterns [0xB1..0xC8] (mirror of [0x80..0x97]).
					konami.mirror_VRAM_patterns_in_vertical_axis(
						source=mem.get_word(0x699E+1),
						destination=mem.get_word(0x69A1+1),
						num=mem.get_byte(0x69A4+1)
					)
					print(f"band={band} C: {vdp.read_vram(mem.get_word(address=0x69A1+1), 8)}")

					## Colors [0xB1..0xC8]
					extra_colors = konami.uncompress_patterns(address=mem.get_word(address=0x69A9+1))
					extra_colors_index = (mem.get_word(address=0x69AC+1) - 0x0000) >> 3
					vdp.set_colors(
						band=band,
						colors=extra_colors,
						index=extra_colors_index
					)

					## Patterns [0x80..0x8C]
					extra_patterns = konami.uncompress_patterns(address=mem.get_word(address=0x69B2+1))
					extra_patterns_index = (mem.get_word(address=0x69B5+1) - 0x2000) >> 3
					vdp.set_patterns(
						band=band,
						patterns=extra_patterns,
						index=extra_patterns_index
					)

					## Patterns [0x8D..0x99]
					konami.mirror_VRAM_patterns_in_vertical_axis(
						source=mem.get_word(0x69BE+1),
						destination=mem.get_word(0x69BB+1),
						num=mem.get_byte(0x69C1+1)
					)

					## Colors [0x80..0x8C,0x8D..0x99]
					extra_colors = konami.uncompress_patterns(address=mem.get_word(address=0x69C6+1))
					extra_colors_index_a = (mem.get_word(address=0x69C9+1) - 0x0000) >> 3
					extra_colors_index_b = (mem.get_word(address=0x69D2+1) - 0x0000) >> 3
					vdp.set_colors(
						band=band,
						colors=extra_colors,
						index=extra_colors_index_a
					)
					vdp.set_colors(
						band=band,
						colors=extra_colors,
						index=extra_colors_index_b
					)

					## Patterns [0x9A..0xB0]
					extra_patterns = konami.uncompress_patterns(address=mem.get_word(address=0x69D8+1))
					extra_patterns_index = (mem.get_word(address=0x69DB+1) - 0x2000) >> 3
					vdp.set_patterns(
						band=band,
						patterns=extra_patterns,
						index=extra_patterns_index
					)

					## Colors [0x9A..0xB0]
					extra_colors = konami.uncompress_patterns(address=mem.get_word(address=0x69E1+1))
					extra_colors_index = (mem.get_word(address=0x69E4+1) - 0x0000) >> 3
					vdp.set_colors(
						band=band,
						colors=extra_colors,
						index=extra_colors_index
					)

				## Stage 4.
				if stage0based == 3:
					vdp.FILVRM(
						address=0x0000 + 0x0800 * band + mem.get_word(0x69F2+1),
						byte=mem.get_byte(0x69F0+1),
						num=mem.get_word(0x69F5+1)
					)
					vdp.FILVRM(
						address=0x0000 + 0x0800 * band + mem.get_word(0x69FD+1),
						byte=mem.get_byte(0x69FB+1),
						num=mem.get_word(0x6A00+1)
					)

			scenery_order_end_address =\
			[
				0x7960,		## Stage 01, start is at 0x78E5.
				0x7C54,		## Stage 02, start is at 0x7BAA.
				0x7C54,		## Stage 03, start is at 0x7BAA.
				0x7960,		## Stage 04, start is at 0x78E5.
				0x7960,		## Stage 05, start is at 0x78E5.
				0x7FE4,		## Stage 06, start is at 0x7F6B.
			][stage0based]
			stage_address = 0x5161 + 6 * stage0based
			track_layout_address    = mem.get_word(address=stage_address + 0)
			scenery_order_address   = mem.get_word(address=stage_address + 2)
			scenery_objects_address = mem.get_word(address=stage_address + 4)

			stage_03_repeat_count   = mem.get_byte(address=0x50FB+1)
			stage_03_draw_non_pylon = True
			stage_03_element_size   = 1

			if stage0based == 2:
				scenery_objects_address = 0x7C54

		## Initialize basic new line.
		pattern_basic_scenery = mem.get_byte(address=0x5191 + stage0based)

		## 0x592A
		num_scenery_columns = 0x16
		assert num_scenery_columns - 1 == rf.get_word(0x5934 + 1)
		addr = ADDRESS['course_pattern_names__upcoming_line']
		for n in range(num_scenery_columns):
			rf.set_byte(addr + n, pattern_basic_scenery)

		## Draw water in stage 3, or snow in stage 6.
		if stage0based in [2,5]:
			## Check for need to wraparound.
			if mem.get_byte(address=water_or_snow_address) == 0xFF:
				if stage0based == 2:
					water_or_snow_address = 0x7C85
				else:
					water_or_snow_address = 0x7FE4

			val = mem.get_word(address=water_or_snow_address, endianness='big')
			print(f"water_or_snow_address=0x{water_or_snow_address:04X} val=0x{val:04X} (initial)")
			for n in range(0x0C):
				val <<= 1
				pattern_name = 0x04 if stage0based == 2 else 0x80
				if val & 0x10000:
					pattern_name = 0x9B if stage0based == 2 else 0x0F
					val &= 0xFFFF
				vdp.WRTVRM(address=0x3801 + n, byte=pattern_name)

			val = mem.get_word(address=water_or_snow_address, endianness='big')
			print(f"water_or_snow_address=0x{water_or_snow_address:04X} val=0x{val:04X}")
			for n in range(0x0A):
				val <<= 1
				pattern_name = 0x04 if stage0based == 2 else 0x80
				if val & 0x10000:
					pattern_name = 0x9B if stage0based == 2 else 0x0F
					val &= 0xFFFF
				vdp.WRTVRM(address=0x3801 + 0x0C + n, byte=pattern_name)

			## 0x556E-0x5573.
			water_or_snow_address += 2

		## Draw shore line in stage 2.
		if stage0based == 1:
			while True:
				shore_line_names = list(mem.get(address=shore_line_pointer, num=4))
				shore_line_pointer += 4
				if shore_line_names[0] != 0xFF:
					break
				shore_line_pointer = 0x7DC5
			vdp.write_vram(start=0x3801, data=shore_line_names)

		## Draw bridge/pylon in stage 3.
		if stage0based == 2:
			current_coarse_scenery_item__num_cols = 0
			mem[0xE08C] += 1
			vram_destination = 0x3801 + (0xE05C - 0xE058)
			for n in range(4):
				pattern_name = mem.get_byte(address=scenery_objects_address)
				vdp.WRTVRM(address=vram_destination, byte=pattern_name)
				vram_destination += 1
				scenery_objects_address += 1

			## 0x55BF
			for n in range(6+1):
				pattern_name = 0xD0
				vdp.WRTVRM(address=vram_destination, byte=pattern_name)
				vram_destination += 1

			for n in range(4):
				pattern_name = mem.get_byte(address=scenery_objects_address)
				vdp.WRTVRM(address=vram_destination, byte=pattern_name)
				vram_destination += 1
				scenery_objects_address += 1

			pattern_name = mem.get_byte(address=scenery_objects_address)
			if pattern_name == 0xFF:
				stage_03_repeat_count -= 1

				if stage_03_repeat_count == 0:
					stage_03_draw_non_pylon = not stage_03_draw_non_pylon
					if stage_03_draw_non_pylon:
						stage_03_repeat_count = 0x10
					else:
						stage_03_repeat_count = 0x01
				if stage_03_draw_non_pylon:
					scenery_objects_address = mem.get_word(address=0x55A6+1)
					assert scenery_objects_address == 0x7C54
				else:
					scenery_objects_address = mem.get_word(address=0x559D+1)
					assert scenery_objects_address == 0x7C23

			## Mark the middle of the road.
			if (mem[0xE08C] & 0x03) < 2:
				vdp.WRTVRM(address=0x3801 + (0xE063 - 0xE058), byte=0xD1)

		if current_coarse_scenery_item__num_rows_left == 1 and stage0based != 2:
			scenery_order_address += 1
			scenery_byte = mem.get_byte(address=scenery_order_address)
			if scenery_byte == 0xFF:
				current_coarse_scenery_item__num_rows = 8
				current_coarse_scenery_item__num_cols = 0
			else:
				scenery_element_index = scenery_byte & 0x0F
				scenery_element_indent = (scenery_byte >> 4) << 1
				scenery_object_address = mem.get_word(address=scenery_objects_address + 2 * scenery_element_index)
				current_coarse_scenery_item__num_rows = mem.get_byte(address=scenery_object_address+0)
				current_coarse_scenery_item__num_cols = mem.get_byte(address=scenery_object_address+1)
				print(f"\tdefb 0x{scenery_byte:02X}\t\t;{scenery_order_address:04x} Scenery element: #{scenery_element_index:02x}, indent from left side: {scenery_element_indent}")
				print(f"\t==> {scenery_object_address:04x} {current_coarse_scenery_item__num_rows}x{current_coarse_scenery_item__num_cols}")
			current_coarse_scenery_item__num_rows_left = current_coarse_scenery_item__num_rows
		else:
			current_coarse_scenery_item__num_rows_left -= 1

		for c in range(current_coarse_scenery_item__num_cols):
			if stage0based == 2:
				break
			offset = scenery_object_address + 2 + (current_coarse_scenery_item__num_rows - current_coarse_scenery_item__num_rows_left) * current_coarse_scenery_item__num_cols + c
			print(f"{scenery_object_address:04x} {offset:04x}")
			name = mem.get_byte(address=offset)

			offset = scenery_element_indent + c
			## Don't write in score section.
			if offset >= 0x16:
				break
			rf.set_byte(0xE058 + offset, name)

		if stage0based == 2:
			print(f"stage={stage0based+1}, scenery_objects_address={scenery_objects_address:04x}")

		## When track, scenery (i.e. the coarse) pattern names 
		## etc are all in RAM, it is copied to actual VRAM.
		rf.x5716_write_upcoming_coarse_line_to_ram_and_vram_coarse()

		## Show the output of the MSX/VDP.
		surf = vdp.make_surface()
		window.blit(source=surf, dest=(0, 0))

		## Show all available characters.
		vdp_patterns_surface = vdp.make_surface(pnt=all_names)
		window.blit(source=vdp_patterns_surface, dest=msx_vdp_patterns_rect)

		pygame.display.update()
		fps_clock.tick(FPS)
