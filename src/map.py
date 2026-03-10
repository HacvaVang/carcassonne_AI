import pygame
from settings import *
from src.tiles import Tile
from src.meeple import Meeple
from src.region import *

class Tileset:
    def __init__(self, seed: int):
        pass
    
class Map:
    def __init__(self, starting_tile: Tile = Tile('D'), game=None):
        # dictionary keyed by (x, y) coordinates storing Tile instances
        self.tileset = {}
        self.place_position = None
        self.meeple_placeable_positions = dict()
        self.regions_list : list[Region] = list()
        self.game = game
        
        if starting_tile:
            self.place_tile((0, 0), starting_tile)

    def can_place_tile(self, pos : tuple, tile : Tile):
        if pos in self.tileset:
            return False
        neighbor_flag = False
        x, y = pos
        for idx, (dx, dy) in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
            neighbor : Tile = self.get_tile(x + dx, y + dy)
            if neighbor:
                neighbor_flag = True
                current_connection = tile.edges[idx]
                neighbor_connection = neighbor.edges[(idx + 2) % 4]
                if current_connection != neighbor_connection:
                    return False
        return neighbor_flag   
    
    def setMonasteryRegion(self, terrain, positions: list, tile_pos):
        x, y = tile_pos
        new_region = MonasteryRegion(tile_pos, positions, terrain)
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]:
            if self.get_tile(x + dx, y + dy):
                new_region.update((x + dx, y + dy))
        self.regions_list.append(new_region)
            
    def setRegion(self, tile : Tile, terrain, positions: list, tile_pos):
        x, y = tile_pos
        
        match terrain:
            case Terrain.City:
                new_region = CityRegion(tile_pos, positions, tile, terrain)
            case Terrain.Road:
                new_region = RoadRegion(tile_pos, positions, terrain)
            case Terrain.Grass:
                new_region = GrassRegion(tile_pos, positions, terrain)

        mask = reduce(lambda acc, ele: acc ^ Neighbor.direction_mask[ele], positions, 0)
        border = tile.edges
        for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
            if mask & (1 << idx) and self.get_tile(x + dx, y + dy):
                if terrain == Terrain.Grass and border[idx] == Terrain.City:
                    continue
                neighbor_pos_list = Neighbor.get_neighbor_pos(positions, (dx, dy))
                for neighbor_pos in neighbor_pos_list:
                    result : Region = next(filter(
                        lambda reg : reg.terrain == terrain and neighbor_pos in reg.tiles.get((x + dx, y + dy), []), self.regions_list
                    ), None)
                    if result:
                        new_region.addRegion(result)
                        self.regions_list.remove(result)
        self.regions_list.append(new_region)
                    
    def place_tile(self, pos, tile : Tile):
        self.place_position = pos
        self.meeple_placeable_positions.clear()
        
        [x.update(pos) for x in self.regions_list  if type(x) is MonasteryRegion]
                
        for terrain, regions in tile.region.items():
            for region in regions:
                if terrain == Terrain.Monastery:
                    self.setMonasteryRegion(terrain, region, pos)       
                else:
                    self.setRegion(tile, terrain, region, pos)

                coordinate = Neighbor().render_pos[region[0]]
                placeholder_pos = (
                    (pos[0] + coordinate[0]) * tile.image.get_width() + SCREEN_WIDTH // 2,
                    (pos[1] + coordinate[1]) * tile.image.get_height() + SCREEN_HEIGHT // 2
                )
                self.meeple_placeable_positions[placeholder_pos] = (terrain, pos)
        
        self.tileset[pos] = tile
        
        for region in self.regions_list:
            if region.is_completed():
                points = region.get_region_points()
                owners = region.get_owner_players() if hasattr(region, "get_owner_players") else []

                if owners:
                    owners_text = ", ".join([p.name for p in owners])
                    for owner in owners:
                        owner.add_score(points)
                    # return meeples to their owners
                    if hasattr(region, "return_meeples"):
                        region.return_meeples()
                    if self.game:
                        self.game.add_score_event(f"{owners_text} +{points} ({region.terrain.name})")
                else:
                    # still mark scored so we don't calculate it again
                    if self.game:
                        self.game.add_score_event(f"{region.terrain.name} completed ({points} pts)")
                self.regions_list.remove(region)

    def can_place_meeple(self, pos):
        # allow placing a meeple if the mouse is over a valid placeholder
        for placeholder in self.meeple_placeable_positions.keys():
            dx = placeholder[0] - pos[0]
            dy = placeholder[1] - pos[1]
            if dx * dx + dy * dy <= 20 * 20:
                return True
        return False
    
    def place_meeple(self, pos, player):
        """Place a meeple near the closest valid placeholder."""
        if not self.can_place_meeple(pos):
            return

        # find closest placeholder
        closest = min(
            self.meeple_placeable_positions.keys(),
            key=lambda p: (p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2,
        )
        terrain, tile_pos = self.meeple_placeable_positions[closest]

        # create meeple and attach to player
        from src.meeple import Meeple
        meeple = Meeple(closest, player)

        # associate meeple with the matching region
        for region in self.regions_list[::1]:
            if region.terrain != terrain:
                continue
            if tile_pos in region.tiles and closest:  # region includes the tile
                region.meeples.append(meeple)
                break

        # Once placed, remove this placeholder
        self.meeple_placeable_positions.pop(closest, None)
        

    def get_tile(self, x, y):
        return self.tileset.get((x, y), None)

    def render(self, screen):
        image = None
        for (x, y), tile in self.tileset.items():
            if not hasattr(tile, 'image'):
                continue
            image = tile.image
            tile.render(screen, (x, y))
        
        for idx, region in enumerate(self.regions_list):
            # print(region.__repr__())
            region.render(screen, image, idx)
        
        # Add mouse position display and highlight the tile under the mouse cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"Mouse: ({mouse_x}, {mouse_y})", True, (255, 255, 255))
        screen.blit(text, (10, 10))  

    def render_avaliable_place(self, screen):
        for pos in self.meeple_placeable_positions:
            pygame.draw.circle(screen, (255, 0, 0), pos, 10)
            