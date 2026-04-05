from src.player import Player
from AI_agent.MCTS.search import mcts_search
from AI_agent.ulti import CarcassonneState, Action
from AI_agent.MCTS.ulti import TreePolicy
from threading import Thread

EXPLOITATION_CONST = 3  # sqrt(2)


class MCTSPlayer(Player):
    def __init__(self, name, color, iterations=600, tree_policy_type=TreePolicy.UCT, exploration_const=EXPLOITATION_CONST):
        super().__init__(name, color)
        self.iterations = iterations
        self.tree_policy_type = tree_policy_type
        self.exploration_const = exploration_const

    def choose_action(self, game):
        """Choose the best action using Ensemble MCTS."""
        from collections import Counter
        import random

        ensemble_count = 4
        votes = []
        threads = []
        
        print(f"Starting Ensemble MCTS with {ensemble_count} threads, {self.iterations} iterations per tree")
        
        def run_tree(base_game):
            state = CarcassonneState(base_game)
            state.tile_deck.generate_fixed_deck()
            action = mcts_search(state, self.iterations, self.tree_policy_type, self.exploration_const)
            if action:
                votes.append(action)

        for e in range(ensemble_count):
            t = Thread(target=run_tree, args=(game,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()
                
        if not votes:
            return None
            
        vote_counts = Counter(votes)
        max_votes = max(vote_counts.values())
        best_actions = [a for a, c in vote_counts.items() if c == max_votes]
        
        best_action = random.choice(best_actions)
        print(f"Ensemble selected action {best_action} with {max_votes}/{ensemble_count} votes")
        return best_action