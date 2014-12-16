import libtcodpy as libtcod
import math

from consts import *
import g
import u
import item
import v
import ui

class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, \
                blocks=False, always_visible=False, light_source=False, light_source_level=0, \
                fighter=None, ai=None, itemCom=None, equipment=None, light=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible

        self.fighter = fighter
        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self
 
        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self

        self.light = light
        if self.light:
            self.light.owner = self
 
        self.item = itemCom
        if self.item:  #let the Item component know who owns it
            self.item.owner = self
 
        self.equipment = equipment
        if self.equipment:  #let the Equipment component know who owns it
            self.equipment.owner = self
 
            #there must be an Item component for the Equipment component to work properly
            self.item = item.Item()
            self.item.owner = self
 
    def wait(self):
        #If we're a fighter, return the time we waited
        if self.fighter:
            return self.fighter.movespeed
        return True

    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not u.is_blocked(self.x + dx, self.y + dy):
            if self.light:
                v.remove_light(self)

            self.x += dx
            self.y += dy

            if self.light:
                v.add_light(self)

            if self.fighter:
                return self.fighter.movespeed
            return True
        else:
            return False
 
    def move_towards(self, target_x, target_y):
        #Do some pathfinding
        path = libtcod.path_new_using_map(g.fov_map)
        #dijkstra_new(map, diagonalCost=1.41)

        libtcod.path_compute(path, self.x, self.y, target_x, target_y)

        dx, dy = libtcod.path_walk(path, True)
        #print str((self.x, self.y)) + " via " + str((dx, dy)) + " to " + str((target_x, target_y))
        if dx:
            return self.move(dx - self.x, dy - self.y)

        return False

    def get_next_move_simple(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
 
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        return (dx, dy)

    def get_next_move_simple_abs(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
 
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        return (self.x + dx, self.y + dy)

    def move_simple(self, target_x, target_y):
        dx, dy = self.get_next_move_simple(target_x, target_y)
        return self.move(dx, dy)

 
    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
 
    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
 
    def send_to_back(self):
        #make this object be drawn first, so all others appear above it if they're in the same tile.
        g.objects.remove(self)
        g.objects.insert(0, self)
 
    def draw(self): #todo: move this to ui
        #only show if it's visible to the player; or it's set to "always visible" and on an explored tile
        #print self.char + ": " + str(map[self.x][self.y].light_level)
        #print "  fov: " + 
        if (libtcod.map_is_in_fov(g.fov_map, self.x, self.y) and \
                ((g.map[self.x][self.y].light_level > MIN_ITEM_LIGHT_LEVEL) or self.distance_to(g.player) < VISION_DISTANCE_WITHOUT_LIGHT)) or \
            (self.always_visible and g.map[self.x][self.y].explored):
            #set the color and then draw the character that represents this object at its position
            if self.ai and self.ai.can_see_player:
                #Draw the background in red!
                libtcod.console_set_char_background(g.con, self.x, self.y, MONSTER_SEEN_COLOR, libtcod.BKGND_SET)

            libtcod.console_set_default_foreground(g.con, self.color)
            #darken the background a little
            libtcod.console_set_char_background(g.con, self.x, self.y, libtcod.Color(128,128,128), libtcod.BKGND_OVERLAY)
            libtcod.console_put_char(g.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    #Draws it without caring about light, etc
    #Basically just for the player
    def draw_always(self):
        libtcod.console_set_default_foreground(g.con, self.color)
        libtcod.console_put_char(g.con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(g.con, self.x, self.y, ' ', libtcod.BKGND_NONE)
 




class Fighter:
    #combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, defense, power, xp, mana=0, stealth=0, movespeed=10, attackspeed=10, 
                 death_function=None, vision_angle = MONSTER_VISION_ANGLE):
        self.base_max_hp = hp
        self.hp = hp
        self.base_defense = defense
        self.base_power = power
        self.xp = xp
        self.base_stealth = stealth
        self.death_function = death_function
        self.base_movespeed = movespeed
        self.base_attackspeed = attackspeed
        self.mana = mana
        self.base_max_mana = mana

        self.vision_angle = vision_angle

        self.inventory = []

        self.look_towards = (-1, -1)
 
    @property
    def power(self):  #return actual power, by summing up the bonuses from all equipped items
        bonus = sum(equipment.power_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_power + bonus
 
    @property
    def defense(self):  #return actual defense, by summing up the bonuses from all equipped items
        bonus = sum(equipment.defense_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_defense + bonus
 
    @property
    def max_hp(self):  #return actual max_hp, by summing up the bonuses from all equipped items
        bonus = sum(equipment.max_hp_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_max_hp + bonus

    @property
    def stealth(self):
        bonus = sum(equipment.stealth_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_stealth + bonus

    @property
    def movespeed(self):
        bonus = sum(equipment.movespeed_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_movespeed + bonus

    @property
    def attackspeed(self):
        bonus = sum(equipment.attackspeed_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_attackspeed + bonus

    @property
    def max_mana(self):
        bonus = sum(equipment.max_mana_bonus for equipment in item.get_all_equipped(self.owner))
        return self.base_max_mana + bonus
 
    def attack(self, target):
        #a simple formula for attack damage
        damage = self.power - target.fighter.defense
 
        if damage > 0:
            #make the target take some damage
            ui.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            ui.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

        return self.attackspeed
 
    def take_damage(self, damage):
        #apply damage if possible
        if damage > 0:
            self.hp -= damage
 
            #check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)
 
                #if self.owner != player:  #yield experience to the player
                #   player.fighter.xp += self.xp
 
    def heal(self, amount):
        #heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def in_vision_cone(self, x, y):
        obj = self.owner
        destx = self.look_towards[0]
        desty = self.look_towards[1]

        sideOD = u.pythdist(obj.x, obj.y, destx, desty)
        sideOP = u.pythdist(obj.x, obj.y, x, y)
        sideDP = u.pythdist(destx, desty, x, y)

        mark = False
        if sideOP == 0:
            mark = False
        elif sideOD == 0:
            mark = False
        else:
            #Now law of cosines!
            unbound = (sideDP**2 - sideOP**2 - sideOD**2) / (2*sideOP*sideOD)
            bound = max(unbound, -1.0)
            bound = min(bound, 1.0)
            angle = math.degrees(math.acos(-1 * bound))

            #print "    " + str(angle)

            if abs(angle) < self.vision_angle:
                mark = True

        return mark

        


class Light:
    def __init__(self, level):
        self.level = level
 