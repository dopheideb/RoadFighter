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
	BACKGROUND = (0,0,0)	## Black.
	window.fill(BACKGROUND)
	FPS = 10
	fps_clock = pygame.time.Clock()



	## Read track data, both patterns and colors.
	track_patterns_list = [
		{## Track patterns 0xD0 upto and including 0xD4.
			'index': (mem.get_word(0x68BC + 1) - 0x2000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x68BF + 1))
		},
		## Track patterns 0xD5 upto and including 0xD8 are mirrors, and are handled later on.
		{## Track patterns 0xD9 upto and including 0xE0.
			'index': (mem.get_word(0x68E2 + 1) - 0x2000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x68E5 + 1))
		},
		{## Track patterns 0xE9 upto and including 0xF2.
			'index': (mem.get_word(0x6908 + 1) - 0x2000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x690B + 1))
		},
	]
	track_colors_list = [
		{## Track colors 0xD0 upto and including 0xD4.
			'index': (mem.get_word(0x68C5 + 1) - 0x0000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x68C8 + 1))
		},
		{## Track colors 0xD5 upto and including 0xD8.
			'index': (mem.get_word(0x68D9 + 1) - 0x0000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x68DC + 1))
		},
		{## Track colors 0xD9 upto and including 0xE0.
			'index': (mem.get_word(0x68EB + 1) - 0x0000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x68EE + 1))
		},
		{## Track colors 0xE1 upto and including 0xE8.
			'index': (mem.get_word(0x68FF + 1) - 0x0000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x6902 + 1))
		},
		{## Track colors 0xE9 upto and including 0xF3.
			'index': (mem.get_word(0x6911 + 1) - 0x0000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x6914 + 1))
		},
		{## Track colors 0xF3 upto and including 0xFA.
			'index': (mem.get_word(0x6925 + 1) - 0x0000) >> 3,
			'data': konami.uncompress_patterns(address=mem.get_word(0x6928 + 1))
		},
	]

	## Copy patterns to VRAM.
	for track_patterns in track_patterns_list:
		for band in range(3):
			vdp.set_patterns(
				patterns=track_patterns['data'],
				index=track_patterns['index'],
				band=band
			)

	## Copy colors to VRAM.
	for track_colors in track_colors_list:
		for band in range(3):
			vdp.set_colors(
				colors=track_colors['data'],
				index=track_colors['index'],
				band=band
			)

	## Track patterns 0xD5 upto and including 0xD8. Mirror source: patterns 0xD1 upto and including 0xD4.
	konami.mirror_VRAM_patterns_in_vertical_axis(
		source=mem.get_word(0x68CE + 1),
		destination=mem.get_word(0x68D1 + 1),
		num=mem.get_byte(0x68D4 + 1)
	)

	## Track patterns 0xE1 upto and including 0xE8. Mirror source: patterns 0xD9 upto and including 0xE0.
	konami.mirror_VRAM_patterns_in_vertical_axis(
		source=mem.get_word(0x68F4 + 1),
		destination=mem.get_word(0x68F7 + 1),
		num=mem.get_byte(0x68FA + 1)
	)

	## Track patterns 0xF3 upto and including 0xF8. Mirror source: patterns 0xEC upto and including 0xF1.
	konami.mirror_VRAM_patterns_in_vertical_axis(
		source=mem.get_word(0x691A + 1),
		destination=mem.get_word(0x691D + 1),
		num=mem.get_byte(0x6920 + 1)
	)

	elements = \
	[
		{
			'index': 0,
			'num_columns': 10,
		},
		{
			'index': 1,
			'num_columns': 11,
		},
		{
			'index': 2,
			'num_columns': 11,
		},
	]
	last_name = 0x3800
	for element in elements:
		start = mem.get_word(0x593A + 2 * element['index'])
		last = start

		num_row_of_tracks = 8
		num_rows_seen = 0
		while num_rows_seen < num_row_of_tracks:
			track_names = mem[
				last
				:
				last + element['num_columns']
			]
			if track_names[0] == 0xFF:
				last = start
				continue
			num_rows_seen += 1
			last += element['num_columns']

			num_indent = 11 - element['num_columns']
			for n, track_name in enumerate(track_names):
				vdp.WRTVRM(last_name + num_indent + n, track_name)
			## Advance to next VPP line
			last_name += 0x20

	all_names = np.tile(np.arange(256), 3)	## [0, ..., 255, 0, ..., 255, 0, ..., 255]
	vdp.color_register = mem.get_byte(0x46B0)
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		## Start with a new canvas, with the backdrop color.
		vdp_backdrop_color_id  = vdp.color_register & 0x0F
		vdp_backdrop_color_rgb = vdp.get_palette()[vdp_backdrop_color_id]
		window.fill(vdp_backdrop_color_rgb, rect=msx_screen_rect)

		surf = vdp.make_surface()
		window.blit(source=surf, dest=(0, 0))

		## Show all available characters.
		vdp_patterns_surface = vdp.make_surface(pnt=all_names)
		window.blit(source=vdp_patterns_surface, dest=msx_vdp_patterns_rect)
		pygame.display.update()
		fps_clock.tick(FPS)
