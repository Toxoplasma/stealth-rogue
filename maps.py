from consts import *
import random

import v
import ui
import u
import g
import tile
import object
import item
import monsters

def make_floor(x, y):
	g.map[x][y].blocked = False
	g.map[x][y].tiletype = 'floor'
	g.map[x][y].block_sight = False
	g.map[x][y].light_color = LIGHT_GROUND_COLOR
	g.map[x][y].dark_color = DARK_GROUND_COLOR

def make_wall(x, y):
	g.map[x][y].blocked = True
	g.map[x][y].tiletype = 'wall'
	g.map[x][y].block_sight = True
	g.map[x][y].light_color = LIGHT_WALL_COLOR
	g.map[x][y].dark_color = DARK_WALL_COLOR

def make_plant(x, y):
	g.map[x][y].blocked = True
	g.map[x][y].tiletype = 'plant'
	g.map[x][y].block_sight = True
	g.map[x][y].light_color = LIGHT_PLANT_COLOR
	g.map[x][y].dark_color = DARK_PLANT_COLOR

def create_room(room):
	#go through the tiles in the rectangle and make them passable
	for x in xrange(room.x1 + 1, room.x2):
		for y in xrange(room.y1 + 1, room.y2):
			make_floor(x, y)

def create_h_tunnel(x1, x2, y):
	#horizontal tunnel. min() and max() are used in case x1>x2
	for x in xrange(min(x1, x2), max(x1, x2) + 1):
		make_floor(x, y)

def create_v_tunnel(y1, y2, x):
	#vertical tunnel
	for y in xrange(min(y1, y2), max(y1, y2) + 1):
		make_floor(x, y)

def make_map():
	#the list of g.objects with just the player
	g.objects = [g.player]
 
	#fill map with "blocked" tiles
	g.map = [[ tile.Tile(True, light_color = LIGHT_WALL_COLOR, dark_color = DARK_WALL_COLOR)
			 for y in xrange(MAP_HEIGHT) ]
		   for x in xrange(MAP_WIDTH) ]
 
	rooms = []
	num_rooms = 0
 
	for r in xrange(MAX_ROOMS):
		#random width and height
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		#random position without going out of the boundaries of the map
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
 
		#"Rect" class makes rectangles easier to work with
		new_room = tile.Rect(x, y, w, h)
 
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
	g.stairs = object.Object(new_x, new_y, '>', 'stairs', libtcod.white, always_visible=True)
	g.objects.append(g.stairs)
	g.stairs.send_to_back()  #so it's drawn below the monsters

	#Generate dungeon features
	place_all_objects()

	#Calculate light
	v.update_lights()

	#Put the player down
	px, py = u.rand_tile_darkest()
	g.player.x = px
	g.player.y = py

	g.fov_map = v.copy_map_to_fov_map()
 


def place_all_objects():
	####Dungeon features
	num_features = item.spawn_features()

	####Items
	num_items = item.spawn_items()

	####Monsters 
	num_monsters = monsters.spawn_monsters()

	print "Generated " + str(num_features) + " features"
	print "Generated " + str(num_items) + " items"
	print "Generated " + str(num_monsters) + " monsters"



