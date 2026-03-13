from src.tiles import Tile
from src.meeple import Meeple
from settings import *
class Region:
    def __init__(self, tile_pos : tuple, region: list):
        self.tiles = dict()
        self.tiles[tile_pos] = set(region)
        self.count = 1
        self.meeples : list[Meeple] = list()
        self.intial_pos = tile_pos
        self.completed_flag = False
        
    def addTile(self, tile_pos: tuple, region : list):
        self.tiles[tile_pos] = set(region)
        self.setCount()
        
    def is_completed(self):
        pass
        
    def get_region_points(self):
        pass
    
    def setCount(self):
        self.count = len(list(self.tiles.items()))
        
    def addRegion(self, region):
        for key, value in region.tiles.items():
            self.tiles[key] = self.tiles.get(key, set()) ^ value
        self.meeples = self.meeples + region.meeples
        self.setCount()
        
    def addMeeple(self, meeple : Meeple):
        self.meeples.append(meeple)
        # print(f"meeple {meeple} is place in {repr(self)}")
    
    def has_owner(self):
        return bool(self.meeples)

    def get_owner_players(self):
        if not self.meeples:
            return []
        counts = {}
        for meeple in self.meeples:
            player = meeple.player
            if not player:
                continue
            player.return_meeple()
            counts[player] = counts.get(player, 0) + 1
        if not counts:
            return []
        max_count = max(counts.values())
        return [p for p, c in counts.items() if c == max_count]

    def render(self, screen):
        [mepple.render(screen, True) for mepple in self.meeples]
        # for tile_pos, region in self.tiles.items():
        #     font = pygame.font.SysFont(None, 20)
        #     coors = [Neighbor.render_pos[key] for key in region] 
        #     text = font.render(f"{idx}", True, (0, 0, 0))
        #     for coordinate in coors:
        #         text_pos = (
        #             (tile_pos[0] + coordinate[0]) * image.get_width() + SCREEN_WIDTH // 2,
        #             (tile_pos[1] + coordinate[1]) * image.get_height() + SCREEN_HEIGHT // 2
        #         )
        #         screen.blit(text, text_pos)

    # def __repr__(self):
    #     return f"tiles: {self.tiles}, count: {self.count}, mepple: {self.meeples}"
        
class CityRegion(Region):
    def __init__(self, tile_pos : tuple, region: list, shield):
        super().__init__(tile_pos, region)
        self.shield = 1 if shield else 0

    def get_region_points(self):
        total = self.shield + self.count
        return total * 2 if self.completed_flag else total

    def addRegion(self, region):
        for key, value in region.tiles.items():
            self.tiles[key] = self.tiles.get(key, set()) ^ value
        self.meeples = self.meeples + region.meeples
        self.setCount()
        self.shield += region.shield
                
    def addTile(self, tile_pos: tuple, region : list, tile : Tile):
        self.tiles[tile_pos] = region
        self.setCount()
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
        self.completed_flag = flag
        
class RoadRegion(Region):
    def __init__(self, tile_pos : tuple, region: list):
        super().__init__(tile_pos, region)

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
                self.completed_flag = (road_traversal(end, self.intial_pos, self.intial_pos) == 0)
            case -1:
                self.completed_flag = False
            case 1:
                self.completed_flag = True

class GrassRegion(Region):
    def __init__(self, tile_pos : tuple, region: list):
        super().__init__(tile_pos, region)
        self.adjency_cities = set()
    
    def addAdjencyCityRegion(self, region: CityRegion):
        self.adjency_cities.add(region)
        print(self.adjency_cities)
    def get_region_points(self):
        print(self.adjency_cities)
        # if not self.adjency_cities: 
        #     return 0
        # finished_cities = len([c for c in list(self.adjency_cities) if c.completed_flag])
        finished_cities = len(list(self.adjency_cities))
        return finished_cities * 3
        
class MonasteryRegion(Region):
    def __init__(self, tile_pos : tuple, region: list):
        super().__init__(tile_pos, region)
        
    def is_completed(self):
        self.completed_flag = (self.count == 9)
    
    def get_region_points(self):
        return self.count
    
    def update(self, tile_pos):
        x, y = tile_pos
        x_, y_ = self.intial_pos
        if abs(x - x_) <= 1 and abs(y - y_) <= 1 and not self.tiles.get(tile_pos, None):
            self.addTile(tile_pos, [8])
            