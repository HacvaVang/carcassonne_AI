from src.player import Player
from AI_agent.MCTS.search import mcts_search
from AI_agent.ulti import CarcassonneState, Action

class MCTSPlayer(Player):
    def __init__(self, name, color, iterations=1000):
        super().__init__(name, color)
        self.iterations = iterations

    def choose_tile_action(self, game):
        """Choose the best tile placement action using MCTS."""
        state = CarcassonneState(game)
        action = mcts_search(state, self.iterations)
        return action

    def choose_meeple_action(self, game):
        """For now, always skip meeple placement."""
        return Action(meeple_pos=None)