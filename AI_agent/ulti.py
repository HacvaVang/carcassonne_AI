from src.player import Player
from src.map import Map
from src.tiles import Tile
from src.tiledeck import TileDeck
from src.meeple import Meeple
from src.region import *
from src import Terrain, GamePhase, Color, Neighbor
import copy
from functools import reduce
from src.game_logic import *

class Action:
    def __init__(self, tile_pos=None, rotation=0, meeple_pos=None):
        self.tile_pos = tile_pos  # (x, y)
        self.rotation = rotation  # 0-3
        self.meeple_pos = meeple_pos  # position for meeple, or None to skip

    def __repr__(self):
        return f"Action(tile_pos={self.tile_pos}, rot={self.rotation}, meeple={self.meeple_pos})"
    
    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return (self.tile_pos, self.rotation, self.meeple_pos) == (other.tile_pos, other.rotation, other.meeple_pos)

    def __hash__(self):
        return hash((self.tile_pos, self.rotation, self.meeple_pos))

class CarcassonneState:
    def __init__(self, game=None):
        if game:
            memo = {}
            # Copy all game parts cleanly using memo dict
            self.players = copy.deepcopy(game.players, memo)
            self.current_player_index = game.current_player_index
            self.current_phase = game.current_phase
            
            # Map, TileDeck, and Regions contain Tiles, Meeples which now implement __setstate__ to handle surfaces
            self.map = copy.deepcopy(game.map, memo)
            self.tile_deck = copy.deepcopy(game.tile_deck, memo)
            self.current_tile = copy.deepcopy(game.current_tile, memo)
            self.regions = copy.deepcopy(game.regions, memo)
            self.complete_cities = copy.deepcopy(game.complete_cities, memo)
            
            self.place_positions = copy.deepcopy(game.place_positions, memo)
            self.avaliable_moves = copy.deepcopy(game.avaliable_moves, memo)
            
            self.game_over = game.game_over

        else:
            # Initialize empty state
            self.players = []
            self.current_player_index = 0
            self.current_phase = GamePhase.PlaceTile
            self.map = Map()
            self.tile_deck = TileDeck()
            self.current_tile = None
            self.regions = {
                Terrain.Grass: [],
                Terrain.City: [],
                Terrain.Monastery: [],
                Terrain.Road: [],
            }
            self.complete_cities = []
            self.place_positions = {}
            self.avaliable_moves = {}
            self.game_over = False

    def addRegionScore(self, end_phase=False):
        for terrain, regions in self.regions.items():
            if terrain == Terrain.Grass and not end_phase:
                continue
            for region in regions[:]:
                if region.completed_flag or end_phase:
                    if not region.meeples:
                        continue
                    if terrain == Terrain.Grass:
                        region.updateAdjencyCities(self.complete_cities)
                    points = region.get_region_points()
                    owners = region.get_owner_players()
                    for player in owners:
                        player.add_points(points)
                    if region.completed_flag and region in self.regions[terrain]:
                        self.regions[terrain].remove(region)
    def get_current_player(self):
        return self.players[self.current_player_index]

    def is_terminal(self):
        return self.game_over

    def get_winner(self):
        if not self.is_terminal():
            return None
        return max(self.players, key=lambda p: p.score)

    def get_score(self, player_index) -> int:
        return self.players[player_index].score

    def get_all_score(self):
        return [self.players[idx].score for idx in range(len(self.players))]

    def get_region_score(self, player_index) -> float:
        """
        Estimate the expected score from incomplete regions a player controls.

        For each region:
          - p_score  = probability the meeple WILL actually be scored
                       (completion probability for completed bonus, else 1.0 for incomplete scoring)
          - expected = p_score * full_value + (1 - p_score) * partial_value
          - weighted by ownership share and discounted by meeples committed
        """
        target_player = self.players[player_index]
        tiles_left = len(self.tile_deck.tiles) if hasattr(self.tile_deck, 'tiles') else 10
        total_tiles = max(tiles_left, 1)
        total_score = 0.0

        for terrain, regions in self.regions.items():
            for region in regions:
                if not region.meeples or region.completed_flag:
                    continue

                # --- 1. Ownership ---
                counts = {}
                for meeple in region.meeples:
                    if meeple.player:
                        counts[meeple.player] = counts.get(meeple.player, 0) + 1
                if not counts:
                    continue
                max_count = max(counts.values())
                owners = [p for p, c in counts.items() if c == max_count]
                if target_player not in owners:
                    continue
                share = 1.0 / len(owners)

                base_points = region.get_region_points()
                meeples_used = counts.get(target_player, 0)

                if terrain == Terrain.City:
                    open_edges = self._count_open_city_edges(region)
                    completed_value = (region.shield + region.count) * 2
                    incomplete_value = base_points
                    # p_complete: chance the city gets closed (= scored at premium)
                    p_complete = max(0.0, 1.0 - (open_edges / (open_edges + total_tiles * 0.3 + 1)))
                    # Meeple is guaranteed to be scored regardless (complete or not at end)
                    # but full bonus only if completed
                    p_scored = 1.0  # meeple participates in scoring either way

                elif terrain == Terrain.Road:
                    open_ends = self._count_open_road_ends(region)
                    completed_value = base_points
                    incomplete_value = base_points
                    p_complete = max(0.0, 1.0 - (open_ends / (open_ends + total_tiles * 0.5 + 1)))
                    p_scored = 1.0

                elif terrain == Terrain.Monastery:
                    tiles_missing = 9 - region.count
                    completed_value = 9
                    incomplete_value = base_points
                    # Fewer tiles missing AND more tiles remaining = higher chance to fill
                    p_complete = max(0.0, 1.0 - (tiles_missing / (total_tiles + 1)))
                    # Monastery only scores all 9 if complete; otherwise scores partial
                    p_scored = 1.0

                elif terrain == Terrain.Grass:
                    completed_value = base_points
                    incomplete_value = base_points * 0.5
                    p_complete = 0.3
                    # Grass only ever scores at game end — chance depends on game stage
                    p_scored = min(1.0, (71 - total_tiles) / 71.0 + 0.1)

                else:
                    continue

                # Expected value: blend completion bonus weighted by p_complete
                expected_value = p_complete * completed_value + (1.0 - p_complete) * incomplete_value

                # Scale by probability that the meeple actually gets scored at all
                expected_value *= p_scored

                # Meeple cost: each meeple locked into a low-p_complete region is expensive
                # Penalty grows if many meeples are tied up in uncertain regions
                lock_penalty = meeples_used * (1.0 - p_complete) * 0.8

                total_score += share * (expected_value - lock_penalty)

        return total_score

    def _count_open_city_edges(self, region) -> int:
        """Count the number of unconnected open border edges of a city region."""
        open_edges = 0
        for tile_pos, positions in region.tiles.items():
            x, y = tile_pos
            for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
                direction_mask = 1 << idx
                if any(pos & direction_mask for pos in positions):
                    if not self.map.get_tile(x + dx, y + dy):
                        open_edges += 1
        return open_edges

    def _count_open_road_ends(self, region) -> int:
        """Count the number of open (unconnected) road endpoints."""
        open_ends = 0
        for tile_pos, positions in region.tiles.items():
            x, y = tile_pos
            for pos in positions:
                if pos == 8:  # center junction - always closed
                    continue
                if pos & 1:  # odd positions are edge-facing
                    dx, dy = list(Neighbor.neighbor.values())[pos // 2]
                    if not self.map.get_tile(x + dx, y + dy):
                        open_ends += 1
        return open_ends


    def get_possible_actions(self):
        if self.is_terminal():
            return []

        actions = []
        tile = self.current_tile
        if not tile:
            return actions

        can_place_meeple = self.players[self.current_player_index].meeples > 0

        for rot in range(tile.rotate_max + 1):
            tile_copy = copy.deepcopy(tile)
            for _ in range(rot):
                tile_copy.rotate()
            moves = self.map.get_placeable_positon(tile_copy)
            for pos in moves:
                # Always offer the no-meeple action
                actions.append(Action(tile_pos=pos, rotation=rot, meeple_pos=None))

                if not can_place_meeple:
                    continue

                # Determine which tile-local positions are free (no existing meeple claim)
                # by checking whether placing would merge with any region that already has meeples.
                available_positions = self._get_free_meeple_positions(tile_copy, pos)
                for meeple_key in available_positions:
                    actions.append(Action(tile_pos=pos, rotation=rot, meeple_pos=meeple_key))

        return actions

    def _get_free_meeple_positions(self, tile_copy, tile_pos):
        """Return list of (terrain, region_first_pos) keys where a meeple can legally be placed.
        A position is valid only if the corresponding region (after merging with neighbors)
        would have no meeples in it.
        """
        from functools import reduce
        x, y = tile_pos
        free_positions = []

        for terrain, tile_regions in tile_copy.region.items():
            if terrain == Terrain.Monastery:
                # Monastery regions can always be claimed if the tile region is free
                for tile_region in tile_regions:
                    free_positions.append((terrain, tile_region[0]))
                continue

            for tile_region in tile_regions:
                first_pos = tile_region[0]
                # Build the direction mask for this tile region
                mask = reduce(lambda acc, ele: acc ^ Neighbor.direction_mask[ele], tile_region, 0)
                border = tile_copy.edges

                region_has_meeple = False
                for idx, (dx, dy) in enumerate(Neighbor.neighbor.values()):
                    if not (mask & (1 << idx)):
                        continue
                    neighbor_tile = self.map.get_tile(x + dx, y + dy)
                    if not neighbor_tile:
                        continue
                    if terrain == Terrain.Grass and border[idx] == Terrain.City:
                        continue
                    # Find matching neighbor region
                    neighbor_pos_list = Neighbor.get_neighbor_pos(tile_region, (dx, dy))
                    for neighbor_pos in neighbor_pos_list:
                        matching_region = next(
                            (reg for reg in self.regions.get(terrain, [])
                             if neighbor_pos in reg.tiles.get((x + dx, y + dy), [])),
                            None
                        )
                        if matching_region and matching_region.meeples:
                            region_has_meeple = True
                            break
                    if region_has_meeple:
                        break

                if not region_has_meeple:
                    free_positions.append((terrain, first_pos))

        return free_positions

    def change_phase(self):

        if len(self.players) == 0:
            self.game_over = True
            return

        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_tile = self.tile_deck.getRandomTile()
        if self.current_tile:
            self.current_tile.image = None

        if not self.current_tile:
            self.game_over = True
            self.current_phase = None
        else:
            self.current_phase = GamePhase.PlaceTile

    def simulate_action(self, action : Action):
        next_state = copy.deepcopy(self)
        next_state.apply_action(action)
        return next_state
    
    def apply_action(self, action):
        if action.tile_pos is None:
            self.change_phase()
            return

        tile = self.current_tile
        if not tile:
            self.change_phase()
            return

        for _ in range(action.rotation):
            tile.rotate()
        self.map.place_tile(action.tile_pos, tile)
        self.updateRegion(action.tile_pos)

        if action.meeple_pos is not None and action.meeple_pos in self.place_positions:
            terrain, region_pos = self.place_positions[action.meeple_pos]
            for region in self.regions[terrain][::-1]:
                if any(region_pos in positions for positions in region.tiles.values()):
                    meeple = Meeple(self.players[self.current_player_index], action.meeple_pos, is_simulation=True)
                    region.addMeeple(meeple)
                    self.players[self.current_player_index].place_meeple()
                    break
                    
        self.addRegionScore()
        self.change_phase()

    def updateRegion(self, pos, start_tile=False):
        self.place_positions.clear()
        tile = self.current_tile
        if tile is None:
            return
        for x in self.regions[Terrain.Monastery]:
            x.update(pos)
            x.is_completed()

        for terrain, tile_regions in tile.region.items():
            for tile_region in tile_regions:
                if terrain == Terrain.Monastery:
                    new_region = add_monastery_region(self.map, tile_region, pos)
                else:
                    new_region = add_region(self.regions, self.map, self.current_tile, terrain, tile_region, pos)
                new_region.is_completed()
                self.regions[terrain].append(new_region)
                
                if terrain == Terrain.City and new_region.completed_flag:
                    self.complete_cities.append(new_region)

                if start_tile or new_region.meeples:
                    continue

                self.place_positions[(terrain, tile_region[0])] = (terrain, tile_region[0])

    def assignPointsAtEndOfGame(self):
        """Assign points for remaining regions at end of game."""
        # Score any remaining completed regions first, then score incomplete ones.
        assign_points_at_end_of_game(self)

def move_heuristic(original_state: CarcassonneState, action: Action, player_index: int) -> float:
    """
    Evaluates an action by simulating it and calculating the score delta 
    (forcing end of game scoring) between the player and their opponent.
    Translated from the provided Java moveHeuristic logic.
    """
    # Simulate the action (returns a deep-copied new state with the move applied and immediate region scores tallied)
    # This automatically handles tile rotation and meeple placements defined in the Action.
    state = original_state.simulate_action(action)
    
    # Get previous scores
    prev_scores = original_state.get_all_score() 
    prev_score = prev_scores[player_index]
    
    # Assuming 2 players for opponent delta calculation
    if len(original_state.players) > 1:
        prev_score_op = max(prev_scores[:player_index] + prev_scores[player_index+1:])
    else:
        prev_score_op = 0

    # Force the state to assign points for incomplete regions as if the game ended
    state.assignPointsAtEndOfGame()
    
    # Get updated scores
    updated_scores = state.get_all_score()
    updated_score = updated_scores[player_index]
    if len(state.players) > 1:
        updated_score_op = max(updated_scores[:player_index] + updated_scores[player_index+1:])
    else:
        updated_score_op = 0

    # The difference between the updated and the previous score minus the 
    # difference between the updated and the previous score of the opponent.
    output = (updated_score - prev_score) - (updated_score_op - prev_score_op)
    
    return output
