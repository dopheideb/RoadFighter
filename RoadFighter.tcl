#debug set_watchpoint write_mem 0xe00d
source RoadFighterOverlay.tcl
## Space+Left are stuck on my OpenMSX, can we "unstuck" them? No.
#after time 2.00 "keymatrixup 8 0x11"

set speed 75
ram_watch add 0xE000 -type byte -desc GameState
ram_watch add 0xE001 -type byte -desc GameSubState
ram_watch add 0xE002 -type byte -desc Level_AB
ram_watch add 0xE008 -type byte -desc NewlyPressedKeys
ram_watch add 0xE009 -type byte -desc PressedKeys
ram_watch add 0xE010 -type byte -desc ?A?
ram_watch add 0xE011 -type byte -desc ?A?
ram_watch add 0xE012 -type byte -desc SndID_A
ram_watch add 0xE013 -type word -desc SndAddr_A
ram_watch add 0xE01D -type byte -desc SndID_B
ram_watch add 0xE01E -type word -desc SndAddr_B
ram_watch add 0xE028 -type byte -desc SndID_C
ram_watch add 0xE029 -type word -desc SndAddr_C
ram_watch add 0xE032 -type word -desc ???
ram_watch add 0xE034 -type word -desc ???
ram_watch add 0xE03F -type byte -desc ScoreBCD_UT
ram_watch add 0xE040 -type byte -desc ScoreBCD_HT
ram_watch add 0xE041 -type byte -desc ScoreBCD_TH
#ram_watch add 0xE042 -type byte -desc ScoreBCD_MT
ram_watch add 0xE043 -type byte -desc Stage
ram_watch add 0xE049 -type byte -desc CarState
ram_watch add 0xE04B -type word -desc CarVPos
#ram_watch add 0xE04C -type byte -desc CarVPos
ram_watch add 0xE04E -type byte -desc CarHPos
ram_watch add 0xE04F -type byte -desc Speed
ram_watch add 0xE057 -type byte -desc FuelTicker
ram_watch add 0xE077 -type word -desc DistanceLM
ram_watch add 0xE079 -type byte -desc DistanceH
ram_watch add 0xE083 -type byte -desc FuelLeft
ram_watch add 0xE0B9 -type byte -desc NumHeartsGrabbed
ram_watch add 0xE105 -type byte -desc TruckAppearing
ram_watch add 0xE10E -type byte -desc MinicarVPos
ram_watch add 0xEB0D -type word -desc ???
ram_watch add 0xEE0D -type word -desc ???
