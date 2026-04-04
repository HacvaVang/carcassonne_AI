import copy
from AI_agent.MCTS.ulti import Node

def mcts_search(root_state, iterations):
    """Performs MCTS search and returns the best action."""
    root = Node(root_state, root_player_index=root_state.current_player_index)
    print(f"Starting MCTS search with {iterations} iterations")

    for i in range(iterations):
        # Selection
        leaf = root.select()

        # Expansion
        if not leaf.state.is_terminal():
            expanded = leaf.expand()
            if expanded is not None:
                leaf = expanded

        # Simulation (Rollout)
        value = leaf.rollout()

        # Backpropagation
        leaf.backpropagate(value)

        if (i + 1) % 100 == 0:
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