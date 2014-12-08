#!/usr/bin/python
#
# libtcod python tutorial
#
 
import libtcodpy as libtcod
import math
import textwrap
import shelve
import random
 
from consts import *

 
 
class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, dark_color, light_color, block_sight = None):
		self.blocked = blocked
 
		#all tiles start unexplored
		self.explored = False

		#Amount of light on the tile
		self.light_level = 0
 
		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

		#colors
		self.dark_color = dark_color
		self.light_color = light_color
 
class Rect:
	#a rectangle on the map. used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

	def center(self):
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)
 
	def intersect(self, other):
		#returns true if this rectangle intersects with another one
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)
 
class Object:
	#this is a generic object: the player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, char, name, color, \
				blocks=False, always_visible=False, light_source=False, light_source_level=0, \
				fighter=None, ai=None, item=None, equipment=None, light=None):
		self.x = x
		self.y = y
		self.char = char
		self.name = name
		self.color = color
		self.blocks = blocks
		self.always_visible = always_visible

		self.fighter = fighter
		if self.fighter:  #let the fighter component know who owns it
			self.fighter.owner = self
 
		self.ai = ai
		if self.ai:  #let the AI component know who owns it
			self.ai.owner = self

		self.light = light
		if self.light:
			self.light.owner = self
 
		self.item = item
		if self.item:  #let the Item component know who owns it
			self.item.owner = self
 
		self.equipment = equipment
		if self.equipment:  #let the Equipment component know who owns it
			self.equipment.owner = self
 
			#there must be an Item component for the Equipment component to work properly
			self.item = Item()
			self.item.owner = self
 
	def wait(self):
		#If we're a fighter, return the time we waited
		if self.fighter:
			return self.fighter.movespeed
		return True

	def move(self, dx, dy):
		#move by the given amount, if the destination is not blocked
		if not is_blocked(self.x + dx, self.y + dy):
			self.x += dx
			self.y += dy
			if self.fighter:
				return self.fighter.movespeed
			return True
		else:
			return False
 
	def move_towards(self, target_x, target_y):
		global fov_map
		#Do some pathfinding
		path = libtcod.path_new_using_map(fov_map)
		#dijkstra_new(map, diagonalCost=1.41)

		libtcod.path_compute(path, self.x, self.y, target_x, target_y)

		dx, dy = libtcod.path_walk(path, True)
		#print str((self.x, self.y)) + " via " + str((dx, dy)) + " to " + str((target_x, target_y))
		if dx:
			return self.move(dx - self.x, dy - self.y)

		return False

	def get_next_move_simple(self, target_x, target_y):
		#vector from this object to the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)
 
		#normalize it to length 1 (preserving direction), then round it and
		#convert to integer so the movement is restricted to the map grid
		dx = int(round(dx / distance))
		dy = int(round(dy / distance))

		return (dx, dy)

	def get_next_move_simple_abs(self, target_x, target_y):
		#vector from this object to the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)
 
		#normalize it to length 1 (preserving direction), then round it and
		#convert to integer so the movement is restricted to the map grid
		dx = int(round(dx / distance))
		dy = int(round(dy / distance))

		return (self.x + dx, self.y + dy)

	def move_simple(self, target_x, target_y):
		dx, dy = self.get_next_move_simple(target_x, target_y)
		return self.move(dx, dy)

 
	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)
 
	def distance(self, x, y):
		#return the distance to some coordinates
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
 
	def send_to_back(self):
		#make this object be drawn first, so all others appear above it if they're in the same tile.
		global objects
		objects.remove(self)
		objects.insert(0, self)
 
	def draw(self):
		#only show if it's visible to the player; or it's set to "always visible" and on an explored tile
		#print self.char + ": " + str(map[self.x][self.y].light_level)
		#print "  fov: " + 
		if (libtcod.map_is_in_fov(fov_map, self.x, self.y) and \
				((map[self.x][self.y].light_level > MIN_ITEM_LIGHT_LEVEL) or self.distance_to(player) < VISION_DISTANCE_WITHOUT_LIGHT)) or \
			(self.always_visible and map[self.x][self.y].explored):
			#set the color and then draw the character that represents this object at its position
			if self.ai and self.ai.can_see_player:
				#Draw the background in red!
				libtcod.console_set_char_background(con, self.x, self.y, MONSTER_SEEN_COLOR, libtcod.BKGND_SET)

			libtcod.console_set_default_foreground(con, self.color)
			#darken the background a little
			libtcod.console_set_char_background(con, self.x, self.y, libtcod.Color(128,128,128), libtcod.BKGND_OVERLAY)
			libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

	#Draws it without caring about light, etc
	#Basically just for the player
	def draw_always(self):
		libtcod.console_set_default_foreground(con, self.color)
		libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
	def clear(self):
		#erase the character that represents this object
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
 
 
class Fighter:
	#combat-related properties and methods (monster, player, NPC).
	def __init__(self, hp, defense, power, xp, stealth=0, movespeed=10, attackspeed=10, death_function=None):
		self.base_max_hp = hp
		self.hp = hp
		self.base_defense = defense
		self.base_power = power
		self.xp = xp
		self.base_stealth = stealth
		self.death_function = death_function
		self.base_movespeed = movespeed
		self.base_attackspeed = attackspeed
 
	@property
	def power(self):  #return actual power, by summing up the bonuses from all equipped items
		bonus = sum(equipment.power_bonus for equipment in get_all_equipped(self.owner))
		return self.base_power + bonus
 
	@property
	def defense(self):  #return actual defense, by summing up the bonuses from all equipped items
		bonus = sum(equipment.defense_bonus for equipment in get_all_equipped(self.owner))
		return self.base_defense + bonus
 
	@property
	def max_hp(self):  #return actual max_hp, by summing up the bonuses from all equipped items
		bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
		return self.base_max_hp + bonus

	@property
	def stealth(self):
		bonus = sum(equipment.stealth_bonus for equipment in get_all_equipped(self.owner))
		return self.base_stealth + bonus

	@property
	def movespeed(self):
		bonus = sum(equipment.movespeed_bonus for equipment in get_all_equipped(self.owner))
		return self.base_movespeed + bonus

	@property
	def attackspeed(self):
		bonus = sum(equipment.attackspeed_bonus for equipment in get_all_equipped(self.owner))
		return self.base_attackspeed + bonus
 
	def attack(self, target):
		#a simple formula for attack damage
		damage = self.power - target.fighter.defense
 
		if damage > 0:
			#make the target take some damage
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

		return self.attackspeed
 
	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
 
			#check for death. if there's a death function, call it
			if self.hp <= 0:
				function = self.death_function
				if function is not None:
					function(self.owner)
 
				#if self.owner != player:  #yield experience to the player
				#	player.fighter.xp += self.xp
 
	def heal(self, amount):
		#heal by the given amount, without going over the maximum
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp
 

##Ais
class BasicMonster:
	def __init__(self):
		self.can_see_player = False
		self.dest = (-1, -1) #(self.owner.x, self.owner.y)

	#AI for a basic monster.
	def take_turn(self):
		monster = self.owner

		actiontime = 0

		#Check if it can see you!
		if detect_player(monster):
			#Send a message about it if it couldn't already see you
			if not self.can_see_player:
				if player_can_see(monster.x, monster.y):
					message("The " + monster.name + " sees you!", libtcod.red)

			self.can_see_player = True
			self.dest = (player.x, player.y)

		else:
			self.can_see_player = False

		#If we're next to the player, attack it
		if self.can_see_player and (monster.distance_to(player) < 2):
			actiontime = monster.fighter.attack(player)

		#Otherwise move towards dest
		else:
			actiontime = monster.move_towards(self.dest[0], self.dest[1])
			#If we fail to move there, set desination to -1, -1 to pick a new one eventually
			if not actiontime:
				self.dest = (-1, -1)
				actiontime = 10 #give them a turn rest

		#Have we reached destination?
		if (monster.x == self.dest[0] and monster.y == self.dest[1]) or \
			(self.dest == (-1, -1)):
			#If we could see the player before, mark it as not true anymore

			#Pick a new destination at random (from within sight)
			newx, newy = rand_tile_in_sight(monster.x, monster.y)
			self.dest = (newx, newy)

		return actiontime

