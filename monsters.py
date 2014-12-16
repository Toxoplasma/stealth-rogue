import math

import g
import u
import v
import ui
import object
import item
from consts import *

##Ais
class BasicMonster:
	def __init__(self, destFunc, lostPlayerFunc = None, eachStepFunc = None): #ADD EACH STEP FUNC
		self.can_see_player = False
		self.state = 'waiting'
		self.waitTicks = 0
		self.destFunc = destFunc
		self.lostPlayerFunc = lostPlayerFunc
		self.eachStepFunc = eachStepFunc
		#self.dest = (-1, -1) #(self.owner.x, self.owner.y)

	#AI for a basic monster.
	def take_turn(self):
		monster = self.owner

		actiontime = 0

		could_see_player = self.can_see_player

		#Regardless of state, check if it can see you
		#Check if it can see you!
		if v.detect_player(monster):
			#Send a message about it if it couldn't already see you
			if not self.can_see_player:
				if v.player_can_see(monster.x, monster.y):
					ui.message("The " + monster.name + " sees you!", libtcod.red)

			self.can_see_player = True
			monster.fighter.look_towards = (g.player.x, g.player.y)
			self.state = 'moving'

		elif could_see_player: #Could see the player but lost them
			self.can_see_player = False

			print "  Shouting, looking at " + str(monster.fighter.look_towards)
			if self.lostPlayerFunc:
				self.lostPlayerFunc(monster)
			

		#If we're next to the player, attack it
		#Do this no matter the state
		if self.can_see_player and (monster.distance_to(g.player) < 2):
			actiontime = monster.fighter.attack(g.player)

		#Check state
		else:
			if self.state == 'waiting':
				if self.waitTicks <= 0: #Done waiting
					self.state = 'moving'

					#Pick a destination
					newx, newy = self.destFunc(monster.x, monster.y)#u.rand_tile_in_sight(monster.x, monster.y)
					monster.fighter.look_towards = (newx, newy)

				else:
					self.waitTicks -= 1

				actiontime = 10

			elif self.state == 'moving':
				oldx = monster.x
				oldy = monster.y

				#Do the onstep whatever it is
				if self.eachStepFunc:
					self.eachStepFunc(monster)

				actiontime = monster.move_towards(monster.fighter.look_towards[0], monster.fighter.look_towards[1])


				#If we fail to move there, set desination to -1, -1 to pick a new one eventually
				if not actiontime:
					monster.fighter.look_towards = (-1, -1)
					actiontime = 10 #give them a turn rest

				#Have we arrived at dest?
				if monster.fighter.look_towards == (-1, -1):
					#Something has gone wrong, immediately move towards new position
					newx, newy = self.destFunc(monster.x, monster.y)#u.rand_tile_in_sight(monster.x, monster.y)
					monster.fighter.look_towards = (newx, newy)
					self.can_see_player = False


				elif (monster.x, monster.y) == monster.fighter.look_towards:			
					self.state = 'waiting'
					self.waitTicks = int(u.rand_gauss_pos(3, 1))

					#Set up look towards where it was walking
					monster.fighter.look_towards = (monster.x + (monster.x - oldx), monster.y + (monster.y - oldy))


		return actiontime

	def hear_noise(self, x, y, source):
		monster = self.owner

		if source: #Someone is shouting, look where they're pointing
			monster.fighter.look_towards = source.fighter.look_towards
			self.state = 'moving'
			print monster.name + " heard shout, heading towards " + str(source.fighter.look_towards)
		else: #Just heard a noise, go check it out
			print monster.name + " heard noise, heading towards " + str((x, y)) 
			monster.fighter.look_towards = (x, y)


