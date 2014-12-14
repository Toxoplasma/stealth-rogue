import math

from consts import *

import object
import g
import ui
import v
import u
import monsters

class Item:
	#an item that can be picked up and used.
	def __init__(self, use_function=None):
		self.use_function = use_function
		self.carrier = None
 
	def pick_up(self, newOwner):
		#add to the player's inventory and remove from the map
		if len(newOwner.fighter.inventory) >= 26:
			if newOwner == g.player:
				ui.message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
			return False
		else:
			newOwner.fighter.inventory.append(self.owner)
			self.carrier = newOwner
			g.objects.remove(self.owner)
			if newOwner == g.player:
				ui.message('You pick up the ' + self.owner.name + '!', libtcod.green)
			else:
				ui.in_sight_message('The ' + newOwner.name + ' picks up the ' + self.owner.name + '.', libtcod.white, self.owner)
 
			#special case: automatically equip, if the corresponding equipment slot is unused
			equipment = self.owner.equipment
			if equipment and get_equipped_in_slot(newOwner, equipment.slot) is None:
				equipment.equip()
 
	def drop(self):
		#special case: if the object has the Equipment component, dequip it before dropping
		if self.owner.equipment:
			self.owner.equipment.dequip()
 
		#add to the map and remove from the player's inventory. also, place it at the player's coordinates
		g.objects.append(self.owner)
		inventory.remove(self.owner)
		self.owner.x = self.carrier.x
		self.owner.y = self.carrier.y
		if newOwner == g.player:
			ui.message('You drop the ' + self.owner.name + '!', libtcod.yellow)
		else:
			ui.in_sight_message('The ' + newOwner.name + ' drops the ' + self.owner.name + '.', libtcod.white, self.owner)
 
	def use(self):
		#special case: if the object has the Equipment component, the "use" action is to equip/dequip
		if self.owner.equipment:
			self.owner.equipment.toggle_equip()
			return
 
		#just call the "use_function" if it is defined
		if self.use_function is None:
			ui.message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				self.carrier.fighter.inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason
 
class Equipment:
	#an object that can be equipped, yielding bonuses. automatically adds the Item component.
	def __init__(self, slot, power_bonus=0, defense_bonus=0, stealth_bonus=0, movespeed_bonus=0, attackspeed_bonus=0, max_hp_bonus=0, max_mana_bonus=0):
		self.power_bonus = power_bonus
		self.defense_bonus = defense_bonus
		self.max_hp_bonus = max_hp_bonus
		self.max_mana_bonus = max_mana_bonus
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
		old_equipment = get_equipped_in_slot(self.owner.item.carrier, self.slot)
		if old_equipment is not None:
			old_equipment.dequip()
 
		#equip object and show a message about it
		self.is_equipped = True
		if self.owner.item.carrier == g.player:
			ui.message('You drop the ' + self.owner.name + '!', libtcod.yellow)
		else:
			ui.in_sight_message('The ' + self.owner.item.carrier.name + ' drops the ' + self.owner.name + '.', libtcod.white, self.owner)


		ui.message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', libtcod.light_green)
 
	def dequip(self):
		#dequip object and show a message about it
		if not self.is_equipped: return
		self.is_equipped = False
		ui.message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.', libtcod.light_yellow)



def get_equipped_in_slot(unit, slot):  #returns the equipment in a slot, or None if it's empty
	for obj in unit.fighter.inventory:
		if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
			return obj.equipment
	return None
 
def get_all_equipped(obj):  #returns a list of equipped items
	equipped_list = []
	for item in obj.fighter.inventory:
		if item.equipment and item.equipment.is_equipped:
			equipped_list.append(item.equipment)
	return equipped_list