class ConfusedMonster:
	#AI for a temporarily confused monster (reverts to previous AI after a while).
	def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns
		self.can_see_player = False
 
	def take_turn(self):
		if self.num_turns > 0:  #still confused...
			#move in a random direction, and decrease the number of turns confused
			speed = self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
			self.num_turns -= 1

			#If they ran into a wall, still make it take up time
			if not speed:
				speed = self.owner.fighter.movespeed

			return speed
 
		else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)
			return self.owner.fighter.movespeed
 
class LightOrbThrowerMonster:
	def __init__(self):
		self.can_see_player = False
		self.dest = (-1, -1) #(self.owner.x, self.owner.y)
		self.last_throw = -100

	#AI for a basic monster.
	def take_turn(self):
		monster = self.owner

		actiontime = 0

		could_see_player = self.can_see_player

		#Check if it can see you!
		if detect_player(monster):
			#Send a message about it if it couldn't already see you
			if not self.can_see_player:
				if player_can_see(monster.x, monster.y):
					message("The " + monster.name + " sees you!", libtcod.red)

			self.can_see_player = True
			self.dest = (player.x, player.y)

		elif could_see_player: #It couldn't see you, so it tries to throw an orb
			self.can_see_player = False

			if time > self.last_throw + ORB_GOBLIN_THROW_RATE:
				message("The " + monster.name + " throws a light orb!", libtcod.red)
				
				#Throw an orb at destination
				orb_ai = LightDarkOrb(LIGHT_ORB_TICK_TIME)
				lit_orb = Object(monster.x, monster.y, '*', 'light orb', LIGHT_ORB_THROWN_COLOR, 
						light_source = True, light_source_level = LIGHT_ORB_LSL, ai = orb_ai)
				throw_object(lit_orb, monster.x, monster.y, self.dest[0], self.dest[1])
				objects.append(lit_orb)
				lit_orb.send_to_back()

				qinsert(lit_orb, time + LIGHT_ORB_TICK_TIME)

				self.last_throw = time

		#If we're next to the player, attack it
		if self.can_see_player and (monster.distance_to(player) < 2):
			actiontime = monster.fighter.attack(player)

		#Otherwise move towards dest
		else:
			actiontime = monster.move_towards(self.dest[0], self.dest[1])
			#If we fail to move there, set desination to -1, -1 to pick a new one eventually
			if not actiontime:
				self.dest = (-1, -1)
				actiontime = 10 #give them a turn rest

		#Have we reached destination?
		if (monster.x == self.dest[0] and monster.y == self.dest[1]) or \
			(self.dest == (-1, -1)):
			#If we could see the player before, mark it as not true anymore

			#Pick a new destination at random (from within sight)
			#These guys don't carry torches, so bias towards light
			newx, newy = rand_tile_in_sight_light_bias(monster.x, monster.y)
			self.dest = (newx, newy)

		return actiontime

class Light:
	def __init__(self, level):
		self.level = level

class Item:
	#an item that can be picked up and used.
	def __init__(self, use_function=None):
		self.use_function = use_function
 
	def pick_up(self):
		#add to the player's inventory and remove from the map
		if len(inventory) >= 26:
			message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('You picked up a ' + self.owner.name + '!', libtcod.green)
 
			#special case: automatically equip, if the corresponding equipment slot is unused
			equipment = self.owner.equipment
			if equipment and get_equipped_in_slot(equipment.slot) is None:
				equipment.equip()
 
	def drop(self):
		#special case: if the object has the Equipment component, dequip it before dropping
		if self.owner.equipment:
			self.owner.equipment.dequip()
 
		#add to the map and remove from the player's inventory. also, place it at the player's coordinates
		objects.append(self.owner)
		inventory.remove(self.owner)
		self.owner.x = player.x
		self.owner.y = player.y
		message('You dropped a ' + self.owner.name + '.', libtcod.yellow)
 
	def use(self):
		#special case: if the object has the Equipment component, the "use" action is to equip/dequip
		if self.owner.equipment:
			self.owner.equipment.toggle_equip()
			return
 
		#just call the "use_function" if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason
 
class Equipment:
	#an object that can be equipped, yielding bonuses. automatically adds the Item component.
	def __init__(self, slot, power_bonus=0, defense_bonus=0, stealth_bonus=0, movespeed_bonus=0, attackspeed_bonus=0, max_hp_bonus=0):
		self.power_bonus = power_bonus
		self.defense_bonus = defense_bonus
		self.max_hp_bonus = max_hp_bonus
		self.stealth_bonus = stealth_bonus
		self.movespeed_bonus = movespeed_bonus
		self.attackspeed_bonus = attackspeed_bonus
 
		self.slot = slot
		self.is_equipped = False
 
	def toggle_equip(self):  #toggle equip/dequip status
		if self.is_equipped:
			self.dequip()
		else:
			self.equip()
 
	def equip(self):
		#if the slot is already being used, dequip whatever is there first
		old_equipment = get_equipped_in_slot(self.slot)
		if old_equipment is not None:
			old_equipment.dequip()
 
		#equip object and show a message about it
		self.is_equipped = True
		message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', libtcod.light_green)
 
	def dequip(self):
		#dequip object and show a message about it
		if not self.is_equipped: return
		self.is_equipped = False
		message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.', libtcod.light_yellow)
 

##Items
class LightDarkOrb:
	#AI for a light or dark orb, turns slowly dimmer/brighter
	def __init__(self, tick_time):
		self.can_see_player = False #Or we get a nice red background... Maybe add an is_enemy flag
		self.tick_time = tick_time
 
	def take_turn(self):
		global objects, q

		orb = self.owner
		if orb.light:
			LSL = orb.light.level
			sign = math.copysign(1, LSL)

			newLSL = int(sign * (abs(LSL) - 1))

			if newLSL == 0:
				orb.light_source = False

				#Remove from everything
				oremove(orb)
				return -1 #don't add it to q again

			orb.light.level = newLSL

			print "  orb LSL: " + str(newLSL)

		return self.tick_time
 

##event AIs ##hidden
class TemporarySpeedUp:
	#AI for a temporarily confused monster (reverts to previous AI after a while).
	def __init__(self, target, speed, tick_time, ticks):
		self.target = target
		self.speed = speed
		self.tick_time = tick_time
		self.end_ticks = ticks
		self.ticks = 0

		self.old_speed = target.fighter.base_movespeed

		self.speed_diff = self.speed - self.old_speed
		self.speed_per_tick = (1.0 * self.speed_diff) / ticks

		self.can_see_player = False #urg

		target.fighter.base_movespeed = self.speed
 
	def take_turn(self):
		speed = self.target.fighter.base_movespeed
		newSpeed = speed - self.speed_per_tick

		self.target.fighter.base_movespeed = newSpeed

		self.ticks += 1

		if self.ticks == self.end_ticks:
			message("Your scroll of speed has worn off...")
			#We're done, remove it
			oremove(self.owner)
			return -1

		return self.tick_time


