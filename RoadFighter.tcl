set speed 75
ram_watch add 0xE002 -type byte -desc DifficultyLevel
ram_watch add 0xE008 -type byte -desc NewlyPressedKeys
ram_watch add 0xE009 -type byte -desc PressedKeys
ram_watch add 0xE028 -type byte -desc SoundID
ram_watch add 0xE049 -type byte -desc CarState
ram_watch add 0xE04C -type byte -desc CarVPos
ram_watch add 0xE04E -type byte -desc CarHPos
ram_watch add 0xE04F -type byte -desc Speed
ram_watch add 0xE057 -type byte -desc FuelTicker
ram_watch add 0xE083 -type byte -desc FuelLeft
ram_watch add 0xE105 -type byte -desc TruckAppearing
ram_watch add 0xE10E -type byte -desc MinicarVPos
