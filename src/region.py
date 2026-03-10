from src.tiles import Tile
from src.meeple import Meeple
from settings import *
class Region:
    def __init__(self, tile_pos : tuple, region: list, terrain : Terrain):
        self.tiles = dict()
        self.tiles[tile_pos] = region
        self.count = 1
        self.meeples : list[Meeple] = list()
        self.terrain = terrain
        self.intial_pos = tile_pos
        
    def addTile(self, tile_pos: tuple, region : list):
        self.tiles[tile_pos] = region
        self.count = self.count + 1
        
    def is_completed(self):
        pass
        
    def get_region_points(self):
        pass
    
    def addRegion(self, region):
        for key, value in region.tiles.items():
            self.tiles[key] = self.tiles.get(key, []) + value
        self.meeples = self.meeples + region.meeples
        self.count = len(list(self.tiles.items()))
    
    def has_owner(self):
        return bool(self.meeples)

    def get_owner_players(self):
        if not self.meeples:
            return []
        counts = {}
        for meeple in self.meeples:
            player = getattr(meeple, "player", None)
            if not player:
                continue
            counts[player] = counts.get(player, 0) + 1
        if not counts:
            return []
        max_count = max(counts.values())
        return [p for p, c in counts.items() if c == max_count]

    def render(self, screen, image, idx):
        [mepple.render(screen, True) for mepple in self.meeples]
        # for tile_pos, region in self.tiles.items():
        #     font = pygame.font.SysFont(None, 36)
        #     coors = [Neighbor.directions[key] for key in region] 
        #     text = font.render(f"{idx}", True, (0, 0, 0))
        #     for coordinate in coors:
        #         text_pos = (
        #             (tile_pos[0] + coordinate[0]) * image.get_width() + SCREEN_WIDTH // 2,
        #             (tile_pos[1] + coordinate[1]) * image.get_height() + SCREEN_HEIGHT // 2
        #         )
        #         screen.blit(text, text_pos)

    def __repr__(self):
        return f"tiles: {self.tiles}, count: {self.count}, terrain: {self.terrain}, mepple: {self.meeples}"
        
class CityRegion(Region):
    def __init__(self, tile_pos : tuple, region: list, tile : Tile, terrain : Terrain):
        super().__init__(tile_pos, region, terrain)
        self.shield = 1 if tile.shield else 0
        self.completed = False

    def get_region_points(self):
        total = self.shield + self.count
        return total * 2 if self.completed else total

    def addRegion(self, region):
        for key, value in region.tiles.items():
            self.tiles[key] = self.tiles.get(key, []) + value
        self.meeples = self.meeples + region.meeples
        self.count = len(list(self.tiles.items()))
        self.shield += region.shield
                
    def addTile(self, tile_pos: tuple, region : list, tile : Tile):
        self.tiles[tile_pos] = region
        self.count = self.count + 1
        self.shield = self.shield + 1 if tile.shield else self.shield 
        
    def is_completed(self):
        visited_mask = dict.fromkeys(self.tiles.keys(), 0)
        visited_mask[self.intial_pos] = 1
        queue = [self.intial_pos]
        
        flag = True
        
        while queue:
            current_tile = queue.pop(0)
            visit_pos = [x for x in self.tiles[current_tile] if (x & 1)]
            visit_directions = [Neighbor.neighbor[x] for x in visit_pos]
            
            x, y = current_tile
            for direction in visit_directions:
                dx, dy = direction
                neighbor_tile = (x + dx, y + dy) 
                if not self.tiles.get(neighbor_tile, None):
                    flag = False
                    break
                if not visited_mask[neighbor_tile]:
                    visited_mask[neighbor_tile] = 1
                    queue.append(neighbor_tile)
                    
        self.completed = flag
        return flag
        
class RoadRegion(Region):
    def __init__(self, tile_pos : tuple, region: list, terrain : Terrain):
        super().__init__(tile_pos, region, terrain)

    def get_region_points(self):
        return self.count
    
    def is_completed(self):
        start, end = self.tiles[self.intial_pos]
        def road_traversal(travel_pos, travel_tile, intial_tile):
            if travel_pos == 8:
                return 0
            dx, dy = Neighbor.neighbor[travel_pos]

            neighbor_pos = self.tiles.get((travel_tile[0] + dx, travel_tile[1] + dy), None)

            if not neighbor_pos:
                return -1
            neighbor_tile = (travel_tile[0] + dx, travel_tile[1] + dy)
            if neighbor_tile == intial_tile:
                return 1
            travel_pos = next(filter(lambda x : x not in Neighbor.neighbor_region[(dx, dy)], neighbor_pos), -1)
            return road_traversal(travel_pos, neighbor_tile, intial_tile)
        
        result = road_traversal(start, self.intial_pos, self.intial_pos)
        match result:
            case 0:
                return road_traversal(end, self.intial_pos, self.intial_pos) == 0
            case -1:
                return False
            case 1:
                return True

class GrassRegion(Region):
    def __init__(self, tile_pos : tuple, region: list, terrain : Terrain):
        super().__init__(tile_pos, region, terrain)
        self.finished_cities = 0
    
    def get_region_points(self):
        return self.finished_cities * 3
        
class MonasteryRegion(Region):
    def __init__(self, tile_pos : tuple, region: list, terrain : Terrain):
        super().__init__(tile_pos, region, terrain)
        
    def is_completed(self):
        return self.count == 9
    
    def get_region_points(self):
        return self.count
    
    def update(self, tile_pos):
        x, y = tile_pos
        x_, y_ = self.intial_pos
        if abs(x - x_) <= 1 and abs(y - y_) <= 1:
            self.addTile(tile_pos, [8])