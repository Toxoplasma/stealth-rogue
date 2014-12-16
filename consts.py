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
SCORE_WIDTH = 30
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

#NUM_MONSTERS = [[5, 1], [10, 2], [15, 4], [25, 6], [35, 8], [50, 10], [80, 13]]
#NUM_ITEMS = [[5, 1], [10, 5], [15, 7]]
#NUM_FEATURES = [[10, 1]]

NUM_MONSTERS = {}
NUM_ITEMS = {}
NUM_FEATURES = {}
 
################################################################################
#Vision stuff
################################################################################

FOV_ALGO = libtcod.FOV_BASIC #libtcod.FOV_SHADOW
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 0 #infinite

LIGHT_MAX = 100
LIGHT_MIN = 0

LIGHT_STRENGTH = 10 #Gets multiplied by LSLs to produce actual light amount provided
MONSTER_VISION_ANGLE = 60 #degrees
VISION_CONE_DISPLAY_DIST = 4
VISION_CONE_RED = 50
VISION_CONE_GREEN = 50
VISION_CONE_BLUE = 50

MIN_ITEM_LIGHT_LEVEL = 0
MIN_TILE_LIGHT_LEVEL = 0

##Colors

MONSTER_SEEN_COLOR = libtcod.Color(100, 0, 0)
DARK_WALL_COLOR = (0, 0, 30)
LIGHT_WALL_COLOR = (50, 30, 0)
DARK_GROUND_COLOR = (20, 20, 40)
LIGHT_GROUND_COLOR = (60, 60, 80)
DARK_PLANT_COLOR = (20, 40, 30)
LIGHT_PLANT_COLOR = (60, 80, 60)

R_FACTOR = 1.5
B_FACTOR = 0.0
G_FACTOR = 0.8

################################################################################
#Item stuff
################################################################################

####Items
LIGHT_ORB_CHANCE = [[15, 1]]
LIGHT_ORB_LSL = 6
LIGHT_ORB_COLOR = libtcod.light_orange
LIGHT_ORB_THROWN_COLOR = libtcod.black
LIGHT_ORB_TICK_TIME = 20

DARK_ORB_CHANCE = [[35, 1]]
DARK_ORB_LSL = -6
DARK_ORB_COLOR = libtcod.light_sky
DARK_ORB_THROWN_COLOR = libtcod.black
DARK_ORB_TICK_TIME = 40

WATERBALLOON_CHANCE = [[10, 1], [20, 3]]
WATERBALLOON_RADIUS = 2
WATERBALLOON_COLOR = libtcod.blue

LIGHTNING_CHANCE = [[5, 4]]
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5

CONFUSE_CHANCE = [[5, 1], [10, 3], [20, 5]]
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 12

FIREBALL_CHANCE = [[0, 1]]
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25

FLASHBANG_CHANCE = [[10, 1], [15, 3], [20, 5]]
FLASHBANG_RADIUS = 5
FLASHBANG_LENGTH = 8

SPEED_CHANCE = [[10, 1], [20, 4]]
SPEED_MUL = 0.5
SPEED_TICK_TIME = 50
SPEED_TICK_NUM = 5

####Features

TORCH_COLOR = libtcod.black

#SMALL_TORCH_CHANCE = [[35, 1], [25, 3], [15, 5], [10, 7]]
SMALL_TORCH_CHANCE = {}
SMALL_TORCH_LSL = 4

#TORCH_CHANCE = [[15, 2], [25, 4], [35, 5]]
MID_TORCH_CHANCE = {}
TORCH_LSL = 8

#LARGE_TORCH_CHANCE = [[5, 3], [15, 5], [25, 7], [35, 9]]
LARGE_TORCH_CHANCE = {}
LARGE_TORCH_LSL = 12


####Grounds






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

ORB_GOBLIN_CHANCE = [[40, 1]]
ORB_GOBLIN_HP = 20
ORB_GOBLIN_POW = 3
ORB_GOBLIN_DEF = 0
ORB_GOBLIN_XP = 45
ORB_GOBLIN_COLOR = libtcod.blue
ORB_GOBLIN_THROW_RATE = 100

