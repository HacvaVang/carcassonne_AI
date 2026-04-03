import logging
import copy
from AI_agent.MCTS.ulti import *

# Initialize logger
logger = logging.getLogger(__name__)

def mcts_search(root_state, iterations=1000):
    """Performs MCTS search and returns the best action."""
    root = Node(root_state)
    print(f"Starting MCTS search with {iterations} iterations")

    for i in range(iterations):
        # Selection
        leaf = root.select()

        # Expansion
        if not leaf.get_state().is_terminal():
            leaf = leaf.expand()
            if leaf is None:
                continue

        # Simulation (Rollout)
        value = leaf.rollout()

        # Backpropagation
        leaf.backpropagate(value)

        if (i + 1) % 100 == 0:
            print(f"MCTS iteration {i+1}/{iterations} completed")

    # Return the best action
    if root.children:
        best_child = max(root.children, key=lambda c: c.visits)
        print(f"MCTS search completed. Best action: {best_child.action}, visits: {best_child.visits}")
        return best_child.action
    else:
        print("No actions found in MCTS search")
        return None

def random_policy(actions):
    """Random policy for selecting actions during rollout."""
    return random.choice(actions) if actions else None