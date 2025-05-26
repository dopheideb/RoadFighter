#!/usr/bin/env python3

import fileinput
import re

for line in fileinput.input(encoding="utf-8"):
	m = re.search(r'^\t((jr (([a-z]+),)?)\$([+-][0-9]+)(\s+);)([0-9A-Fa-f]+)$', line)
	if not m:
		print(line, end='')
		continue
	#print(line, end='')
	condition = m.group(4)
	offset = int(m.group(5))
	address = int(m.group(7), base=16)
	jump_destination_absolute = address + offset
	disassembly = f"{m.group(2)}${offset:+d}"
	spacing = "\t\t\t" if len(disassembly) < 8 else "\t\t"
	if_str = f"if ({condition}) " if condition else ""
	print(f"\t{disassembly}{spacing};{address:04x} {if_str}jump to 0x{jump_destination_absolute:04X}")
