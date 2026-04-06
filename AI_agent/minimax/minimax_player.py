from src.player import Player
from AI_agent.minimax.minimax import get_best_action
from AI_agent.ulti import CarcassonneState, Action

class MinimaxPlayer(Player):
    def __init__(self, name, color, depth=4, seed=1, meeple_prob=0.5):
        super().__init__(name, color)
        self.depth = depth
        self.seed = seed
        self.meeple_prob = meeple_prob

    def choose_action(self, game):
        """Choose the best combined tile and meeple placement action using Monte Carlo Minimax."""
        state = CarcassonneState(game)
        player_index = game.players.index(self)
        action : Action = get_best_action(state, self.depth, player_index, meeple_prob=self.meeple_prob, seed=self.seed)
        return action