def get_equipped_in_slot(slot):  #returns the equipment in a slot, or None if it's empty
	for obj in inventory:
		if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
			return obj.equipment
	return None
 
def get_all_equipped(obj):  #returns a list of equipped items
	if obj == player:
		equipped_list = []
		for item in inventory:
			if item.equipment and item.equipment.is_equipped:
				equipped_list.append(item.equipment)
		return equipped_list
	else:
		return []  #other objects have no equipment

def pythdist(x1, y1, x2, y2):
	return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
 
###RANDOM

#Returns true if under chance
def randPercent(chance):
	return libtcod.random_get_int(0, 0, 99) < chance

#Gaussian random integers
def rand_gauss(mu, sigma):
	return int(random.gauss(mu, sigma))

#Positive random ints
def rand_gauss_pos(mu, sigma):
	return max(0, int(random.gauss(mu, sigma)))

#Fluctuate linearly around a point, +-/10%
def rand_lin_fluc(num):
	return int(random.uniform(num - num/10.0, num + num/10.0))


def rand_tile_in_sight_light_bias(x, y):
	global map

	startx = max(x - MAX_MONSTER_MOVE, 0)
	starty = max(y - MAX_MONSTER_MOVE, 0)
	endx = min(x + MAX_MONSTER_MOVE + 1, MAP_WIDTH)
	endy = min(y + MAX_MONSTER_MOVE + 1, MAP_HEIGHT)

	obj_fov_map = copy_submap_to_fov_map(startx, starty, endx - startx, endy - starty)
	libtcod.map_compute_fov(obj_fov_map, x - startx, y - starty, MAX_MONSTER_MOVE, FOV_LIGHT_WALLS, FOV_ALGO)

	def invalidChoice(x_, y_):
		return (not libtcod.map_is_in_fov(obj_fov_map, x_ - startx, y_ - starty)) or map[x_][y_].blocked

	#Now pick a random spot from within sight of that
	chances = {}
	for i in range (startx, endx):
		for j in range(starty, endy):
			if not invalidChoice(i, j):
				chances[(i, j)] = map[i][j].light_level + 1 #do this so they don't get abandoned by orcs and have all 0s
	
	return random_choice(chances)

def rand_tile_in_sight(x, y):
	global map

	startx = max(x - MAX_MONSTER_MOVE, 0)
	starty = max(y - MAX_MONSTER_MOVE, 0)
	endx = min(x + MAX_MONSTER_MOVE + 1, MAP_WIDTH)
	endy = min(y + MAX_MONSTER_MOVE + 1, MAP_HEIGHT)

	obj_fov_map = copy_submap_to_fov_map(startx, starty, endx - startx, endy - starty)
	libtcod.map_compute_fov(obj_fov_map, x - startx, y - starty, MAX_MONSTER_MOVE, FOV_LIGHT_WALLS, FOV_ALGO)

	def invalidChoice(x_, y_):
		return (not libtcod.map_is_in_fov(obj_fov_map, x_ - startx, y_ - starty)) or map[x_][y_].blocked

	#Now pick a random spot from within sight of that
	tx = x
	ty = y
	while ((tx == x) and (ty == y)) or invalidChoice(tx, ty):
		tx = libtcod.random_get_int(0, startx, endx)
		ty = libtcod.random_get_int(0, starty, endy)

	return (tx, ty)

#Get a random tile with darkness bias
def rand_tile_dark_bias(power):
	global map

	def invalidChoice(x_, y_):
		return is_blocked(x_, y_)

	chances = {}
	for j in range(0, MAP_HEIGHT):
		for i in range (0, MAP_WIDTH):
			if not invalidChoice(i, j):
				chances[(i, j)] = (99 - map[i][j].light_level)**power #do this so they don't get abandoned by orcs and have all 0s
	
	return random_choice(chances)

#Get a random empty tile with light bias
def rand_tile_light_bias(power):
	global map

	def invalidChoice(x_, y_):
		return is_blocked(x_, y_)

	chances = {}
	for j in range(0, MAP_HEIGHT):
		for i in range (0, MAP_WIDTH):
			if not invalidChoice(i, j):
				chances[(i, j)] = (map[i][j].light_level + 1)**power #do this so they don't get abandoned by orcs and have all 0s
	
	return random_choice(chances)

#Get a random tile that's totally dark
#If it fails, just does cubic dark bias
def rand_tile_darkest():
	global map

	def invalidChoice(x_, y_):
		return is_blocked(x_, y_)

	poss = []

	for j in range(0, MAP_HEIGHT):
		for i in range (0, MAP_WIDTH):
			if map[i][j].light_level == LIGHT_MIN and not invalidChoice(i, j):
				poss.append((i,j))

	
	if len(poss) > 0:
		return random.choice(poss)

	return rand_tile_dark_bias(3)

def get_empty_tile():
	global map
	x = libtcod.random_get_int(0, 0, MAP_WIDTH - 1)
	y = libtcod.random_get_int(0, 0, MAP_HEIGHT - 1)

	while is_blocked(x, y):
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - 1)

	return x, y

def random_choice_index(chances):  #choose one option from list of chances, returning its index
	#the dice will land on some number between 1 and the sum of the chances
	dice = libtcod.random_get_int(0, 1, sum(chances))
 
	#go through all chances, keeping the sum so far
	running_sum = 0
	choice = 0
	for w in chances:
		running_sum += w
 
		#see if the dice landed in the part that corresponds to this choice
		if dice <= running_sum:
			return choice
		choice += 1
 
def random_choice(chances_dict):
	#choose one option from dictionary of chances, returning its key
	chances = chances_dict.values()
	strings = chances_dict.keys()
 
	return strings[random_choice_index(chances)]

def is_blocked(x, y):
	#first test the map tile
	if map[x][y].blocked:
		return True
 
	#now check for any blocking objects
	for object in objects:
		if object.blocks and object.x == x and object.y == y:
			return True
 
	return False
 
def blocked_by(x, y):
	#first test the map tile
	if map[x][y].blocked:
		return "wall"
 
	#now check for any blocking objects
	for object in objects:
		if object.blocks and object.x == x and object.y == y:
			return object.name
 
	return False

def make_floor(x, y):
	global map
	map[x][y].blocked = False
	map[x][y].block_sight = False
	map[x][y].light_color = LIGHT_GROUND_COLOR
	map[x][y].dark_color = DARK_GROUND_COLOR

