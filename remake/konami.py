#!/usr/bin/env python3

import memory
import numpy as np

class Konami:
	def __init__(self, memory: memory.Memory) -> None:
		self.memory = memory

	def uncompress_patterns(self, address) -> np.array:
		'''

		Uncompresses compressed patterns starting at memory 
		specified offset.

		The resuling numpy array (dtype=np.uint8) is essentially 
		a list of patterns. Every element is 1 pattern (8 
		bytes).

		'''
		## Cut into separate patterns later.
		patterns_raw = []

		while True:
			opcode = self.memory[address]
			if opcode == 0x00:
				break

			if opcode <= 0x7F:
				copy_count = opcode
				address += 1
				byte = self.memory[address]
				address += 1
				for _ in range(copy_count):
					patterns_raw.append(byte)
				continue

			if opcode == 0x80:
				raise NotImplementedError
				continue

			if opcode >= 0x81:
				copy_count = opcode & 0x7F
				address += 1
				for _ in range(copy_count):
					byte = self.memory[address]
					address += 1
					patterns_raw.append(byte)
				continue

		return np.array(
				patterns_raw,
				dtype=np.uint8,
			).reshape((-1, 8))



if __name__ == '__main__':
	from   memory import Memory
	import pygame
	from   rom import ROM
	from   tms9918a import TMS9918A

	pygame.init()
	pygame.display.set_caption('Konami')
	screen = pygame.display.set_mode(
	        size=(32 * 8, 24 * 8),
	        flags=pygame.SCALED,
	)

	## Set background to, say, green, so we can test if the 
	## transparent color works.
	BACKGROUND = (0,0x80,0)
	screen.fill(BACKGROUND)

	rom = ROM(file='./RoadFighter.rom')
	mem = Memory(rom=rom)
	vdp = TMS9918A()

	## We want to see __all__ characters.
	vdp.pattern_name_table = np.array([*range(256)] * 3)

	## Symbols: roughly A-Z
	##
	## Patterns start at 0x478A.
	patterns = Konami(mem).uncompress_patterns(mem.get_word(0x4776 + 1))
	colors   = np.array([mem[0x477F + 1]] * 8 * patterns.shape[0])
	for band in range(3):
		vdp.set_patterns(patterns, index=0x10, band=band)
		vdp.set_pattern_colors(colors, index=0x10, band=band)

	## Road Fighter logo.
	##
	## Patterns start at 0x4A25.
	patterns = Konami(mem).uncompress_patterns(mem.get_word(0x49B1 + 1))
	colors   = np.array([mem[0x48D8 + 1]] * 8 * patterns.shape[0])
	for band in range(3):
		vdp.set_patterns(patterns, index=0xC0, band=band)
		vdp.set_pattern_colors(colors, index=0xC0, band=band)

	surf = vdp.make_surface()
	screen.blit(surf, (0, 0))
	pygame.display.update()

	running = True
	while running:
		event = pygame.event.wait()
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_q:
				running = False


	##
	## Konami logo
	##
	vdp.clear()

	## Light blue background.
	screen.fill(vdp.get_palette()[5])

	## Patterns start at 0490F.
	patterns = Konami(mem).uncompress_patterns(mem.get_word(0x48C9 + 1))
	colors   = np.array([mem[0x48D8 + 1]] * 8 * patterns.shape[0])
	character_id = 0x40
	for band in range(3):
		vdp.set_patterns(patterns, index=character_id, band=band)
		vdp.set_pattern_colors(colors, index=character_id, band=band)

	## Organize the characters to show the Konami logo.
	E00E = 0x3AAA - 0x3800
	character_id = 0x40
	for num in (0x03, 0x0B, 0x0C):
		vdp.pattern_name_table[E00E:E00E+num] = \
			list(range(character_id, character_id + num))

		character_id += num
		E00E += 0x20

	surf = vdp.make_surface()
	screen.blit(surf, (0, 0))
	pygame.display.update()

	running = True
	while running:
		event = pygame.event.wait()
		if event.type == pygame.QUIT:
			running = False
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_q:
				running = False

	pygame.quit()
