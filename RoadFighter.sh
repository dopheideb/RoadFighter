#!/bin/bash
ROAD_FIGHTER_DIR="$(dirname "$0")"
openmsx\
	"${ROAD_FIGHTER_DIR}/RoadFighter.rom"\
	-machine C-BIOS_MSX1\
	-script "${ROAD_FIGHTER_DIR}/RoadFighter.tcl" &
