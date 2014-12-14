import g
import u
import v
import ui
import object
import item
from consts import *

##Ais
class BasicMonster:
	def __init__(self):
		self.can_see_player = False
		self.state = 'waiting'
		self.waitTicks = 0
		#self.dest = (-1, -1) #(self.owner.x, self.owner.y)

	#AI for a basic monster.
	def take_turn(self):
		monster = self.owner

		actiontime = 0

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

		else:
			self.can_see_player = False

		#If we're next to the player, attack it
		#Do this no matter the state
		if self.can_see_player and (monster.distance_to(g.player) < 2):
			actiontime = monster.fighter.attack(g.player)

		#Check state
		else:
			if self.state == 'waiting':
				print "  " + str(self.waitTicks)
				if self.waitTicks <= 0: #Done waiting
					self.state = 'moving'

					#Pick a destination
					newx, newy = u.rand_tile_in_sight(monster.x, monster.y)
					monster.fighter.look_towards = (newx, newy)

				else:
					self.waitTicks -= 1

				actiontime = 10

			elif self.state == 'moving':
				oldx = monster.x
				oldy = monster.y

				actiontime = monster.move_towards(monster.fighter.look_towards[0], monster.fighter.look_towards[1])

				#If we fail to move there, set desination to -1, -1 to pick a new one eventually
				if not actiontime:
					monster.fighter.look_towards = (-1, -1)
					actiontime = 10 #give them a turn rest

				#Have we arrived at dest?
				if (monster.x, monster.y) == monster.fighter.look_towards or monster.fighter.look_towards == (-1, -1):			
					self.state = 'waiting'
					self.waitTicks = int(u.rand_gauss_pos(3, 1))

					#Set up look towards where it was walking
					monster.fighter.look_towards = (monster.x + (monster.x - oldx), monster.y + (monster.y - oldy))


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



#chance of each monster
def spawn_monsters():
	monster_chances = {}
	monster_chances['goblin'] = 	u.from_dungeon_level(GOBLIN_CHANCE)
	monster_chances['orb goblin'] = u.from_dungeon_level(ORB_GOBLIN_CHANCE)
	monster_chances['orc'] = 		u.from_dungeon_level(ORC_CHANCE)  #orc always shows up, even if all other monsters have 0 chance
	monster_chances['troll'] = 		u.from_dungeon_level(TROLL_CHANCE)

	#choose random number of monsters
	target_num_monsters = u.from_dungeon_level(NUM_MONSTERS)
	num_monsters = u.rand_gauss_pos(target_num_monsters, target_num_monsters / 3)
 
	for i in range(num_monsters):
		#choose random spot for this monster
		x, y = u.get_empty_tile()
 
		#only place it if the tile is not blocked
		if not u.is_blocked(x, y):
			choice = u.random_choice(monster_chances)
			if choice == 'orc':
				#create an orc
				fighter_component = object.Fighter(hp=ORC_HP, defense=ORC_DEF, power=ORC_POW, xp=ORC_XP, death_function=monster_death)
				ai_component = BasicMonster()
				l = object.Light(ORC_LSL)

				monster = object.Object(x, y, 'o', 'orc', ORC_COLOR,
								 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
								 fighter=fighter_component, ai=ai_component)
 
			elif choice == 'goblin':
				#create a goblin
				fighter_component = object.Fighter(hp=GOBLIN_HP, defense=GOBLIN_DEF, power=GOBLIN_POW, xp=GOBLIN_XP, death_function=monster_death)
				ai_component = BasicMonster()
				l = object.Light(GOBLIN_LSL)

				monster = object.Object(x, y, 'g', 'goblin', GOBLIN_COLOR,
								 blocks=True, light = l, #TODO: Add them actually carrying torches, not just lights
								 fighter=fighter_component, ai=ai_component)

			elif choice == 'orb goblin':
				#Redo x, y to be light-biased

				x,y = u.rand_tile_light_bias(3) #cubic bias
				#create a goblin
				fighter_component = object.Fighter(hp=ORB_GOBLIN_HP, defense=ORB_GOBLIN_DEF, power=ORB_GOBLIN_POW, xp=ORB_GOBLIN_XP, death_function=monster_death)
				ai_component = LightOrbThrowerMonster()

				monster = object.Object(x, y, 'g', 'orb goblin', ORB_GOBLIN_COLOR,
								 blocks=True, #TODO: Add them actually carrying torches, not just lights
								 fighter=fighter_component, ai=ai_component)

			elif choice == 'troll':
				#create a troll
				fighter_component = object.Fighter(hp=TROLL_HP, defense=TROLL_DEF, power=TROLL_POW, xp=TROLL_XP, death_function=monster_death)
				ai_component = BasicMonster()
 
				monster = object.Object(x, y, 'T', 'troll', TROLL_COLOR,
								 blocks=True, fighter=fighter_component, ai=ai_component)
 
			g.objects.append(monster)

			u.qinsert(monster, g.time + 2) #player gets inserted at 1, monsters at 2

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