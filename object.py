class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, \
                blocks=False, always_visible=False, light_source=False, light_source_level=0, \
                fighter=None, ai=None, item=None, equipment=None, light=None):
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
 
        self.item = item
        if self.item:  #let the Item component know who owns it
            self.item.owner = self
 
        self.equipment = equipment
        if self.equipment:  #let the Equipment component know who owns it
            self.equipment.owner = self
 
            #there must be an Item component for the Equipment component to work properly
            self.item = Item()
            self.item.owner = self
 
    def wait(self):
        #If we're a fighter, return the time we waited
        if self.fighter:
            return self.fighter.movespeed
        return True

    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            if self.fighter:
                return self.fighter.movespeed
            return True
        else:
            return False
 
    def move_towards(self, target_x, target_y):
        global fov_map
        #Do some pathfinding
        path = libtcod.path_new_using_map(fov_map)
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
        global objects
        objects.remove(self)
        objects.insert(0, self)
 
    def draw(self):
        #only show if it's visible to the player; or it's set to "always visible" and on an explored tile
        #print self.char + ": " + str(map[self.x][self.y].light_level)
        #print "  fov: " + 
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) and \
                ((map[self.x][self.y].light_level > MIN_ITEM_LIGHT_LEVEL) or self.distance_to(player) < VISION_DISTANCE_WITHOUT_LIGHT)) or \
            (self.always_visible and map[self.x][self.y].explored):
            #set the color and then draw the character that represents this object at its position
            if self.ai and self.ai.can_see_player:
                #Draw the background in red!
                libtcod.console_set_char_background(con, self.x, self.y, MONSTER_SEEN_COLOR, libtcod.BKGND_SET)

            libtcod.console_set_default_foreground(con, self.color)
            #darken the background a little
            libtcod.console_set_char_background(con, self.x, self.y, libtcod.Color(128,128,128), libtcod.BKGND_OVERLAY)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    #Draws it without caring about light, etc
    #Basically just for the player
    def draw_always(self):
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
 