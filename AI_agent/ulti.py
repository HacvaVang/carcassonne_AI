from src.player import Player
from src.map import Map
from src.tiles import Tile
from src.tiledeck import TileDeck
from src.region import *
from src import Terrain, GamePhase, Color
import copy

class Action:
    def __init__(self, tile_pos=None, rotation=0, meeple_pos=None):
        self.tile_pos = tile_pos  # (x, y)
        self.rotation = rotation  # 0-3
        self.meeple_pos = meeple_pos  # position for meeple, or None to skip

class CarcassonneState:
    def __init__(self, game=None):
        if game:
            # Copy relevant parts of the game without pygame surfaces
            self.players = copy.deepcopy(game.players)
            self.current_player_index = game.current_player_index
            self.current_phase = game.current_phase
            
            # Copy map without surfaces
            self.map : Map = Map()
            self.map.tileset = {}
            for pos, tile in game.map.tileset.items():
                copied_tile = Tile(tile.tile_type)
                copied_tile.image = None
                self.map.tileset[pos] = copied_tile
            self.map.adjency_tile = set(game.map.adjency_tile)
            
            # Copy tile_deck
            self.tile_deck = TileDeck()
            self.tile_deck.tileset = dict(game.tile_deck.tileset)
            self.tile_deck.count = game.tile_deck.count
            self.tile_deck.starting_tile = game.tile_deck.starting_tile
            
            # Copy current_tile
            self.current_tile = Tile(game.current_tile.tile_type) if game.current_tile else None
            if self.current_tile:
                self.current_tile.image = None
                
            # Copy regions without surfaces
            self.regions = copy.deepcopy({k: [r.get_info_state() for r in v] for k, v in game.regions.items()})
            self.complete_cities = copy.deepcopy([c.get_info_state() for c in game.complete_cities])
            
            self.game_over = game.game_over
        else:
            # Initialize empty state
            self.players = []
            self.current_player_index = 0
            self.current_phase = GamePhase.PlaceTile
            self.map = Map()
            self.tile_deck = TileDeck()
            self.current_tile = None
            self.regions = {
                Terrain.Grass: [],
                Terrain.City: [],
                Terrain.Monastery: [],
                Terrain.Road: [],
            }
            self.complete_cities = []
            self.game_over = False

    def get_current_player(self):
        return self.players[self.current_player_index]

    def is_terminal(self):
        return self.game_over

    def get_winner(self):
        if not self.is_terminal():
            return None
        return max(self.players, key=lambda p: p.score)

    def get_score(self, player_index) -> int:
        return self.players[player_index].score

    def get_possible_actions(self):
        if self.is_terminal():
            return []

        actions = []
        if self.current_phase == GamePhase.PlaceTile:
            tile = self.current_tile
            if tile:
                for rot in range(4):
                    tile_copy = copy.deepcopy(tile)
                    for _ in range(rot):
                        tile_copy.rotate()
                    moves = self.map.get_placeable_positon(tile_copy)
                    for pos in moves:
                        actions.append(Action(tile_pos=pos, rotation=rot))
        elif self.current_phase == GamePhase.PlaceMeeple:
            actions.append(Action(meeple_pos=None))
            # TODO: add actual meeple placement options
        return actions

    def change_phase(self):
        if self.current_phase == GamePhase.PlaceTile:
            self.current_phase = GamePhase.PlaceMeeple
            return

        if len(self.players) == 0:
            self.game_over = True
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_tile = self.tile_deck.getRandomTile()
        if self.current_tile:
            self.current_tile.image = None

        if not self.current_tile:
            self.game_over = True
            self.current_phase = None
        else:
            self.current_phase = GamePhase.PlaceTile

    def simulate_action(self, action):
        print("Copying state for simulation")
        next_state = copy.deepcopy(self)

        if next_state.current_phase == GamePhase.PlaceTile:
            if action.tile_pos is None:
                return next_state

            tile = next_state.current_tile
            if not tile:
                return next_state

            for _ in range(action.rotation):
                tile.rotate()
            next_state.map.place_tile(action.tile_pos, tile)
            # TODO: properly update regions / scoring
            next_state.change_phase()
        elif next_state.current_phase == GamePhase.PlaceMeeple:
            # no meeple placement in simplified rollout
            next_state.change_phase()

        return next_state
    
    def apply_action(self, action):
        if self.current_phase == GamePhase.PlaceTile:
            if action.tile_pos is None:
                return

            tile = self.current_tile
            if not tile:
                return

            for _ in range(action.rotation):
                tile.rotate()
            self.map.place_tile(action.tile_pos, tile)
            # TODO: properly update regions / scoring
            self.change_phase()
        elif self.current_phase == GamePhase.PlaceMeeple:
            # no meeple placement in simplified rollout
            self.change_phase()

