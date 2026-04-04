import math
import random
import copy
from ..ulti import CarcassonneState, Action
from src import GamePhase

EXPLOITATION_CONST = 3  # sqrt(2)

def meeple_policy(actions):
    """Place meeple policy when possible."""
    if not actions:
        return None
    place_actions = [a for a in actions if getattr(a, 'meeple_pos', None) is not None]
    if place_actions:
        return random.choice(place_actions)
    return actions[0]



class Node:
    def __init__(self, state=None, parent=None, action=None, root_player_index=None):
        self.state : CarcassonneState = state  # Only root has state initially
        self.parent : Node = parent
        self.children : list[Node] = list()
        self.visits = 0
        self.value = 0  # total value (always from root player's perspective)
        self.action = action  # The action that led to this node
        self.unvisited_actions = self.get_possible_actions() if self.state and not self.state.is_terminal() else []
        # Track which player index is the "root" (the one we're optimising for)
        if root_player_index is not None:
            self.root_player_index = root_player_index
        elif parent is not None:
            self.root_player_index = parent.root_player_index
        else:
            self.root_player_index = state.current_player_index if state else 0

    # -------------------------------------------------------
    # SELECT PHASE
    # -------------------------------------------------------
    def select(self):
        node = self
        while node.is_fully_expanded() and node.children:
            node = node.best_child_uct()
        return node

    # -------------------------------------------------------
    # EXPAND PHASE
    # -------------------------------------------------------
    def expand(self):
        if not self.unvisited_actions:
            return None
        action = self.unvisited_actions.pop()
        child_state = self.state.simulate_action(action)
        child = Node(state=child_state, parent=self, action=action)
        self.children.append(child)
        return child

    # -------------------------------------------------------
    # ROLLOUT PHASE
    # -------------------------------------------------------
    def rollout(self):
        state : CarcassonneState = copy.deepcopy(self.state)
        while not state.is_terminal():
            actions = state.get_possible_actions()
            if not actions:
                break

            action = random.choice(actions)
            state.apply_action(action)
        state.assignPointsAtEndOfGame()
        # Score the final state from the root player's perspective
        player_scores = [state.get_score(i) for i in range(len(state.players))]
        print(f"player_scores: {player_scores}")
        value = player_scores[self.root_player_index]
        if len(state.players) > 1:
            opponent_max_score = max(
                player_scores[idx]
                for idx in range(len(state.players))
                if idx != self.root_player_index
            )
        else:
            opponent_max_score = 0
        print(value - opponent_max_score)
        return value - opponent_max_score

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

    def get_possible_actions(self):
        return self.state.get_possible_actions()

    def best_child_uct(self, c=EXPLOITATION_CONST):
        if not self.children:
            return None

        def uct_score(child):
            if child.visits == 0:
                return float('inf')
            exploit = child.value / child.visits
            explore = c * math.sqrt(math.log(self.visits) / child.visits)
            return exploit + explore

        return max(self.children, key=uct_score)

        