##Items
class LightDarkOrb:
	#AI for a light or dark orb, turns slowly dimmer/brighter
	def __init__(self, tick_time):
		self.can_see_player = False #Or we get a nice red background... Maybe add an is_enemy flag
		self.tick_time = tick_time
 
	def take_turn(self):
		orb = self.owner
		if orb.light:
			#Remove its light from surroundings
			v.remove_light(orb)

			#Update its light level
			LSL = orb.light.level
			sign = math.copysign(1, LSL)

			newLSL = int(sign * (abs(LSL) - 1))

			#If it's dead, remove it from the game
			if newLSL == 0:
				orb.light = None

				#Remove from everything
				u.oremove(orb)
				return -1 #don't add it to q again

			#Otherwise, change its light level and add back in its light
			orb.light.level = newLSL
			v.add_light(orb)

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
			ui.message("Your scroll of speed has worn off...")
			#We're done, remove it
			u.oremove(self.owner)
			return -1

		return self.tick_time



def spawn_features():
	feat_chances = {}
	feat_chances['small torch'] = u.from_dungeon_level(SMALL_TORCH_CHANCE)
	feat_chances['torch'] = u.from_dungeon_level(TORCH_CHANCE)
	feat_chances['large torch'] = u.from_dungeon_level(LARGE_TORCH_CHANCE)


	target_num_features = u.from_dungeon_level(NUM_FEATURES)
	num_features = u.rand_gauss_pos(target_num_features, target_num_features / 3)
	for i in range(num_features):
		x, y = u.get_empty_tile()
		choice = u.random_choice(feat_chances)

		if choice == 'small torch':
			#Create a throwable light orb!
			l = object.Light(SMALL_TORCH_LSL)
			feat = object.Object(x, y, '!', 'small torch', TORCH_COLOR,
				#blocks=True, 
				light=l)

		elif choice == 'torch':
			#Create a throwable light orb!
			l = object.Light(TORCH_LSL)
			feat = object.Object(x, y, '!', 'torch', TORCH_COLOR,
				#blocks=True, 
				light = l)

		elif choice == 'large torch':
			#Create a throwable light orb!
			l = object.Light(LARGE_TORCH_LSL)
			feat = object.Object(x, y, '!', 'large torch', TORCH_COLOR,
				#blocks=True, 
				light = l)


		g.objects.append(feat)
		feat.send_to_back()  #items appear below other g.objects


	#Redo lighting so we can spawn relevant monsters in the right places
	v.update_lights()

	return num_features


