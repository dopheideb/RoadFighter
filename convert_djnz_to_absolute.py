#!/usr/bin/env python3

import fileinput
import re

for line in fileinput.input(encoding="utf-8"):
	m = re.search(r'^\tdjnz \$([+-][0-9]+)\s+;([0-9A-Fa-f]+)$', line)
	if not m:
		#print(line, end='')
		continue
	#print(line, end='')
	offset = int(m.group(1))
	address = int(m.group(2), base=16)
	jump_destination_absolute = address + offset
	disassembly = f"djnz ${offset:+d}"
	spacing = "\t\t\t" if len(disassembly) < 8 else "\t\t"
	print(f"\t{disassembly}{spacing};{address:04x} if (--B != 0) jump to 0x{jump_destination_absolute:04X}")
