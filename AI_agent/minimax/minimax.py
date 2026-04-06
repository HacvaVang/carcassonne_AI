<<<<<<< Updated upstream
=======
from AI_agent.MCTS.ulti import CarcassonneState, Action
>>>>>>> Stashed changes
import math
import time
from AI_agent.ulti import CarcassonneState, Action, move_heuristic


def max_n(state: CarcassonneState, depth: int, root_idx: int, alpha: float, beta: float) -> float:
    """
    Thuật toán Minimax với cắt tỉa Alpha-Beta dành cho game nhiều người chơi.
    Tính toán dựa trên góc nhìn của root_idx (AI).
    """
<<<<<<< Updated upstream
    # 1. Điều kiện dừng: Đạt độ sâu tối đa hoặc game kết thúc
    if depth == 0 or state.is_terminal():
        return move_heuristic(state, Action(), root_idx)
=======
    if depth == 0:
        if metrics is not None:
            metrics['limit_depth_hits'] = metrics.get('limit_depth_hits', 0) + 1
        result = tuple(heuristic_score(state, i) for i in range(len(state.players)))
        return result

    if state.is_terminal():
        result = tuple(state.get_score(i) for i in range(len(state.players)))
        return result

    if metrics is not None:
        metrics['nodes_evaluated'] += 1
>>>>>>> Stashed changes

    actions = state.get_possible_actions()
    if not actions:
        return move_heuristic(state, Action(), root_idx)

<<<<<<< Updated upstream
    curr_player = state.current_player_index

    # 2. Lượt của AI (Maximizing Player)
    if curr_player == root_idx:
        val = -math.inf
        for a in actions:
            # Giả lập nước đi và đệ quy
            sim_state = state.simulate_action(a)
            val = max(val, max_n(sim_state, depth - 1, root_idx, alpha, beta))
            alpha = max(alpha, val)
            if beta <= alpha:
                break  # Cắt tỉa Beta
        return val
=======
    best_tuple = None
    player_idx = state.current_player_index
    best_diff = -math.inf

    for action in actions:
        next_state = state.simulate_action(action)
        eval_tuple = max_n(next_state, depth - 1, metrics)
        
        # Evaluate by score differential
        my_score = eval_tuple[player_idx]
        best_opponent_score = max([eval_tuple[i] for i in range(len(eval_tuple)) if i != player_idx]) if len(eval_tuple) > 1 else 0
        diff = my_score - best_opponent_score
        
        if best_tuple is None or diff > best_diff:
            best_tuple = eval_tuple
            best_diff = diff
>>>>>>> Stashed changes

    # 3. Lượt của đối thủ (Minimizing Player)
    else:
        val = math.inf
        for a in actions:
            sim_state = state.simulate_action(a)
            val = min(val, max_n(sim_state, depth - 1, root_idx, alpha, beta))
            beta = min(beta, val)
            if beta <= alpha:
                break  # Cắt tỉa Alpha
        return val


def get_best_action(state: CarcassonneState, depth: int, player_index: int) -> Action:
    """
<<<<<<< Updated upstream
    Hàm thực thi chính để tìm nước đi tốt nhất.
    """
=======
    Get the best action using Max-N algorithm focusing on Score Differential.
    """
    start_time = time.time()
    metrics = {'nodes_evaluated': 0}

    # Optionally rank actions (e.g., prioritize meeple placements) to traverse better paths first
>>>>>>> Stashed changes
    actions = state.get_possible_actions()
    actions.sort(key=lambda a: (a.meeple_pos is not None, a.rotation), reverse=True)
    
    if not actions:
        return None

    # Tối ưu Depth dựa trên số lượng nước đi để tránh treo máy
    actual_depth = depth
    if len(actions) > 40:
        actual_depth = 1
    elif len(actions) > 20:
        actual_depth = 2

<<<<<<< Updated upstream
    best_action = None
    best_val = -math.inf
=======
    for action in actions:
        next_state = state.simulate_action(action)
        metrics['nodes_evaluated'] += 1
        eval_tuple = max_n(next_state, depth - 1, metrics)
        
        # Emphasize score differential!
        my_score = eval_tuple[player_index]
        best_opponent_score = max([eval_tuple[i] for i in range(len(eval_tuple)) if i != player_index]) if len(eval_tuple) > 1 else 0
        value = my_score - best_opponent_score
        
        if value > best_value:
            best_value = value
            best_action = action
>>>>>>> Stashed changes

    print(f"\n[MINIMAX THINKING] Actions: {len(actions)} | Target Depth: {actual_depth}")
    start_time = time.time()

    # Sắp xếp actions: Ưu tiên tính toán các nước đi có Meeple trước (Heuristic search)
    # Điều này giúp Alpha-Beta cắt tỉa hiệu quả hơn
    actions.sort(key=lambda a: a.meeple_pos is not None, reverse=True)

    for a in actions:
        # Tính toán giá trị nước đi bằng Max-N
        val = max_n(state.simulate_action(a), actual_depth - 1, player_index, -math.inf, math.inf)

        # Chiến thuật Tie-breaking: 
        # Nếu điểm bằng nhau, ưu tiên nước đi có Meeple (để chiếm đất sớm)
        is_better = val > best_val
        is_equal_but_meeple = (val == best_val and best_action and
                               best_action.meeple_pos is None and a.meeple_pos is not None)

        if is_better or is_equal_but_meeple:
            best_val = val
            best_action = a

    end_time = time.time()
    duration = end_time - start_time

    # Debug kết quả ra Console
    m_info = "None"
    if best_action.meeple_pos:
        terrain, idx = best_action.meeple_pos
        m_info = f"{terrain.name}({idx})"

    print(f"[DECISION] Time: {duration:.2f}s | Score: {best_val:.2f}")
    print(f"           Pos: {best_action.tile_pos} | Rot: {best_action.rotation} | Meeple: {m_info}")

<<<<<<< Updated upstream
    return best_action
=======
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
>>>>>>> Stashed changes