class WanderMonster:
	def __init__(self, destFunc, eachStepFunc = None):
		self.can_see_player = False
		self.destFunc = destFunc
		self.eachStepFunc = eachStepFunc

		self.dest = (-1, -1)

		self.look_towards = (-1, -1) #don't want to show facing on these guys

	def take_turn(self):
		monster = self.owner

		actiontime = 0
			
		oldx = monster.x
		oldy = monster.y

		#Do the onstep whatever it is
		if self.eachStepFunc:
			self.eachStepFunc(monster)

		actiontime = monster.move_towards(self.dest[0], self.dest[1])

		#If we fail to move there, set desination to -1, -1 to pick a new one eventually
		if not actiontime:
			self.dest = (-1, -1)
			actiontime = 10 #give them a turn rest

		#Have we arrived at dest?
		if self.dest == (-1, -1) or (monster.x, monster.y) == self.dest:
			#Something has gone wrong, immediately move towards new position
			newx, newy = self.destFunc(monster.x, monster.y)
			self.dest = (newx, newy)

		return actiontime

	def hear_noise(self, x, y, source):
		return

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
			ui.message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)
			return self.owner.fighter.movespeed

class LightOrbThrowerMonster:
	def __init__(self):
		self.can_see_player = False
		self.last_throw = -100

	#AI for a basic monster.
	def take_turn(self):
		monster = self.owner

		actiontime = 0

		could_see_player = self.can_see_player

		#Check if it can see you!
		if v.detect_player(monster):
			#Send a message about it if it couldn't already see you
			if not self.can_see_player:
				if v.player_can_see(monster.x, monster.y):
					ui.message("The " + monster.name + " sees you!", libtcod.red)

			self.can_see_player = True
			monster.fighter.look_towards = (g.player.x, g.player.y)

		elif could_see_player: #It couldn't see you, so it tries to throw an orb
			self.can_see_player = False
			ui.message("The " + monster.name + " lost sight of you.", libtcod.green)

			if g.time > self.last_throw + ORB_GOBLIN_THROW_RATE:
				ui.message("The " + monster.name + " throws a light orb!", libtcod.orange)
				
				#Throw an orb at destination
				orb_ai = item.LightDarkOrb(LIGHT_ORB_TICK_TIME)
				l = object.Light(LIGHT_ORB_LSL)
				lit_orb = object.Object(monster.x, monster.y, '*', 'light orb', LIGHT_ORB_THROWN_COLOR, 
						light = l, ai = orb_ai)
				v.add_light(lit_orb)

				u.throw_object(lit_orb, monster.x, monster.y, monster.fighter.look_towards[0], monster.fighter.look_towards[1])

				g.objects.append(lit_orb)
				lit_orb.send_to_back()

				u.qinsert(lit_orb, g.time + LIGHT_ORB_TICK_TIME)

				self.last_throw = g.time

		#If we're next to the player, attack it
		if self.can_see_player and (monster.distance_to(g.player) < 2):
			actiontime = monster.fighter.attack(g.player)

		#Otherwise move towards dest
		else:
			actiontime = monster.move_towards(monster.fighter.look_towards[0], monster.fighter.look_towards[1])
			#If we fail to move there, set desination to -1, -1 to pick a new one eventually
			if not actiontime:
				monster.fighter.look_towards = (-1, -1)
				actiontime = 10 #give them a turn rest

		#Have we reached destination?
		if (monster.x == monster.fighter.look_towards[0] and monster.y == monster.fighter.look_towards[1]) or \
			(monster.fighter.look_towards == (-1, -1)):
			#If we could see the player before, mark it as not true anymore

			#Pick a new destination at random (from within sight)
			#These guys don't carry torches, so bias towards light
			newx, newy = u.rand_tile_in_sight_light_bias(monster.x, monster.y)
			monster.fighter.look_towards = (newx, newy)

		return actiontime

class DeadTorchMonster:
	#AI for a light or dark orb, turns slowly dimmer/brighter
	def __init__(self, tick_time):
		self.can_see_player = False #Or we get a nice red background... Maybe add an is_enemy flag
		self.tick_time = tick_time
 
	def take_turn(self):
		corpse = self.owner
		if corpse.light:
			#Remove its light from surroundings
			v.remove_light(corpse)

			#Update its light level
			LSL = corpse.light.level
			sign = math.copysign(1, LSL)

			newLSL = int(sign * (abs(LSL) - 1))

			#If it's dead, remove it from the game
			if newLSL == 0:
				corpse.light = None

				#Remove from everything
				return -1 #don't add it to q again

			#Otherwise, change its light level and add back in its light
			corpse.light.level = newLSL
			v.add_light(corpse)

			print "  corpse LSL: " + str(newLSL)

		return self.tick_time