def make_grounds():
	g.objects = [g.player]
	g.map = [[ tile.Tile(True, 'wall', light_color = LIGHT_WALL_COLOR, dark_color = DARK_WALL_COLOR)
			 for y in xrange(MAP_HEIGHT) ]
		   for x in xrange(MAP_WIDTH) ]

	#Empty everything but the border
	for x in xrange(1, MAP_WIDTH - 1):
		for y in xrange(1, MAP_HEIGHT - 1):
			make_floor(x, y)

	#Make a bunch of random outbuildings and stuff

	door_locations = []

	for i in xrange(5):
		#Get coordinates
		width = u.rand_int(4, 6)
		height = u.rand_int(4, 6)

		startx = u.rand_int(1, MAP_WIDTH - 1 - width)
		starty = u.rand_int(1, MAP_HEIGHT - 1 - height)

		filled_tiles = []

		#Now, make all those spots filled
		for x in xrange(startx, startx + width + 1):
			for y in xrange(starty, starty + height + 1):
				#Make the edges only
				if x == startx or y == starty or x == startx + width or y == starty + height:
					make_wall(x, y)
					filled_tiles.append((x, y))

		#print filled_tiles
		#Knock a hole in the wall
		#TODO: make this a door instead
		door_loc = random.choice(filled_tiles)
		door_locations.append(door_loc)
		make_floor(door_loc[0], door_loc[1])


	### Make the stairs and player

	#Pick a random empty tile at the top of the map
	stairs_x = u.rand_int(5, MAP_WIDTH - 6)
	while g.map[stairs_x][1].blocked:
		stairs_x = u.rand_int(5, MAP_WIDTH - 6)

	#Put the stairs
	g.stairs = object.Object(stairs_x, 1, '>', 'stairs', libtcod.white, always_visible=True)
	g.objects.append(g.stairs)
	g.stairs.send_to_back()  #so it's drawn below the monsters

	#Same procedure for player, but other end of the map
	player_x = u.rand_int(1, MAP_WIDTH - 1)
	while g.map[player_x][MAP_HEIGHT - 2].blocked:
		player_x = u.rand_int(1, MAP_WIDTH - 1)

	#Put the player
	g.player.x = player_x
	g.player.y = MAP_HEIGHT - 2


	#Put torches next to walls on the inside of the map
	feat_chances = {}
	feat_chances['small torch'] = u.from_branch_level(SMALL_TORCH_CHANCE)
	feat_chances['torch'] = u.from_branch_level(MID_TORCH_CHANCE)
	feat_chances['large torch'] = u.from_branch_level(LARGE_TORCH_CHANCE)


	target_num_features = u.from_branch_level(NUM_FEATURES)
	num_features = u.rand_gauss_pos(target_num_features, target_num_features / 3)
	for i in xrange(num_features):
		x, y = u.get_empty_tile()

		#If it's the first one, put it on the stairs
		if i == 0:
			y = 1
			dx = random.choice([-1, 1])

			if g.map[stairs_x + dx][y].blocked:
				dx = -1 * dx

			if not g.map[stairs_x + dx][y].blocked:
				x = stairs_x + dx
		

		#Position chosen, pick the type	
		choice = u.random_choice(feat_chances)

		if choice == 'small torch':
			l = object.Light(SMALL_TORCH_LSL)
			feat = object.Object(x, y, '!', 'small torch', TORCH_COLOR,
				#blocks=True, 
				light=l)

		elif choice == 'torch':
			l = object.Light(TORCH_LSL)
			feat = object.Object(x, y, '!', 'torch', TORCH_COLOR,
				#blocks=True, 
				light = l)

		elif choice == 'large torch':
			l = object.Light(LARGE_TORCH_LSL)
			feat = object.Object(x, y, '!', 'large torch', TORCH_COLOR,
				#blocks=True, 
				light = l)


		g.objects.append(feat)
		feat.send_to_back()  #items appear below other g.objects

	#Redo lighting so we can spawn relevant monsters in the right places
	v.update_lights()


	#Spawn monsters
	#monsters.make_torch_guard(20, 20)
	monsters.spawn_monsters()

	return num_features
	### Make features
	#place_all_objects()

