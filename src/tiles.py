from src.assetloader import *
from src.ulti import Terrain

class Tile:
    def __init__(self, tile_type = None):
        self.tile_type = tile_type
        self.image = get_image(tile_type, "Tile")
        self.shield = False
        self.region = dict()
        self.edges = list()
        self.adjency = list()
        
        self.rotate_count = 0
        self.rotate_max = 3
        self.set_tileinfo()
    
    def rotation_update(self, pos):
        if pos != 8:
            pos = (pos + 2) % 8
        return pos

    def rotate(self):
        self.rotate_count += 1
        if self.rotate_count > self.rotate_max:
            self.rotate_count = 0
            
        self.edges = self.edges[-1:] + self.edges[:-1]
        
        for key, value in list(self.region.items()):
            self.region[key] = [[self.rotation_update(pos) for pos in group] for group in value]

    def __getstate__(self):
        state = self.__dict__.copy()
        state['image'] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def render(self, screen, pos, camera=None, not_place=False):
        image = self.image
        tw, th = image.get_width(), image.get_height()
        world_x = pos[0] * tw
        world_y = pos[1] * th

        if camera:
            sx, sy = camera.world_to_screen(world_x, world_y)
            draw_w = max(1, int(tw * camera.zoom))
            draw_h = max(1, int(th * camera.zoom))
        else:
            sx = SCREEN_WIDTH // 2 + world_x
            sy = SCREEN_HEIGHT // 2 + world_y
            draw_w, draw_h = tw, th

        if not self.tile_type:
            placeholder = get_image("0", "Tile")
            if draw_w != tw or draw_h != th:
                placeholder = pygame.transform.scale(placeholder, (draw_w, draw_h))
            screen.blit(placeholder, (sx, sy))
            return

        rotated_image = pygame.transform.rotate(image, -90 * self.rotate_count)
        if draw_w != tw or draw_h != th:
            rotated_image = pygame.transform.scale(rotated_image, (draw_w, draw_h))
        if not_place:
            rotated_image.set_alpha(100)
        screen.blit(rotated_image, (sx, sy))
        

    def set_tileinfo(self):
        match self.tile_type:
            case 'A':
                self.edges = [Terrain.Grass, Terrain.Grass, Terrain.Road, Terrain.Grass]
                self.region = {
                    Terrain.Grass : [[0, 1, 2, 3, 4, 5, 6, 7]],
                    Terrain.Monastery : [[8]],
                    Terrain.Road : [[5, 8]]
                }
                
            case 'B':
                self.edges = [Terrain.Grass, Terrain.Grass, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.Grass : [[0, 1, 2, 3, 4, 5, 6, 7]],
                    Terrain.Monastery : [[8]],
                }
                self.rotate_max = 0

            case 'C':
                self.edges = [Terrain.City, Terrain.City, Terrain.City, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 5, 7]],
                }
                self.shield = True
                self.rotate_max = 0

            case 'D':
                self.edges = [Terrain.City, Terrain.Road, Terrain.Grass, Terrain.Road]
                self.region = {
                    Terrain.Road : [[3, 7]],
                    Terrain.City : [[1]],
                    Terrain.Grass : [[0, 2], [5, 6, 4]],
                }
            case 'E':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[5, 0, 2, 3, 4, 6 ,7]]
                }

            case 'F':
                self.edges = [Terrain.Grass, Terrain.City, Terrain.Grass, Terrain.City]
                self.shield = True
                self.region = {
                    Terrain.City : [[3, 7]],
                    Terrain.Grass : [[1, 0,  2], [5, 4, 6]],
                }
                self.rotate_max = 1

            case 'G':
                self.edges = [Terrain.Grass, Terrain.City, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[3, 7]],
                    Terrain.Grass : [[1, 0,  2], [5, 4, 6]],
                }
                self.rotate_max = 1

            case 'H':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.City, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1], [5]],
                    Terrain.Grass : [[3, 0, 2,  4, 6, 7]],
                }
                self.rotate_max = 1
            case 'I':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[1], [7]],
                    Terrain.Grass : [[4, 0, 2, 3, 5, 6]],
                }
            case 'J': 
                self.edges = [Terrain.City, Terrain.Road, Terrain.Road, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[7, 0, 2, 6], [4]],
                    Terrain.Road : [[3, 5]]
                }
            case 'K':
                self.edges = [Terrain.City, Terrain.Grass, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.City : [[1]],
                    Terrain.Grass : [[3, 0, 2, 4], [6]],
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
                    Terrain.Grass : [[6, 0, 4, 5,  7]],
                }
                self.shield = True

            case 'N':
                self.edges = [Terrain.City, Terrain.City, Terrain.Grass, Terrain.Grass]
                self.region = {
                    Terrain.City : [[1, 3]],
                    Terrain.Grass : [[6, 0, 4, 5, 7]],
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
                    Terrain.Grass : [[5, 4, 6]],
                }
                self.shield = True

            case 'R':
                self.edges = [Terrain.City, Terrain.City, Terrain.Grass, Terrain.City]
                self.region = {
                    Terrain.City : [[1, 3, 7]],
                    Terrain.Grass : [[5, 4, 6]],
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
                    Terrain.Grass : [[7, 0,  6], [3, 2, 4]],
                    Terrain.Road : [[5, 1]]
                }
                self.rotate_max = 1

            case 'V':
                self.edges = [Terrain.Grass, Terrain.Grass, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.Grass : [[6], [ 2, 0, 1, 3, 4]],
                    Terrain.Road : [[5, 7]]
                }

            case 'W':
                self.edges = [Terrain.Grass, Terrain.Road, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.Grass : [[1, 0, 2], [4], [6]],
                    Terrain.Road : [[5, 8], [3, 8], [7, 8]]
                }
            case 'X':
                self.edges = [Terrain.Road, Terrain.Road, Terrain.Road, Terrain.Road]
                self.region = {
                    Terrain.Grass : [[0], [2], [4], [6]],
                    Terrain.Road : [[5, 8], [3, 8], [7, 8], [1, 8]]
                }
                self.rotate_max = 0


