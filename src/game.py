import threading
from enum import Enum

from src.map import Map
from settings import *
from src.tiledeck import TileDeck
from src.hud import HUD
from src.meeple import Meeple
from src.player import Player
from src.region import *
from src import Terrain, GamePhase, Color
from AI_agent.MCTS.mcts_player import MCTSPlayer

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.running = False
        
        self.players = []  # list of Player instances
        self.current_player_index = 0  # index of whose turn it is
        self.current_phase = None
        
        self.current_tile = None
        self.events = list()
        self.score_events = []
        
        self.regions = {
            Terrain.Grass       : list(),
            Terrain.City        : list(),
            Terrain.Monastery   : list(),
            Terrain.Road        : list(),
        }
            
        self.complete_cities = list()
        self.place_positions = dict()
        self.avaliable_moves = dict()
        
        self.hud = HUD()
        self.map = Map()

        # Game over state (when there are no tiles left to draw)
        self.game_over = False
        self.game_over_message = ""

        # AI thinking state
        self.ai_thinking = False
        self.pending_action = None

    def start(self):
        self.running = True

        self.tile_deck = TileDeck()
        self.current_tile = self.tile_deck.getStartingTile()
        self.place_tile((0, 0), self.current_tile, True)
        self.current_tile = self.drawTile()
        self.players = [Player(f"Player", list(Color.color.keys())[1])] + [MCTSPlayer(f"AI Player", list(Color.color.keys())[0])]
        # self.players = [Player(f"Player", list(Color.color.keys())[1])] + [Player(f"AI Player", list(Color.color.keys())[3])]
        self.current_player_index = 0
        self.current_phase = GamePhase.PlaceTile

    def isGameOver(self):
        return self.game_over

    def drawTile(self):
        flag = True
        while flag:
            tile : Tile = self.tile_deck.getRandomTile()
            if not tile:
                return None
            self.getAvaliableMoves(tile)
            if not self.checkAvaliableMoves():
                self.tile_deck.returnToTileDeck(tile)
            else:
                flag = False
        return tile
    
    def getAvaliableMoves(self, tile : Tile):
        for _ in range(4):
            moves = self.map.get_placeable_positon(tile)
            if moves:
                self.avaliable_moves[tile.rotate_count] = moves
            tile.rotate()
            
    def checkAvaliableMoves(self):
        return True if self.avaliable_moves else False
    
    def update(self, dt):
        if not self.running:
            return

        # When the game is over we still want to render and fade out score events,
        # but we no longer process player input or tile/meeple placement.
        if getattr(self, "game_over", False):
            for event in self.score_events[:]:
                event["remaining"] -= dt
                if event["remaining"] <= 0:
                    self.score_events.remove(event)
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
                        continue

                    grid_pos = get_grid_position(pos, self.current_tile.image)
                    if self.place_tile(grid_pos, self.current_tile):
                        self.addRegionScore()
                        self.changePhase()
                elif action == "Rotate":
                    if piece is not None and hasattr(piece, "rotate"):
                        piece.rotate()
            elif self.current_phase == GamePhase.PlaceMeeple:
                if action == "Place":
                    if self.can_place_meeple(pos):
                        meeple = Meeple(piece, pos)
                        self.place_meeple(pos, meeple)
                        self.addRegionScore()
                        self.changePhase()
                else:
                    self.changePhase()

        # Handle AI turns
        if not self.game_over and isinstance(self.players[self.current_player_index], MCTSPlayer) and not self.ai_thinking and self.pending_action is None:
            self.ai_thinking = True
            def ai_thread():
                if self.current_phase == GamePhase.PlaceTile:
                    action = self.players[self.current_player_index].choose_tile_action(self)
                    self.pending_action = action
                elif self.current_phase == GamePhase.PlaceMeeple:
                    action = self.players[self.current_player_index].choose_meeple_action(self)
                    self.pending_action = action
                self.ai_thinking = False
            thread = threading.Thread(target=ai_thread)
            thread.start()

        # Apply pending AI action
        if not self.ai_thinking and self.pending_action is not None:
            action = self.pending_action
            self.pending_action = None
            if self.current_phase == GamePhase.PlaceTile:
                # Rotate the tile
                for _ in range(action.rotation):
                    self.current_tile.rotate()
                # Place the tile
                if self.place_tile(action.tile_pos, self.current_tile):
                    self.addRegionScore()
                    self.changePhase()
            elif self.current_phase == GamePhase.PlaceMeeple:
                # For now, always skip meeple placement
                self.changePhase()

        # always age score events
        for event in self.score_events[:]:
            event["remaining"] -= dt
            if event["remaining"] <= 0:
                self.score_events.remove(event)

    def addRegionScore(self, end_phase = False):
        for terrain, regions in self.regions.items():
            # print(regions)

            if terrain == Terrain.Grass and not end_phase:
                continue
            for region in regions:
                if region.completed_flag or end_phase:
                    if not region.meeples:
                        continue
                    if terrain == Terrain.Grass:
                        region.updateAdjencyCities(self.complete_cities)
                    points = region.get_region_points()
                    owners = region.get_owner_players()
                    for player in owners:
                        player.add_points(points)
                        if region.completed_flag:
                            self.regions[terrain].remove(region)
                            self.add_score_event(f"+{points} points for {player.name}")
                        else:
                            self.add_score_event(
                                f"+{points} points for {player.name} (incomplete {terrain.name})"
                            )
                    
                    
                    
    def endGame(self):
        """End the game due to no tiles remaining and score remaining regions."""
        if getattr(self, "game_over", False):
            return

        self.game_over = True
        self.current_phase = None

        # Score any remaining completed regions first, then score incomplete ones.
        self.addRegionScore()
        self.addRegionScore(True)
        self.add_score_event("Game over! Final scores calculated.", duration=5.0)

    def changePhase(self):
        """Rotate turn order and draw next tile."""
        if self.current_phase == GamePhase.PlaceTile:
            self.current_phase = GamePhase.PlaceMeeple
        else:  
            self.avaliable_moves.clear()
            self.place_positions.clear()
            
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

            self.current_tile = self.drawTile()
            if self.current_tile is None:
                # No more tiles available -> end the game and score remaining regions
                self.endGame()
                return
            self.current_phase = GamePhase.PlaceTile

    def handle_event(self, event):
        # Ignore input while AI is thinking
        if getattr(self, 'ai_thinking', False):
            return

        # Allow exiting to menu when game is over
        if getattr(self, "game_over", False):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            return

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
                game_event["piece"] = self.players[self.current_player_index]
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

    def can_place_meeple(self, pos):
        if self.players[self.current_player_index].meeples == 0:
            return False

        # Define a click radius around the placeholder dots.
        radius = 20
        if self.current_tile and getattr(self.current_tile, "image", None):
            radius = max(radius, int(self.current_tile.image.get_width() * 0.25))
        radius_sq = radius * radius

        for placeholder in self.place_positions.keys():
            dx = placeholder[0] - pos[0]
            dy = placeholder[1] - pos[1]
            if dx * dx + dy * dy <= radius_sq:
                return True
        return False

    def place_meeple(self, pos, meeple : Meeple):
        if not self.place_positions:
            return

        closest = min(
            self.place_positions.keys(),
            key=lambda p: (p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2,
        )
        
        grid_pos = get_grid_position(pos, self.current_tile.image)

        terrain, region_pos = self.place_positions[closest]
        for region in self.regions[terrain][::-1]:
            if region_pos in region.tiles.get(grid_pos, None):
                region.addMeeple(meeple)
                self.players[self.current_player_index].place_meeple()
                break

    def place_tile(self, pos, tile: Tile | None = None, start_tile = False) -> bool:
        if tile is None:
            return False

        if not start_tile and not (pos in self.avaliable_moves.get(tile.rotate_count, [])):
            return False

        self.map.place_tile(pos, tile)
        self.updateRegion(pos, start_tile)
        return True


    def updateRegion(self, pos, start_tile = False):
        
        tile = self.current_tile
        if tile is None:
            return
        for x in self.regions[Terrain.Monastery]:
            x.update(pos)
            x.is_completed()

        
        for terrain, tile_regions in tile.region.items():
            for tile_region in tile_regions:
                if terrain == Terrain.Monastery:
                    new_region = self.addMonasteryRegion(tile_region, pos)
                else:
                    new_region = self.addRegion(terrain, tile_region, pos)
                new_region.is_completed()
                self.regions[terrain].append(new_region)
                
                if terrain == Terrain.City and new_region.completed_flag:
                    self.complete_cities.append(new_region)
                
                if start_tile or new_region.meeples:
                    continue
                                
                coor = Neighbor().render_pos[tile_region[0]]
                placeholder_pos = (
                    int((pos[0] + coor[0]) * tile.image.get_width() + SCREEN_WIDTH // 2),
                    int((pos[1] + coor[1]) * tile.image.get_height() + SCREEN_HEIGHT // 2),
                )
                self.place_positions[placeholder_pos] = (terrain, tile_region[0])
            
    def addRegion(self, terrain, positions: list, tile_pos):
        x, y = tile_pos
        match terrain:
            case Terrain.City:
                new_region = CityRegion(tile_pos, positions, self.current_tile.shield)
            case Terrain.Road:
                new_region = RoadRegion(tile_pos, positions)
            case Terrain.Grass:
                new_region = GrassRegion(tile_pos, positions)

        mask = reduce(lambda acc, ele: acc ^ Neighbor.direction_mask[ele], positions, 0)
        border = self.current_tile.edges
        for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
            if mask & (1 << idx) and self.map.get_tile(x + dx, y + dy):
                if terrain == Terrain.Grass and border[idx] == Terrain.City:
                    continue
                neighbor_pos_list = Neighbor.get_neighbor_pos(positions, (dx, dy))
                for neighbor_pos in neighbor_pos_list:
                    result : Region = next(filter(
                        lambda reg : neighbor_pos in reg.tiles.get((x + dx, y + dy), []), 
                        self.regions[terrain]), None)
                    if not result:
                        continue
                    new_region.addRegion(result)
                    self.regions[terrain].remove(result)
        return new_region

    def addMonasteryRegion(self, positions: list, tile_pos):
        x, y = tile_pos
        new_region = MonasteryRegion(tile_pos, positions)
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0)]:
            if self.map.get_tile(x + dx, y + dy):
                new_region.update((x + dx, y + dy))
        return new_region
    
    def render(self):
        if not self.running:
            return
        
        self.screen.fill((50, 50, 50))
        self.map.render(self.screen)
        
        tile_image = getattr(self.current_tile, "image", None)

        if self.current_phase == GamePhase.PlaceTile and tile_image is not None:
            pos = get_grid_position(pygame.mouse.get_pos(), tile_image)
            self.current_tile.render(self.screen, pos, not_place=True)
            
            for pos in self.avaliable_moves.get(self.current_tile.rotate_count, []):
                Tile().render(self.screen, pos)
        else:
            for pos in self.place_positions:
                pygame.draw.circle(self.screen, (200, 0, 0), pos, 10)

        for region in [r for rl in list(self.regions.values()) for r in rl]:  
            region.render(self.screen)
        
        # draw the HUD over the map
        if hasattr(self, 'hud'):
            self.hud.render(self.screen, self)