def create_room(room):
	global map
	#go through the tiles in the rectangle and make them passable
	for x in range(room.x1 + 1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			make_floor(x, y)
 
def create_h_tunnel(x1, x2, y):
	global map
	#horizontal tunnel. min() and max() are used in case x1>x2
	for x in range(min(x1, x2), max(x1, x2) + 1):
		make_floor(x, y)
 
def create_v_tunnel(y1, y2, x):
	global map
	#vertical tunnel
	for y in range(min(y1, y2), max(y1, y2) + 1):
		make_floor(x, y)
 
def make_map():
	global map, objects, stairs
	global fov_map
 
	#the list of objects with just the player
	objects = [player]
 
	#fill map with "blocked" tiles
	map = [[ Tile(True, light_color = LIGHT_WALL_COLOR, dark_color = DARK_WALL_COLOR)
			 for y in range(MAP_HEIGHT) ]
		   for x in range(MAP_WIDTH) ]
 
	rooms = []
	num_rooms = 0
 
	for r in range(MAX_ROOMS):
		#random width and height
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		#random position without going out of the boundaries of the map
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
 
		#"Rect" class makes rectangles easier to work with
		new_room = Rect(x, y, w, h)
 
		#run through the other rooms and see if they intersect with this one
		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				#break

		failed = False
 
		if not failed:
			#this means there are no intersections, so this room is valid
 
			#"paint" it to the map's tiles
			create_room(new_room)
 
			#center coordinates of new room, will be useful later
			(new_x, new_y) = new_room.center()
 
 			if num_rooms > 0:
				#connect it to the previous room with a tunnel

				#center coordinates of previous room
				(prev_x, prev_y) = rooms[num_rooms-1].center()

				#draw a coin (random number that is either 0 or 1)
				if libtcod.random_get_int(0, 0, 1) == 1:
					#first move horizontally, then vertically
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
				else:
					#first move vertically, then horizontally
					create_v_tunnel(prev_y, new_y, prev_x)
					create_h_tunnel(prev_x, new_x, new_y)
 
			#finally, append the new room to the list
			rooms.append(new_room)
			num_rooms += 1

	print "Generated " + str(num_rooms) + " rooms"

	#create stairs at the center of the last room
	stairs = Object(new_x, new_y, '>', 'stairs', libtcod.white, always_visible=True)
	objects.append(stairs)
	stairs.send_to_back()  #so it's drawn below the monsters

	#Generate dungeon features
	place_all_objects()

	#Calculate light
	update_lights()

	#Put the player down
	px, py = rand_tile_darkest()
	player.x = px
	player.y = py

	fov_map = copy_map_to_fov_map()
 
def from_dungeon_level(table):
	#returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
	for (value, level) in reversed(table):
		if dungeon_level >= level:
			return value
	return 0

def place_all_objects():
	global map, q, time

	####Dungeon features
	feat_chances = {}
	feat_chances['small torch'] = from_dungeon_level(SMALL_TORCH_CHANCE)
	feat_chances['torch'] = from_dungeon_level(TORCH_CHANCE)
	feat_chances['large torch'] = from_dungeon_level(LARGE_TORCH_CHANCE)


	target_num_features = from_dungeon_level(NUM_FEATURES)
	num_features = rand_gauss_pos(target_num_features, target_num_features / 3)
	for i in range(num_features):
		x, y = get_empty_tile()
		choice = random_choice(feat_chances)

		if choice == 'small torch':
			#Create a throwable light orb!
			l = Light(SMALL_TORCH_LSL)
			feat = Object(x, y, '!', 'small torch', TORCH_COLOR,
				#blocks=True, 
				light=l)

		elif choice == 'torch':
			#Create a throwable light orb!
			l = Light(TORCH_LSL)
			feat = Object(x, y, '!', 'torch', TORCH_COLOR,
				#blocks=True, 
				light = l)

		elif choice == 'large torch':
			#Create a throwable light orb!
			l = Light(LARGE_TORCH_LSL)
			feat = Object(x, y, '!', 'large torch', TORCH_COLOR,
				#blocks=True, 
				light = l)


		objects.append(feat)
		feat.send_to_back()  #items appear below other objects


	#Redo lighting so we can spawn relevant monsters in the right places
	update_lights()


	####Items
	#maximum number of items per floor
 
	#chance of each item (by default they have a chance of 0 at level 1, which then goes up)
	item_chances = {}
	#item_chances['heal'] = 35  #healing potion always shows up, even if all other items have 0 chance
	item_chances['light orb'] = 	from_dungeon_level(LIGHT_ORB_CHANCE)
	item_chances['dark orb'] = 		from_dungeon_level(DARK_ORB_CHANCE)
	item_chances['water balloon'] = from_dungeon_level(WATERBALLOON_CHANCE)
	item_chances['lightning'] = 	from_dungeon_level(LIGHTNING_CHANCE)
	item_chances['confuse'] =   	from_dungeon_level(CONFUSE_CHANCE)
	item_chances['flashbang'] = 	from_dungeon_level(FLASHBANG_CHANCE)
	item_chances['speed'] = 		from_dungeon_level(SPEED_CHANCE)
	item_chances['fireball'] =  0 #from_dungeon_level([[25, 6]])
	item_chances['sword'] =     0 #from_dungeon_level([[5, 4]])
	item_chances['shield'] =    0 #from_dungeon_level([[15, 8]])

	#choose random number of items
	target_num_items = from_dungeon_level(NUM_ITEMS)
	num_items = rand_gauss_pos(target_num_items, target_num_items / 3)
 
	for i in range(num_items):
		#choose random spot for this item
		x, y = get_empty_tile()
 
		#only place it if the tile is not blocked
		if not is_blocked(x, y):
			choice = random_choice(item_chances)
			# if choice == 'heal':
			# 	#create a healing potion
			# 	item_component = Item(use_function=cast_heal)
			# 	item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
			if choice == 'light orb':
				#Create a throwable light orb!
				item_component = Item(use_function=throw_light_orb)
				item = Object(x, y, '.', 'light orb', LIGHT_ORB_COLOR, item=item_component)

			elif choice == 'dark orb':
				#Create a throwable light orb!
				item_component = Item(use_function=throw_dark_orb)
				item = Object(x, y, '.', 'dark orb', DARK_ORB_COLOR, item=item_component)

			elif choice == 'water balloon':
				#Create a throwable light orb!
				item_component = Item(use_function=throw_water_balloon)
				item = Object(x, y, '^', 'water balloon', WATERBALLOON_COLOR, item=item_component)
 
			elif choice == 'lightning':
				#create a lightning bolt scroll
				item_component = Item(use_function=cast_lightning)
				item = Object(x, y, '?', 'scroll of lightning bolt', libtcod.light_yellow, item=item_component)
 
			elif choice == 'fireball':
				#create a fireball scroll
				item_component = Item(use_function=cast_fireball)
				item = Object(x, y, '?', 'scroll of fireball', libtcod.light_yellow, item=item_component)
 
			elif choice == 'confuse':
				#create a confuse scroll
				item_component = Item(use_function=cast_confuse)
				item = Object(x, y, '?', 'scroll of confusion', libtcod.light_yellow, item=item_component)

			elif choice == 'flashbang':
				#create a confuse scroll
				item_component = Item(use_function=cast_flashbang)
				item = Object(x, y, '^', 'flashbang grenade', libtcod.light_yellow, item=item_component)

			elif choice == 'speed':
				#create a confuse scroll
				item_component = Item(use_function=cast_speed)
				item = Object(x, y, '?', 'scroll of speed', libtcod.light_yellow, item=item_component)
 
			elif choice == 'sword':
				#create a sword
				equipment_component = Equipment(slot='right hand', power_bonus=3)
				item = Object(x, y, '/', 'sword', libtcod.sky, equipment=equipment_component)
 
			elif choice == 'shield':
				#create a shield
				equipment_component = Equipment(slot='left hand', defense_bonus=1)
				item = Object(x, y, '[', 'shield', libtcod.darker_orange, equipment=equipment_component)
 
			objects.append(item)
			item.send_to_back()  #items appear below other objects
			item.always_visible = True  #items are visible even out-of-FOV, if in an explored area


	####Monsters
	#maximum number of monsters per room
 
	#chance of each monster
	monster_chances = {}
	monster_chances['goblin'] = from_dungeon_level(GOBLIN_CHANCE)
	monster_chances['orb goblin'] = from_dungeon_level(ORB_GOBLIN_CHANCE)
	monster_chances['orc'] = from_dungeon_level(ORC_CHANCE)  #orc always shows up, even if all other monsters have 0 chance
	monster_chances['troll'] = from_dungeon_level(TROLL_CHANCE)

	#choose random number of monsters
	target_num_monsters = from_dungeon_level(NUM_MONSTERS)
	num_monsters = rand_gauss_pos(target_num_monsters, target_num_monsters / 3)
 
	for i in range(num_monsters):
		#choose random spot for this monster
		x, y = get_empty_tile()
 
		#only place it if the tile is not blocked
		if not is_blocked(x, y):
			choice = random_choice(monster_chances)
			if choice == 'orc':
				#create an orc
				fighter_component = Fighter(hp=ORC_HP, defense=ORC_DEF, power=ORC_POW, xp=ORC_XP, death_function=monster_death)
				ai_component = BasicMonster()
				l = Light(ORC_LSL)

				monster = Object(x, y, 'o', 'orc', ORC_COLOR,
								 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
								 fighter=fighter_component, ai=ai_component)
 
			elif choice == 'goblin':
				#create a goblin
				fighter_component = Fighter(hp=GOBLIN_HP, defense=GOBLIN_DEF, power=GOBLIN_POW, xp=GOBLIN_XP, death_function=monster_death)
				ai_component = BasicMonster()
				l = Light(GOBLIN_LSL)

				monster = Object(x, y, 'g', 'goblin', GOBLIN_COLOR,
								 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
								 fighter=fighter_component, ai=ai_component)

			elif choice == 'orb goblin':
				#Redo x, y to be light-biased

				x,y = rand_tile_light_bias(3) #cubic bias
				#create a goblin
				fighter_component = Fighter(hp=ORB_GOBLIN_HP, defense=ORB_GOBLIN_DEF, power=ORB_GOBLIN_POW, xp=ORB_GOBLIN_XP, death_function=monster_death)
				ai_component = LightOrbThrowerMonster()

				monster = Object(x, y, 'g', 'orb goblin', ORB_GOBLIN_COLOR,
								 blocks=True, #TODO: Add them actually carrying torches, not just lights
								 fighter=fighter_component, ai=ai_component)

			elif choice == 'troll':
				#create a troll
				fighter_component = Fighter(hp=TROLL_HP, defense=TROLL_DEF, power=TROLL_POW, xp=TROLL_XP, death_function=monster_death)
				ai_component = BasicMonster()
 
				monster = Object(x, y, 'T', 'troll', TROLL_COLOR,
								 blocks=True, fighter=fighter_component, ai=ai_component)
 
			objects.append(monster)

			qinsert(monster, time + 2) #player gets inserted at 1, monsters at 2

	print "Generated " + str(num_features) + " features"
	print "Generated " + str(num_items) + " items"
	print "Generated " + str(num_monsters) + " monsters"
 
 
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	#render a bar (HP, experience, etc). first calculate the width of the bar
	bar_width = int(float(value) / maximum * total_width)
 
	#render the background first
	libtcod.console_set_default_background(panel, back_color)
	libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
 
	#now render the bar on top
	libtcod.console_set_default_background(panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
 
	#finally, some centered text with the values
	libtcod.console_set_default_foreground(panel, libtcod.white)
	libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
								 name + ': ' + str(value) + '/' + str(maximum))
 
def get_names_under_mouse():
	global mouse
	#return a string with the names of all objects under the mouse
 
	(x, y) = (mouse.cx, mouse.cy)
 
	#create a list with the names of all objects at the mouse's coordinates and in FOV
	names = [obj.name for obj in objects
			 if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
 
	names = ', '.join(names)  #join the names, separated by commas
	return names.capitalize()
 
def BFS(x, y, xt, yt):
	global map

	reachable = []

	curX = x
	curY = y
	curDist = 0.0
	queue = [(curX, curY, curDist)]

	print "Starting BFS at " + str((curX,curY))

	#loop through
	while(len(queue) > 0):
		curX, curY, curDist = queue.pop(0)

		if curDist < depth:
			#Add it to list of reachable tiles
			reachable.append(map[curX][curY])

			#print "On tile " + str((curX, curY))

			#Now, if it's less than depth, add all neighboring tile sthat haven't been reached
			if curDist < depth and map[curX][curY].block_sight == False:
				for dx in [-1, 0, 1]:
					for dy in [-1, 0, 1]:
						if dx != 0 and dy != 0:
							newx = curX + dx
							newy = curY + dy
							if(map[newx][newy] not in reachable):
								queue.append((newx, newy, curDist + pythdist(curX, curY, newx, newy)))
	return reachable



def detect_player(monster):
	global map, player
	if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

		already_seen = 0
		if monster.ai.can_see_player:
			already_seen = 50

		#Light-based contribution
		light_chance = map[player.x][player.y].light_level - player.fighter.stealth

		#Proximity
		near_chance = (max((VISION_DISTANCE_WITHOUT_LIGHT - pythdist(player.x, player.y, monster.x, monster.y)), 0)**2) * 10 - player.fighter.stealth / 2

		chance = light_chance + near_chance + already_seen
		chance = max(chance, 0)
		if randPercent(chance):
			return True

	return False

def player_can_see(x, y):
	LOS = libtcod.map_is_in_fov(fov_map, x, y)
	visible = LOS and ((map[x][y].light_level > MIN_TILE_LIGHT_LEVEL) or (pythdist(x, y, player.x, player.y) < VISION_DISTANCE_WITHOUT_LIGHT))

	return visible

def update_lights():
	global map, fov_map, objects

	#Reset them
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			map[x][y].light_level = 0

	#For every light source...
	for obj in objects:
		if obj.light:
			add_light(obj)

	#Bound everything
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			oldL = map[x][y].light_level
			newL = newL = min(LIGHT_MAX, oldL)
			newL = max(LIGHT_MIN, newL)

			#if map[x][y].blocked:
			#	newL = min(1, newL) #Make walls not show light levels

			map[x][y].light_level = newL

def update_light_at_location(tx, ty, LSL):

	center_level = LSL * LIGHT_STRENGTH

	#Calculate a new fov map from that location
	startx = max(tx - abs(LSL), 0)
	starty = max(ty - abs(LSL), 0)
	endx = min(tx + abs(LSL) + 1, MAP_WIDTH)
	endy = min(ty + abs(LSL) + 1, MAP_HEIGHT)

	obj_fov_map = copy_submap_to_fov_map(startx, starty, endx - startx, endy - starty)
	libtcod.map_compute_fov(obj_fov_map, tx - startx, ty - starty, abs(LSL), FOV_LIGHT_WALLS, FOV_ALGO)

	#Get distance to each tile
	for y in range(starty, endy):
		for x in range(startx, endx):
			blocked = not libtcod.map_is_in_fov(obj_fov_map, x - startx, y - starty)
			# #If that tile is seeable from the light source
			if not blocked:
				#Update it's light value!
				oldL = map[x][y].light_level
				sign = math.copysign(1, LSL)
				modifier = sign * (abs(center_level) - (abs(center_level)/abs(LSL)) * pythdist(tx, ty, x, y))
				newL = oldL + int(modifier)
				map[x][y].light_level = newL

def add_light(obj):
	global map
	if obj.light:
		update_light_at_location(obj.x, obj.y, obj.light.level)
		

def get_light(x, y):
	global map

	l = map[x][y].light_level
	l = min(LIGHT_MAX, l)
	l = max(LIGHT_MIN, l)

	return l

def remove_light(obj):
	global map
	print "removing light from " + obj.name
	if obj.light:
		update_light_at_location(obj.x, obj.y, -1 * obj.light.level)

def update_fov():
	libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

def render_all():
	global fov_map
	global fov_recompute
	global objects
	global map

	if fov_recompute:
		fov_recompute = False

		#Compute light levels
		#update_lights()
		
		#recompute FOV if needed (the player moved or something)
		update_fov()

	#Generate colormap
	colormap = [[[0, 0, 0] for y in range(0, MAP_HEIGHT)] for x in range(0, MAP_WIDTH)]

	#go through all tiles, and set their background color according to the FOV
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			LOS = libtcod.map_is_in_fov(fov_map, x, y)
			visible = LOS and ((map[x][y].light_level > MIN_TILE_LIGHT_LEVEL) or (pythdist(x, y, player.x, player.y) < VISION_DISTANCE_WITHOUT_LIGHT))
			if not visible:
				#if it's not visible right now, the player can only see it if it's explored
				if map[x][y].explored:
					(r, g, b) = map[x][y].dark_color
					colormap[x][y][0] += r
					colormap[x][y][1] += g
					colormap[x][y][2] += b
			else:
				#it's visible
				light = get_light(x, y)

				#Don't show light levels on walls, makes it too confusing
				if map[x][y].blocked:
					light = 0 #light / 2 #/2 is nice but you can see through walls...
				#light = rand_lin_fluc(light) #Randomly fluctuate a little, for style points
				(r, g, b) = map[x][y].light_color

				colormap[x][y][0] += r + R_FACTOR*light
				colormap[x][y][1] += g + G_FACTOR*light
				colormap[x][y][2] += b + B_FACTOR*light
				
				#since it's visible, mark it as explored
				map[x][y].explored = True

	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			color = libtcod.Color(int(colormap[x][y][0]), 
								  int(colormap[x][y][1]), 
								  int(colormap[x][y][2]))
			libtcod.console_set_char_background(con, x, y, color, libtcod.BKGND_SET)
 
	#draw all objects in the list, except the player. we want it to
	#always appear over all other objects! so it's drawn later.
	for object in objects:
		if object != player:
			object.draw()
	player.draw_always()
 
	#blit the contents of "con" to the root console
	libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
 
 
	#prepare to render the GUI panel
	libtcod.console_set_default_background(panel, libtcod.black)
	libtcod.console_clear(panel)
 
	#print the game messages, one line at a time
	y = 1
	for (line, color) in game_msgs:
		libtcod.console_set_default_foreground(panel, color)
		libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
		y += 1
 
	#show the player's stats
	render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
			   libtcod.light_red, libtcod.darker_red)
	libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(dungeon_level))
 
	#display names of objects under the mouse
	libtcod.console_set_default_foreground(panel, libtcod.light_gray)
	libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
 
	#blit the contents of "panel" to the root console
	libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
 
 
