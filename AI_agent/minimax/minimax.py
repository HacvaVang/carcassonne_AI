from AI_agent.ulti import CarcassonneState, Action
import math
import time
import logging

logger = logging.getLogger(__name__)

def max_n(state: CarcassonneState, depth, metrics=None):
    """
    Max-N algorithm for N-player games. Returns a tuple of scores for all players.
    """
    if depth == 0:
        if metrics is not None:
            metrics['limit_depth_hits'] = metrics.get('limit_depth_hits', 0) + 1
        result = tuple(heuristic_score(state, i) for i in range(len(state.players)))
        # print(f"Max-N hit depth limit (0). Score: {result}")
        return result

    if state.is_terminal():
        result = tuple(state.get_score(i) for i in range(len(state.players)))
        # print(f"Max-N hit terminal state. Score: {result}")
        return result

    if metrics is not None:
        metrics['nodes_evaluated'] += 1

    actions = state.get_possible_actions()
    if not actions:
        return tuple(state.get_score(i) for i in range(len(state.players)))

    best_tuple = None
    player_idx = state.current_player_index

    for action in actions:
        print(f"Max-N action: {repr(action)}, depth: {depth}")
        next_state = state.simulate_action(action)
        eval_tuple = max_n(next_state, depth - 1, metrics)
        
        if best_tuple is None or eval_tuple[player_idx] > best_tuple[player_idx]:
            best_tuple = eval_tuple

    return best_tuple


def get_best_action(state: CarcassonneState, depth, player_index, seed=-1):
    """
    Get the best action using Max-N algorithm.
    """
    start_time = time.time()
    metrics = {'nodes_evaluated': 0}

    actions = state.get_possible_actions()
    if not actions:
        return None

    best_action : Action = None
    best_value = -math.inf

    for action in actions:
        next_state = state.simulate_action(action)
        metrics['nodes_evaluated'] += 1
        eval_tuple = max_n(next_state, depth - 1, metrics)
        value = eval_tuple[player_index]
        
        if value > best_value:
            best_value = value
            best_action = action

    duration = time.time() - start_time
    limit_hits = metrics.get('limit_depth_hits', 0)
    print(f"[DEBUG] Max-N evaluated {metrics['nodes_evaluated']} nodes in {duration:.2f} seconds (Depth: {depth}). Hit Depth Limit: {limit_hits} times. Best action {repr(best_action)}")
    return best_action

def heuristic_score(state: CarcassonneState, player_index):
    """
    Heuristic = committed score + expected region value + meeple flexibility bonus.

    Meeple flexibility:
      - Each free meeple is worth more early (more regions to claim)
      - Value tapers to 0 as the tile deck runs out
    Out-of-meeples penalty applies when the player is fully committed with no flexibility.
    """
    player = state.players[player_index]
    tiles_left = len(state.tile_deck.tiles) if hasattr(state.tile_deck, 'tiles') else 10
    game_progress = 1.0 - (tiles_left / max(71, 1))  # 0.0 = start, 1.0 = end

    heuristic_value = state.get_region_score(player_index)

    # Meeple flexibility: free meeples are most valuable early in the game
    # Each free meeple can be placed in a future region worth ~2 pts on average
    free_meeples = player.meeples
    flexibility_per_meeple = 2.0 * (1.0 - game_progress)  # tapers to 0 at end
    heuristic_value += free_meeples * flexibility_per_meeple

    # Hard penalty for being completely out of meeples
    if free_meeples <= 0:
        heuristic_value -= 3.0

    return state.get_score(player_index) + heuristic_value


def minimax(state: CarcassonneState, depth, maximizing_player_index, alpha=-math.inf, beta=math.inf):
    """
    Minimax algorithm with alpha-beta pruning for Carcassonne.
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
            eval = minimax(next_state, depth - 1, maximizing_player_index, alpha, beta)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        # Opponent's turn - assume they minimize our score
        min_eval = math.inf
        for action in actions:
            next_state = state.simulate_action(action)
            eval = minimax(next_state, depth - 1, maximizing_player_index, alpha, beta)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
