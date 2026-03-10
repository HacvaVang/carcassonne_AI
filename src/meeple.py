from src.tiles import Tile
from settings import *
from src.assetloader import *
from src.player import Player
class Meeple:
    def __init__(self, pos, player : Player=None, ):
        self.player = player
        self.player.place_meeple()
        self.position = pos
        self.image = get_image(player.color, "Meeple")
        
    def add_points(self, points):
        return self.player.add_points(points)
        
    def render(self, screen, is_gardener):
        print(self.position)
        # Placeholder rendering logic
        if is_gardener:
            screen.blit(self.image, self.position)
        else:
            pygame.draw.circle(screen, self.player.color, self.position, 15)
        