def message(new_msg, color = libtcod.white):
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]
 
		#add the new line as a tuple, with the text and the color
		game_msgs.append( (line, color) )
 
 
def player_move_or_attack(dx, dy):
	global fov_recompute
 
	#the coordinates the player is moving to/attacking
	x = player.x + dx
	y = player.y + dy
 
	#try to find an attackable object there
	target = None
	for object in objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break
 
	#attack if target found, move otherwise
	if target is not None:
		player.fighter.attack(target)
		return player.fighter.attackspeed
	else:
		fov_recompute = True
		return player.move(dx, dy)
 
 
def text_input(header):
	width = len(header)
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	if header == '':
		header_height = 0
	height = 1 + header_height

	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)

	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
 
	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/6 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

 	#Now, get key input repeatedly
 	text = ""

	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)

	while key.vk != libtcod.KEY_ENTER and key.vk != libtcod.KEY_ESCAPE:
		if key.vk == libtcod.KEY_BACKSPACE:
			if len(text) > 0:
				text = text[:-1] #Cut off the last one
		elif key.c >= 32 and key.c <= 127:
			key_char = chr(key.c)
			text += key_char

		#Redraw
		#render_all()

		window = libtcod.console_new(width, height)

		#print the header, with auto-wrap
		libtcod.console_set_default_foreground(window, libtcod.white)
		libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
		#libtcod.console_print_ex(window, 0, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'Ravi')
		libtcod.console_print_ex(window, 0, 1, libtcod.BKGND_NONE, libtcod.LEFT, text)
		#libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
	 
		#blit the contents of "window" to the root console
		libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

		libtcod.console_flush()

		key = libtcod.console_wait_for_keypress(True)

	return text



