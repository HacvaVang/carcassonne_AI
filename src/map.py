from settings import *
from src.tiles import Tile

class Tileset:
    def __init__(self, seed: int):
        pass
    
class Map:
    def __init__(self, game=None):
        self.tileset = {}
        self.place_position = None
        self.meeple_placeable_positions = dict()
        self.game = game
        
    def can_place_tile(self, pos : tuple, tile : Tile):
        x, y = pos
        if pos in self.tileset:
            return False
        neighbor_flag = False
        for idx, (dx, dy) in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            neighbor : Tile = self.get_tile(x + dx, y + dy)
            if neighbor:
                neighbor_flag = True
                current_connection = tile.edges[idx]
                neighbor_connection = neighbor.edges[(idx + 2) % 4]
                if current_connection != neighbor_connection:
                    return False
        return neighbor_flag   

    def place_tile(self, pos, tile : Tile):       
        self.tileset[pos] = tile

    def get_tile(self, x, y):
        return self.tileset.get((x, y), None)

    def render(self, screen):
        for (x, y), tile in self.tileset.items():
            if not hasattr(tile, 'image'):
                continue
            tile.render(screen, (x, y))


            