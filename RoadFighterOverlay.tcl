## Usage:
##   source RoadFighterOverlay.tcl
##   toggle_road_fighter_overlay
namespace eval road_fighter_overlay {

variable road_fighter_overlay_active false
variable text_height 8

variable game_states [list\
	"Not playing"\
	"Level select"\
	"Demo running"\
	"Pre game setup?"\
	"Demo"\
	"Playing"\
	"Crashed"\
	"GAME OVER"\
	"Reached checkpoint"
]
variable game_substates [list\
	[list "Game startup" "Scroll up Konami logo" "Show software" "Show/blink ROAD FIGHTER logo"]\
	[list "Waiting for input"]\
	[list "Start demo?" "Playing demo"]\
	[list\
		"Start new game"\
		"Play victorious music"\
		"???"\
		"Clear screen"\
		"Draw stage XX"\
		"03-05"\
		"03-06"\
		"03-07"\
		"Show empty screen"\
		"Show traffic light"\
	]\
	[list "04-00"]\
	[list\
		"Blue cars drive away"\
		"Racing"\
	]\
	[list "06-00"]\
	[list\
		"Erase circuit"\
		"Show GAME OVER letters"\
	]\
	[list "Reached checkpoint" "Clear screen" "Show progress map" "Blink minicar" "Goto nextstage"]\
]
proc init {} {
	variable text_height
	
	## Create OSD master element. It autoscales the widgets.
	osd_widgets::msx_init road_fighter
	
	osd create rectangle road_fighter.game_state\
		-x 0x08 -y 0x00\
		-w 0xC8 -h [expr {0x02 + $text_height}]\
		-rgba 0x00000080
	osd create text road_fighter.game_state.text -x 0 -y 0 -size $text_height -text ""
	
	osd create rectangle road_fighter.game_substate\
		-relx 0x08 -rely [expr {0x00 + ($text_height} + 0x02)]\
		-w 0xC8 -h [expr {0x02 + $text_height}]\
		-rgba 0x00000080
	osd create text road_fighter.game_substate.text -x 0 -y 0 -size $text_height -text ""
	
	osd create rectangle road_fighter.pos\
		-relx 0x00 -w 0x10\
		-rely 0x00 -h 0x10\
		-rgba 0x00000080
	
	osd create rectangle road_fighter.speed\
		-x 0xE0 -y 0x80\
		-w 0x13	-h $text_height\
		-rgba 0x00000080
	osd create text road_fighter.speed.text -x 0 -y 0 -size $text_height -text ""
	
	osd create rectangle road_fighter.fuel\
		-x 0xFC -y 0x80\
		-w 0x13	-h $text_height\
		-rgba 0x00000080
	osd create text road_fighter.fuel.text -x 0 -y 0 -size $text_height -text ""
	
	update_overlay
}
proc toggle_road_fighter_overlay {} {
	variable road_fighter_overlay_active
	set road_fighter_overlay_active [expr {!$road_fighter_overlay_active}]
	if {$road_fighter_overlay_active} {
		init
		set text "Road Fighter overlay activated!"
	} else {
		osd destroy road_fighter
		set text "Road Fighter overlay deactivated."
	}
	message $text info
	return $text
}
proc update_overlay {} {
	variable road_fighter_overlay_active
	if {!$road_fighter_overlay_active} return
	update_impl
	after frame [namespace code update_overlay]
}
proc update_impl {} {
	## Game state
	variable game_states
	set text_color 0xffffff
	set game_state [peek 0xE000]
	set text [format "   State 0x%02X: %s" $game_state\
		[lindex $game_states $game_state]]
	osd configure road_fighter.game_state.text\
		-text $text -rgb $text_color
	
	## Game substate
	variable game_substates
	set text_color 0xffffff
	set game_state [peek 0xE000]
	set game_substate [peek 0xE001]
	set game_substate_text\
		[lindex [lindex $game_substates $game_state] $game_substate]
	set text [format "Substate 0x%02X: %s" $game_substate $game_substate_text]
	osd configure road_fighter.game_substate.text\
		-text $text -rgb $text_color
	#if {$game_substate_text == ""} { debug break }
	
	## Car position
	#set hpos [peek 0xE04E]
	#set vpos [peek 0xE04C]
	#set hpos [peek 0xE113]
	#set vpos [peek 0xE112]
	set hpos [peek 0xE11B]
	set vpos [peek 0xE11A]
	osd configure road_fighter.pos -relx $hpos -rely $vpos

	## Speed
	set speed [format "0x%02X" [peek 0xE04F]]
	set text_color 0xffffff
	if {$speed == 0xD7} {set text_color 0xff0000}
	osd configure road_fighter.speed.text\
		-text $speed -rgb $text_color
	
	## Fuel
	set fuel [format "0x%02X" [peek 0xE083]]
	set text_color 0xffffff
	if {$fuel <= 0x09} {set text_color 0xffa500}
	if {$fuel <= 0x00} {set text_color 0xff0000}
	osd configure road_fighter.fuel.text\
		-text $fuel -rgb $text_color
}

namespace export toggle_road_fighter_overlay
};## namespace road_fighter_overlay

namespace import road_fighter_overlay::*
