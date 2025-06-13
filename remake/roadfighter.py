#!/usr/bin/env python3

from   konami import Konami
from   memory import Memory
import numpy as np
import pygame
import pygame.locals
import rom as _rom
import sys
from   tms9918a import TMS9918A
from   typing import cast

## Initialize all used pygame modules.
pygame.init()

FPS = 50
fps_clock = pygame.time.Clock()

width = 32 * 8
height = 24 * 8
pygame.display.set_caption('Road Fighter')
window = pygame.display.set_mode(
	size=(width * 2, height),
	flags=pygame.SCALED,
)
msx_screen_rect = ((0, 0), (width, height))
msx_vdp_patterns_rect = ((width, 0), (width, height))
BACKGROUND = (0,0x80,0)
window.fill(BACKGROUND)

rom = _rom.ROM(file='./RoadFighter.rom')
mem = Memory(rom)
vdp = TMS9918A()

GAME_STATE = 0xE000
GAME_SUBSTATE = 0xE001
KONAMI_LOGO_SCROLL_UP_NUM_LEFT = 0xE00A
KONAMI_LOGO_PNT_ADDRESS = 0xE00E

## Implements 0x48DD.
def write_upwards_scrolling_konami_logo(vdp: TMS9918A, mem: Memory):
	name_offset = mem.get_word(KONAMI_LOGO_PNT_ADDRESS)
	name_offset -= 0x20
	mem.set_word(KONAMI_LOGO_PNT_ADDRESS, name_offset)

	## Patterns start at 0x490F, see 0x48C9.
	patterns = Konami(mem).uncompress_patterns(address=mem.get_word(0x48C9 + 1))
	num_patterns = len(patterns)
	## Just 1 color (white), see 0x48D8.
	color = mem.get_word(0x48D8 + 1)
	colors = np.array([color] * (8 * num_patterns))

	character_id = 0x40
	## Copy characters to VRAM.
	for band in range(3):
		vdp.set_patterns(patterns, index=character_id, band=band)
		vdp.set_pattern_colors(colors, index=character_id, band=band)

	for num in (0x03, 0x0B, 0x0C):
		vdp.write_vram(name_offset,
			np.arange(character_id, character_id + num)
		)

		name_offset += 0x20
		character_id += num
	num = 0x0C
	vdp.write_vram(name_offset, np.zeros(num))
	vdp.write_vram(0x3800, [0x59])

	mem[KONAMI_LOGO_SCROLL_UP_NUM_LEFT] -= 1

def gamestate00_substate01(vdp: TMS9918A, mem: Memory):
	write_upwards_scrolling_konami_logo(vdp, mem)
	if mem[KONAMI_LOGO_SCROLL_UP_NUM_LEFT] != 0x00:
		return

	mem[GAME_SUBSTATE] += 1


all_names = np.tile(np.arange(256), 3)	## [0, ..., 255, 0, ..., 255, 0, ..., 255]
vdp.color_register = 0xE4	## 0x46B0
running = True
while running:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

	## Start with a new canvas, with the backdrop color.
	vdp_backdrop_color_id  = vdp.color_register & 0x0F
	vdp_backdrop_color_rgb = vdp.get_palette()[vdp_backdrop_color_id]
	window.fill(vdp_backdrop_color_rgb, rect=msx_screen_rect)

	print(f"gamestate={mem[GAME_STATE]:02X}, substate={mem[GAME_SUBSTATE]:02X}")
	if mem[GAME_STATE] == 0x00:
		if mem[GAME_SUBSTATE] == 0x00:
			mem[KONAMI_LOGO_SCROLL_UP_NUM_LEFT] = mem[0x48BB+1]
			mem.set_word(KONAMI_LOGO_PNT_ADDRESS, mem.get_word(0x48C0+1))
			mem[GAME_SUBSTATE] = 0x01
		elif mem[GAME_SUBSTATE] == 0x01:
			gamestate00_substate01(vdp, mem)
		else:
			raise NotImplementedError
	else:
		raise NotImplementedError

	surf = vdp.make_surface()
	window.blit(source=surf, dest=(0, 0))

	## Show all available characters.
	if True:
		vdp_patterns_surface = vdp.make_surface(pnt=all_names)
		window.blit(source=vdp_patterns_surface, dest=msx_vdp_patterns_rect)

	pygame.display.update()
	fps_clock.tick(FPS)
	#fps_clock.tick(10)