def spawn_items():
	#chance of each item (by default they have a chance of 0 at level 1, which then goes up)
	item_chances = {}
	#item_chances['heal'] = 35  #healing potion always shows up, even if all other items have 0 chance
	item_chances['light orb'] = 	u.from_dungeon_level(LIGHT_ORB_CHANCE)
	item_chances['dark orb'] = 		u.from_dungeon_level(DARK_ORB_CHANCE)
	item_chances['water balloon'] = u.from_dungeon_level(WATERBALLOON_CHANCE)
	item_chances['lightning'] = 	u.from_dungeon_level(LIGHTNING_CHANCE)
	item_chances['confuse'] =   	u.from_dungeon_level(CONFUSE_CHANCE)
	item_chances['flashbang'] = 	u.from_dungeon_level(FLASHBANG_CHANCE)
	item_chances['speed'] = 		u.from_dungeon_level(SPEED_CHANCE)
	item_chances['fireball'] =  0 #from_dungeon_level([[25, 6]])
	item_chances['sword'] =     0 #from_dungeon_level([[5, 4]])
	item_chances['shield'] =    0 #from_dungeon_level([[15, 8]])

	#choose random number of items
	target_num_items = u.from_dungeon_level(NUM_ITEMS)
	num_items = u.rand_gauss_pos(target_num_items, target_num_items / 3)
 
	for i in range(num_items):
		#choose random spot for this item
		x, y = u.get_empty_tile()
 
		#only place it if the tile is not blocked
		if not u.is_blocked(x, y):
			choice = u.random_choice(item_chances)
			# if choice == 'heal':
			# 	#create a healing potion
			# 	item_component = Item(use_function=cast_heal)
			# 	item = object.Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
			if choice == 'light orb':
				#Create a throwable light orb!
				item_component = Item(use_function=throw_light_orb)
				newitem = object.Object(x, y, '.', 'light orb', LIGHT_ORB_COLOR, itemCom=item_component)

			elif choice == 'dark orb':
				#Create a throwable light orb!
				item_component = Item(use_function=throw_dark_orb)
				newitem = object.Object(x, y, '.', 'dark orb', DARK_ORB_COLOR, itemCom=item_component)

			elif choice == 'water balloon':
				#Create a throwable light orb!
				item_component = Item(use_function=throw_water_balloon)
				newitem = object.Object(x, y, '^', 'water balloon', WATERBALLOON_COLOR, itemCom=item_component)
 
			elif choice == 'lightning':
				#create a lightning bolt scroll
				item_component = Item(use_function=cast_lightning)
				newitem = object.Object(x, y, '?', 'scroll of lightning bolt', libtcod.light_yellow, itemCom=item_component)
 
			elif choice == 'fireball':
				#create a fireball scroll
				item_component = Item(use_function=cast_fireball)
				newitem = object.Object(x, y, '?', 'scroll of fireball', libtcod.light_yellow, itemCom=item_component)
 
			elif choice == 'confuse':
				#create a confuse scroll
				item_component = Item(use_function=cast_confuse)
				newitem = object.Object(x, y, '?', 'scroll of confusion', libtcod.light_yellow, itemCom=item_component)

			elif choice == 'flashbang':
				#create a confuse scroll
				item_component = Item(use_function=cast_flashbang)
				newitem = object.Object(x, y, '^', 'flashbang grenade', libtcod.light_yellow, itemCom=item_component)

			elif choice == 'speed':
				#create a confuse scroll
				item_component = Item(use_function=cast_speed)
				newitem = object.Object(x, y, '?', 'scroll of speed', libtcod.light_yellow, itemCom=item_component)
 
			elif choice == 'sword':
				#create a sword
				equipment_component = Equipment(slot='right hand', power_bonus=3)
				newitem = object.Object(x, y, '/', 'sword', libtcod.sky, equipment=equipment_component)
 
			elif choice == 'shield':
				#create a shield
				equipment_component = Equipment(slot='left hand', defense_bonus=1)
				newitem = object.Object(x, y, '[', 'shield', libtcod.darker_orange, equipment=equipment_component)
 
			g.objects.append(newitem)
			newitem.send_to_back()  #items appear below other g.objects
			newitem.always_visible = True  #items are visible even out-of-FOV, if in an explored area

	return num_items



###SPELLS ###MAGIC

