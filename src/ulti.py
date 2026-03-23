from settings import *

class FullMove:
    def __init__(self, pos, rotation):
        self.pos = pos
        self.rotation = rotation
        self.place_meeple = None
        

class Terrain(Enum):
    Grass = 1
    Road = 2
    City = 3
    Monastery = 4 

class GamePhase(Enum):
    PlaceTile = 1
    PlaceMeeple = 2

class Neighbor():
    render_pos = {
        0 : (0.25, 0.25),
        1 : (0.5, 0.1),
        2 : (0.75, 0.25),
        3 : (0.9, 0.5),
        4 : (0.75, 0.75),
        5 : (0.5, 0.9),
        6 : (0.25, 0.75),
        7 : (0.1, 0.5),
        8 : (0.5, 0.5),
    }
    
    direction_mask = {
        0 : 0b1001,
        1 : 0b0001,
        2 : 0b0011,
        3 : 0b0010,
        4 : 0b0110,
        5 : 0b0100,
        6 : 0b1100,
        7 : 0b1000,
        8 : 0b0000,
    }
    
    neighbor = {
            1 : (0, -1),
            3 : (1, 0),
            5 : (0, 1),
            7 : (-1, 0),
        }
    
    neighbor_region = {
        (0, -1) : [4, 5, 6],
        (1, 0)  : [6, 7, 0],
        (0, 1)  : [0, 1, 2],
        (-1, 0) : [2, 3, 4],        
    }

    @staticmethod
    def get_neighbor_pos(pos, directon):
        dx, dy = directon
        if dy == 0:
            pos = list(map(lambda x : (10 - x) % 8, pos))
        elif dx == 0:
            pos = list(map(lambda x : (6 - x) % 8, pos))
        result = list(filter(
            lambda x : x in Neighbor.neighbor_region[directon], pos
        ))
        return result

class Color():
    color = {
        'red'       : (200, 0, 0),
        'blue'      : (0, 0, 200),
        'green'     : (0, 200, 0),
        'yellow'    : (200, 200, 0),
        'black'     : (0, 0 ,0) 
    }