##Orcs
ORC_CHANCE = {} #[[80, 1]]
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


##Basic guards
GUARD_CHANCE = {} #[[80, 1]]
SMALL_TORCH_GUARD_CHANCE = {}
MID_TORCH_GUARD_CHANCE = {}
GUARD_HP = 30
GUARD_POW = 4
GUARD_DEF = 0
GUARD_XP = 35
GUARD_LSL = 6
GUARD_COLOR = libtcod.white
GUARD_CHAR = 'g'
SMALL_TORCH_GUARD_LSL = 4
MID_TORCH_GUARD_LSL = 6

##Glowmoths!
GLOWMOTH_CHANCE = {} #[[80, 1]]
GLOWMOTH_HP = 20
GLOWMOTH_POW = 3
GLOWMOTH_DEF = 0
GLOWMOTH_XP = 20
GLOWMOTH_COLOR = libtcod.light_blue
GLOWMOTH_CHAR = 'w'
GLOWMOTH_ORB_TICKTIME = 40
GLOWMOTH_ORB_LSL = 3

##Screaming flower



DEAD_GUARD_TORCH_TICK = 10



################################################################################
#Misc game stuff
################################################################################


#spell values
HEAL_AMOUNT = 40

REMEMBER_LEVEL = {}

 
#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150


VISION_DISTANCE_WITHOUT_LIGHT = 4

#VISION STUFF
 

################################################################################
#Level stuff
################################################################################

#Grounds
REMEMBER_LEVEL['grounds'] = True
NUM_MONSTERS['grounds'] = [[5, 1], [8, 2], [12, 3], [15, 4], [20, 5]]
NUM_ITEMS['grounds'] = [[3, 1], [4, 2], [5, 3], [6, 4], [7, 5]]
NUM_FEATURES['grounds'] = [[8, 1], [12, 2], [16, 3], [20, 4], [24, 5]]

GUARD_CHANCE['grounds'] = [[30, 1]]
SMALL_TORCH_GUARD_CHANCE['grounds'] = [[30, 1], [25, 3], [15, 5]]
MID_TORCH_GUARD_CHANCE['grounds'] = [[15, 1], [20, 3], [30, 5]]

SMALL_TORCH_CHANCE['grounds'] = [[35, 1], [25, 3], [15, 5]]
MID_TORCH_CHANCE['grounds'] = [[15, 1], [25, 2], [20, 3], [10, 5]]
LARGE_TORCH_CHANCE['grounds'] = [[10, 2], [20, 3], [30, 4], [35, 5]]


#Gardens
REMEMBER_LEVEL['gardens'] = False
NUM_MONSTERS['gardens'] = [[10, 1], [14, 2], [18, 3], [22, 4], [25, 5]]
NUM_ITEMS['gardens'] = [[3, 1], [4, 2], [5, 3], [6, 4], [7, 5]]
NUM_FEATURES['gardens'] = [[120, 1]] #This gets ignored currently

GUARD_CHANCE['gardens'] = [[30, 1]]
SMALL_TORCH_GUARD_CHANCE['gardens'] = [[0, 1]]
MID_TORCH_GUARD_CHANCE['gardens'] = [[0, 1]]
GLOWMOTH_CHANCE['gardens'] = [[5, 1]]

SMALL_TORCH_CHANCE['gardens'] = [[35, 1], [25, 3], [15, 5]]
MID_TORCH_CHANCE['gardens'] = [[0, 1]]
LARGE_TORCH_CHANCE['gardens'] = [[0, 1]]

NUM_GARDEN_DIRECTORS = 60
GARDEN_DIR_MIN = 10
GARDEN_DIR_MAX = 30
GARDEN_DIR_MIN_SPEED = 10
GARDEN_DIR_MAX_SPEED = 40

GARDEN_TORCH_FREQ = 8