from src.player import Player
from AI_agent.minimax.minimax import get_best_action
from AI_agent.ulti import CarcassonneState, Action

class MinimaxPlayer(Player):
    def __init__(self, name, color, depth=2, seed=1):
        super().__init__(name, color)
        self.depth = depth
        self.seed = seed

    def choose_action(self, game):
        """Choose the best combined tile and meeple placement action using Max-N."""
        state = CarcassonneState(game)
        player_index = game.players.index(self)
        action : Action = get_best_action(state, self.depth, player_index, self.seed)
        return action

