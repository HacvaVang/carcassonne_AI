import random
import copy
from src.player import Player
from AI_agent.MCTS.ulti import Action

class RandomPlayer(Player):
    def __init__(self, name, color):
        super().__init__(name, color)

    def choose_tile_action(self, game):
        if game.current_tile is None:
            return None

        actions = []
        for rot in range(4):
            tile_copy = copy.deepcopy(game.current_tile)
            for _ in range(rot):
                tile_copy.rotate()
            places = game.map.get_placeable_positon(tile_copy)
            for pos in places:
                actions.append(Action(tile_pos=pos, rotation=rot))

        return random.choice(actions) if actions else None

    def choose_meeple_action(self, game):
        return Action(meeple_pos=None)