def menu(header, options, width):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
 
	#calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	if header == '':
		header_height = 0
	height = len(options) + header_height
 
	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)
 
	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
 
	#print all the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1
 
	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
 
	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
 
	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)
 
	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None
 
def inventory_menu(header):
	#show a menu with each item of the inventory as an option
	if len(inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = []
		for item in inventory:
			text = item.name
			#show additional information, in case it's equipped
			if item.equipment and item.equipment.is_equipped:
				text = text + ' (on ' + item.equipment.slot + ')'
			options.append(text)
 
	index = menu(header, options, INVENTORY_WIDTH)
 
	#if an item was chosen, return it
	if index is None or len(inventory) == 0: return None
	return inventory[index].item
 
def msgbox(text, width=50):
	menu(text, [], width)  #use menu() as a sort of "message box"
 
def handle_keys():
	global key
 
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
	elif key.vk == libtcod.KEY_ESCAPE:
		return 'exit'  #exit game
 
	if game_state == 'playing':
		key_char = chr(key.c)
		#movement keys
		if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8 or key_char == 'k':
			return player_move_or_attack(0, -1)
		elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2 or key_char == 'j':
			return player_move_or_attack(0, 1)
		elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4 or key_char == 'h':
			return player_move_or_attack(-1, 0)
		elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6 or key_char == 'l':
			return player_move_or_attack(1, 0)
		elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7 or key_char == 'y':
			return player_move_or_attack(-1, -1)
		elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9 or key_char == 'u':
			return player_move_or_attack(1, -1)
		elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1 or key_char == 'b':
			return player_move_or_attack(-1, 1)
		elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3 or key_char == 'n':
			return player_move_or_attack(1, 1)
		elif key.vk == libtcod.KEY_KP5 or key_char == 's' or key_char == '.':
			return player.wait()
			#pass  #do nothing ie wait for the monster to come to you
		else:
			#test for other keys
 
			if key_char == ',' or key_char == 'g':
				#pick up an item
				for object in objects:  #look for an item in the player's tile
					if object.x == player.x and object.y == player.y and object.item:
						object.item.pick_up()
						break
 
			if key_char == 'i':
				#show the inventory; if an item is selected, use it
				chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.use()
 
			if key_char == 'd':
				#show the inventory; if an item is selected, drop it
				chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.drop()
 
			if key_char == 'c':
				#show character information
				level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
				msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
					   '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
					   '\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense), CHARACTER_SCREEN_WIDTH)
 
			if key_char == '>':
				#go down stairs, if the player is on them
				if stairs.x == player.x and stairs.y == player.y:
					next_level()
 
			return False
 
def check_level_up():
	#see if the player's experience is enough to level-up
	level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
	if player.fighter.xp >= level_up_xp:
		#it is! level up and ask to raise some stats
		player.level += 1
		player.fighter.xp -= level_up_xp
		message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)
 
		choice = None
		while choice == None:  #keep asking until a choice is made
			choice = menu('Level up! Choose a stat to raise:\n',
						  ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
						   'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
						   'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'], LEVEL_SCREEN_WIDTH)
 
		if choice == 0:
			player.fighter.base_max_hp += 20
			player.fighter.hp += 20
		elif choice == 1:
			player.fighter.base_power += 1
		elif choice == 2:
			player.fighter.base_defense += 1
 
def add_highscore(score):
	playername = player.playername

	#Load highscores from file
	try:
		file = shelve.open('highscores', 'r')
		scores = file['scores']
		file.close()

		#Insert score
		i = 0
		while i < len(q) and score <= scores[i][1]:
			i += 1

		scores.insert(i, (playername, score))

	except:
		print "No highscore file found."
		scores = [(playername, score)]

	#Write them back to the file
	file = shelve.open('highscores', 'n')
	file['scores'] = scores
	file.close()

