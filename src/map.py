from settings import *
from src.tiles import Tile
from src.meeple import Meeple
from src.region import *

class Tileset:
    def __init__(self, seed: int):
        pass
    
class Map:
    def __init__(self, game=None):
        # dictionary keyed by (x, y) coordinates storing Tile instances
        self.tileset = {}
        self.place_position = None
        self.meeple_placeable_positions = dict()
        # self.regions_list : list[Region] = list()
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
    
    # def setMonasteryRegion(self, terrain, positions: list, tile_pos):
    #     x, y = tile_pos
    #     new_region = MonasteryRegion(tile_pos, positions, terrain)
    #     for dx, dy in [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]:
    #         if self.get_tile(x + dx, y + dy):
    #             new_region.update((x + dx, y + dy))
    #     self.regions_list.append(new_region)
            
    # def setRegion(self, tile : Tile, terrain, positions: list, tile_pos):
    #     x, y = tile_pos
        
    #     match terrain:
    #         case Terrain.City:
    #             new_region = CityRegion(tile_pos, positions, tile, terrain)
    #         case Terrain.Road:
    #             new_region = RoadRegion(tile_pos, positions, terrain)
    #         case Terrain.Grass:
    #             new_region = GrassRegion(tile_pos, positions, terrain)

    #     mask = reduce(lambda acc, ele: acc ^ Neighbor.direction_mask[ele], positions, 0)
    #     border = tile.edges
    #     for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
    #         if mask & (1 << idx) and self.get_tile(x + dx, y + dy):
    #             if terrain == Terrain.Grass and border[idx] == Terrain.City:
    #                 continue
    #             neighbor_pos_list = Neighbor.get_neighbor_pos(positions, (dx, dy))
    #             for neighbor_pos in neighbor_pos_list:
    #                 result : Region = next(filter(
    #                     lambda reg : reg.terrain == terrain and neighbor_pos in reg.tiles.get((x + dx, y + dy), []), self.regions_list
    #                 ), None)
    #                 if result:
    #                     new_region.addRegion(result)
    #                     self.regions_list.remove(result)
    #     self.regions_list.append(new_region)
                    
    def place_tile(self, pos, tile : Tile):
        # for terrain, tile_regions in tile.region.items():
        #     for tile_region in tile_regions:
        #         coordinate = Neighbor().render_pos[tile_region[0]]
        #         placeholder_pos = (
        #             (pos[0] + coordinate[0]) * tile.image.get_width() + SCREEN_WIDTH // 2,
        #             (pos[1] + coordinate[1]) * tile.image.get_height() + SCREEN_HEIGHT // 2
        #         )
        #         self.meeple_placeable_positions[placeholder_pos] = (terrain, pos)
        
        self.tileset[pos] = tile

    def get_tile(self, x, y):
        return self.tileset.get((x, y), None)

    def render(self, screen):
        for (x, y), tile in self.tileset.items():
            if not hasattr(tile, 'image'):
                continue
            tile.render(screen, (x, y))


            