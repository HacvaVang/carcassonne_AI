import copy
from AI_agent.MCTS.ulti import Node, TreePolicy


def mcts_search(root_state, iterations, tree_policy_type=TreePolicy.UCT, exploration_const=1.414):
    """Performs MCTS search and returns the best action."""
    root_actions = root_state.get_possible_actions()
    if len(root_actions) == 0:
        return None
    if len(root_actions) == 1:
        return root_actions[0]

    root = Node(action=None, parent=None, unvisited_actions=root_actions, root_player_index=root_state.current_player_index)
    print(f"Starting MCTS search with {iterations} iterations, policy: {tree_policy_type}")

    import random
    for i in range(iterations):
        state = copy.deepcopy(root_state)
        
        # 1. Selection
        leaf : Node = root.tree_policy(state, tree_policy_type=tree_policy_type, exploration_const=exploration_const)

        # 2. Expansion
        if not leaf.is_fully_expanded():    
            action = leaf.unvisited_actions.pop()
            state.apply_action(action)
            child_actions = state.get_possible_actions() if not state.is_terminal() else []
            child = Node(action=action, parent=leaf, unvisited_actions=child_actions)
            leaf.children.append(child)
            leaf = child

        # 3. Simulation (Rollout)
        from AI_agent.MCTS.ulti import meeple_policy
        while not state.is_terminal():
            actions = state.get_possible_actions()
            if not actions:
                break
            action = meeple_policy(state, actions)
            state.apply_action(action)
            
        state.assignPointsAtEndOfGame()
        player_scores = [state.get_score(idx) for idx in range(len(state.players))]
        value = player_scores[root.root_player_index]
        if len(state.players) > 1:
            opponent_max_score = max(
                player_scores[idx]
                for idx in range(len(state.players))
                if idx != root.root_player_index
            )
        else:
            opponent_max_score = 0
            
        score_diff = value - opponent_max_score

        # 4. Backpropagation
        leaf.backpropagate(score_diff)

        if (i + 1) % 10 == 0:
            print(f"MCTS iteration {i+1}/{iterations} completed")

    # Return the best action (most visited child is most robust)
    if root.children:
        # Use most-visited child as the final policy (more robust than max avg value)
        best_child = max(root.children, key=lambda c: c.visits)
        avg_val = best_child.value / best_child.visits if best_child.visits else 0
        print(f"MCTS search completed. Best action: {best_child.action}, visits: {best_child.visits}, avg value: {avg_val:.2f}")
        return best_child.action
    else:
        print("No actions found in MCTS search")
        return None

def random_policy(actions):
    """Random policy for selecting actions during rollout."""
    import random
    return random.choice(actions) if actions else None