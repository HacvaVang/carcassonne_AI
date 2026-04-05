import math
import random
import copy
import heapq
from ..ulti import CarcassonneState, Action
from src import GamePhase
from enum import Enum


class TreePolicy(Enum):
    UCT = 1
    HEURISTIC = 2

def get_meeple_placement_probability(state):
    """Calculate dynamic meeple placement probability."""
    player = state.get_current_player()
    if player.meeples <= 0:
        return 0.0
        
    tiles_remaining = state.tile_deck.count

    if player.meeples >= tiles_remaining:
        return 1.0

    # Game progress from 0.0 (start) to 1.0 (end)
    progress = min(1.0, 1.0 - (tiles_remaining / 36.0))
    
    # Assume 7 standard meeples per player
    meeple_ratio = player.meeples / 7.0
    
    # Base 10%, plus up to 50% from having many meeples, plus up to 40% from game ending soon
    prob = 0.1 + (0.5 * meeple_ratio) + (0.4 * progress)
    return prob

def meeple_policy(state, actions):
    """Place meeple policy with a dynamically computed probability."""
    if not actions:
        return None
    
    prob = get_meeple_placement_probability(state)
    
    meeple_actions = [a for a in actions if getattr(a, 'meeple_pos', None) is not None]
    no_meeple_actions = [a for a in actions if getattr(a, 'meeple_pos', None) is None]

    if meeple_actions and no_meeple_actions:
        if random.random() < prob:
            return random.choice(meeple_actions)
        else:
            return random.choice(no_meeple_actions)
            
    return random.choice(actions)


class Node:
    def __init__(self, action=None, parent=None, unvisited_actions=None, root_player_index=0):
        self.parent : Node = parent
        self.children : list[Node] = list()
        self.children_heap = [] # List of (-uct_score, node)
        self.visits = 0
        self.value = 0  # total value (always from root player's perspective)
        self.action = action  # The action that led to this node
        self.unvisited_actions = unvisited_actions if unvisited_actions is not None else []
        self.root_player_index = root_player_index
        self.last_heap_visits = -1 # Cache parent visits to detect stale heap scores

    # -------------------------------------------------------
    # TREE POLICY / SELECT PHASE
    # -------------------------------------------------------
    def tree_policy(self, state, tree_policy_type=TreePolicy.UCT, exploration_const=math.sqrt(2)):
        node = self
        while node.is_fully_expanded() and node.children:
            if tree_policy_type == TreePolicy.UCT:
                node = node.best_child_uct(c=exploration_const)
            elif tree_policy_type == TreePolicy.HEURISTIC:
                node = node.best_child_heuristic(state)
            else:
                print(f"Invalid tree policy type: {tree_policy_type}")
                import sys
                sys.exit(-1)
            state.apply_action(node.action)
        return node

    # -------------------------------------------------------
    # BACKPROPAGATE PHASE
    # -------------------------------------------------------
    def backpropagate(self, value):
        self.visits += 1
        self.value += value
        if self.parent:
            self.parent.backpropagate(value)
            
            
    def is_fully_expanded(self):
        return len(self.unvisited_actions) == 0

    def best_child_uct(self, c):
        if not self.children:
            return None

        # Re-calc and heapify if parent visits have changed (all child UCT scores depend on parent.visits)
        if self.visits != self.last_heap_visits:
            self.children_heap = []
            log_n = math.log(self.visits) if self.visits > 0 else 0
            
            for child in self.children:
                if child.visits == 0:
                    score = float('inf')
                else:
                    score = (child.value / child.visits) + c * math.sqrt(log_n / child.visits)
                # Store negated score for max-heap behavior with heapq
                # Add id(child) as tie-breaker to avoid comparing Node objects
                self.children_heap.append((-score, id(child), child))
            
            heapq.heapify(self.children_heap)
            self.last_heap_visits = self.visits
        
        # Get the first element (the max score)
        return self.children_heap[0][2]

    def best_child_heuristic(self, state):
        if not self.children:
            return None
        
        import AI_agent.ulti as ai_ulti
        def heuristic_score(child):
            if not hasattr(child, 'h_score'):
                child.h_score = ai_ulti.move_heuristic(state, child.action, self.root_player_index)
            return child.h_score
            
        return max(self.children, key=heuristic_score)