def throw_light_orb():
	#Create a puddle of light around it
	ui.message('Left-click a target tile for the light orb, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = ui.target_tile()
	if x is None: return 'cancelled'
 
	#TODO: make this land a bit randomly
	orb_ai = LightDarkOrb(LIGHT_ORB_TICK_TIME)
	l = object.Light(LIGHT_ORB_LSL)
	lit_orb = object.Object(g.player.x, g.player.y, '*', 'light orb', LIGHT_ORB_THROWN_COLOR, 
			light = l, ai = orb_ai)
	v.add_light(lit_orb)

	u.throw_object(lit_orb, g.player.x, g.player.y, x, y)

	g.objects.append(lit_orb)
	lit_orb.send_to_back()

	u.qinsert(lit_orb, g.time + LIGHT_ORB_TICK_TIME)

	ui.message('The light orb bursts into magical fire as it lands on the ground!', libtcod.orange)
	g.fov_recompute = True

def throw_dark_orb():
	#Create a puddle of light around it
	ui.message('Left-click a target tile for the dark orb, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = ui.target_tile()
	if x is None: return 'cancelled'
 
	#TODO: make this land a bit randomly
	#TODO: make this stop being lit eventually
	orb_ai = LightDarkOrb(DARK_ORB_TICK_TIME)
	l = object.Light(DARK_ORB_LSL)
	lit_orb = object.Object(g.player.x, g.player.y, '*', 'dark orb', DARK_ORB_THROWN_COLOR, 
				light = l, ai = orb_ai)
	v.add_light(lit_orb)
	
	u.throw_object(lit_orb, g.player.x, g.player.y, x, y)

	g.objects.append(lit_orb)
	lit_orb.send_to_back()

	u.qinsert(lit_orb, g.time + DARK_ORB_TICK_TIME)

	ui.message('The temperature drops as the orb begins to absorb light!', libtcod.light_violet)
	g.fov_recompute = True

def throw_water_balloon():
	#ask the player for a target tile to throw a fireball at
	ui.message('Left-click a target tile for the water balloon, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = ui.target_tile()
	if x is None: return 'cancelled'
	ui.message('The water balloon bursts, dampening everything around it!', libtcod.light_blue)
 
	for obj in g.objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= WATERBALLOON_RADIUS and obj.light:
			if obj.ai:
				ui.message('The ' + obj.name + '\'s torch goes out!', libtcod.light_blue)
			else:
				ui.message('The ' + obj.name + ' goes out!', libtcod.light_blue)

			v.remove_light(obj)

			obj.light = None
			g.fov_recompute = True

def cast_heal():
	#heal the player
	if g.player.fighter.hp == g.player.fighter.max_hp:
		ui.message('You are already at full health.', libtcod.red)
		return 'cancelled'
 
	ui.message('Your wounds start to feel better!', libtcod.light_violet)
	g.player.fighter.heal(HEAL_AMOUNT)
 
def cast_lightning():
	#find closest enemy (inside a maximum range) and damage it
	monster = closest_monster(LIGHTNING_RANGE)
	if monster is None:  #no enemy found within maximum range
		ui.message('No enemy is close enough to strike.', libtcod.red)
		return 'cancelled'
 
	#zap it!
	ui.message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
			+ str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
	monster.fighter.take_damage(LIGHTNING_DAMAGE)
 
def cast_fireball():
	#ask the player for a target tile to throw a fireball at
	ui.message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = ui.target_tile()
	if x is None: return 'cancelled'
	ui.message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)
 
	for obj in g.objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
			ui.message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
			obj.fighter.take_damage(FIREBALL_DAMAGE)
 
def cast_confuse():
	#ask the player for a target to confuse
	ui.message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
	monster = ui.target_monster(CONFUSE_RANGE)
	if monster is None: return 'cancelled'
 
	#replace the monster's AI with a "confused" one; after some turns it will restore the old AI
	old_ai = monster.ai
	monster.ai = monsters.ConfusedMonster(old_ai)
	monster.ai.owner = monster  #tell the new component who owns it
	ui.message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)
 
def cast_flashbang():
	#ask the player for a target tile to throw a fireball at
	ui.message('Left-click a target tile for the flashbang, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = ui.target_tile()
	if x is None: return 'cancelled'
	ui.message('The flashbang explodes, blinding and deafening everything within ' + str(FLASHBANG_RADIUS) + ' tiles!', libtcod.orange)
 
	for obj in g.objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= FLASHBANG_RADIUS and obj.fighter and obj.ai:
			old_ai = obj.ai
			obj.ai = monsters.ConfusedMonster(old_ai, FLASHBANG_LENGTH)
			obj.ai.owner = obj

			ui.message("The " + obj.name + " is dazed and confused!", libtcod.light_green)

def cast_speed():
	speed_ai = TemporarySpeedUp(g.player, g.player.fighter.base_movespeed * SPEED_MUL, SPEED_TICK_TIME, SPEED_TICK_NUM) #This changes the speed
	speed_obj = object.Object(-1, -1, ' ', 'ERROR: SPEED', libtcod.white, ai = speed_ai)

	g.objects.append(speed_obj)
	speed_obj.send_to_back()

	u.qinsert(speed_obj, g.time + SPEED_TICK_TIME)

	ui.message("You feel lightning fast!")