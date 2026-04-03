from src.tiles import Tile
from settings import *
from src.assetloader import *
from src.player import Player
class Meeple:
    def __init__(self, player : Player, pos : tuple):
        self.player = player
        self.image = get_image(player.color, "Meeple")
        self.rect = self.image.get_rect(center=pos)
        
    def render(self, screen, is_gardener):
        if is_gardener:
            screen.blit(self.image, self.rect)
        else:
            pygame.draw.circle(screen, self.player.color, self.position, 15)

    def get_info_state(self):
        return {
            'player': self.player,
            'position': self.rect.center
        }
