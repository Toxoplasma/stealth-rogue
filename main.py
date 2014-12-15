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
import g
import tile
import object
import item
import ui
import v
import u
import monsters
import maps



 
 
def player_move_or_attack(dx, dy): #TODO: just make this a subfunction of fighter
 	#the coordinates the player is moving to/attacking
	x = g.player.x + dx
	y = g.player.y + dy
 
	#try to find an attackable object there
	target = None
	for object in g.objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break
 
	#attack if target found, move otherwise
	if target is not None:
		#If target can see player, it's a fight!
		if target.ai.can_see_player:
			g.player.fighter.attack(target)
		else: #Can't see the player, ITS A STAB
			stab(target)
		return g.player.fighter.attackspeed
	else:
		g.fov_recompute = True
		return g.player.move(dx, dy)
 

def stab(target):
	#ui.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
	ui.message('Stabby stab stab! You stab the ' + target.name + ' to death.')
	target.fighter.take_damage(10000)


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
		scorewin, scorew, scoreh = ui.show_highscores()
		x = 2
		y = 2
		libtcod.console_blit(scorewin, 0, 0, scorew, scoreh, 0, x, y, 1.0, 0.7)
		#libtcod.console_flush()

		#show options and wait for the player's choice
		choice = ui.menu('', ['Play a new game', 'Continue last saved game', 'Start debug game', 'Save and quit'], 24)
 
		if choice == 0:  #new game
			new_game()
			play_game()
		elif choice == 1:  #load last game
			try:
				load_game()
			except:
				ui.msgbox('\n No saved game to load.\n', 24)
				continue
			play_game()
		elif choice == 2:  #start debug game
			new_debug_game()
			play_game()
		elif choice == 3:  #quit
			break
 
def handle_keys():
	key = g.key

 	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
	elif key.vk == libtcod.KEY_ESCAPE:
		return 'exit'  #exit game
 
	if g.game_state == 'playing':
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
			return g.player.wait()
			#pass  #do nothing ie wait for the monster to come to you
		else:
			#test for other keys
 
			if key_char == ',' or key_char == 'g':
				#pick up an item
				for object in g.objects:  #look for an item in the player's tile
					if object.x == g.player.x and object.y == g.player.y and object.item:
						object.item.pick_up(g.player)
						break
 
			if key_char == 'i':
				#show the inventory; if an item is selected, use it
				chosen_item = ui.inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.use()
 
			if key_char == 'd':
				#show the inventory; if an item is selected, drop it
				chosen_item = ui.inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
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
				if g.stairs.x == g.player.x and g.stairs.y == g.player.y:
					next_level()
 
			return False
 
def check_level_up():
	#see if the player's experience is enough to level-up
	level_up_xp = LEVEL_UP_BASE + g.player.level * LEVEL_UP_FACTOR
	if g.player.fighter.xp >= level_up_xp:
		#it is! level up and ask to raise some stats
		level_up()
		

def level_up():
	g.player.level += 1
	#g.player.fighter.xp -= level_up_xp
	ui.message('Your skills grow! You reached level ' + str(g.player.level) + '!', libtcod.yellow)

	choices = ui.multimenu("Multimenu test\n", 
	 	['Test 1',
	 	 'Test 2',
	 	 'TEST 3'], LEVEL_SCREEN_WIDTH, 2, True)

	choice = None
	while choice == None:  #keep asking until a choice is made
		choice = menu('Level up! Choose a stat to raise:\n',
					  ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
					   'Strength (+1 attack, from ' + str(player.fighter.power) + ')',
					   'Agility (+1 defense, from ' + str(player.fighter.defense) + ')'], LEVEL_SCREEN_WIDTH)

	if choice == 0:
		g.player.fighter.base_max_hp += 20
		g.player.fighter.hp += 20
	elif choice == 1:
		g.player.fighter.base_power += 1
	elif choice == 2:
		g.player.fighter.base_defense += 1

 
def add_highscore(score):
	playername = g.player.playername

	#Load highscores from file
	try:
		file = shelve.open('highscores', 'r')
		scores = file['scores']
		file.close()

		#Insert score
		i = 0
		while i < len(scores) and score <= scores[i][1]:
			i += 1

		scores.insert(i, (playername, score))

	except:
		print "No highscore file found."
		scores = [(playername, score)]

	#Write them back to the file
	file = shelve.open('highscores', 'n')
	file['scores'] = scores
	file.close()



def player_death(player):
	#the game ended!
	global game_state
	ui.message('You died!', libtcod.red)
	g.game_state = 'dead'
 
	#for added effect, transform the player into a corpse!
	g.player.char = '%'
	g.player.color = libtcod.dark_red

	#Put their score into a high score
	score = g.dungeon_level

	add_highscore(score)


	# #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
	# while True:
	# 	#render the screen. this erases the inventory and shows the names of g.objects under the mouse.
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
 

def closest_monster(max_range):
	#find closest enemy, up to a maximum range, and in the player's FOV
	closest_enemy = None
	closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
	for object in g.objects:
		if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
			#calculate distance between this object and the player
			dist = player.distance_to(object)
			if dist < closest_dist:  #it's closer, so remember it
				closest_enemy = object
				closest_dist = dist
	return closest_enemy
 

