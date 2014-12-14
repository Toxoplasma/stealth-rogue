import libtcodpy as libtcod
import textwrap
import shelve
import math


import g
import vision
import u
import v

from consts import *

def in_sight_message(msg, color, actor):
	if player_can_see_obj(actor):
		message(msg, color)
		return True

	return False

def message(new_msg, color = libtcod.white):
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(g.game_msgs) == MSG_HEIGHT:
			del g.game_msgs[0]
 
		#add the new line as a tuple, with the text and the color
		g.game_msgs.append( (line, color) )


def render_all():
	global g #THIS IS DUMB

	if g.fov_recompute:
		g.fov_recompute = False

		#Compute light levels
		#update_lights()
		
		#recompute FOV if needed (the player moved or something)
		vision.update_fov() #TODO: move this somewhere more sensible

	#Generate colormap
	colormap = [[[0, 0, 0] for y in range(0, MAP_HEIGHT)] for x in range(0, MAP_WIDTH)]
	visibleMap = [[False for y in range(0, MAP_HEIGHT)] for x in range(0, MAP_WIDTH)]

	#go through all tiles, and set their background color according to the FOV
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			LOS = libtcod.map_is_in_fov(g.fov_map, x, y)
			visible = LOS and ((g.map[x][y].light_level > MIN_TILE_LIGHT_LEVEL) or (u.pythdist(x, y, g.player.x, g.player.y) < VISION_DISTANCE_WITHOUT_LIGHT))
			if not visible:
				#if it's not visible right now, the player can only see it if it's explored
				if g.map[x][y].explored:
					(rc, gc, bc) = g.map[x][y].dark_color
					colormap[x][y][0] += rc
					colormap[x][y][1] += gc
					colormap[x][y][2] += bc
			else:
				#it's visible
				visibleMap[x][y] = True
				light = v.get_light(x, y)

				#Don't show light levels on walls, makes it too confusing
				if g.map[x][y].blocked:
					light = 0 #light / 2 #/2 is nice but you can see through walls...
				#light = rand_lin_fluc(light) #Randomly fluctuate a little, for style points
				(rc, gc, bc) = g.map[x][y].light_color

				colormap[x][y][0] += rc + R_FACTOR*light
				colormap[x][y][1] += gc + G_FACTOR*light
				colormap[x][y][2] += bc + B_FACTOR*light
				
				#since it's visible, mark it as explored
				g.map[x][y].explored = True

	#Go through units, add vision cones
	for obj in g.objects:
		if obj.fighter and obj.ai and visibleMap[obj.x][obj.y]:
			if obj.fighter.look_towards != (-1, -1):
				for x in u.boundedX(obj.x - VISION_CONE_DISPLAY_DIST, obj.x + VISION_CONE_DISPLAY_DIST + 1):
					for y in u.boundedY(obj.y - VISION_CONE_DISPLAY_DIST, obj.y + VISION_CONE_DISPLAY_DIST + 1):
						if u.pythdist(obj.x, obj.y, x, y) <= VISION_CONE_DISPLAY_DIST:
							if obj.fighter.in_vision_cone(x, y) and visibleMap[x][y]:
								colormap[x][y][0] += VISION_CONE_RED
								colormap[x][y][1] += VISION_CONE_GREEN
								colormap[x][y][2] += VISION_CONE_BLUE

	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			color = libtcod.Color(min(int(colormap[x][y][0]), 255), 
								  min(int(colormap[x][y][1]), 255), 
								  min(int(colormap[x][y][2]), 255))
			libtcod.console_set_char_background(g.con, x, y, color, libtcod.BKGND_SET)
 
	#draw all g.objects in the list, except the player. we want it to
	#always appear over all other g.objects! so it's drawn later.
	for object in g.objects:
		if object != g.player:
			#print "Drawing " + object.name + " at " + str((object.x, object.y))
			object.draw()
	g.player.draw_always()
 
	#blit the contents of "con" to the root console
	libtcod.console_blit(g.con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
 
 
	#prepare to render the GUI panel
	libtcod.console_set_default_background(g.panel, libtcod.black)
	libtcod.console_clear(g.panel)
 
	#print the game messages, one line at a time
	y = 1
	for (line, color) in g.game_msgs:
		libtcod.console_set_default_foreground(g.panel, color)
		libtcod.console_print_ex(g.panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
		y += 1
 
	#show the player's stats
	render_bar(1, 1, BAR_WIDTH, 'HP', g.player.fighter.hp, g.player.fighter.max_hp,
			   libtcod.light_red, libtcod.darker_red)

	render_bar(1, 2, BAR_WIDTH, 'MP', g.player.fighter.mana, g.player.fighter.max_mana,
			   libtcod.light_blue, libtcod.darker_blue)


	libtcod.console_print_ex(g.panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(g.dungeon_level))
 
	#display names of g.objects under the mouse
	libtcod.console_set_default_foreground(g.panel, libtcod.light_gray)
	libtcod.console_print_ex(g.panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
 
	#blit the contents of "panel" to the root console
	libtcod.console_blit(g.panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

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
	for i in range(0, min(25, len(scores))): #(name, score) in scores[0 : min(25, len(scores))]:
		(name, score) = scores[i]
		spacecount = max(20 - len(name) - len(str(i)), 0)
		texts.append(str(i) + ". " + name + (' ' * spacecount) + str(score))
	#menu("High Scores", texts, SCORE_WIDTH)

	#calculate total height for the header (after auto-wrap) and one line per option
	header = "High Scores"
	width = SCORE_WIDTH
	header_height = libtcod.console_get_height_rect(g.con, 0, 0, width, SCREEN_HEIGHT, header)
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
		text = option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1

	return window, width, height





def menu(header, options, width):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
 
	#calculate total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(g.con, 0, 0, width, SCREEN_HEIGHT, header)
	if header == '':
		header_height = 0
	height = len(options) + header_height
 
	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)

	#libtcod.console_fill_background(window, libtcod.red)
 
	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	#libtcod.console_set_default_background(window, libtcod.red)
	#print "SETTING IT TO RED: " + header
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_SET, libtcod.LEFT, header)
 
	#print all the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_SET, libtcod.LEFT, text)
		y += 1
		letter_index += 1
 
	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.0)
 
	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
 
	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)
 
	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None