def show_highscores():
	#Load them from a file
	try:
		file = shelve.open('highscores', 'r')
		scores = file['scores']
		file.close()

	except:
		print "No highscore file found."
		scores = []

	#Format them into an array of lines

	texts = []
	for (name, score) in scores[0 : min(25, len(scores))]:
		spacecount = max(20 - len(name), 0)
		texts.append(name + (' ' * spacecount) + str(score))
	#menu("High Scores", texts, SCORE_WIDTH)

	#calculate total height for the header (after auto-wrap) and one line per option
	header = "High Scores"
	width = SCORE_WIDTH
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	if header == '':
		header_height = 0
	height = len(texts) + header_height
 
	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)
 
	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
 
	#print all the options
	y = header_height
	letter_index = 1
	for option_text in texts:
		text = str(letter_index) + '. ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1

	return window, width, height
 
	# #blit the contents of "window" to the root console
	# x = SCREEN_WIDTH/2 - width/2
	# y = SCREEN_HEIGHT/2 - height/2
	# libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
 
	# #present the root console to the player and wait for a key-press
	# libtcod.console_flush()
	# key = libtcod.console_wait_for_keypress(True)
 
	# if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
	# 	libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)
 
	# #convert the ASCII code to an index; if it corresponds to an option, return it
	# index = key.c - ord('a')
	# if index >= 0 and index < len(options): return index
	# return None


def player_death(player):
	#the game ended!
	global game_state
	message('You died!', libtcod.red)
	game_state = 'dead'
 
	#for added effect, transform the player into a corpse!
	player.char = '%'
	player.color = libtcod.dark_red

	#Put their score into a high score
	score = dungeon_level

	add_highscore(score)

 
def monster_death(monster):
	#transform it into a nasty corpse! it doesn't block, can't be
	#attacked and doesn't move
	msg = 'The ' + monster.name + ' is dead!'
	if monster.light:
		msg += " Its torch falls to the ground and gutters out."
	message(msg, libtcod.orange)

	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.light = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()
 
def target_tile(max_range=None):
	global key, mouse
	#return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
	while True:
		#render the screen. this erases the inventory and shows the names of objects under the mouse.
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
		render_all()
 
		(x, y) = (mouse.cx, mouse.cy)
 
		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			return (None, None)  #cancel if the player right-clicked or pressed Escape
 
		#accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
		if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
				(max_range is None or player.distance(x, y) <= max_range)):
			return (x, y)

def throw_object(object, startx, starty, endx, endy, max_range=None):
	#Continuously move the object
	while (object.x != endx or object.y != endy) and (max_range == None or object.distance(startx, starty) < max_range):
		if not object.move_simple(endx, endy):
			block_x, block_y = object.get_next_move_simple_abs(endx, endy)
			hitName = blocked_by(block_x, block_y)
			message("The " + object.name + " hits the " + hitName)
			break


	# #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
	# while True:
	# 	#render the screen. this erases the inventory and shows the names of objects under the mouse.
	# 	libtcod.console_flush()
	# 	libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
	# 	render_all()
 
	# 	(x, y) = (mouse.cx, mouse.cy)
 
	# 	if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
	# 		return (None, None)  #cancel if the player right-clicked or pressed Escape
 
	# 	#accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
	# 	if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
	# 			(max_range is None or player.distance(x, y) <= max_range)):
	# 		return (x, y)
 
def target_monster(max_range=None):
	#returns a clicked monster inside FOV up to a range, or None if right-clicked
	while True:
		(x, y) = target_tile(max_range)
		if x is None:  #player cancelled
			return None
 
		#return the first clicked monster, otherwise continue looping
		for obj in objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != player:
				return obj
 
def closest_monster(max_range):
	#find closest enemy, up to a maximum range, and in the player's FOV
	closest_enemy = None
	closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
	for object in objects:
		if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
			#calculate distance between this object and the player
			dist = player.distance_to(object)
			if dist < closest_dist:  #it's closer, so remember it
				closest_enemy = object
				closest_dist = dist
	return closest_enemy
 

###SPELLS ###MAGIC

