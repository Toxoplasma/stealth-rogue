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
MAP_WIDTH = 120
MAP_HEIGHT = 50
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 20 #15
ROOM_MIN_SIZE = 4 #6
MAX_ROOMS = 30
 
################################################################################
#Vision stuff
################################################################################

FOV_ALGO = libtcod.FOV_BASIC #libtcod.FOV_SHADOW
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 0 #infinite

LIGHT_MAX = 100
LIGHT_MIN = 0

MIN_ITEM_LIGHT_LEVEL = 30
MIN_TILE_LIGHT_LEVEL = 20

##Colors

MONSTER_SEEN_COLOR = libtcod.Color(100, 0, 0)
DARK_WALL_COLOR = (0, 0, 100)
LIGHT_WALL_COLOR = (90, 70, 10)
DARK_GROUND_COLOR = (50, 50, 100)
LIGHT_GROUND_COLOR = (155, 125, 0)

################################################################################
#Item stuff
################################################################################

LIGHT_ORB_CHANCE = 35
LIGHTORB_LSL = 6

DARK_ORB_CHANCE = 35
DARKORB_LSL = -6

TORCH_LSL = 8

################################################################################
#Enemy stuff
################################################################################

#AI stuff
MAX_MONSTER_MOVE = 10

########################################
#Enemy stuff
########################################

##Orcs
ORC_HP = 30
ORC_POW = 4
ORC_DEF = 0
ORC_XP = 35

##Trolls
TROLL_HP = 30
TROLL_POW = 8
TROLL_DEF = 2
TROLL_XP = 100


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
 