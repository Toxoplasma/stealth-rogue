import math

from consts import *

import u
import g

##Fov
def copy_submap_to_fov_map(startx, starty, width, height):
	new_fov_map = libtcod.map_new(width, height)
	for y in range(starty, starty + height):
		for x in range(startx, startx + width):
			libtcod.map_set_properties(new_fov_map, x - startx, y - starty, not g.map[x][y].block_sight, not g.map[x][y].blocked)

	return new_fov_map
 
def copy_map_to_fov_map():
	new_fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			libtcod.map_set_properties(new_fov_map, x, y, not g.map[x][y].block_sight, not g.map[x][y].blocked)

	return new_fov_map

def initialize_fov():
	g.fov_recompute = True

	g.fov_map = copy_map_to_fov_map()
def update_fov():
	libtcod.map_compute_fov(g.fov_map, g.player.x, g.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)


 

def in_player_fov(x, y):
	return libtcod.map_is_in_fov(g.fov_map, x, y)




def add_light(obj):
	if obj.light:
		#print "Adding " + obj.name + " " + str(obj.light.level)
		update_light_at_location(obj.x, obj.y, obj.light.level)
		

def get_light(x, y):
	l = g.map[x][y].light_level
	l = min(LIGHT_MAX, l)
	l = max(LIGHT_MIN, l)

	return l

def remove_light(obj):
	if obj.light:
		update_light_at_location(obj.x, obj.y, -1 * obj.light.level)


				

def detect_player(monster):
	if libtcod.map_is_in_fov(g.fov_map, monster.x, monster.y):
		if monster.fighter.in_vision_cone(g.player.x, g.player.y):
			already_seen = 0
			if monster.ai.can_see_player:
				already_seen = 50

			#Light-based contribution
			light_chance = g.map[g.player.x][g.player.y].light_level - g.player.fighter.stealth

			#Proximity
			near_chance = (max((VISION_DISTANCE_WITHOUT_LIGHT - u.pythdist(g.player.x, g.player.y, monster.x, monster.y)), 0)**2) * 10 - g.player.fighter.stealth / 2

			chance = light_chance + near_chance + already_seen
			chance = max(chance, 0)
			if u.randPercent(chance):
				return True

	return False

def player_can_see(x, y):
	LOS = libtcod.map_is_in_fov(g.fov_map, x, y)
	visible = LOS and ((g.map[x][y].light_level > MIN_TILE_LIGHT_LEVEL) or (u.pythdist(x, y, g.player.x, g.player.y) < VISION_DISTANCE_WITHOUT_LIGHT))

	return visible

def update_lights():
	#Reset them
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			g.map[x][y].light_level = AMBIENT_LIGHT[g.branch]

	#For every light source...
	for obj in g.objects:
		if obj.light:
			add_light(obj)

	#Bound everything
	# for x in range(MAP_WIDTH):
	# 	for y in range(MAP_HEIGHT):
	# 		oldL = g.map[x][y].light_level
	# 		newL = min(LIGHT_MAX, oldL)
	# 		newL = max(LIGHT_MIN, newL)

	# 		#if map[x][y].blocked:
	# 		#	newL = min(1, newL) #Make walls not show light levels

	# 		g.map[x][y].light_level = newL

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
				oldL = g.map[x][y].light_level
				sign = math.copysign(1, LSL)
				modifier = sign * (abs(center_level) - (abs(center_level)/abs(LSL)) * u.pythdist(tx, ty, x, y))
				if modifier * sign > 0:
					newL = oldL + int(modifier)
					g.map[x][y].light_level = newL

 
def player_can_see_obj(obj):
	return in_player_fov(obj.x, obj.y) and \
		((g.map[obj.x][obj.y].light_level > MIN_ITEM_LIGHT_LEVEL) or obj.distance_to(g.player) < VISION_DISTANCE_WITHOUT_LIGHT)