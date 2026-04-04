import pygame
from enum import Enum
import os
from functools import reduce

DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

    
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

filepath  = ""


def get_path(relative_path):
    return os.path.join(ASSETS_DIR, relative_path)

def resize_font(default_font_size):
    return int(rezise(default_font_size))

def rezise(size):
    return size / DEFAULT_SCREEN_WIDTH * SCREEN_WIDTH

def resize_assets(original_size):
    width, height = original_size
    width = width / DEFAULT_SCREEN_WIDTH * SCREEN_WIDTH
    height = height / DEFAULT_SCREEN_HEIGHT * SCREEN_HEIGHT
    return width, height

def get_grid_position(mouse_pos, image, camera=None):
    tw, th = image.get_width(), image.get_height()
    if camera:
        wx, wy = camera.screen_to_world(mouse_pos[0], mouse_pos[1])
        return (int(wx // tw), int(wy // th))
    mouse_x, mouse_y = mouse_pos
    return (
        (mouse_x - SCREEN_WIDTH // 2) // tw,
        (mouse_y - SCREEN_HEIGHT // 2) // th,
    )