def multimenu(header, options, width, numChoices, removeAfter):
	choices = []

	newOptions = options

	while len(choices) < numChoices:
		choice = menu(header, newOptions, width)

		if choice == None:
			return None

		choices.append(options.index(newOptions[choice]))

		if removeAfter:
			newOptions.remove(newOptions[choice])

		#Redraw block behind menu
		render_all()

	return choices

 
def inventory_menu(header):
	#show a menu with each item of the inventory as an option
	if len(g.player.fighter.inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = []
		for item in g.player.fighter.inventory:
			text = item.name
			#show additional information, in case it's equipped
			if item.equipment and item.equipment.is_equipped:
				text = text + ' (on ' + item.equipment.slot + ')'
			options.append(text)
 
	index = menu(header, options, INVENTORY_WIDTH)
 
	#if an item was chosen, return it
	if index is None or len(g.player.fighter.inventory) == 0: return None
	return g.player.fighter.inventory[index].item
 
def msgbox(text, width=50):
	menu(text, [], width)  #use menu() as a sort of "message box"


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	#render a bar (HP, experience, etc). first calculate the width of the bar
	bar_width = int(float(value) / maximum * total_width)
 
	#render the background first
	libtcod.console_set_default_background(g.panel, back_color)
	libtcod.console_rect(g.panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
 
	#now render the bar on top
	libtcod.console_set_default_background(g.panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(g.panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
 
	#finally, some centered text with the values
	libtcod.console_set_default_foreground(g.panel, libtcod.white)
	libtcod.console_print_ex(g.panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
								 name + ': ' + str(value) + '/' + str(maximum))


 
def get_names_under_mouse():
	#return a string with the names of all g.objects under the mouse
 
	(x, y) = (g.mouse.cx, g.mouse.cy)
 
	#create a list with the names of all g.objects at the mouse's coordinates and in FOV
	names = [obj.name for obj in g.objects
			 if obj.x == x and obj.y == y and libtcod.map_is_in_fov(g.fov_map, obj.x, obj.y)]
 
	names = ', '.join(names)  #join the names, separated by commas
	return names.capitalize()


def text_input(header):
	width = len(header)
	header_height = libtcod.console_get_height_rect(g.con, 0, 0, width, SCREEN_HEIGHT, header)
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


def target_tile(max_range=None):
	#return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
	while True:
		#render the screen. this erases the inventory and shows the names of g.objects under the mouse.
		libtcod.console_flush()
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, g.key, g.mouse)
		render_all()
 
		(x, y) = (g.mouse.cx, g.mouse.cy)
 
		if g.mouse.rbutton_pressed or g.key.vk == libtcod.KEY_ESCAPE:
			return (None, None)  #cancel if the player right-clicked or pressed Escape
 
		#accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
		if (g.mouse.lbutton_pressed and libtcod.map_is_in_fov(g.fov_map, x, y) and
				(max_range is None or g.player.distance(x, y) <= max_range)):
			return (x, y)




def target_monster(max_range=None):
	#returns a clicked monster inside FOV up to a range, or None if right-clicked
	while True:
		(x, y) = target_tile(max_range)
		if x is None:  #player cancelled
			return None
 
		#return the first clicked monster, otherwise continue looping
		for obj in g.objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != player:
				return obj
 