def makeShoutFunc(vol):
	def s(monster):
		shout(monster, vol)

	return s

def shout(monster, vol):
	u.make_noise(monster.x, monster.y, vol, monster)

	ui.message("Hey you!")
	#if not ui.in_sight_message("'Hey you! Stop right there!'")

def glowmothDropLightOrb(monster):
	orb_ai = item.LightDarkOrb(GLOWMOTH_ORB_TICKTIME)
	l = object.Light(GLOWMOTH_ORB_LSL)
	lit_orb = object.Object(monster.x, monster.y, ' ', 'glow dust', LIGHT_ORB_THROWN_COLOR, 
			light = l, ai = orb_ai)
	v.add_light(lit_orb)

	g.objects.append(lit_orb)
	lit_orb.send_to_back()

	u.qinsert(lit_orb, g.time + GLOWMOTH_ORB_TICKTIME)

	g.fov_recompute = True


#chance of each monster
def spawn_monsters():
	monster_chances = {}
	#monster_chances['goblin'] = 	u.from_dungeon_level(GOBLIN_CHANCE)
	#monster_chances['orb goblin'] = u.from_dungeon_level(ORB_GOBLIN_CHANCE)
	#monster_chances['orc'] = 		u.from_dungeon_level(ORC_CHANCE)  #orc always shows up, even if all other monsters have 0 chance
	#monster_chances['troll'] = 		u.from_dungeon_level(TROLL_CHANCE)

	monster_chances['guard'] = u.from_branch_level(GUARD_CHANCE)
	monster_chances['small torch guard'] = u.from_branch_level(SMALL_TORCH_GUARD_CHANCE)
	monster_chances['mid torch guard'] = u.from_branch_level(MID_TORCH_GUARD_CHANCE)
	monster_chances['glowmoth'] = u.from_branch_level(GLOWMOTH_CHANCE)


	#choose random number of monsters
	target_num_monsters = u.from_branch_level(NUM_MONSTERS)
	num_monsters = u.rand_gauss_pos(target_num_monsters, target_num_monsters / 3)
 
	for i in range(num_monsters):
		#choose random spot for this monster
		x, y = u.get_empty_tile()
 
		#only place it if the tile is not blocked
		if not u.is_blocked(x, y):
			choice = u.random_choice(monster_chances)
			if choice == 'guard':
				make_guard(x, y)
			elif choice == 'small torch guard':
				make_small_torch_guard(x, y)
			elif choice == 'mid torch guard':
				make_mid_torch_guard(x, y)

			elif choice == 'glowmoth':
				make_glowmoth(x, y)

	return num_monsters


def monster_death(monster):
	#transform it into a nasty corpse! it doesn't block, can't be
	#attacked and doesn't move
	msg = 'The ' + monster.name + ' is dead!'
	if monster.light:
		msg += " Its torch falls to the ground and gutters out."
	ui.message(msg, libtcod.orange)

	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	v.remove_light(monster)
	monster.light = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()


def drop_torch_death(monster):
	#Message about him dying
	msg = 'The ' + monster.name + ' is dead!'
	if monster.light:
		msg += " Its torch falls to the ground and starts to gutter out."
	ui.message(msg, libtcod.orange)

	#Make it dead
	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = DeadTorchMonster(DEAD_GUARD_TORCH_TICK)
	monster.ai.owner = monster
	#v.remove_light(monster)
	#monster.light = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back() #DEAD_GUARD_TORCH_TICK

