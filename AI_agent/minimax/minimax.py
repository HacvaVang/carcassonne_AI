from AI_agent.ulti import CarcassonneState, Action
import math
import time
import logging

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# HEURISTIC
# -------------------------------------------------------

def heuristic_score(state: CarcassonneState, player_index: int) -> float:
    """
    Heuristic = pending region score + meeple flexibility bonus.

    NOTE: We do NOT add state.get_score() here to avoid double-counting
    with the caller (get_best_action / max_n at depth-0 both use this).
    The committed score is already reflected via get_region_score which
    includes completed-feature points tracked by the state.

    Meeple flexibility:
      - Each free meeple is worth more early (more regions to claim)
      - Value tapers to 0 as the tile deck runs out
    """
    player = state.players[player_index]

    # Use dynamic total tiles from state if available, fall back to 72 (standard Carcassonne)
    total_tiles = getattr(state.tile_deck, 'total_tiles', 72)
    tiles_left = state.tile_deck.count if hasattr(state.tile_deck, 'count') else \
                 len(state.tile_deck.tiles) if hasattr(state.tile_deck, 'tiles') else total_tiles

    game_progress = 1.0 - (tiles_left / max(total_tiles, 1))  # 0.0 = start, 1.0 = end

    # Pending value from regions the player currently has meeples in
    region_value = state.get_region_score(player_index)

    # Meeple flexibility: free meeples can still be placed in future regions
    free_meeples = player.meeples
    flexibility_per_meeple = 2.0 * (1.0 - game_progress)  # tapers to 0 at end
    flexibility_bonus = free_meeples * flexibility_per_meeple

    # Penalty for being completely out of meeples
    out_of_meeples_penalty = 3.0 if free_meeples <= 0 else 0.0

    return region_value + flexibility_bonus - out_of_meeples_penalty


# -------------------------------------------------------
# EVALUATION  (mirrors MCTS score_diff logic)
# -------------------------------------------------------

def evaluate_terminal(state: CarcassonneState, player_index: int) -> float:
    """
    Call assignPointsAtEndOfGame first (same as MCTS does before reading scores),
    then return score_diff = our_score - best_opponent_score.
    """
    state.assignPointsAtEndOfGame()
    player_scores = [state.get_score(i) for i in range(len(state.players))]
    our_score = player_scores[player_index]
    if len(state.players) > 1:
        opponent_best = max(
            player_scores[i] for i in range(len(state.players)) if i != player_index
        )
    else:
        opponent_best = 0
    return our_score - opponent_best


def evaluate_heuristic(state: CarcassonneState, player_index: int) -> float:
    """
    Non-terminal evaluation: score_diff using committed scores + heuristic bonus.
    Mirrors the terminal form so depth-0 and terminal are consistent.
    """
    player_scores = [state.get_score(i) + heuristic_score(state, i)
                     for i in range(len(state.players))]
    our_score = player_scores[player_index]
    if len(state.players) > 1:
        opponent_best = max(
            player_scores[i] for i in range(len(state.players)) if i != player_index
        )
    else:
        opponent_best = 0
    return our_score - opponent_best


# -------------------------------------------------------
# MAX-N  (N-player)
# -------------------------------------------------------

def max_n(state: CarcassonneState, depth: int, root_player_index: int, metrics: dict = None):
    """
    Max-N algorithm for N-player games.
    Returns a scalar: score_diff from the root player's perspective.
    Each node maximises the CURRENT player's score_diff.
    """
    if state.is_terminal():
        if metrics is not None:
            metrics['terminal_hits'] = metrics.get('terminal_hits', 0) + 1
        return evaluate_terminal(state, root_player_index)

    if depth == 0:
        if metrics is not None:
            metrics['limit_depth_hits'] = metrics.get('limit_depth_hits', 0) + 1
        return evaluate_heuristic(state, root_player_index)

    if metrics is not None:
        metrics['nodes_evaluated'] = metrics.get('nodes_evaluated', 0) + 1

    actions = state.get_possible_actions()
    if not actions:
        return evaluate_heuristic(state, root_player_index)

    current_player = state.current_player_index
    best_value = -math.inf

    for action in actions:
        next_state = state.simulate_action(action)
        value = max_n(next_state, depth - 1, root_player_index, metrics)

        # Each player maximises their own perspective.
        # For the root player: maximise score_diff directly.
        # For opponents: they maximise THEIR score_diff, which means minimising ours.
        if current_player == root_player_index:
            if value > best_value:
                best_value = value
        else:
            # Opponent maximises their own score → minimises root player's diff
            if best_value == -math.inf or value < best_value:
                best_value = value

    return best_value


# -------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------

def get_best_action(state: CarcassonneState, depth: int, player_index: int, seed: int = -1) -> Action:
    """
    Get the best action using Max-N algorithm.
    Returns the action that maximises the root player's score_diff.
    """
    start_time = time.time()
    metrics = {'nodes_evaluated': 0}

    actions = state.get_possible_actions()
    if not actions:
        return None
    if len(actions) == 1:
        return actions[0]

    best_action: Action = None
    best_value = -math.inf

    for action in actions:
        next_state = state.simulate_action(action)
        metrics['nodes_evaluated'] += 1
        value = max_n(next_state, depth - 1, player_index, metrics)

        logger.debug("Action %s → value %.2f", repr(action), value)

        if value > best_value:
            best_value = value
            best_action = action

    duration = time.time() - start_time
    logger.info(
        "[Max-N] depth=%d | nodes=%d | terminal_hits=%d | depth_limit_hits=%d | "
        "time=%.2fs | best_value=%.2f | best_action=%s",
        depth,
        metrics.get('nodes_evaluated', 0),
        metrics.get('terminal_hits', 0),
        metrics.get('limit_depth_hits', 0),
        duration,
        best_value,
        repr(best_action),
    )
    return best_action