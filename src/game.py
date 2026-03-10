from enum import Enum
import pygame
from src.map import Map
from settings import *
from src.tiles import Tile
from src.hud import HUD
from src.player import Player

class GamePhase(Enum):
    PlaceTile = 1
    PlaceMeeple = 2

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.running = False
        
        self.players = []  # list of Player instances
        self.current_player = 0  # index of whose turn it is
        self.current_phase = None
        
        self.tile_bag = []  # list of remaining Tile instances to draw from
        self.current_tile = None

        self.score_events = []  # transient UI messages for scoring
        
        self.hud = HUD()
        self.map = Map(starting_tile=Tile('D'), game=self)
        
    
    def start(self):
        self.running = True
        self.tile_bag = [Tile('V'), Tile('V'), Tile('V'), Tile('W'), Tile('V'), Tile('V'), Tile('V'), Tile('W'), Tile('K'), Tile('J'), Tile('A'),Tile('E'), Tile('E'), Tile('A'), Tile('C'), Tile('I'), Tile('O'), Tile('O'), Tile('O')]
        self.current_tile = self.tile_bag.pop() if self.tile_bag else None
        # print(f"Starting game with tile bag: {len(self.tile_bag)} tiles")
        
        
        self.players = [Player(f"Player {i+1}", list(Color.color.keys())[i]) for i in range(4)]
        self.current_player = 0
        
        self.current_phase = GamePhase.PlaceTile

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if GamePhase.PlaceTile == self.current_phase:
                if event.button == 1:
                    pos = get_grid_position(pygame.mouse.get_pos(), self.current_tile.image)
                    if self.map.can_place_tile(pos, self.current_tile):
                        self.map.place_tile(pos, self.current_tile)
                        # print(f"Starting game with tile bag: {len(self.tile_bag)} tiles")
                        self.current_phase = GamePhase.PlaceMeeple

                elif event.button == 3:
                    # print(f"Right button clicked at {event.pos}")
                    self.current_tile.rotate()
            elif self.current_phase == GamePhase.PlaceMeeple:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if self.map.can_place_meeple(pos):
                        self.map.place_meeple(pos, self.players[self.current_player])
                        self.current_tile = self.tile_bag.pop() if self.tile_bag else None
                        self.current_player = (self.current_player + 1) % len(self.players)
                        self.current_phase = GamePhase.PlaceTile
                elif event.button == 3:
                    self.current_tile = self.tile_bag.pop() if self.tile_bag else None
                    self.current_player = (self.current_player + 1) % len(self.players)
                    self.current_phase = GamePhase.PlaceTile

    def add_score_event(self, text: str, duration: float = 2.0):
        """Add a transient score event to be displayed in the HUD."""
        self.score_events.append({
            "text": text,
            "remaining": duration,
            "duration": duration,
        })

    def update(self, dt):
        if not self.running:
            return

        # Update transient scoring messages
        for event in self.score_events[:]:
            event["remaining"] -= dt
            if event["remaining"] <= 0:
                self.score_events.remove(event)


    def render(self):
        if not self.running:
            return
        self.screen.fill((50, 50, 50))
        
        self.map.render(self.screen)
        
        
        if self.current_phase == GamePhase.PlaceTile:
            pos = get_grid_position(pygame.mouse.get_pos(), self.current_tile.image)
            self.current_tile.render(self.screen, pos, not_place=True)
        else:
            self.map.render_avaliable_place(self.screen)
        
        # draw the HUD over the map
        if hasattr(self, 'hud'):
            self.hud.render(self.screen, self)