def make_gardens():
	g.objects = [g.player]
	g.map = [[ tile.Tile(True, 'wall', light_color = LIGHT_WALL_COLOR, dark_color = DARK_WALL_COLOR)
			 for y in xrange(MAP_HEIGHT) ]
		   for x in xrange(MAP_WIDTH) ]

	#Empty everything but the border
	for x in xrange(1, MAP_WIDTH - 1):
		for y in xrange(1, MAP_HEIGHT - 1):
			make_floor(x, y)

	### Make the stairs and player

	#Pick a random empty tile at the top of the map
	stairs_x = u.rand_int(5, MAP_WIDTH - 6)
	while g.map[stairs_x][1].blocked:
		stairs_x = u.rand_int(5, MAP_WIDTH - 6)

	#Put the stairs
	g.stairs = object.Object(stairs_x, 1, '>', 'stairs', libtcod.white, always_visible=True)
	g.objects.append(g.stairs)
	g.stairs.send_to_back()  #so it's drawn below the monsters

	#Same procedure for player, but other end of the map
	player_x = u.rand_int(1, MAP_WIDTH - 1)
	while g.map[player_x][MAP_HEIGHT - 2].blocked:
		player_x = u.rand_int(1, MAP_WIDTH - 1)

	#Put the player
	g.player.x = player_x
	g.player.y = MAP_HEIGHT - 2

	#Put the garden directors!
	for i in xrange(NUM_GARDEN_DIRECTORS):
		starttile = [u.rand_tile_cond(u.is_empty)]
		#tiles = [(x, i * 3 + 1) for x in range(u.rand_int(1, 20), u.rand_int(MAP_WIDTH - 21, MAP_WIDTH - 2))]

		ai_component = GardenDirector(u.rand_int(GARDEN_DIR_MIN_SPEED, GARDEN_DIR_MAX_SPEED), starttile)
		director = object.Object(-1, -1, ' ', 'ERROR: garden director', GUARD_COLOR, ai=ai_component)

		for i in xrange(u.rand_int(GARDEN_DIR_MIN, GARDEN_DIR_MAX)):
			director.ai.add_plant()

		g.objects.append(director)
		u.qinsert(director, g.time + 2) #player gets inserted at 1, monsters at 2



	#Put torches next to walls on the inside of the map
	feat_chances = {}
	feat_chances['small torch'] = u.from_branch_level(SMALL_TORCH_CHANCE)
	feat_chances['torch'] = u.from_branch_level(MID_TORCH_CHANCE)
	feat_chances['large torch'] = u.from_branch_level(LARGE_TORCH_CHANCE)

	num_features = 0

	#Place torches
	for x in xrange(1, MAP_WIDTH - 1):
		for y in xrange(1, MAP_HEIGHT - 1):
			if x % GARDEN_TORCH_FREQ == 0 and y % GARDEN_TORCH_FREQ == 0:
				newx = x + random.choice([-1, 0, 1])
				newy = y + random.choice([-1, 0, 1])

				if u.is_empty(newx, newy):
					item.spawn_small_torch(newx, newy)

					num_features += 1

	#Put one next to the stairs
	y = 1
	dx = random.choice([-1, 1])
	if g.map[stairs_x + dx][y].blocked:
		dx = -1 * dx
	if not g.map[stairs_x + dx][y].blocked:
		x = stairs_x + dx
		item.spawn_small_torch(x, y)

	#Redo lighting so we can spawn relevant monsters in the right places
	v.update_lights()


	#Spawn monsters!
	#monsters.make_torch_guard(20, 20)
	print "Num monsters: " + str(monsters.spawn_monsters())

	print "Num features: " + str(num_features)
	### Make features
	#place_all_objects()




class GardenDirector:
	def __init__(self, ticktime, plants):
		self.ticktime = ticktime
		self.plants = plants

		#Make all tiles plants
		for x, y in plants:
			make_plant(x, y)

	def add_plant(self):
		front = self.plants[0]
		x, y = front

		poss = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]

		poss = filter(lambda (a,b): u.is_empty(a, b), poss)

		if len(poss) > 0:
			#Ok, now pick a random one
			cx, cy = random.choice(poss)

			#Add it
			make_plant(cx, cy)
			u.fov_map_update_tile(cx, cy)
			self.plants.insert(0, (cx, cy))

			return True

		return False

	def take_turn(self):
		#Add a plant to the front
		if self.add_plant(): #It worked!
			#Remove from tail
			rx, ry = self.plants[-1]
			make_floor(rx, ry)
			u.fov_map_update_tile(rx, ry)
			self.plants = self.plants[:-1]
		else: #we're stuck! reverse
			self.plants = self.plants[::-1]

		return self.ticktime

		

def make_map():
	if g.branch == 'grounds':
		make_grounds()
	elif g.branch == 'gardens':
		make_gardens()