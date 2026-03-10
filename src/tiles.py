import os
from unittest import case
from settings import *
from src.assetloader import *


class Tile:
    def __init__(self, tile_type):
        self.tile_type = tile_type
        self.image = get_image(tile_type, "Tile")
        self.edges = list()
        self.shield = False
        self.region = dict()

        self.rotate_count = 0
        self.set_tileinfo()
    
    def rotation_update(self, pos):
        if pos != 8:
            pos = (pos + 2) % 8
        return pos

    def rotate(self):
        self.rotate_count = (self.rotate_count + 1) % 4
        self.edges = self.edges[-1:] + self.edges[:-1]
        
        for key, value in list(self.region.items()):
            self.region[key] = [[self.rotation_update(pos) for pos in group] for group in value]

    def render(self, screen, pos, not_place=False):
        image = self.image
        tw, th = image.get_width(), image.get_height()
        new_pos = (
            SCREEN_WIDTH // 2 + pos[0] * tw,
            SCREEN_HEIGHT // 2 + pos[1] * th,
        )
        rotated_image = pygame.transform.rotate(image, - 90 * self.rotate_count)
        if not_place:
            rotated_image.set_alpha(100)  # make it semi-transparent
        screen.blit(rotated_image, new_pos)
        

    def set_tileinfo(self):
        match self.tile_type:
            case 'A':
                self.edges = [Terrain.Grass, Terrain.Grass, Terrain.Road, Terrain.Grass]
                self.region = {
                    Terrain.Grass : [[0, 1, 2, 3, 4, 5, 6, 7]],
                    Terrain.Monastery : [[8]],
                    Terrain.Road : [[8, 5]]
                }
                
            case 'B':
                self.edges = [Terrain.Grass, Terrain.Grass, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.Grass : [[0, 1, 2, 3, 4, 5, 6, 7]],
                    Terrain.Monastery : [[8]],
                }
            case 'C':
                self.edges = [Terrain.City, Terrain.City, Terrain.City, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 5, 7]],
                }
                self.shield = True
            case 'D':
                self.edges = [Terrain.City, Terrain.Road, Terrain.Grass, Terrain.Road]
                self.region = {
                    Terrain.Road : [[3, 7]],
                    Terrain.City : [[1]],
                    Terrain.Grass : [[0, 2], [4, 5, 6]],
                }
            case 'E':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[0, 2, 3, 4, 5, 6 ,7]]
                }
            case 'F':
                self.edges = [Terrain.Grass, Terrain.City, Terrain.Grass, Terrain.City]
                self.shield = True
                self.region = {
                    Terrain.City : [[3, 7]],
                    Terrain.Grass : [[0, 1, 2], [4, 5, 6]],
                }
            case 'G':
                self.edges = [Terrain.Grass, Terrain.City, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[3, 7]],
                    Terrain.Grass : [[0, 1, 2], [4, 5, 6]],
                }

            case 'H':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.City, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1], [5]],
                    Terrain.Grass : [[0, 2, 3, 4, 6, 7]],
                }
            case 'I':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[1], [7]],
                    Terrain.Grass : [[0, 2, 3, 4, 5, 6]],
                }
            case 'J': 
                self.edges = [Terrain.City, Terrain.Road, Terrain.Road, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[0, 2, 6, 7], [4]],
                    Terrain.Road : [[3, 5]]
                }
            case 'K':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[0, 2, 3, 4], [6]],
                    Terrain.Road : [[5, 7]]
                }
            case 'L':
                self.edges = [Terrain.City, Terrain.Road, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[0, 2], [4], [6]],
                    Terrain.Road : [[5, 8], [7, 8], [3, 8]]
                }

            case 'M':
                self.edges = [Terrain.City, Terrain.City, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1, 3]],
                    Terrain.Grass : [[0, 4, 5, 6, 7]],
                }
                self.shield = True

            case 'N':
                self.edges = [Terrain.City, Terrain.City, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1, 3]],
                    Terrain.Grass : [[0, 4, 5, 6, 7]],
                }

            case 'O':
                self.edges = [Terrain.City, Terrain.Road, Terrain.Road, Terrain.City]
                self.region = {
                    Terrain.City : [[7, 1]],
                    Terrain.Grass : [[2, 6], [4]],
                    Terrain.Road : [[5, 3]]
                }
                self.shield = True

            case 'P':
                self.edges = [Terrain.City, Terrain.Road, Terrain.Road, Terrain.City]
                self.region = {
                    Terrain.City : [[7, 1]],
                    Terrain.Grass : [[2, 6], [4]],
                    Terrain.Road : [[5, 3]]
                }

            case 'Q':
                self.edges = [Terrain.City, Terrain.City, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 7]],
                    Terrain.Grass : [[4, 5, 6]],
                }
                self.shield = True

            case 'R':
                self.edges = [Terrain.City, Terrain.City, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 7]],
                    Terrain.Grass : [[4, 5, 6]],
                }

            case 'S':
                self.edges = [Terrain.City, Terrain.City, Terrain.Road, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 7]],
                    Terrain.Grass : [[4], [6]],
                    Terrain.Road : [[5, 8]]
                }
                self.shield = True

            case 'T':
                self.edges = [Terrain.City, Terrain.City, Terrain.Road, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 7]],
                    Terrain.Grass : [[4], [6]],
                    Terrain.Road : [[5, 8]]
                }

            case 'U':
                self.edges = [Terrain.Road, Terrain.Grass, Terrain.Road, Terrain.Grass]
                self.region = {
                    Terrain.Grass : [[0, 7, 6], [2, 3, 4]],
                    Terrain.Road : [[5, 1]]
                }

            case 'V':
                self.edges = [Terrain.Grass, Terrain.Grass, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.Grass : [[6], [0, 1, 2, 3, 4]],
                    Terrain.Road : [[5, 7]]
                }

            case 'W':
                self.edges = [Terrain.Grass, Terrain.Road, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.Grass : [[0, 1, 2], [4], [6]],
                    Terrain.Road : [[5, 8], [3, 8], [7, 8]]
                }
            case 'X':
                self.edges = [Terrain.Road, Terrain.Road, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.Grass : [[0], [2], [4], [6]],
                    Terrain.Road : [[5, 8], [3, 8], [7, 8], [1, 8]]
                }


