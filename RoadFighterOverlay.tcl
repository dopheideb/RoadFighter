## Usage:
##   source RoadFighterOverlay.tcl
##   toggle_road_fighter_overlay
namespace eval road_fighter_overlay {

variable road_fighter_overlay_active false
variable text_height 7

variable game_states [list\
	"Not playing"\
	"Level select"\
	"Demo running"\
	"Pre game setup"\
	"Demo"\
	"Playing"\
	"Crashed"\
	"GAME OVER"\
	"Reached checkpoint"
]
variable game_substates [list\
	[list\
		"Game startup"\
		"Scroll up Konami logo"\
		"Show software"\
		"Show ROAD FIGHTER logo"\
		"Blink ROAD FIGHTER logo"\
	]\
	[list\
		"Waiting for input"\
	]\
	[list\
		"Start demo?"\
		"Playing demo"\
	]\
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
	[list\
		"Reached checkpoint"\
		"Clear screen"\
		"Show progress map"\
		"Blink minicar"\
		"Go to next stage"\
	]\
]
variable car_states [list\
	"All okay"\
	"Crashed"\
	"Out of fuel, with speed>0"\
	"Reached checkpoint"\
	"Skidding"\
	"Bounce"\
	"Respawn"\
	"Spinning"\
]
variable moving_object_idx2name [list\
	"Green car"\
	"Blue car (regular)"\
	"Blue car (speeding)"\
	"Purple car"\
	"Redneck hot rodder (regular)"\
	"Redneck hot rodder (speeding)"\
	"18-wheeler (no oil drum)"\
	"18-wheeler (with oil drum)"\
	"Bonus fuel heart"\
]
variable moving_object_idx2rgb [list\
	0x21c842\
	0x0000ff\
	0x0000ff\
	0xc95bba\
	0x000000\
	0x000000\
	0xcccccc\
	0xcccccc\
	0xc95bba\
]
proc init {} {
	variable text_height

	## Create OSD master element. It autoscales the widgets.
	osd_widgets::msx_init road_fighter

	osd create rectangle road_fighter.game_state\
		-relx 0x08 -rely [expr {0 * (0x01 + $text_height)}]\
		-relw 0xC8 -relh [expr {0x01 + $text_height}]\
		-rgba 0x00000080
	osd create text road_fighter.game_state.text -x 0 -y 0 -size $text_height -text ""

	osd create rectangle road_fighter.game_substate\
		-relx 0x08 -rely [expr {1 * (0x01 + $text_height)}]\
		-relw 0xC8 -relh [expr {0x01 + $text_height}]\
		-rgba 0x00000080
	osd create text road_fighter.game_substate.text -x 0 -y 0 -size $text_height -text ""

	osd create rectangle road_fighter.car_state\
		-relx 0x08 -rely [expr {2 * (0x01 + $text_height)}]\
		-relw 0xC8 -relh [expr {0x01 + $text_height}]\
		-rgba 0x00000080
	osd create text road_fighter.car_state.text -x 0 -y 0 -size $text_height -text ""

	osd create rectangle road_fighter.next_moving_object\
		-relx 0x08 -rely [expr {3 * (0x01 + $text_height)}]\
		-relw 0xC8 -relh [expr {0x01 + $text_height}]\
		-rgba 0x00000080
	osd create text road_fighter.next_moving_object.text -x 0 -y 0 -size $text_height -text ""

	#osd create rectangle road_fighter.pos_box\
	#	-relx 0x00 -relw 0x09\
	#	-rely  666 -relh 0x10\
	#	-rgba 0x00000060
	osd_widgets::create_power_bar\
		road_fighter.pos_box\
		9 16\
		0x00000000 0xff770020 0xff0000ff
	osd create text road_fighter.pos_text\
		-relx 666 -rely 666\
		-size $text_height -text ""

	osd create rectangle road_fighter.speed\
		-relx [expr { 0xC0 + 4 }] -rely 0x80\
		-relw 0x13 -relh $text_height\
		-rgba 0x00000080
	osd create text road_fighter.speed.text\
		-relx 0 -rely 0x20\
		-size $text_height -text ""

	osd create rectangle road_fighter.fuel\
		-relx [expr { 0xD8 + 4 }] -rely 0x80\
		-relw 0x13 -relh $text_height\
		-rgba 0x00000080
	osd create text road_fighter.fuel.text\
		-relx 0 -rely 0\
		-size $text_height -text ""

	osd create rectangle road_fighter.distance_travelled\
		-relx [expr { 0xC8 + 2 }] -rely 0x70\
		-relw 0x13 -relh $text_height\
		-rgba 0x00000080
	osd create text road_fighter.distance_travelled.text\
		-relx 0 -rely 0\
		-size $text_height -text ""

	update_overlay
}
proc toggle_road_fighter_overlay {} {
	variable road_fighter_overlay_active
	set road_fighter_overlay_active [expr {!$road_fighter_overlay_active}]
	if {$road_fighter_overlay_active} {
		osd destroy road_fighter
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
	set text [format "Game state 0x%02X: %s" $game_state\
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
	set text [format "Game substate 0x%02X: %s" $game_substate $game_substate_text]
	osd configure road_fighter.game_substate.text\
		-text $text -rgb $text_color
	#if {$game_substate_text == ""} { debug break }

	## Car state.
	variable car_states
	set text_color 0xffffff
	set car_state [peek 0xE049]
	set car_state_text\
		[lindex $car_states $car_state]
	set text [format "Car state %d: %s" $car_state $car_state_text]
	osd configure road_fighter.car_state.text\
		-text $text -rgb $text_color

	variable moving_object_idx2name
	variable moving_object_idx2rgb
	set num_spare_moving_objects [peek 0xE0C1]
	if {$num_spare_moving_objects == 0 || $num_spare_moving_objects >= 3} {
		set text_color 0xffffff
		set text [format ""]
	} else {
		if {$num_spare_moving_objects == 1} {
			set next_moving_object_address 0xE0D3
		} else {
			set next_moving_object_address 0xE0C3
		}
		set next_moving_object_idx [peek $next_moving_object_address]
		set next_moving_object_text\
			[lindex $moving_object_idx2name $next_moving_object_idx]
		set text_color\
			[lindex $moving_object_idx2rgb $next_moving_object_idx]
		set text [format "Next object #1 %d: %s" $next_moving_object_idx $next_moving_object_text]
	}
	osd configure road_fighter.next_moving_object.text\
		-text $text -rgb $text_color

	## Car position
	set vpos [peek 0xE112]
	set hpos [peek 0xE113]
	if {$vpos >= 0xC0} {
		osd configure road_fighter.pos_box\
			-rely 999
	} else {
		osd configure road_fighter.pos_box\
			-relx [expr {$hpos+4}]\
			-rely [expr {$vpos+1}]
		set pos [format "(%d,%d)" $hpos $vpos]
		set text_color 0xff0000
		osd configure road_fighter.pos_box.text\
			-text $pos
	}

	## Speed
	set speed [format "#%02X" [peek 0xE04F]]
	set text_color 0xffffff
	if {$speed == 0xD7} {set text_color 0xff0000}
	osd configure road_fighter.speed.text\
		-text $speed -rgb $text_color

	## Fuel
	set fuel [format "#%02X" [peek 0xE083]]
	set text_color 0xffffff
	if {$fuel <= 0x09} {set text_color 0xffa500}
	if {$fuel <= 0x00} {set text_color 0xff0000}
	osd configure road_fighter.fuel.text\
		-text $fuel -rgb $text_color

	## Distance travelled.
	set distance_travelled [format "#%06X" [expr {[peek_u16 0xE077] | [peek_u8 0xE079] << 16}]]
	set text_color 0xffffff
	osd configure road_fighter.distance_travelled.text\
		-text $distance_travelled -rgb $text_color
}

namespace export toggle_road_fighter_overlay
};## namespace road_fighter_overlay

namespace import road_fighter_overlay::*

## Set to on.
toggle_road_fighter_overlay
