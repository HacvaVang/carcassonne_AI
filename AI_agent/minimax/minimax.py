import math
import time
from AI_agent.ulti import CarcassonneState, Action, move_heuristic


def max_n(state: CarcassonneState, depth: int, root_idx: int, alpha: float, beta: float) -> float:
    """
    Thuật toán Minimax với cắt tỉa Alpha-Beta dành cho game nhiều người chơi.
    Tính toán dựa trên góc nhìn của root_idx (AI).
    """
    # 1. Điều kiện dừng: Đạt độ sâu tối đa hoặc game kết thúc
    if depth == 0 or state.is_terminal():
        return move_heuristic(state, Action(), root_idx)

    actions = state.get_possible_actions()
    if not actions:
        return move_heuristic(state, Action(), root_idx)

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
    Hàm thực thi chính để tìm nước đi tốt nhất.
    """
    actions = state.get_possible_actions()
    if not actions:
        return None

    # Tối ưu Depth dựa trên số lượng nước đi để tránh treo máy
    actual_depth = depth
    if len(actions) > 40:
        actual_depth = 1
    elif len(actions) > 20:
        actual_depth = 2

    best_action = None
    best_val = -math.inf

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

    return best_action