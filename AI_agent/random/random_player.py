import random
import copy
from AI_agent.ulti import CarcassonneState, Action
from src.player import Player

class RandomPlayer(Player):
    def __init__(self, name, color):
        super().__init__(name, color)

    def choose_action(self, game):
        if game.current_tile is None:
            return None
        state : CarcassonneState = CarcassonneState(game)
        actions = state.get_possible_actions()

        return random.choice(actions) if actions else None