def throw_light_orb():
	global objects, fov_recompute, time
	#Create a puddle of light around it
	message('Left-click a target tile for the light orb, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
 
	#TODO: make this land a bit randomly
	#TODO: make this stop being lit eventually
	orb_ai = LightDarkOrb(LIGHT_ORB_TICK_TIME)
	l = Light(LIGHT_ORB_LSL)
	lit_orb = Object(player.x, player.y, '*', 'light orb', LIGHT_ORB_THROWN_COLOR, 
			light = l, ai = orb_ai)
	throw_object(lit_orb, player.x, player.y, x, y)
	objects.append(lit_orb)
	lit_orb.send_to_back()

	qinsert(lit_orb, time + LIGHT_ORB_TICK_TIME)

	message('The light orb bursts into magical fire as it lands on the ground!', libtcod.orange)
	fov_recompute = True

def throw_dark_orb():
	global objects, fov_recompute
	#Create a puddle of light around it
	message('Left-click a target tile for the dark orb, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
 
	#TODO: make this land a bit randomly
	#TODO: make this stop being lit eventually
	orb_ai = LightDarkOrb(DARK_ORB_TICK_TIME)
	l = Light(DARK_ORB_LSL)
	lit_orb = Object(player.x, player.y, '*', 'dark orb', DARK_ORB_THROWN_COLOR, 
				light = l, ai = orb_ai)
	throw_object(lit_orb, player.x, player.y, x, y)
	objects.append(lit_orb)
	lit_orb.send_to_back()

	qinsert(lit_orb, time + DARK_ORB_TICK_TIME)

	message('The temperature drops as the orb begins to absorb light!', libtcod.light_violet)
	fov_recompute = True

def throw_water_balloon():
	global fov_recompute
	#ask the player for a target tile to throw a fireball at
	message('Left-click a target tile for the water balloon, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
	message('The water balloon bursts, dampening everything around it!', libtcod.light_blue)
 
	for obj in objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= WATERBALLOON_RADIUS and obj.light:
			if obj.ai:
				message('The ' + obj.name + '\'s torch goes out!', libtcod.light_blue)
			else:
				message('The ' + obj.name + ' goes out!', libtcod.light_blue)
			obj.light = None
			fov_recompute = True

def cast_heal():
	#heal the player
	if player.fighter.hp == player.fighter.max_hp:
		message('You are already at full health.', libtcod.red)
		return 'cancelled'
 
	message('Your wounds start to feel better!', libtcod.light_violet)
	player.fighter.heal(HEAL_AMOUNT)
 
def cast_lightning():
	#find closest enemy (inside a maximum range) and damage it
	monster = closest_monster(LIGHTNING_RANGE)
	if monster is None:  #no enemy found within maximum range
		message('No enemy is close enough to strike.', libtcod.red)
		return 'cancelled'
 
	#zap it!
	message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
			+ str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
	monster.fighter.take_damage(LIGHTNING_DAMAGE)
 
def cast_fireball():
	#ask the player for a target tile to throw a fireball at
	message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
	message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)
 
	for obj in objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
			message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
			obj.fighter.take_damage(FIREBALL_DAMAGE)
 
def cast_confuse():
	#ask the player for a target to confuse
	message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
	monster = target_monster(CONFUSE_RANGE)
	if monster is None: return 'cancelled'
 
	#replace the monster's AI with a "confused" one; after some turns it will restore the old AI
	old_ai = monster.ai
	monster.ai = ConfusedMonster(old_ai)
	monster.ai.owner = monster  #tell the new component who owns it
	message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)
 
def cast_flashbang():
	#ask the player for a target tile to throw a fireball at
	message('Left-click a target tile for the flashbang, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
	message('The flashbang explodes, blinding and deafening everything within ' + str(FLASHBANG_RADIUS) + ' tiles!', libtcod.orange)
 
	for obj in objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= FLASHBANG_RADIUS and obj.fighter and obj.ai:
			old_ai = obj.ai
			obj.ai = ConfusedMonster(old_ai, FLASHBANG_LENGTH)
			obj.ai.owner = obj

			message("The " + obj.name + " is dazed and confused!", libtcod.light_green)

def cast_speed():
	global time
	speed_ai = TemporarySpeedUp(player, player.fighter.base_movespeed * SPEED_MUL, SPEED_TICK_TIME, SPEED_TICK_NUM) #This changes the speed
	speed_obj = Object(-1, -1, ' ', 'ERROR: SPEED', libtcod.white, ai = speed_ai)

	objects.append(speed_obj)
	speed_obj.send_to_back()

	qinsert(speed_obj, time + SPEED_TICK_TIME)

	message("You feel lightning fast!")

	
##Queue stuff
#Insert into q at time t
def qinsert(o, t):
	global q

	i = 0
	while i < len(q) and t > q[i][1]:
		i += 1

	q.insert(i, (o, t))

#If movement ever goes wrong check this out
def qremove(o):
	global q
	for i in q:
		if i[0] == o:
			q.remove(i)
 
#Remove an object both from the q and from objects
def oremove(o):
	global q, objects
	qremove(o)
	objects.remove(o)

##Saving and ##loading
def save_game():
	#open a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = map
	file['objects'] = objects
	file['player_index'] = objects.index(player)  #index of player in objects list
	file['stairs_index'] = objects.index(stairs)  #same for the stairs
	file['inventory'] = inventory
	file['game_msgs'] = game_msgs
	file['game_state'] = game_state
	file['dungeon_level'] = dungeon_level
	file['q'] = q
	file['time'] = time
	file.close()
 
def load_game():
	#open the previously saved shelve and load the game data
	global map, objects, player, stairs, inventory, game_msgs, game_state, dungeon_level, q, time
 
	file = shelve.open('savegame', 'r')
	map = file['map']
	objects = file['objects']
	player = objects[file['player_index']]  #get index of player in objects list and access it
	stairs = objects[file['stairs_index']]  #same for the stairs
	inventory = file['inventory']
	game_msgs = file['game_msgs']
	game_state = file['game_state']
	dungeon_level = file['dungeon_level']
	time = file['time']
	q = file['q']
	file.close()
 
	initialize_fov()
 

##New game
def new_game(name = ""):
	global player, inventory, game_msgs, game_state, dungeon_level, q, time
 
	#create object representing the player
	fighter_component = Fighter(hp=100, defense=1, power=2, xp=0, death_function=player_death)
	player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
 
	player.level = 1

	inventory = []


	#Set up the game timer!
	time = 0
	#create the list of game messages and their colors, starts empty
	game_msgs = []
 
	#generate map (at this point it's not drawn to the screen)
	dungeon_level = 0
	next_level()
	#make_map()
	#initialize_fov()
 
	game_state = 'playing'

	#Get the player's name
	if name == "":
		name = text_input("What is your name?")
	player.playername = name
 
	#a warm welcoming message!
	message('Welcome ' + name + '! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
 
	#initial equipment: a dagger
	equipment_component = Equipment(slot='right hand', power_bonus=2)
	obj = Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
	inventory.append(obj)
	equipment_component.equip()
	obj.always_visible = True

##New debug game
def new_debug_game():
	new_game("Debugger")

 
#advance to the next level
def next_level():
	global dungeon_level, q, time, inventory
	message('You descend deeper into the dungeon')
	#message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
	#player.fighter.heal(player.fighter.max_hp / 2)  #heal the player by 50%
 
	dungeon_level += 1

	#Reset the movement queue to just the player
	q = [(player, time + 1)]

	#If the player has any items with timed, put them in the queue
	for item in inventory:
		if item.ai:
			qinsert(item, time + 2)

	make_map()  #create a fresh new level!
	initialize_fov()

	
##Fov
def copy_submap_to_fov_map(startx, starty, width, height):
	new_fov_map = libtcod.map_new(width, height)
	for y in range(starty, starty + height):
		for x in range(startx, startx + width):
			libtcod.map_set_properties(new_fov_map, x - startx, y - starty, not map[x][y].block_sight, not map[x][y].blocked)

	return new_fov_map
 
def copy_map_to_fov_map():
	new_fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			libtcod.map_set_properties(new_fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

	return new_fov_map

def initialize_fov():
	global fov_recompute, fov_map
	fov_recompute = True

	fov_map = copy_map_to_fov_map()
 
	#create the FOV map, according to the generated map
 
	libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)
 
##Main game
def play_game():
	global key, mouse
	global fov_recompute
	global q, time

	#Give all monsters a free step to compute their destinations
	for unit in objects:
		if unit.ai:
			unit.ai.take_turn()
			fov_recompute = True

			
	player_action = None
 
	mouse = libtcod.Mouse()
	key = libtcod.Key()
	#main loop
	while not libtcod.console_is_window_closed():
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
		#render the screen
		render_all()
 
		libtcod.console_flush()
 
		#level up if needed
		check_level_up()
 
		#erase all objects at their old locations, before they move
		for object in objects:
			object.clear()
 
		#handle keys and exit game if needed
		player_action = handle_keys()
		if player_action == 'exit':
			save_game()
			break
 
		#let monsters take their turn
		if game_state == 'playing' and player_action != False:
			#Update FOV after moving
			update_fov()

			#Pop player off queue,
			_, playerstarttime = q.pop(0)
			time = playerstarttime
			qinsert(player, time + player_action)

			print "player moving at time " + str(playerstarttime)

			time = time +  + player_action
				
			#Now, repeatedly pop other things off until we get a player
			while(q[0][0] != player):
				unit, newtime = q.pop(0)

				if unit.ai:
					time = newtime

					print unit.name + " moving at time " + str(time)

					remove_light(unit)
					turntime = unit.ai.take_turn()
					add_light(unit)

					#Readd to movement queue
					if turntime >= 0:
						qinsert(unit, time + turntime)

 
def main_menu():
	img = libtcod.image_load('menu_background.png')
 
	while not libtcod.console_is_window_closed():
		#show the background image, at twice the regular console resolution
		libtcod.image_blit_2x(img, 0, 0, 0)
 
		#show the game's title, and some credits!
		libtcod.console_set_default_foreground(0, libtcod.light_yellow)
		libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
								 'Steal all that junk!')
		libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER, 'By Toxy')

		#Show the scoreboard on the left!
		scorewin, scorew, scoreh = show_highscores()
		x = 2
		y = 2
		libtcod.console_blit(scorewin, 0, 0, scorew, scoreh, 0, x, y, 1.0, 0.7)
		#libtcod.console_flush()

		#show options and wait for the player's choice
		choice = menu('', ['Play a new game', 'Continue last game', 'Start debug game', 'Quit'], 24)
 
		if choice == 0:  #new game
			new_game()
			play_game()
		elif choice == 1:  #load last game
			try:
				load_game()
			except:
				msgbox('\n No saved game to load.\n', 24)
				continue
			play_game()
		elif choice == 2:  #start debug game
			new_debug_game()
			play_game()
		elif choice == 3:  #quit
			break

#terminal12x12_gs_ro.png
libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
 
main_menu()