from settings import *
from src.assetloader import *
from src.player import Player
from src.ulti import Color

class Meeple:
    def __init__(self, player : Player, pos : tuple, is_simulation=False):
        self.player = player
        self.pos = pos
        # Only load image assets for real-game meeples (not AI simulation copies)
        if not is_simulation:
            self.image = get_image(player.color, "Meeple")
        else:
            self.image = None

    def render(self, screen, is_gardener, camera=None):
        wx, wy = self.pos
        if camera:
            sx, sy = camera.world_to_screen(wx, wy)
            zoom = camera.zoom
        else:
            sx = int(wx) + SCREEN_WIDTH // 2
            sy = int(wy) + SCREEN_HEIGHT // 2
            zoom = 1.0

        if self.image is not None:
            # Scale the meeple image with camera zoom
            base_w = self.image.get_width()
            base_h = self.image.get_height()
            draw_w = max(1, int(base_w * zoom))
            draw_h = max(1, int(base_h * zoom))
            scaled = pygame.transform.scale(self.image, (draw_w, draw_h))
            rect = scaled.get_rect(center=(sx, sy))
            screen.blit(scaled, rect)
        else:
            # Fallback circle — resolve color string → RGB tuple safely
            raw = self.player.color
            rgb = Color.color.get(raw, (200, 200, 200)) if isinstance(raw, str) else raw
            pygame.draw.circle(screen, rgb, (int(sx), int(sy)),
                               max(5, int(15 * zoom)))

    def get_info_state(self):
        return {
            'player': self.player,
            'pos': self.pos,
        }

    def __getstate__(self):
        state = self.__dict__.copy()
        state['image'] = None   # pygame Surfaces can't be pickled / deep-copied
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