##Saving and ##loading
def save_game():
	print "Saving game..."

	#Make each object in the queue remember its position
	for obj in g.objects:
		obj.in_q = False
	for (obj, movetime) in g.q:
		obj.in_q = True
		obj.next_move = movetime

	#open a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = g.map
	file['objects'] = g.objects
	file['player_index'] = g.objects.index(g.player)  #index of player in g.objects list
	file['stairs_index'] = g.objects.index(g.stairs)  #same for the stairs
	file['game_msgs'] = g.game_msgs
	file['game_state'] = g.game_state
	file['dungeon_level'] = g.dungeon_level
	file['time'] = g.time
	file.close()

	for object in g.objects:
		print "  " + object.name + ": " + str((object.x, object.y))
 
def load_game():
	#open the previously saved shelve and load the game data
	print "Loading game..."
 
	file = shelve.open('savegame', 'r')
	g.map = file['map']
	g.objects = file['objects']
	g.player = g.objects[file['player_index']]  #get index of player in g.objects list and access it
	g.stairs = g.objects[file['stairs_index']]  #same for the stairs
	g.game_msgs = file['game_msgs']
	g.game_state = file['game_state']
	g.dungeon_level = file['dungeon_level']
	#q = file['q']
	g.time = file['time']
	file.close()

	print "  Loaded variables, initializing FOV..."
 
	v.initialize_fov()

	print "  Updating lights..."
	v.update_lights()

	print "  Rebuilding queue..."
	#Rebuild the queue
	g.q = [(g.player, g.time)]
 
 	for obj in g.objects:
		if obj != g.player and obj.in_q:
			print "    Inserting " + obj.name + " into queue at time " + str(obj.next_move)
			u.qinsert(obj, obj.next_move)

##New game
def new_game(name = ""): 
	#create object representing the player
	fighter_component = object.Fighter(hp=100, defense=1, power=2, xp=0, mana=100, death_function=player_death)
	g.player = object.Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)
 
	g.player.level = 1

	inventory = []
	g.player.fighter.inventory = inventory

	#g.skills = {'Stealth': 0,
	#			'Stabbing': 0,
	#			'Translocation': 0}


	#Set up the game timer!
	g.time = 0
	#create the list of game messages and their colors, starts empty
	g.game_msgs = []
 
	#generate map (at this point it's not drawn to the screen)
	g.dungeon_level = 0
	next_level()
	#make_map()
	#initialize_fov()
 
	g.game_state = 'playing'

	#Get the player's name
	if name == "":
		name = ui.text_input("What is your name?")
	g.player.playername = name
 
	#a warm welcoming message!
	ui.message('Welcome ' + name + '! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
 
	#initial equipment: a dagger
	equipment_component = item.Equipment(slot='right hand', power_bonus=2)
	obj = object.Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
	g.objects.append(obj)
	obj.item.pick_up(g.player)
	#player.fighter.inventory.append(obj)
	equipment_component.equip()
	obj.always_visible = True

##New debug game
def new_debug_game():
	new_game("Debugger")

 
#advance to the next level
def next_level():
	ui.message('You descend deeper into the dungeon')
	#ui.message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
	#player.fighter.heal(player.fighter.max_hp / 2)  #heal the player by 50%
 
	g.dungeon_level += 1
	g.branch = 'grounds'

	#Reset the movement queue to just the player
	g.q = [(g.player, g.time + 1)]

	#If the player has any items with timed, put them in the queue
	for item in g.player.fighter.inventory:
		if item.ai:
			qinsert(item, time + 2)

	#maps.make_map()  #create a fresh new level!
	maps.make_grounds()
	v.initialize_fov()


##Main game
def play_game():
	#Give all monsters a free step to compute their destinations
	for unit in g.objects:
		if unit.ai:
			unit.ai.take_turn()
			
	player_action = None

 
	g.mouse = libtcod.Mouse()
	g.key = libtcod.Key()
	# answer = ui.multimenu("Multimenu test\n", 
	# 	['Test 1',
	# 	 'Test 2',
	# 	 'TEST 3'], LEVEL_SCREEN_WIDTH, 2, True)

	# print answer
	#main loop
	while not libtcod.console_is_window_closed():
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, g.key, g.mouse)
		#render the screen
		ui.render_all()
 
		libtcod.console_flush()
 
		#level up if needed
		check_level_up()
 
		#erase all g.objects at their old locations, before they move
		for object in g.objects:
			object.clear()
 
		#handle keys and exit game if needed
		player_action = handle_keys()
		if player_action == 'exit':
			save_game()
			break
 
		#let monsters take their turn
		if g.game_state == 'playing' and player_action != False:
			#Update FOV after moving
			v.update_fov()

			#Pop player off queue,
			_, playerstarttime = g.q.pop(0)
			g.time = playerstarttime
			u.qinsert(g.player, g.time + player_action)

			print "player moving at time " + str(playerstarttime)

			#g.time = time + player_action
				
			#Now, repeatedly pop other things off until we get a player
			while(g.q[0][0] != g.player):
				unit, newtime = g.q.pop(0)

				if unit.ai:
					g.time = newtime

					print unit.name + " moving at time " + str(g.time)

					turntime = unit.ai.take_turn()

					#Readd to movement queue
					if turntime >= 0:
						u.qinsert(unit, g.time + turntime)

 


#terminal12x12_gs_ro.png
libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
libtcod.sys_set_fps(LIMIT_FPS)
g.con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
libtcod.console_clear(g.con)  #unexplored areas start black (which is the default background color)

g.panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
 
main_menu()