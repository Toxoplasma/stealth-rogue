import math

from consts import *
import u
import ui

##Items
class LightDarkOrb:
	#AI for a light or dark orb, turns slowly dimmer/brighter
	def __init__(self, tick_time):
		self.can_see_player = False #Or we get a nice red background... Maybe add an is_enemy flag
		self.tick_time = tick_time
 
	def take_turn(self):
		orb = self.owner
		if orb.light:
			LSL = orb.light.level
			sign = math.copysign(1, LSL)

			newLSL = int(sign * (abs(LSL) - 1))

			if newLSL == 0:
				orb.light_source = False

				#Remove from everything
				u.oremove(orb)
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
			ui.message("Your scroll of speed has worn off...")
			#We're done, remove it
			u.oremove(self.owner)
			return -1

		return self.tick_time
