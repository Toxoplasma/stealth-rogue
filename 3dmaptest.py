#!/usr/bin/python

import libtcodpy as libtcod
#import math
import timeit

from math import floor, ceil, sqrt


#actual size of the window
SCREEN_WIDTH = 100 #80
SCREEN_HEIGHT = 60 #50
 
#size of the map
MAP_WIDTH = 100 #80
MAP_HEIGHT = 50 #45
MAP_DEPTH = 30

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 0

LIMIT_FPS = 20  #20 frames-per-second maximum

color_dark_wall = (0, 0, 100)#libtcod.Color(0, 0, 100)
color_light_wall = (50, 50, 50)#libtcod.Color(130, 110, 50)
color_dark_ground = (50, 50, 150)#libtcod.Color(50, 50, 150)
color_light_ground = (200, 180, 50)#libtcod.Color(200, 180, 50)

MAX_SIGHT_DOWN = 2

#Map gen
FLOOR_HEIGHT = 20
CHANNEL_HEIGHT = 15

class Tile:
	#a tile of the map and its properties
	def __init__(self, wall, dark_color, light_color, block_sight = None):
		self.wall = wall
		#self.floor = floor
 
		#all tiles start unexplored
		self.explored = False

		#Amount of light on the tile
		self.light_level = 0
 
		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = wall or floor
		self.block_sight = block_sight

		#colors
		self.dark_color = dark_color
		self.light_color = light_color


class Object:
	#this is a generic object: the player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, z, char, color):
		self.x = x
		self.y = y
		self.z = z
		self.char = char
		self.color = color
 
	def move(self, dx, dy, dz):
		#move by the given amount, if the destination is not blocked
		if not map[self.x + dx][self.y + dy][self.z + dz].wall:
			self.x += dx
			self.y += dy
			self.z += dz
 
	def draw(self):
		#only show if it's visible to the player
		#if libtcod.map_is_in_fov(fov_map, self.x, self.y):
			#set the color and then draw the character that represents this object at its position
		libtcod.console_set_default_foreground(con, self.color)
		libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
	def clear(self):
		#erase the character that represents this object
		libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

playerX = 20
playerY = 20


def make_empty(x, y, z):
	global map

	map[x][y][z].wall = False
	#map[x][y][z].floor = False
	map[x][y][z].block_sight = False
	#map[x][y][z].blocked = False

def make_floor(x, y, z):
	global map

	map[x][y][z].wall = False
	#map[x][y][z].floor = True
	map[x][y][z].block_sight = True

def make_wall(x, y, z):
	global map

	map[x][y][z].wall = True
	#map[x][y][z].floor = False
	map[x][y][z].block_sight = True


def genMap():
	global map, surfaces

	floor_level = FLOOR_HEIGHT
	channel_level = CHANNEL_HEIGHT

	#Make it all even ground
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			for z in range(MAP_DEPTH):
				if z > floor_level:
					make_empty(x, y, z)

				# elif z == 50:
				# 	make_floor(x, y, z)


	#Carve a channel
	for z in range(channel_level, channel_level + 6):
		for y in range(MAP_HEIGHT):
			for x in range(20, 30):
				make_empty(x, y, z)
				# if z == 44:
				# 	make_floor(x, y, z)


	#Make a bridge
	for y in range(10, 15):
		for x in range(20, 30):
			make_wall(x, y, floor_level)

	surfaces = surface_list()


def mark_line(x1, y1, z1, x2, y2, z2, fov_map):
	x = x1
	y = y1
	z = z1

	vector = (x2 - x1, y2 - y1, z2 - z1)
	vector_mag = math.sqrt(vector[0]**2 + vector[1]**2 + vector[2]**2)
	norm_vector = (vector[0]/vector_mag, vector[1]/vector_mag, vector[2]/vector_mag)

	while int(round(x)) != x2 or int(round(y)) != y2 or int(round(z)) != z2:
		#Move them
		x += norm_vector[0]
		y += norm_vector[1]
		z += norm_vector[2]

		rx = int(round(x))
		ry = int(round(y))
		rz = int(round(z))

		#print str((x, y, z))

		fov_map[int(rx)][int(ry)][int(rz)] = True

		#Mark it
		if map[int(rx)][int(ry)][int(rz)].block_sight:
			break

	return fov_map



