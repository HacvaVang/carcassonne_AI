from functools import reduce
from src.ulti import Terrain, Neighbor
from src.region import CityRegion, RoadRegion, GrassRegion, MonasteryRegion, Region

def add_region(regions, map_obj, current_tile, terrain, positions: list, tile_pos):
    x, y = tile_pos
    match terrain:
        case Terrain.City:
            new_region = CityRegion(tile_pos, positions, current_tile.shield)
        case Terrain.Road:
            new_region = RoadRegion(tile_pos, positions)
        case Terrain.Grass:
            new_region = GrassRegion(tile_pos, positions)

    mask = reduce(lambda acc, ele: acc ^ Neighbor.direction_mask[ele], positions, 0)
    border = current_tile.edges
    for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
        if mask & (1 << idx) and map_obj.get_tile(x + dx, y + dy):
            if terrain == Terrain.Grass and border[idx] == Terrain.City:
                continue
            neighbor_pos_list = Neighbor.get_neighbor_pos(positions, (dx, dy))
            for neighbor_pos in neighbor_pos_list:
                result : Region = next(filter(
                    lambda reg : neighbor_pos in reg.tiles.get((x + dx, y + dy), []), 
                    regions[terrain]), None)
                if not result:
                    continue
                new_region.addRegion(result)
                if result in regions[terrain]:
                    regions[terrain].remove(result)
    return new_region

def add_monastery_region(map_obj, positions: list, tile_pos):
    x, y = tile_pos
    new_region = MonasteryRegion(tile_pos, positions)
    for dx, dy in [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]:
        if map_obj.get_tile(x + dx, y + dy):
            new_region.update((x + dx, y + dy))
    return new_region

def assign_points_at_end_of_game(game_instance):
    """Assign points for remaining regions at end of game."""
    # Score any remaining completed regions first, then score incomplete ones.
    game_instance.addRegionScore()
    game_instance.addRegionScore(True)
