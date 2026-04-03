from src.tiles import Tile
from src.meeple import Meeple
from settings import *
from src import Neighbor
class Region:
    def __init__(self, tile_pos : tuple, region: list):
        self.tiles = dict()
        self.tiles[tile_pos] = set(region)
        self.count = 1
        self.meeples : list[Meeple] = list()
        self.initial_pos = tile_pos
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

    def get_info_state(self):
        return {
            'type': type(self).__name__,
            'tiles': self.tiles,
            'count': self.count,
            'meeples': [m.get_info_state() for m in self.meeples],
            'initial_pos': self.initial_pos,
            'completed_flag': self.completed_flag
        }

    def __repr__(self):
        return f"{type(self)}: count: {self.count}, mepple: {self.meeples}"
        
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

    def get_info_state(self):
        info = super().get_info_state()
        info['shield'] = self.shield
        return info 
        
    def is_completed(self):
        visited_mask = dict.fromkeys(self.tiles.keys(), 0)
        visited_mask[self.initial_pos] = 1
        queue = [self.initial_pos]
        
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
        start, end = self.tiles[self.initial_pos]
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
        
        result = road_traversal(start, self.initial_pos, self.initial_pos)
        match result:
            case 0:
                self.completed_flag = (road_traversal(end, self.initial_pos, self.initial_pos) == 0)
            case -1:
                self.completed_flag = False
            case 1:
                self.completed_flag = True

class GrassRegion(Region):
    def __init__(self, tile_pos : tuple, region: list):
        super().__init__(tile_pos, region)
        self.adjency_cities = set()

    @staticmethod
    def _positions_touch(pos_a, pos_b):
        # Defines tile-local adjacency of edge/corner positions
        adjacent = {
            0: {1, 7},
            1: {0, 2},
            2: {1, 3},
            3: {2, 4},
            4: {3, 5},
            5: {4, 6},
            6: {5, 7},
            7: {6, 0},
            8: set(range(0, 8)),
        }
        for a in pos_a:
            for b in pos_b:
                if b in adjacent.get(a, set()) or a in adjacent.get(b, set()):
                    return True
        return False

    def is_adjacent_to(self, city_region):
        direction_by_delta = {(0, -1): 1, (1, 0): 3, (0, 1): 5, (-1, 0): 7}
        opposite_edge = {1: 5, 3: 7, 5: 1, 7: 3}

        # Same-tile adjacency
        for grass_tile, grass_pos in self.tiles.items():
            city_pos = city_region.tiles.get(grass_tile)
            if city_pos and self._positions_touch(grass_pos, city_pos):
                return True

        # Cross-tile adjacency along cardinal edges
        for grass_tile, grass_pos in self.tiles.items():
            for city_tile, city_pos in city_region.tiles.items():
                dx = city_tile[0] - grass_tile[0]
                dy = city_tile[1] - grass_tile[1]
                direction = direction_by_delta.get((dx, dy))
                if not direction:
                    continue
                opposite = opposite_edge[direction]
                if direction in grass_pos and opposite in city_pos:
                    return True

        return False

    def updateAdjencyCities(self, cities_list : list):
        # self.adjency_cities.clear()
        for city in cities_list:
            if self.is_adjacent_to(city):
                self.adjency_cities.add(city)

    def get_region_points(self):
        # print(self.adjency_cities)
        finished_cities = len(self.adjency_cities)
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
        x_, y_ = self.initial_pos
        if abs(x - x_) <= 1 and abs(y - y_) <= 1 and not self.tiles.get(tile_pos, None):
            self.addTile(tile_pos, [8])
            