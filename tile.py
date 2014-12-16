

class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, tiletype, dark_color, light_color, block_sight = None):
		self.blocked = blocked

		self.tiletype = tiletype
 
		#all tiles start unexplored
		self.explored = False

		#Amount of light on the tile
		self.light_level = 0
 
		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

		#colors
		self.dark_color = dark_color
		self.light_color = light_color
 
class Rect:
	#a rectangle on the map. used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

	def center(self):
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)
 
	def intersect(self, other):
		#returns true if this rectangle intersects with another one
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)