def make_torch_guard(x, y, l):
	fighter_component = object.Fighter(hp=GUARD_HP, defense=GUARD_DEF, power=GUARD_POW, xp=GUARD_XP, death_function=drop_torch_death)
	ai_component = BasicMonster(destFunc = u.rand_tile_in_sight, lostPlayerFunc = makeShoutFunc(30))
	monster = object.Object(x, y, GUARD_CHAR, 'guard', GUARD_COLOR,
					 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
					 fighter=fighter_component, ai=ai_component)

	add_monster(monster)


def make_small_torch_guard(x, y):
	l = object.Light(SMALL_TORCH_GUARD_LSL)
	make_torch_guard(x, y, l)


def make_mid_torch_guard(x, y):
	l = object.Light(MID_TORCH_GUARD_LSL)
	make_torch_guard(x, y, l)


def make_guard(x, y):
	fighter_component = object.Fighter(hp=GUARD_HP, defense=GUARD_DEF, power=GUARD_POW, xp=GUARD_XP, death_function=monster_death)
	ai_component = BasicMonster(destFunc = u.rand_tile_in_sight_light_bias, lostPlayerFunc = makeShoutFunc(30))
	monster = object.Object(x, y, GUARD_CHAR, 'guard', GUARD_COLOR,
					 blocks=True, fighter=fighter_component, ai=ai_component)

	add_monster(monster)

def make_glowmoth(x, y):
	fighter_component = object.Fighter(hp=GUARD_HP, defense=GUARD_DEF, power=GUARD_POW, xp=GUARD_XP, death_function=monster_death)
	ai_component = WanderMonster(destFunc = u.rand_tile_in_sight, eachStepFunc = glowmothDropLightOrb)
	monster = object.Object(x, y, GLOWMOTH_CHAR, 'glowmoth', GLOWMOTH_COLOR,
					 blocks=True, fighter=fighter_component, ai=ai_component)

	add_monster(monster)

def add_monster(monster):
	v.add_light(monster)
	g.objects.append(monster)
	u.qinsert(monster, g.time + 2) #player gets inserted at 1, monsters at 2




# if choice == 'orc':
# 				#create an orc
# 				fighter_component = object.Fighter(hp=ORC_HP, defense=ORC_DEF, power=ORC_POW, xp=ORC_XP, death_function=monster_death)
# 				ai_component = BasicMonster()
# 				l = object.Light(ORC_LSL)

# 				monster = object.Object(x, y, 'o', 'orc', ORC_COLOR,
# 								 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
# 								 fighter=fighter_component, ai=ai_component)
 
# 			elif choice == 'goblin':
# 				#create a goblin
# 				fighter_component = object.Fighter(hp=GOBLIN_HP, defense=GOBLIN_DEF, power=GOBLIN_POW, xp=GOBLIN_XP, death_function=monster_death)
# 				ai_component = BasicMonster()
# 				l = object.Light(GOBLIN_LSL)

# 				monster = object.Object(x, y, 'g', 'goblin', GOBLIN_COLOR,
# 								 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
# 								 fighter=fighter_component, ai=ai_component)

# 			elif choice == 'orb goblin':
# 				#Redo x, y to be light-biased

# 				x,y = u.rand_tile_light_bias(3) #cubic bias
# 				#create a goblin
# 				fighter_component = object.Fighter(hp=ORB_GOBLIN_HP, defense=ORB_GOBLIN_DEF, power=ORB_GOBLIN_POW, xp=ORB_GOBLIN_XP, death_function=monster_death)
# 				ai_component = LightOrbThrowerMonster()

# 				monster = object.Object(x, y, 'g', 'orb goblin', ORB_GOBLIN_COLOR,
# 								 blocks=True, #TODO: Add them actually carrying torches, not just lights
# 								 fighter=fighter_component, ai=ai_component)

# 			elif choice == 'troll':
# 				#create a troll
# 				fighter_component = object.Fighter(hp=TROLL_HP, defense=TROLL_DEF, power=TROLL_POW, xp=TROLL_XP, death_function=monster_death)
# 				ai_component = BasicMonster()
 
# 				monster = object.Object(x, y, 'T', 'troll', TROLL_COLOR,
# 								 blocks=True, fighter=fighter_component, ai=ai_component)