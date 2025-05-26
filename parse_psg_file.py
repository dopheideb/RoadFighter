#!/usr/bin/env python3

## Based on documentation in OpenMSX file 
## /usr/share/openmsx/scripts/_psg_log.tcl

import argparse
import math
#import pprint
import sys



parser = argparse.ArgumentParser(description='Parse a PSG (Programmable Sound Generator) file')
parser.add_argument('psg_filename', help='The name of the PSG file to parse.')
args = parser.parse_args()

psg = open(args.psg_filename, 'rb').read()

if psg[0] != 0x50: ## 'P'
	raise AssertionError(f'The file does not begin with a PSG header. Byte 0 is {psg[0]:#02x} instead of 0x50.')
if psg[1] != 0x53: ## 'S'
	raise AssertionError(f'The file does not begin with a PSG header. Byte 1 is {psg[1]:#02x} instead of 0x53.')
if psg[2] != 0x47: ## 'G'
	raise AssertionError(f'The file does not begin with a PSG header. Byte 2 is {psg[2]:#02x} instead of 0x47.')
if psg[3] != 0x1A:
	raise AssertionError(f'The file does not begin with a PSG header. Byte 3 is {psg[3]:#02x} instead of 0x1A.')



def freqdiv2note(freqdiv):
	if freqdiv == 0x000:
		return 'n/a'
	## "A common choice is setting the A above middle C (A4) at f0 = 440 Hz."
	A4_freq = 440.000
	
	CPU_FREQ = 3579545.0
	PSG_EXT_FREQ = CPU_FREQ / 2
	PSG_NGC_FREQ = PSG_EXT_FREQ / 16
	freq = PSG_NGC_FREQ / freqdiv
	## Base of logarithm is irrelevant, so no need to specify the base.
	steps_from_A4 = round((math.log(freq) - math.log(A4_freq)) / (math.log(2)/12))
	octave = 4 + (steps_from_A4 + 9) // 12
	note_idx = (steps_from_A4 + 9) % 12
	notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
	note = notes[note_idx]
	return f'{note}{octave}'
assert freqdiv2note(0xd5d) == 'C1'
assert freqdiv2note(0x6af) == 'C2'
assert freqdiv2note(0x357) == 'C3'
assert freqdiv2note(0x1ac) == 'C4'
assert freqdiv2note(0x0d6) == 'C5'
assert freqdiv2note(0x06b) == 'C6'
assert freqdiv2note(0x035) == 'C7'
assert freqdiv2note(0x01b) == 'C8'
assert freqdiv2note(0xc9c) == 'C#1'
assert freqdiv2note(0x64e) == 'C#2'
assert freqdiv2note(0x327) == 'C#3'
assert freqdiv2note(0x194) == 'C#4'
assert freqdiv2note(0x0ca) == 'C#5'
assert freqdiv2note(0x065) == 'C#6'
assert freqdiv2note(0x032) == 'C#7'
assert freqdiv2note(0x019) == 'C#8'

reg2name =\
{
	0x0:	'Channel A freq div (lsb8)',
	0x1:	'Channel A freq div (msb4)',
	0x2:	'Channel B freq div (lsb8)',
	0x3:	'Channel B freq div (msb4)',
	0x4:	'Channel C freq div (lsb8)',
	0x5:	'Channel C freq div (msb4)',
	0x6:	'Noise (lsb5)',
	0x7:	'Mixer',
	0x8:	'Channel A volume (lsb5)',
	0x9:	'Channel B volume (lsb5)',
	0xA:	'Channel C volume (lsb5)',
	0xB:	'Envelope freq div (lsb8)',
	0xC:	'Envelope freq div (msb8)',
	0xD:	'Envelope shape (lsb4)',
	0xE:	'Port A',
	0xF:	'Port B',
}

prev_reg_history = bytearray((0).to_bytes(16))
reg_history      = bytearray((0).to_bytes(16))
vdp_tick = 0
idx = 0x10
while True:
	try:
		reg = psg[idx]
		idx += 1
		
		if reg == 0xFD:
			## 0xFD means 'end of file'.
			break
		
		if reg == 0xFE or reg == 0xFF:
			## 0xFE means 'number of interrupts'.
			if reg == 0xFE:
				val = psg[idx]
				idx += 1
			else:
				## 0xFF means 'single interrupt'.
				val = 1
                        
			freqdiv_A = (reg_history[1] << 8) | reg_history[0]
			if reg_history[8] == 0x00:
				freqdiv_A = 0x0
			freqdiv_B = (reg_history[3] << 8) | reg_history[2]
			if reg_history[9] == 0x00:
				freqdiv_B = 0x0
			freqdiv_C = (reg_history[5] << 8) | reg_history[4]
			if reg_history[10] == 0x00:
				freqdiv_C = 0x0
			
			mode = 'full'
			if mode == 'full':
				print(f'VDP tick {vdp_tick:05d}: A={freqdiv_A:03x},{freqdiv2note(freqdiv_A):3s}@{reg_history[8]:2d} B={freqdiv_B:03x},{freqdiv2note(freqdiv_B):3s}@{reg_history[9]:2d} C={freqdiv_C:03x},{freqdiv2note(freqdiv_C):3s}@{reg_history[10]:2d} N={reg_history[6]:x} E={reg_history[12]:02x}{reg_history[11]:02x}@{reg_history[13]:x} M={reg_history[7]:02x} ~Mn={~reg_history[7]>>3&0x7:03b} ~Mt={~reg_history[7]&0x7:03b}')
			elif (mode == 'compact' and (
					reg_history[0:8]   != prev_reg_history[0:8] or
					reg_history[11:16] != prev_reg_history[11:16] or
					(reg_history[8]  & 0x10) != (prev_reg_history[8]  & 0x10) or
					(reg_history[9]  & 0x10) != (prev_reg_history[9]  & 0x10) or
					(reg_history[10] & 0x10) != (prev_reg_history[10] & 0x10) or
					False)):#reg_history[8:11]  != prev_reg_history[8:11]:
				print(f'VDP tick {vdp_tick:05d}: A={freqdiv_A:03x},{freqdiv2note(freqdiv_A):3s} B={freqdiv_B:03x},{freqdiv2note(freqdiv_B):3s} C={freqdiv_C:03x},{freqdiv2note(freqdiv_C):3s} N={reg_history[6]:x} E={reg_history[12]:02x}{reg_history[11]:02x}@{reg_history[13]:x} M={reg_history[7]:02x} ~Mn={~reg_history[7]>>3&0x7:03b} ~Mt={~reg_history[7]&0x7:03b}')
			else:
				raise ValueError
			
			prev_reg_history[:] = reg_history
			vdp_tick += val
			continue
		
		val = psg[idx]
		idx += 1
		reg_history[reg] = val
		#print(f'{reg}={val}')
	except IndexError:
		## (Beyond) end of file.
		break
