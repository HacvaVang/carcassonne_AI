
EXPLOITATION_CONST = 1.414  # sqrt(2)
import math
import random
import logging
import copy
from ..ulti import CarcassonneState, Action

logger = logging.getLogger(__name__)



class Node:
    def __init__(self, state=None, action=None, parent=None):
        self.state = state  # Only root has state initially
        self.action : Action = action
        self.parent : Node = parent
        self.children : list[Node] = list()
        self.visits = 0
        self.value = 0  # total value

    def get_state(self):
        if self.state is not None:
            return self.state
        # Compute state by applying action to parent's state
        if self.parent is None:
            return None  # Should not happen
        parent_state = self.parent.get_state()
        self.state = parent_state.simulate_action(self.action)
        return self.state

    # -------------------------------------------------------
    # SELECT PHASE
    # -------------------------------------------------------
    def select(self):
        node = self
        while node.children:
            node = node.best_child()
        return node

    # -------------------------------------------------------
    # EXPAND PHASE
    # -------------------------------------------------------
    def expand(self):
        actions = self.get_possible_actions()
        if not actions:
            return None
        action = random.choice(actions)
        child = Node(action=action, parent=self)
        self.children.append(child)
        return child

    # -------------------------------------------------------
    # ROLLOUT PHASE
    # -------------------------------------------------------
    def rollout(self):
        state : CarcassonneState = copy.deepcopy(self.get_state())
        player_index = state.current_player_index  # The player for whom we're evaluating
        while not state.is_terminal():
            actions = state.get_possible_actions()
            if not actions:
                break
            action = random.choice(actions)
            state = state.simulate_action(action)
        # Return score for the player we're evaluating
        return state.get_score(player_index)

    # -------------------------------------------------------
    # BACKPROPAGATE PHASE
    # -------------------------------------------------------
    def backpropagate(self, value):
        self.visits += 1
        self.value += value
        if self.parent:
            self.parent.backpropagate(value)
            
            
    def is_fully_expanded(self):
        return len(self.children) == len(self.get_possible_actions())

    def get_possible_actions(self):
        return self.get_state().get_possible_actions()

    def best_child(self, c=EXPLOITATION_CONST):
        if not self.children:
            return None
        best = max(self.children, key=lambda child: child.value / child.visits + c * math.sqrt(math.log(self.visits) / child.visits) if child.visits > 0 else float('inf'))
        return best

            