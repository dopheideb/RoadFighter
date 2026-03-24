#!/usr/bin/env python3

from   konami import Konami
from   memory import Memory
import numpy as np
import pygame
from   tms9918a import TMS9918A
import rom as _rom

if __name__ == '__main__':
	rom = _rom.ROM(file='./RoadFighter.rom')
	mem = Memory(rom)
	vdp = TMS9918A()
	konami = Konami(memory=mem, vdp=vdp)

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

	## Patterns 0..15: fill with the corresponding color.
	for band in range(3):
		## Set the pattern.
		vdp.FILVRM(address=0x2000 + 0x800 * band, byte=0x00, num=8 * 16)

		## Set the color.
		for n in range(16):
			color = n
			vdp.FILVRM(address=0x0000 + 0x800 * band + 8 * n, byte=color, num=8)

	stage0based = 1
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

			## Track patterns and colors 0xD0 upto and including 0xD4.
			compressed_road_patterns = mem.get_word(0x68BF+1)
			compressed_road_colors   = mem.get_word(0x68C8+1)
			road_patterns = konami.uncompress_patterns(address=compressed_road_patterns)
			road_colors   = konami.uncompress_patterns(address=compressed_road_colors)
			road_patterns_index = (mem.get_word(0x68BC+1) - 0x2000) >> 3
			road_colors_index   = (mem.get_word(0x68C5+1) - 0x0000) >> 3

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

				vdp.set_patterns(
					patterns=road_patterns,
					index=road_patterns_index,
					band=band
				)
				vdp.set_pattern_colors(
					colors=road_colors,
					index=road_colors_index,
					band=band
				)

				## Stage 2
				if stage0based == 1:
					extra_patterns = konami.uncompress_patterns(address=mem.get_word(address=0x698C+1))
					extra_patterns_index = (mem.get_word(address=0x698F+1) - 0x2000) >> 3
					vdp.set_patterns(
						band=band,
						patterns=extra_patterns,
						index=extra_patterns_index
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

		## Copy VDP lines downwards, starting at the next to last line.
		for r in reversed(range(23)):
			pattern_line = vdp.read_vram(start=0x3800 + 0x20 * r, num=0x20)
			vdp.write_vram(start=0x3800 + 0x20 * (r + 1), data=pattern_line)

		## Initialize basic new line.
		num_initial_black = 0x1
		num_scenery_columns = 0x16
		pattern_black = 0x00
		pattern_basic_scenery = mem.get_byte(address=0x5191 + stage0based)
		for col in range(0, num_initial_black):
			vdp.WRTVRM(0x3800, pattern_black)
		for col in range(num_initial_black, num_initial_black + num_scenery_columns + 1):
			vdp.WRTVRM(0x3800 + col, pattern_basic_scenery)
		for col in range(num_initial_black + num_scenery_columns, 0x20):
			vdp.WRTVRM(0x3800 + col, 0x00)

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

			vram_offset = 1 + scenery_element_indent + c
			## Don't write in score section.
			if vram_offset >= 0x17:
				break
			vdp.WRTVRM(0x3800 + vram_offset, name)

		if stage0based == 2:
			print(f"stage={stage0based+1}, scenery_objects_address={scenery_objects_address:04x}")

		## Show the output of the MSX/VDP.
		surf = vdp.make_surface()
		window.blit(source=surf, dest=(0, 0))

		## Show all available characters.
		vdp_patterns_surface = vdp.make_surface(pnt=all_names)
		window.blit(source=vdp_patterns_surface, dest=msx_vdp_patterns_rect)

		pygame.display.update()
		fps_clock.tick(FPS)
