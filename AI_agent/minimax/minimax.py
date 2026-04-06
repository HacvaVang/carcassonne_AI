import math
import time
import random
from AI_agent.ulti import CarcassonneState, Action, move_heuristic


def minimax_search(state: CarcassonneState, depth: int, root_idx: int, alpha: float, beta: float, config: dict) -> float:
    """
    Minimax search with heuristic evaluation and Alpha-Beta pruning.
    """
    if depth == 0 or state.is_terminal():
        return move_heuristic(state, Action(), root_idx)

    actions = state.get_possible_actions()
    if not actions:
        return move_heuristic(state, Action(), root_idx)

    meeple_prob = config.get('meeple_prob', 1.0)
    if meeple_prob < 1.0:
        filtered = []
        for a in actions:
            if a.meeple_pos is None or config['rng'].random() < meeple_prob:
                filtered.append(a)
        if filtered:
            actions = filtered

    curr_player = state.current_player_index
    if curr_player == root_idx:
        # Maximizing our own score differential
        val = -math.inf
        for a in actions:
            sim_state = state.simulate_action(a)
            val = max(val, minimax_search(sim_state, depth - 1, root_idx, alpha, beta, config))
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return val
    else:
        # Minimizing (assuming opponents want to reduce our score differential)
        val = math.inf
        for a in actions:
            sim_state = state.simulate_action(a)
            val = min(val, minimax_search(sim_state, depth - 1, root_idx, alpha, beta, config))
            beta = min(beta, val)
            if beta <= alpha:
                break
        return val


def get_best_action(state: CarcassonneState, depth: int, player_index: int, meeple_prob: float = 0.5, seed: int = 1) -> Action:
    """
    Hàm thực thi chính để tìm nước đi tốt nhất sử dụng Monte Carlo Minimax.
    """
    actions = state.get_possible_actions()
    if not actions:
        return None

    # Filter actions by meeple probability at root as well (Java-like behavior)
    rng = random.Random(seed)
    if meeple_prob < 1.0:
        filtered = [a for a in actions if a.meeple_pos is None or rng.random() < meeple_prob]
        if filtered: actions = filtered

    # Sort actions to improve alpha-beta pruning effectiveness
    actions.sort(key=lambda a: (a.meeple_pos is not None, a.rotation), reverse=True)

    # Heuristic depth limiting for performance
    if len(actions) > 80:
        actual_depth = depth - 2

    elif len(actions) > 40:
        actual_depth = depth - 1
    else:
        actual_depth = depth

    if actual_depth <= 0:
        actual_depth = 2
        

    best_action = None
    best_val = -math.inf

    print(f"\n[MINIMAX THINKING] Actions: {len(actions)} | Target Depth: {actual_depth}")
    start_time = time.time()

    config = {'rng': rng, 'meeple_prob': meeple_prob, 'seed': seed}

    for a in actions:
        # Simulation step
        val = minimax_search(state.simulate_action(a), actual_depth - 1, player_index, -math.inf, math.inf, config)

        if val > best_val:
            best_val = val
            best_action = a

    duration = time.time() - start_time
    m_info = f"{best_action.meeple_pos[0].name}({best_action.meeple_pos[1]})" if best_action.meeple_pos else "None"

    print(f"[DECISION] Time: {duration:.2f}s | Val: {best_val:.2f}")
    print(f"           Pos: {best_action.tile_pos} | Rot: {best_action.rotation} | Meeple: {m_info}")

    return best_action
