import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    """Handles world-to-screen coordinate transforms (pan + zoom)."""

    def __init__(self):
        self.pan_x = 0.0   # world-pixel offset added before zoom
        self.pan_y = 0.0
        self.zoom = 1.0
        self.zoom_min = 0.2
        self.zoom_max = 4.0
        self.pan_speed = 600  # world pixels per second

    # ------------------------------------------------------------------ #
    #  Coordinate transforms                                               #
    # ------------------------------------------------------------------ #

    def world_to_screen(self, wx, wy):
        """World pixel coords  →  screen pixel coords."""
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        sx = int(cx + (wx + self.pan_x) * self.zoom)
        sy = int(cy + (wy + self.pan_y) * self.zoom)
        return sx, sy

    def screen_to_world(self, sx, sy):
        """Screen pixel coords  →  world pixel coords."""
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        wx = (sx - cx) / self.zoom - self.pan_x
        wy = (sy - cy) / self.zoom - self.pan_y
        return wx, wy

    # ------------------------------------------------------------------ #
    #  Zoom                                                                #
    # ------------------------------------------------------------------ #

    def zoom_at(self, factor, pivot_screen):
        """Zoom in/out keeping the cursor's world position fixed."""
        px, py = pivot_screen
        wx, wy = self.screen_to_world(px, py)          # world pos of pivot

        self.zoom = max(self.zoom_min, min(self.zoom_max, self.zoom * factor))

        # Re-derive pan so the pivot world pos maps back to the same screen pos
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.pan_x = (px - cx) / self.zoom - wx
        self.pan_y = (py - cy) / self.zoom - wy

    # ------------------------------------------------------------------ #
    #  Update (WASD pan)                                                   #
    # ------------------------------------------------------------------ #

    def update(self, dt, keys):
        """Call every frame with the pygame key state and delta-time."""
        speed = self.pan_speed * dt / self.zoom   # constant apparent speed
        if keys[pygame.K_w]:
            self.pan_y += speed
        if keys[pygame.K_s]:
            self.pan_y -= speed
        if keys[pygame.K_a]:
            self.pan_x += speed
        if keys[pygame.K_d]:
            self.pan_x -= speed
