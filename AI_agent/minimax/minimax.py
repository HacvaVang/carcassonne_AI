import logging
from AI_agent.MCTS.ulti import CarcassonneState, Action
import math

logger = logging.getLogger(__name__)

def minimax(state: CarcassonneState, depth, maximizing_player_index):
    """
    Minimax algorithm for Carcassonne.
    maximizing_player_index is the player whose score we want to maximize.
    """
    if depth == 0 or state.is_terminal():
        return state.get_score(maximizing_player_index)

    actions = state.get_possible_actions()

    if not actions:
        return state.get_score(maximizing_player_index)

    if state.current_player_index == maximizing_player_index:
        # Maximizing player's turn
        max_eval = -math.inf
        for action in actions:
            next_state = state.simulate_action(action)
            eval = minimax(next_state, depth - 1, maximizing_player_index)
            max_eval = max(max_eval, eval)
        return max_eval
    else:
        # Opponent's turn - assume they maximize their own score
        opponent_index = state.current_player_index
        max_eval = -math.inf
        for action in actions:
            next_state = state.simulate_action(action)
            eval = minimax(next_state, depth - 1, maximizing_player_index)
            max_eval = max(max_eval, eval)
        return max_eval

def get_best_action(state: CarcassonneState, depth, player_index):
    """
    Get the best action using minimax.
    """
    actions = state.get_possible_actions()
    if not actions:
        return None

    best_action = None
    best_value = -math.inf

    for action in actions:
        next_state = state.simulate_action(action)
        value = minimax(next_state, depth - 1, player_index)
        if value > best_value:
            best_value = value
            best_action = action

    logger.info(f"Minimax best action: {best_action}, value: {best_value}")
    return best_action