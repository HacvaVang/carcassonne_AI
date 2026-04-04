import threading
from enum import Enum

from src.camera import Camera
from src.map import Map
from settings import *
from src.tiledeck import TileDeck
from src.hud import HUD
from src.meeple import Meeple
from src.player import Player
from src.region import *
from src.game_logic import *
from src import Terrain, GamePhase, Color
from AI_agent.MCTS.mcts_player import MCTSPlayer
from AI_agent.minimax.minimax_player import MinimaxPlayer
from AI_agent.random.random_player import RandomPlayer 

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
        self.camera = Camera()

        # Game over state (when there are no tiles left to draw)
        self.game_over = False
        self.game_over_message = ""

        # AI thinking state
        self.ai_thinking = False
        self.pending_action = None

        # Last opponent tile highlight
        self.last_opponent_tile_pos = None   # grid (x, y)
        self.last_opponent_color = (255, 220, 0)  # fallback yellow

    def start(self):
        self.running = True

        self.tile_deck = TileDeck()
        self.current_tile = self.tile_deck.getStartingTile()
        self.place_tile((0, 0), self.current_tile, True)
        self.current_tile = self.drawTile()
        self.players = [MCTSPlayer(f"MCTS1", list(Color.color.keys())[1])] + [MCTSPlayer(f"MCTS2", list(Color.color.keys())[2])]
        # self.players = [Player(f"Hac", list(Color.color.keys())[0])] + [MCTSPlayer(f"MCTS", list(Color.color.keys())[1])] + [RandomPlayer(f"Random", list(Color.color.keys())[2])]
        # self.players = [Player(f"Player", list(Color.color.keys())[1])] + [Player(f"AI Player", list(Color.color.keys())[3])]
        self.current_player_index = 0
        self.current_phase = GamePhase.PlaceTile

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

        # Camera pan via WASD
        keys = pygame.key.get_pressed()
        self.camera.update(dt, keys)

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

                    grid_pos = get_grid_position(pos, self.current_tile.image, self.camera)
                    if self.place_tile(grid_pos, self.current_tile):
                        self.addRegionScore()
                        self.changePhase()
                elif action == "Rotate":
                    if piece is not None and hasattr(piece, "rotate"):
                        piece.rotate()
            elif self.current_phase == GamePhase.PlaceMeeple:
                # Auto-skip if player has no meeples
                if self.players[self.current_player_index].meeples <= 0:
                    self.changePhase()
                    continue
                if action == "Place":
                    if self.can_place_meeple(pos):
                        # Snap to nearest placeholder (world coords)
                        wx, wy = self.camera.screen_to_world(*pos)
                        closest = min(
                            self.place_positions.keys(),
                            key=lambda p: (p[0] - wx) ** 2 + (p[1] - wy) ** 2,
                        )
                        meeple = Meeple(piece, closest)
                        self.place_meeple(closest, meeple)
                        self.addRegionScore()
                        self.changePhase()
                else:
                    self.changePhase()

        # Handle AI turns
        if not self.game_over and type(self.players[self.current_player_index]) is not Player and not self.ai_thinking and self.pending_action is None:
            self.ai_thinking = True
            def ai_thread():
                action : Action = self.players[self.current_player_index].choose_action(self)
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
                    # Record the tile position for the opponent highlight
                    self.last_opponent_tile_pos = action.tile_pos
                    opponent = self.players[self.current_player_index]
                    raw = opponent.color
                    self.last_opponent_color = Color.color[raw] if isinstance(raw, str) else (255, 220, 0)

                    # Process Unified AI Meeple placement
                    if action.meeple_pos is not None:
                        terrain, region_pos = action.meeple_pos
                        for placeholder_pos, (t, r_pos) in self.place_positions.items():
                            if t == terrain and r_pos == region_pos:
                                meeple = Meeple(self.players[self.current_player_index], placeholder_pos)
                                # Directly add to region using world coords
                                tw = self.current_tile.image.get_width()
                                th = self.current_tile.image.get_height()
                                grid_pos = (int(placeholder_pos[0] // tw), int(placeholder_pos[1] // th))
                                for region in self.regions[terrain][::-1]:
                                    if r_pos in region.tiles.get(grid_pos, set()):
                                        region.addMeeple(meeple)
                                        self.players[self.current_player_index].place_meeple()
                                        break
                                self.addRegionScore()
                                break

                    self.changePhase() # advance to PlaceMeeple
                    self.changePhase() # bypass PlaceMeeple instantly for unified AI agent turn

        # always age score events
        for event in self.score_events[:]:
            event["remaining"] -= dt
            if event["remaining"] <= 0:
                self.score_events.remove(event)

    def addRegionScore(self, end_phase = False):
        for terrain, regions in self.regions.items():
            if terrain == Terrain.Grass and not end_phase:
                continue

            to_remove = []
            for region in regions[:]:           # snapshot — safe to mutate original
                if region.completed_flag or end_phase:
                    if not region.meeples:
                        continue
                    if terrain == Terrain.Grass:
                        region.updateAdjencyCities(self.complete_cities)
                    points = region.get_region_points()
                    owners = region.get_owner_players()  # also returns meeples

                    owner_names = []
                    for player in owners:
                        player.add_points(points)
                        owner_names.append(player.name)

                    if region.completed_flag:
                        to_remove.append(region)
                        self.add_score_event(
                            f"+{points} pts → {', '.join(owner_names)}"
                        )
                    else:
                        self.add_score_event(
                            f"+{points} pts → {', '.join(owner_names)} (incomplete {terrain.name})"
                        )

            for region in to_remove:
                if region in self.regions[terrain]:
                    self.regions[terrain].remove(region)


                    
    def assignPointsAtEndOfGame(self):
        """Assign points for remaining regions at end of game."""
        # Score any remaining completed regions first, then score incomplete ones.
        self.addRegionScore()
        self.addRegionScore(True)

    def endGame(self):
        """End the game due to no tiles remaining and score remaining regions."""
        if getattr(self, "game_over", False):
            return

        self.game_over = True
        self.current_phase = None

        self.assignPointsAtEndOfGame()
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
            # Ignore scroll here; handled in MOUSEWHEEL
            if event.button in (4, 5):
                pass
            else:
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

        elif event.type == pygame.MOUSEWHEEL:
            factor = 1.1 if event.y > 0 else 1.0 / 1.1
            self.camera.zoom_at(factor, pygame.mouse.get_pos())

    def add_score_event(self, text: str, duration: float = 2.0):
        """Add a transient score event to be displayed in the HUD."""
        self.score_events.append({
            "text": text,
            "remaining": duration,
            "duration": duration,
        })

    def can_place_meeple(self, screen_pos):
        if self.players[self.current_player_index].meeples == 0:
            return False
        if not self.place_positions:
            return False
        wx, wy = self.camera.screen_to_world(*screen_pos)
        # Radius in world pixels (25% of tile width)
        tw = self.current_tile.image.get_width() if self.current_tile else 100
        radius_sq = (tw * 0.35) ** 2
        for placeholder in self.place_positions.keys():
            dx = placeholder[0] - wx
            dy = placeholder[1] - wy
            if dx * dx + dy * dy <= radius_sq:
                return True
        return False

    def place_meeple(self, world_pos, meeple : Meeple):
        if not self.place_positions:
            return

        closest = min(
            self.place_positions.keys(),
            key=lambda p: (p[0] - world_pos[0]) ** 2 + (p[1] - world_pos[1]) ** 2,
        )
        tw = self.current_tile.image.get_width()
        th = self.current_tile.image.get_height()
        grid_pos = (int(closest[0] // tw), int(closest[1] // th))

        terrain, region_pos = self.place_positions[closest]
        for region in self.regions[terrain][::-1]:
            if region_pos in region.tiles.get(grid_pos, set()):
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
                    new_region = add_monastery_region(self.map, tile_region, pos)
                else:
                    new_region = add_region(self.regions, self.map, self.current_tile, terrain, tile_region, pos)
                new_region.is_completed()
                self.regions[terrain].append(new_region)
                
                if terrain == Terrain.City and new_region.completed_flag:
                    self.complete_cities.append(new_region)
                
                if start_tile or new_region.meeples:
                    continue
                                
                coor = Neighbor().render_pos[tile_region[0]]
                placeholder_pos = (
                    int((pos[0] + coor[0]) * tile.image.get_width()),
                    int((pos[1] + coor[1]) * tile.image.get_height()),
                )
                self.place_positions[placeholder_pos] = (terrain, tile_region[0])
    
    def render(self):
        if not self.running:
            return
        
        self.screen.fill((50, 50, 50))
        self.map.render(self.screen, self.camera)

        # ── Opponent last-move highlight ─────────────────────────────────────
        if self.last_opponent_tile_pos is not None:
            ref_tile = self.map.get_tile(*self.last_opponent_tile_pos)
            if ref_tile and ref_tile.image is not None:
                tw = ref_tile.image.get_width()
                th = ref_tile.image.get_height()
                gx, gy = self.last_opponent_tile_pos
                world_x, world_y = gx * tw, gy * th
                sx, sy = self.camera.world_to_screen(world_x, world_y)
                dw = max(1, int(tw * self.camera.zoom))
                dh = max(1, int(th * self.camera.zoom))

                # Semi-transparent tinted fill
                overlay = pygame.Surface((dw, dh), pygame.SRCALPHA)
                r, g, b = self.last_opponent_color
                overlay.fill((r, g, b, 70))
                self.screen.blit(overlay, (sx, sy))

                # Bright border
                border_rect = pygame.Rect(sx, sy, dw, dh)
                pygame.draw.rect(self.screen, self.last_opponent_color, border_rect, max(2, int(3 * self.camera.zoom)))
        # ─────────────────────────────────────────────────────────────────────
        
        tile_image = getattr(self.current_tile, "image", None)

        if self.current_phase == GamePhase.PlaceTile and tile_image is not None:
            grid_pos = get_grid_position(pygame.mouse.get_pos(), tile_image, self.camera)
            for pos in self.avaliable_moves.get(self.current_tile.rotate_count, []):
                if pos != grid_pos:
                    Tile().render(self.screen, pos, camera=self.camera)

            self.current_tile.render(self.screen, grid_pos, camera=self.camera, not_place=True)
        else:
            for world_pos in self.place_positions:
                sx, sy = self.camera.world_to_screen(world_pos[0], world_pos[1])
                pygame.draw.circle(self.screen, (200, 0, 0), (sx, sy), max(4, int(10 * self.camera.zoom)))

        for region in [r for rl in list(self.regions.values()) for r in rl]:  
            region.render(self.screen, self.camera)
        
        # draw the HUD over the map
        if hasattr(self, 'hud'):
            self.hud.render(self.screen, self)