def compute_FOV_2(startx, starty, startz):
	depth_map = [[[0 for z in range(MAP_DEPTH)] for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

	depth_map[startx][starty][startz] = 2

	def distFromStart((x, y, z)):
		return (x-startx)**2 + (y-starty)**2 + (z-startz)**2

	#Do this a lot
	points = []
	for x in range(0, MAP_WIDTH):
		for y in range(0, MAP_HEIGHT):
			for z in range(0, MAP_DEPTH):
				points.append((x, y, z))

	points.remove((startx, starty, startz))

	points.sort(key = (lambda p: distFromStart(p)))

	#print points

	#for i in range(1, max(MAP_WIDTH, MAP_HEIGHT)):
	#	points = [(-y, )]
	#	for y in range(starty - i, starty + i + 1):
	#		for x in range(startx - i, startx + i + 1):
	for (x, y, z) in points:
		#print (x, y)
		debug = False
		if x == player.x - 1 and y == player.y - 1:
			debug = False

		dx = startx - x
		dy = starty - y
		dz = startz - z
		distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
 
		#normalize it to length 1 (preserving direction)
		dx = dx / distance
		dy = dy / distance
		dz = dz / distance

		curX = x + dx
		curY = y + dy
		curZ = z + dz

		while (int(round(curX)), int(round(curY)), int(round(curZ))) == (startx, starty, startz): #(curX == x and curY == y) or 
			#print str((curX, curY, curZ))
			curX += dx
			curY += dy
			curZ += dz

		next = depth_map[int(round(curX))][int(round(curY))][int(round(curZ))]

		if debug:
			print "  curX, y: " + str((curX, curY))
			print "  curZ: " + str(curZ)
			print "  z: " + str(z)
			print "  next: " + str(next)

		if next == 2: #Can see through it
			if map[x][y][z].block_sight:
				depth_map[x][y][z] = 1 #Can't see through it but can see it

			else:
				depth_map[x][y][z] = 2 #Can see through it
		else:
			depth_map[x][y][z] = 0 #Can't see it

	return depth_map

# def compute_seen_depth_top(startx, starty, startz):
# 	depth_map = [[-1 for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

# 	depth_map[startx][starty] = startz - 1

# 	def isValid(x, y):
# 		return x < MAP_WIDTH and x >= 0 and y < MAP_HEIGHT and y >= 0

# 	def distFromStart((x, y)):
# 		return (x-startx)**2 + (y-starty)**2

# 	#Do this a lot
# 	points = []
# 	for x in range(0, MAP_WIDTH):
# 		for y in range(0, MAP_HEIGHT):
# 			points.append((x, y))

# 	points.remove((startx, starty))

# 	points.sort(key = (lambda p: distFromStart(p)))

# 	#print points

# 	#for i in range(1, max(MAP_WIDTH, MAP_HEIGHT)):
# 	#	points = [(-y, )]
# 	#	for y in range(starty - i, starty + i + 1):
# 	#		for x in range(startx - i, startx + i + 1):
# 	for (x, y) in points:
# 		#print (x, y)
# 		if isValid(x, y):# and (y == starty - i or y == starty + i or x == startx - i or x == startx + i):
# 			#print "x, y: " + str((x, y))
# 			debug = False
# 			if x == player.x - 1 and y == player.y - 1:
# 				debug = False

# 			z = -1
# 			#for zDepth in range(startz, 0, -1): #Drop a line down on each square, compute if we can see that based on previously processed squares
# 			for zDepth in range(MAP_DEPTH - 2, -1, -1): #Drop a line down on each square, compute if we can see that based on previously processed squares
# 				if map[x][y][zDepth].block_sight and not map[x][y][zDepth + 1].block_sight:
# 					z = zDepth
					
# 					dx = startx - x
# 					dy = starty - y
# 					dz = startz - z
# 					distanceXY = math.sqrt(dx ** 2 + dy ** 2)
			 
# 					#normalize it to length 1 (preserving direction), then round it and
# 					#convert to integer so the movement is restricted to the map grid
# 					dx = dx / distanceXY
# 					dy = dy / distanceXY
# 					dz = dz / distanceXY

# 					curX = x + dx
# 					curY = y + dy
# 					curZ = z + dz

# 					while depth_map[int(round(curX))][int(round(curY))] == -1: #(curX == x and curY == y) or 
# 						#print str((curX, curY, curZ))
# 						curX += dx
# 						curY += dy
# 						curZ += dz

# 					next = depth_map[int(round(curX))][int(round(curY))]

# 					if debug:
# 						print "  curX, y: " + str((curX, curY))
# 						print "  curZ: " + str(curZ)
# 						print "  z: " + str(z)
# 						print "  next: " + str(next)

# 					if z >= next - MAX_SIGHT_DOWN * (curZ - z):
# 						depth_map[x][y] = z
# 						break
# 					else:
# 						depth_map[x][y] = -1 #Can't see it

# 			#else:
# 			#	print "ERROR: BOTTOMLESS PIT?"


# 	return depth_map

#This works well but only looks up
def compute_seen_depth_inverted(startx, starty, startz):
	global depth_map_up, see_map_up
	#print "player: " + str((player.x, player.y))
	#depth_map = [[DepthMapCell(-1, False, False) for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]
	#depth_map = [[DepthMapCell(-1, False) for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]
	

	# depth_map[startx][starty].z = startz - 1
	# depth_map[startx][starty].can_see = True
	depth_map_up[startx][starty] = startz - 1
	see_map_up[startx][starty] = True

	def isValid(x, y):
		return x < MAP_WIDTH and x >= 0 and y < MAP_HEIGHT and y >= 0

	def distFromStart((x, y)):
		return (x-startx)**2 + (y-starty)**2

	def roundToPlayer(x, y, z):
		if player.x < x:
			x = floor(x)
		else:
			x = ceil(x)

		if player.y < y:
			y = floor(y)
		else:
			y = ceil(y)

		if player.z < z:
			z = floor(z)
		else:
			z = ceil(z)

		return x, y, z

	#Get all points other than the start and sort them by distance
	points = []
	for x in xrange(0, MAP_WIDTH):
		for y in xrange(0, MAP_HEIGHT):
			points.append((x, y))

	points.remove((startx, starty))

	points.sort(key = (lambda p: distFromStart(p)))

	count = 0
	#print "points length: " + str(len(points))

	#For each point
	#for (x, y) in points:
	for i in xrange(len(points)):
		x, y = points[i]
		#print (x, y)
		#print "x, y: " + str((x, y))
		debug = False
		if x == player.x + 1 and y == player.y - 1:
			debug = True

		#Find the highest block lower than the player (we're looking down)
		z = -1
		for zDepth in xrange(startz, MAP_DEPTH, 1): #Drop a line down on each square, compute if we can see that based on previously processed squares
			if map[x][y][zDepth].block_sight:
				z = zDepth
				break

		#Assuming we're not over a bottomless pit
		if z != -1:
			#Compute vector towards player
			dx = startx - x
			dy = starty - y
			dz = startz - z
			distanceXY = sqrt(dx ** 2 + dy ** 2)
	 
			#normalize it to length 1 (preserving direction) in XY, and get the Z/step in that direction
			dx = dx / distanceXY
			dy = dy / distanceXY
			dz = dz / distanceXY

			#Start at the location and step towards the center
			curX = x + dx
			curY = y + dy
			curZ = z + dz

			nextX, nextY, nextZ = roundToPlayer(curX, curY, curZ)
			nextX = int(nextX)
			nextY = int(nextY)
			nextZ = int(nextZ)

			#If we can see the current tile, then we simply need to check if we can see x,y over that tile
			#So set forwards until we can see the tile in the way
			#while depth_map[nextX][nextY].can_see == False: #(curX == x and curY == y) or 
			failed = False
			while see_map_up[nextX][nextY] == False: #(curX == x and curY == y) or 
				if map[nextX][nextY][nextZ].wall:
					failed = True
					break
				#print str((curX, curY, curZ))
				curX += dx
				curY += dy
				curZ += dz

				nextX, nextY, nextZ = roundToPlayer(curX, curY, curZ)
				nextX = int(nextX)
				nextY = int(nextY)
				nextZ = int(nextZ)

				count += 1

			next = depth_map_up[nextX][nextY]

			if not failed and next > curZ:

				depth_map_up[x][y] = z
				see_map_up[x][y] = True
			else:
				depth_map_up[x][y] = -1 #Can't see it
				see_map_up[x][y] = False
				# depth_map[x][y].can_see_past = True

		else:
			depth_map_up[x][y] = MAP_DEPTH + 1
			see_map_up[x][y] = True


#This works well but doesn't look up
def compute_seen_depth(startx, starty, startz):
	global depth_map_down, see_map_down
	#print "player: " + str((player.x, player.y))
	#depth_map = [[DepthMapCell(-1, False, False) for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]
	#depth_map = [[DepthMapCell(-1, False) for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]

	# depth_map[startx][starty].z = startz - 1
	# depth_map[startx][starty].can_see = True
	depth_map_down[startx][starty] = startz - 1
	see_map_down[startx][starty] = True

	def isValid(x, y):
		return x < MAP_WIDTH and x >= 0 and y < MAP_HEIGHT and y >= 0

	def distFromStart((x, y)):
		return (x-startx)**2 + (y-starty)**2

	def roundToPlayer(x, y, z):
		if player.x < x:
			x = floor(x)
		else:
			x = ceil(x)

		if player.y < y:
			y = floor(y)
		else:
			y = ceil(y)

		if player.z < z:
			z = floor(z)
		else:
			z = ceil(z)

		return x, y, z

	#Get all points other than the start and sort them by distance
	points = []
	for x in xrange(0, MAP_WIDTH):
		for y in xrange(0, MAP_HEIGHT):
			points.append((x, y))

	points.remove((startx, starty))

	points.sort(key = (lambda p: distFromStart(p)))

	count = 0
	#print "points length: " + str(len(points))

	#For each point
	#for (x, y) in points:
	for i in xrange(len(points)):
		x, y = points[i]
		#print (x, y)
		#print "x, y: " + str((x, y))
		debug = False
		if x == player.x + 1 and y == player.y - 1:
			debug = True

		#Find the highest block lower than the player (we're looking down)
		z = -1
		for zDepth in xrange(startz, 0, -1): #Drop a line down on each square, compute if we can see that based on previously processed squares
			if map[x][y][zDepth].block_sight:
				z = zDepth
				break

		#Assuming we're not over a bottomless pit
		if z != -1:
			#Compute vector towards player
			dx = startx - x
			dy = starty - y
			dz = startz - z
			distanceXY = sqrt(dx ** 2 + dy ** 2)
	 
			#normalize it to length 1 (preserving direction) in XY, and get the Z/step in that direction
			dx = dx / distanceXY
			dy = dy / distanceXY
			dz = dz / distanceXY

			#Start at the location and step towards the center
			curX = x + dx
			curY = y + dy
			curZ = z + dz

			nextX, nextY, nextZ = roundToPlayer(curX, curY, curZ)
			nextX = int(nextX)
			nextY = int(nextY)
			nextZ = int(nextZ)

			#If we can see the current tile, then we simply need to check if we can see x,y over that tile
			#So set forwards until we can see the tile in the way
			#while depth_map[nextX][nextY].can_see == False: #(curX == x and curY == y) or 
			failed = False
			while see_map_down[nextX][nextY] == False: #(curX == x and curY == y) or 
				if map[nextX][nextY][nextZ].wall:
					failed = True
					break
				#print str((curX, curY, curZ))
				curX += dx
				curY += dy
				curZ += dz

				nextX, nextY, nextZ = roundToPlayer(curX, curY, curZ)
				nextX = int(nextX)
				nextY = int(nextY)
				nextZ = int(nextZ)

				count += 1

			next = depth_map_down[nextX][nextY]

			if not failed and next < curZ:

				depth_map_down[x][y] = z
				see_map_down[x][y] = True
			else:
				depth_map_down[x][y] = -1 #Can't see it
				see_map_down[x][y] = False
				# depth_map[x][y].can_see_past = True

		else:
			depth_map_down[x][y] = -1
			see_map_down[x][y] = True


def compute_FOV(startx, starty, startz):
	#For each edge point, cast a line towards it, marking all points along the way
	fov_map = [[[True for z in range(MAP_DEPTH)] for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

	#Top/bottom
	# for z in [0, MAP_DEPTH-1]:
	# 	for y in range(MAP_HEIGHT):
	# 		for x in range(MAP_WIDTH):
	# 			fov_map = mark_line(startx, starty, startz, x, y, z, fov_map)

	# for x in [0, MAP_WIDTH - 1]:
	# 	for z in range(MAP_DEPTH):
	# 		for y in range(MAP_HEIGHT):
	# 			fov_map = mark_line(startx, starty, startz, x, y, z, fov_map)

	# for y in [0, MAP_HEIGHT - 1]:
	# 	for z in range(MAP_DEPTH):
	# 		for x in range(MAP_WIDTH):
	# 			fov_map = mark_line(startx, starty, startz, x, y, z, fov_map)

	return fov_map

def isValid(x, y, z):
	return x < MAP_WIDTH and x >= 0 and y < MAP_HEIGHT and y >= 0 and z >= 0 and z < MAP_DEPTH

#Gets a list of all walls orthogonally next to open spaces
def surface_list():
	global map

	l = []

	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			for z in range(MAP_DEPTH):
				#Is it a surface?
				#Can't be a surface unless it's a wall
				if map[x][y][z].wall:
					poss = [(-1, 0, 0), (1, 0, 0),(0, -1, 0), (0, 1, 0),(0, 0, -1), (0, 0, 1)]

					surface = False
					for (dx, dy, dz) in poss:
						if isValid(x + dx, y + dy, z + dz):
							if not map[x + dx][y + dy][z + dz].wall:
								surface = True
								break

					if surface:
						l.append((x, y, z))

	return l


def surface_FOV(startx, starty, startz):
	global map, surfaces

	def rpz(n):
		if n < startz:
			return int(ceil(n))
		return int(floor(n))

	fov_map = [[[False for z in range(MAP_DEPTH)] for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

	def ir(n):
		return int(round(n))

	for (x, y, z) in surfaces:
		#Draw a line, marking each tile as visible

		#Compute difference
		dx = x - startx
		dy = y - starty
		dz = z - startz

		magnitude = sqrt(dx**2 + dy**2 + dz**2)

		dx = dx/magnitude
		dy = dy/magnitude
		dz = dz/magnitude

		cx = startx
		cy = starty
		cz = startz

		while ir(cx) != x or ir(cy) != y or ir(cz) != z:
			#Mark it visible
			fov_map[ir(cx)][ir(cy)][ir(cz)] = True

			#Increment
			cx += dx
			cy += dy
			cz += dz

			#If increment is blocked, break
			if map[ir(cx)][ir(cy)][rpz(cz)].wall:
				break

			if fov_map[ir(cx)][ir(cy)][ir(cz)]:
				break

	return fov_map

def render_top_down():
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			z = -1

			for zDepth in xrange(MAP_DEPTH - 1, -1, -1): #Drop a line down on each square, compute if we can see that based on previously processed squares
				if map[x][y][zDepth].block_sight:
					z = zDepth
					break

			print str((x, y, z))

			if z != -1:
				tile = map[x][y][z]
				r, g, b = tile.light_color #If player can see more than 1 adjacent? tile in that z-depth, it's a wall
				r += z
				g += z
				b += z
				libtcod.console_set_char_background(con, x, y, libtcod.Color(r, g, b), libtcod.BKGND_SET)

			else:
				libtcod.console_set_char_background(con, x, y, libtcod.Color(0, 0, 0), libtcod.BKGND_SET)

	#Draw player
	for object in objects:
		object.draw()

	#blit the contents of "con" to the root console
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


def render_all():
	#go through all tiles, and set their background color according to the FOV
	#Get fov map
	#fov_map = compute_FOV(player.x, player.y, player.z)

	#print "time: " + str(timeit.timeit(wrapper, number = 10))
	compute_seen_depth(player.x, player.y, player.z)
	compute_seen_depth_inverted(player.x, player.y, player.z)
	#depth_map_i = compute_seen_depth_inverted(player.x, player.y, player.z)
	#fov_map = compute_FOV_2(player.x, player.y, player.z)

	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			z = -1

			#Find the z-depth there
			# for zi in range(MAP_DEPTH - 1, -1, -1):
			# 	if map[x][y][zi].block_sight:
			# 		z = zi
			# 		break

			# print "Highest filled Z: " + str(highestFilledZ)
			#visible = libtcod.map_is_in_fov(fov_map, x, y)
			zdown = depth_map_down[x][y]
			zup = depth_map_up[x][y]

			#Down takes priority unless its a wall
			#If down is a wall, show up if it exists
			if zdown < 0 and zup >= MAP_DEPTH:
				libtcod.console_set_char_background(con, x, y, libtcod.Color(0, 0, 0), libtcod.BKGND_SET)
			else:
				if zdown >= 0 and zup >= MAP_DEPTH:
					z = zdown

				elif zdown < 0 and zup < MAP_DEPTH:
					z = zup

				#If we get to here, they're both valid. Pick lower one unless its a wall
				else: #map[x][y][zdown].wall and map[x][y][zup]
					#Pick lower one
					z = zdown

				if z < player.z:
					see_map = see_map_down
				else:
					see_map = see_map_up

				if see_map[x][y]:
					tile = map[x][y][z]
					r, g, b = tile.light_color #If player can see more than 1 adjacent? tile in that z-depth, it's a wall

					if z > -1:
						r += z
						g += z
						b += z
					libtcod.console_set_char_background(con, x, y, libtcod.Color(r, g, b), libtcod.BKGND_SET)
			# elif zi > -1:
			# 	tile = map[x][y][zi]
			# 	r, g, b = tile.light_color #If player can see more than 1 adjacent? tile in that z-depth, it's a wall

			# 	#print str((x, y)) + ": " + str(z)

			# 	r += zi
			# 	g += zi
			# 	b += zi

			# 	libtcod.console_set_char_background(con, x, y, libtcod.Color(r, g, b), libtcod.BKGND_SET)
				else:
					libtcod.console_set_char_background(con, x, y, libtcod.Color(0, 0, 0), libtcod.BKGND_SET)

	#Draw player
	for object in objects:
		object.draw()

	#blit the contents of "con" to the root console
	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


# def render_all():
# 	#go through all tiles, and set their background color according to the FOV
# 	#Get fov map
# 	#fov_map = compute_FOV(player.x, player.y, player.z)

# 	#print "time: " + str(timeit.timeit(wrapper, number = 10))
# 	#depth_map_i = compute_seen_depth_inverted(player.x, player.y, player.z)
# 	#fov_map = compute_FOV_2(player.x, player.y, player.z)

# 	fov_map = surface_FOV(player.x, player.y, player.z)


# 	for y in range(MAP_HEIGHT):
# 		for x in range(MAP_WIDTH):
# 			z = -1

# 			#Find the z-depth there
# 			for zi in range(MAP_DEPTH - 1, -1, -1):
# 				#print "zi: " + str(zi)
# 				if fov_map[x][y][zi]:
# 					z = zi
# 					break

# 			print str((x, y, z))

# 			if z > -1:
# 				tile = map[x][y][z]
# 				r, g, b = tile.light_color #If player can see more than 1 adjacent? tile in that z-depth, it's a wall

# 				r += z
# 				g += z
# 				b += z
# 				libtcod.console_set_char_background(con, x, y, libtcod.Color(r, g, b), libtcod.BKGND_SET)

# 			else:
# 				libtcod.console_set_char_background(con, x, y, libtcod.Color(0, 0, 0), libtcod.BKGND_SET)

# 	#Draw player
# 	for object in objects:
# 		object.draw()

# 	#blit the contents of "con" to the root console
# 	libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


def handle_keys():
	#key = libtcod.console_check_for_keypress()  #real-time
	key = libtcod.console_wait_for_keypress(True)  #turn-based
 
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
	elif key.vk == libtcod.KEY_ESCAPE:
		return True  #exit game
 
	#movement keys
	if libtcod.console_is_key_pressed(libtcod.KEY_UP):
		player.move(0, -1, 0)
 
	elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
		player.move(0, 1, 0)
 
	elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
		player.move(-1, 0, 0)
 
	elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
		player.move(1, 0, 0)

	elif key.c == ord('w'):
		player.move(0, 0, 1)
 
	elif key.c == ord('s'):
		player.move(0, 0, -1)



libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
 
#create object representing the player
player = Object(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, FLOOR_HEIGHT + 1, '@', libtcod.white)
 
#create an NPC
npc = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2, FLOOR_HEIGHT + 1, '@', libtcod.yellow)

#the list of objects with those two
objects = [npc, player]

map = [[[Tile(True, color_dark_wall, color_light_wall) for z in range(MAP_DEPTH)] for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

depth_map_up = [[-1 for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]
see_map_up = [[False for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]
depth_map_down = [[-1 for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]
see_map_down = [[False for y in xrange(MAP_HEIGHT)] for x in xrange(MAP_WIDTH)]

genMap()

playerMoved = True

while not libtcod.console_is_window_closed():
 
	#render the screen
	#render_top_down()
	render_all()
 
	libtcod.console_flush()
 
	#erase all objects at their old locations, before they move
	for object in objects:
		object.clear()
 
	#handle keys and exit game if needed
	exit = handle_keys()
	if exit:
		break