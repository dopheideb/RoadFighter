#!/bin/bash

if [ $# -eq 0 ]
then
	<<__EOT__ cat
Usage: $0 START [END]

Examples:

    Single word at RAM 0x4000:
        $0 0x4000
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
if [ $[ ($END - $START) % 2 ] -eq 0 ]
then
	## Fix user error, we want whole words.
	END=$[ $END + 1  ]
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
	-e 's/(..)(..)/\tdefw 0x\U\2\1\t\t;\n/g'\
| while IFS='' read -r LINE
do
	if [ "${LINE}" = '' ]; then continue; fi
	printf "%s%04x\n" "${LINE}" "${START}"
	let ++START
done
