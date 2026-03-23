from src.player import Player
from AI_agent.minimax.minimax import get_best_action
from AI_agent.MCTS.ulti import CarcassonneState, Action

class MinimaxPlayer(Player):
    def __init__(self, name, color, depth=3):
        super().__init__(name, color)
        self.depth = depth

    def choose_tile_action(self, game):
        """Choose the best tile placement action using Minimax."""
        state = CarcassonneState(game)
        player_index = game.players.index(self)
        action = get_best_action(state, self.depth, player_index)
        return action

    def choose_meeple_action(self, game):
        """For now, always skip meeple placement."""
        return Action(meeple_pos=None)