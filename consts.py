import libtcodpy as libtcod

################################################################################
#Ui configs
################################################################################

#actual size of the window
SCREEN_WIDTH = 100
SCREEN_HEIGHT = 60

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

LIMIT_FPS = 20  #20 frames-per-second maximum
 
################################################################################
#Dungeon gen configs
################################################################################

#size of the map
MAP_WIDTH = 100
MAP_HEIGHT = 50
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 15 #15
ROOM_MIN_SIZE = 4 #6
MAX_ROOMS = 50

MAX_MONSTERS = [[10, 1], [15, 2], [21, 4], [30, 6], [45, 8], [60, 10], [90, 13]]
MAX_ITEMS = [[7, 1], [10, 5], [15, 7]]
 
################################################################################
#Vision stuff
################################################################################

FOV_ALGO = libtcod.FOV_BASIC #libtcod.FOV_SHADOW
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 0 #infinite

LIGHT_MAX = 100
LIGHT_MIN = 0

MIN_ITEM_LIGHT_LEVEL = 30
MIN_TILE_LIGHT_LEVEL = 0

##Colors

MONSTER_SEEN_COLOR = libtcod.Color(100, 0, 0)
DARK_WALL_COLOR = (0, 0, 30)
LIGHT_WALL_COLOR = (50, 30, 0)
DARK_GROUND_COLOR = (20, 20, 40)
LIGHT_GROUND_COLOR = (90, 80, 70)

################################################################################
#Item stuff
################################################################################

####Items
LIGHT_ORB_CHANCE = [[35, 1]]
LIGHTORB_LSL = 6

DARK_ORB_CHANCE = [[35, 1]]
DARKORB_LSL = -6

WATERBALLOON_CHANCE = [[10, 1], [20, 3]]
WATERBALLOON_RADIUS = 2

LIGHTNING_CHANCE = [[5, 4]]

CONFUSE_CHANCE = [[10, 2]]

####Features

SMALL_TORCH_CHANCE = [[35, 1], [25, 3], [15, 5], [10, 7]]
SMALL_TORCH_LSL = 4

TORCH_CHANCE = [[15, 2], [25, 4], [35, 5]]
TORCH_LSL = 8

LARGE_TORCH_CHANCE = [[5, 3], [15, 5], [25, 7], [35, 9]]
LARGE_TORCH_LSL = 12


################################################################################
#Enemy stuff
################################################################################

#AI stuff
MAX_MONSTER_MOVE = 10

########################################
#Enemy stuff
########################################

##Goblins
GOBLIN_CHANCE = [[80, 1], [50, 3], [15, 5]]
GOBLIN_HP = 20
GOBLIN_POW = 3
GOBLIN_DEF = 0
GOBLIN_XP = 15
GOBLIN_LSL = 4
GOBLIN_COLOR = libtcod.desaturated_green

##Orcs
ORC_CHANCE = [[80, 1]]
ORC_HP = 30
ORC_POW = 4
ORC_DEF = 0
ORC_XP = 35
ORC_LSL = 6
ORC_COLOR = libtcod.desaturated_green

##Trolls
TROLL_CHANCE = [[15, 3], [30, 5], [60, 7]]
TROLL_HP = 30
TROLL_POW = 8
TROLL_DEF = 2
TROLL_XP = 100
TROLL_COLOR = libtcod.darker_green


################################################################################
#Misc game stuff
################################################################################


#spell values
HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25
 
#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150




VISION_DISTANCE_WITHOUT_LIGHT = 4

#VISION STUFF
 