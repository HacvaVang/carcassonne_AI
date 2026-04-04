from src.player import Player
from AI_agent.MCTS.search import mcts_search
from AI_agent.ulti import CarcassonneState, Action

class MCTSPlayer(Player):
    def __init__(self, name, color, iterations=250):
        super().__init__(name, color)
        self.iterations = iterations

    def choose_action(self, game):
        """Choose the best action using MCTS for the current phase."""
        state = CarcassonneState(game)
        action = mcts_search(state, self.iterations)
        return action