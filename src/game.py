import logging
import os
from enum import Enum

import pygame

from src.map import Map
from settings import *
from src.tiles import Tile
from src.tiledeck import TileDeck
from src.hud import HUD
from src.meeple import Meeple
from src.player import Player
from src.region import *

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "game.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("game")


class GamePhase(Enum):
    PlaceTile = 1
    PlaceMeeple = 2


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.running = False
        
        self.players = []  # list of Player instances
        self.current_player = None  # index of whose turn it is
        self.current_phase = None
        
        self.current_tile = None
        self.events = list()
        self.score_events = []
        
        self.regions_list : list[Region] = list()
        self.place_positions = dict()
        
        self.hud = HUD()
        self.map = Map(game=self)
        
        
    
    def start(self):
        logger.info("Starting new game")
        self.running = True

        self.tile_deck = TileDeck()
        self.current_tile = self.tile_deck.getStartingTile()
        logger.debug("Starting tile is %s", self.current_tile.tile_type)
        self.place_tile((0, 0), self.current_tile, True)

        self.current_tile = self.tile_deck.draw_random()
        logger.debug("Drew first tile: %s", getattr(self.current_tile, "tile_type", None))

        self.players = [Player(f"Player {i+1}", list(Color.color.keys())[i]) for i in range(4)]
        self.current_player = self.players[0]
        self.current_phase = GamePhase.PlaceTile

    def update(self, dt):
        if not self.running:
            return

        for event in self.events[:]:
            action = event.get("action", None)
            piece = event.get("piece", None)
            pos = event.get("pos", None)
            self.events.remove(event)

            if not action:
                continue

            if GamePhase.PlaceTile == self.current_phase:
                if action == "Place":
                    if self.current_tile is None:
                        logger.debug("No current tile available to place")
                        continue

                    grid_pos = get_grid_position(pos, self.current_tile.image)
                    if self.place_tile(grid_pos, self.current_tile):
                        logger.debug("Placed tile %s at %s", self.current_tile.tile_type, grid_pos)
                        self.addScore()
                        self.current_phase = GamePhase.PlaceMeeple
                elif action == "Rotate":
                    if piece is not None and hasattr(piece, "rotate"):
                        piece.rotate()
                        logger.debug("Rotated tile %s (rotation count=%s)", getattr(piece, "tile_type", None), getattr(piece, "rotate_count", None))
            elif self.current_phase == GamePhase.PlaceMeeple:
                if action == "Place":
                    if self.can_place_meeple(pos):
                        meeple = Meeple(piece, pos)
                        self.place_meeple(pos, meeple)
                        logger.debug("Placed meeple for player %s at %s", getattr(piece, "name", None), pos)
                        self.addScore()
                        self.changePlayer()
                else:
                    logger.debug("Player %s passed meeple placement", getattr(self.current_player, "name", None))
                    self.changePlayer()

        for event in self.score_events[:]:
            event["remaining"] -= dt
            if event["remaining"] <= 0:
                self.score_events.remove(event)

    def addScore(self):
        """Award points for completed regions and remove them from tracking."""
        completed = [r for r in self.regions_list if r.completed_flag and r.meeples]
        for region in completed:
            points = region.get_region_points()
            owners = region.get_owner_players()
            logger.debug("Scoring region %s for %s points to %s", region, points, owners)
            for player in owners:
                player.add_points(points)
                logger.debug("Player %s now has %s points", player.name, player.score)
            self.regions_list.remove(region)

    def changePlayer(self):
        """Rotate turn order and draw next tile."""
        player = self.players.pop(0)
        self.players.append(player)
        self.current_player = self.players[0]
        logger.debug("Current player is now %s", self.current_player.name)

        self.current_tile = self.tile_deck.draw_random() if hasattr(self, "tile_deck") else None
        logger.debug("Drew tile for next turn: %s", getattr(self.current_tile, "tile_type", None))
        self.current_phase = GamePhase.PlaceTile        

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            game_event = {
                "pos": pygame.mouse.get_pos(),
            }

            if GamePhase.PlaceTile == self.current_phase:
                game_event["piece"] = self.current_tile
                if event.button == 1:
                    game_event["action"] = "Place"
                elif event.button == 3:
                    game_event["action"] = "Rotate"

            elif self.current_phase == GamePhase.PlaceMeeple:
                logger.debug("Player %s is attempting to place a meeple", getattr(self.current_player, "name", None))
                game_event["piece"] = self.current_player
                if event.button == 1:
                    game_event["action"] = "Place"
                elif event.button == 3:
                    game_event["action"] = "Pass"

            self.events.append(game_event)

    def add_score_event(self, text: str, duration: float = 2.0):
        """Add a transient score event to be displayed in the HUD."""
        self.score_events.append({
            "text": text,
            "remaining": duration,
            "duration": duration,
        })

    def render(self):
        if not self.running:
            return
        self.screen.fill((50, 50, 50))
        
        self.map.render(self.screen)
        
        
        if self.current_phase == GamePhase.PlaceTile and self.current_tile is not None:
            pos = get_grid_position(pygame.mouse.get_pos(), self.current_tile.image)
            self.current_tile.render(self.screen, pos, not_place=True)
        else:
            for pos in self.place_positions:
                pygame.draw.circle(self.screen, (200, 0, 0), pos, 10)

        for idx, region in enumerate(self.regions_list):
            # print(region.__repr__())
            region.render(self.screen, self.current_tile.image, idx)
        
        # draw the HUD over the map
        if hasattr(self, 'hud'):
            self.hud.render(self.screen, self)

    def can_place_meeple(self, pos):
        if self.current_player.meeples == 0:
            return False
        for placeholder in self.place_positions.keys():
            dx = placeholder[0] - pos[0]
            dy = placeholder[1] - pos[1]
            if dx * dx + dy * dy <= 20 * 20:
                return True
        return False

    def place_meeple(self, pos, meeple : Meeple):
        closest = min(
            self.place_positions.keys(),
            key=lambda p: (p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2,
        )
        
        terrain, tile_pos = self.place_positions[closest]        
        for region in self.regions_list[::-1]:
            if region.terrain != terrain:
                continue
            if tile_pos in region.tiles and closest:  # region includes the tile
                region.addMeeple(meeple)
                self.current_player.place_meeple()
                break

    def place_tile(self, pos, tile: Tile | None = None, start_tile = False) -> bool:
        if tile is None:
            return False

        if not start_tile and not self.map.can_place_tile(pos, tile):
            return False

        self.map.place_tile(pos, tile)
        self.updateRegion(pos)
        return True


    def updateRegion(self, pos):
        self.place_positions.clear()
        tile = self.map.get_tile(*pos)
        if tile is None:
            return
        for x in self.regions_list:
            if type(x) is MonasteryRegion:
                x.update(pos)
                x.is_completed()

        
        for terrain, tile_regions in tile.region.items():
            for tile_region in tile_regions:
                if terrain == Terrain.Monastery:
                    new_region = self.addMonasteryRegion(tile_region, pos)
                else:
                    new_region = self.addRegion(terrain, tile_region, pos)
                new_region.is_completed()
                if not new_region.meeples:
                    coor = Neighbor().render_pos[tile_region[0]]
                    placeholder_pos = (
                        (pos[0] + coor[0]) * tile.image.get_width() + SCREEN_WIDTH // 2,
                        (pos[1] + coor[1]) * tile.image.get_height() + SCREEN_HEIGHT // 2
                    )
                    self.place_positions[placeholder_pos] = (terrain, pos)

    def addRegion(self, terrain, positions: list, tile_pos):
        x, y = tile_pos
        tile = self.map.get_tile(x, y)
        match terrain:
            case Terrain.City:
                new_region = CityRegion(tile_pos, positions, tile)
            case Terrain.Road:
                new_region = RoadRegion(tile_pos, positions)
            case Terrain.Grass:
                new_region = GrassRegion(tile_pos, positions)

        mask = reduce(lambda acc, ele: acc ^ Neighbor.direction_mask[ele], positions, 0)
        border = tile.edges
        for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
            if mask & (1 << idx) and self.map.get_tile(x + dx, y + dy):
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
        return new_region

    def addMonasteryRegion(self, positions: list, tile_pos):
        x, y = tile_pos
        new_region = MonasteryRegion(tile_pos, positions)
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]:
            if self.map.get_tile(x + dx, y + dy):
                new_region.update((x + dx, y + dy))
        self.regions_list.append(new_region)
        return new_region

