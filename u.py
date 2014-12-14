import random
import math

from consts import *
import g
import v
import ui

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

	startx = max(x - MAX_MONSTER_MOVE, 0)
	starty = max(y - MAX_MONSTER_MOVE, 0)
	endx = min(x + MAX_MONSTER_MOVE + 1, MAP_WIDTH)
	endy = min(y + MAX_MONSTER_MOVE + 1, MAP_HEIGHT)

	obj_fov_map = v.copy_submap_to_fov_map(startx, starty, endx - startx, endy - starty)
	libtcod.map_compute_fov(obj_fov_map, x - startx, y - starty, MAX_MONSTER_MOVE, FOV_LIGHT_WALLS, FOV_ALGO)

	def invalidChoice(x_, y_):
		return (not libtcod.map_is_in_fov(obj_fov_map, x_ - startx, y_ - starty)) or g.map[x_][y_].blocked

	#Now pick a random spot from within sight of that
	chances = {}
	for i in range (startx, endx):
		for j in range(starty, endy):
			if not invalidChoice(i, j):
				chances[(i, j)] = g.map[i][j].light_level + 1 #do this so they don't get abandoned by orcs and have all 0s
	
	return random_choice(chances)

def rand_tile_in_sight(x, y):
	startx = max(x - MAX_MONSTER_MOVE, 0)
	starty = max(y - MAX_MONSTER_MOVE, 0)
	endx = min(x + MAX_MONSTER_MOVE + 1, MAP_WIDTH)
	endy = min(y + MAX_MONSTER_MOVE + 1, MAP_HEIGHT)

	obj_fov_map = v.copy_submap_to_fov_map(startx, starty, endx - startx, endy - starty)
	libtcod.map_compute_fov(obj_fov_map, x - startx, y - starty, MAX_MONSTER_MOVE, FOV_LIGHT_WALLS, FOV_ALGO)

	def invalidChoice(x_, y_):
		return (not libtcod.map_is_in_fov(obj_fov_map, x_ - startx, y_ - starty)) or g.map[x_][y_].blocked

	#Now pick a random spot from within sight of that
	tx = x
	ty = y
	while ((tx == x) and (ty == y)) or invalidChoice(tx, ty):
		tx = libtcod.random_get_int(0, startx, endx)
		ty = libtcod.random_get_int(0, starty, endy)

	return (tx, ty)

#Get a random tile with darkness bias
def rand_tile_dark_bias(power):
	def invalidChoice(x_, y_):
		return is_blocked(x_, y_)

	chances = {}
	for j in range(0, MAP_HEIGHT):
		for i in range (0, MAP_WIDTH):
			if not invalidChoice(i, j):
				chances[(i, j)] = (99 - g.map[i][j].light_level)**power #do this so they don't get abandoned by orcs and have all 0s
	
	return random_choice(chances)

#Get a random empty tile with light bias
def rand_tile_light_bias(power):
	def invalidChoice(x_, y_):
		return is_blocked(x_, y_)

	chances = {}
	for j in range(0, MAP_HEIGHT):
		for i in range (0, MAP_WIDTH):
			if not invalidChoice(i, j):
				chances[(i, j)] = (g.map[i][j].light_level + 1)**power #do this so they don't get abandoned by orcs and have all 0s
	
	return random_choice(chances)

#Get a random tile that's totally dark
#If it fails, just does cubic dark bias
def rand_tile_darkest():
	def invalidChoice(x_, y_):
		return is_blocked(x_, y_)

	poss = []

	for j in range(0, MAP_HEIGHT):
		for i in range (0, MAP_WIDTH):
			if g.map[i][j].light_level == LIGHT_MIN and not invalidChoice(i, j):
				poss.append((i,j))

	
	if len(poss) > 0:
		return random.choice(poss)

	return rand_tile_dark_bias(3)

def get_empty_tile():
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
	if g.map[x][y].blocked:
		return True
 
	#now check for any blocking g.objects
	for object in g.objects:
		if object.blocks and object.x == x and object.y == y:
			return True
 
	return False
 
def blocked_by(x, y):
	#first test the map tile
	if g.map[x][y].blocked:
		return "wall"
 
	#now check for any blocking g.objects
	for object in g.objects:
		if object.blocks and object.x == x and object.y == y:
			return object.name
 
	return False


def from_dungeon_level(table):
	#returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
	for (value, level) in reversed(table):
		if g.dungeon_level >= level:
			return value
	return 0


##Queue stuff
#Insert into q at time t
def qinsert(o, t):
	# s = "q: "
	# for (obj, movetime) in g.q:
	# 	s += str((obj.name, movetime)) + ", "
	# print s

	i = 0
	while i < len(g.q) and t >= g.q[i][1]:
		i += 1

	g.q.insert(i, (o, t))

#If movement ever goes wrong check this out
def qremove(o):
	for i in g.q:
		if i[0] == o:
			g.q.remove(i)
 
#Remove an object both from the q and from g.objects
def oremove(o):
		#If it's a light source, remove it!
	if o.light:
		v.remove_light(o)

	qremove(o)
	g.objects.remove(o)





def throw_object(object, startx, starty, endx, endy, max_range=None):
	#Continuously move the object
	while (object.x != endx or object.y != endy) and (max_range == None or object.distance(startx, starty) < max_range):
		if not object.move_simple(endx, endy):
			block_x, block_y = object.get_next_move_simple_abs(endx, endy)
			hitName = blocked_by(block_x, block_y)
			ui.message("The " + object.name + " hits the " + hitName)
			break


def BFS(x, y, xt, yt):
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
			reachable.append(g.map[curX][curY])

			#print "On tile " + str((curX, curY))

			#Now, if it's less than depth, add all neighboring tile sthat haven't been reached
			if curDist < depth and g.map[curX][curY].block_sight == False:
				for dx in [-1, 0, 1]:
					for dy in [-1, 0, 1]:
						if dx != 0 and dy != 0:
							newx = curX + dx
							newy = curY + dy
							if(g.map[newx][newy] not in reachable):
								queue.append((newx, newy, curDist + pythdist(curX, curY, newx, newy)))
	return reachable



def boundedX(start, stop):
	bstart = max(start, 0)
	bstop = min(stop, MAP_WIDTH)
	return range(bstart, bstop)

def boundedY(start, stop):
	bstart = max(start, 0)
	bstop = min(stop, MAP_HEIGHT)
	return range(bstart, bstop)
