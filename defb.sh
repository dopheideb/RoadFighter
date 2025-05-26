#!/bin/bash

if [ $# -eq 0 ]
then
	<<__EOT__ cat
Usage: $0 START [END]

Examples:

    Single byte at RAM 0x4001:
        $0 0x4001
__EOT__
	exit 1
fi

START="${1:-0x4000}"
if [ "${START:0:2}" = '0x' ]
then
	## Interpret as hex.
	START=$[ ${START} ]
fi
END="${2:-${START}}"
if [ "${END:0:2}" = '0x' ]
then
	## Interpret as hex.
	END=$[ ${END} ]
fi

dd\
	if=RoadFighter.rom\
	bs=1\
	skip="$[${START} - 0x4000]"\
	count=$[$END - $START + 1]\
	status=none\
| xxd\
	-plain\
	--cols 0\
| sed\
	-r\
	-e 's/(..)/\tdefb 0x\U\1\t\t;\n/g'\
| while IFS='' read -r LINE
do
	if [ "${LINE}" = '' ]; then continue; fi
	printf "%s%04x\n" "${LINE}" "${START}"
	let ++START
done
