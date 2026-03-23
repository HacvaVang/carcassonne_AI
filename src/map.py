from settings import *
from src.tiles import Tile
from src import Neighbor

class Tileset:
    def __init__(self, seed: int):
        pass
    
class Map:
    def __init__(self):
        self.tileset = {}
        self.adjency_tile : set = {(0, 0)}
        
    def can_place_tile(self, pos : tuple, tile : Tile):
        x, y = pos
        if pos not in self.adjency_tile:
            return False
        neighbor_flag = False
        for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
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
        self.adjency_tile.discard(pos)
        x, y = pos
        
        for dx, dy in Neighbor.neighbor.values():
            if (x + dx, y + dy) not in self.tileset.keys():
                self.adjency_tile.add((x + dx, y + dy))
            
    def get_placeable_positon(self, tile: Tile):
        return list(filter(
            lambda pos : self.can_place_tile(pos, tile), self.adjency_tile
        ))
        

    def get_tile(self, x, y):
        return self.tileset.get((x, y), None)

    def render(self, screen):
        for (x, y), tile in self.tileset.items():
            if not hasattr(tile, 'image'):
                continue
            tile.render(screen, (x, y))



            