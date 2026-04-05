import os
import random
from typing import Dict, Optional

from settings import BASE_DIR
from src.tiles import Tile


class TileDeck:
    DEFAULT_INFO_FILE = os.path.join(BASE_DIR, "info", "tile_info.txt")

    def __init__(self, filepath: Optional[str] = None):
        self.starting_tile = "D"
        self.tileset: Dict[str, int] = {}
        self.count = 0

        if filepath is None:
            filepath = TileDeck.DEFAULT_INFO_FILE

        if os.path.exists(filepath):
            self.load_from_file(filepath)

    def _normalize_tile_name(self, name: str) -> str:
        return str(name).strip().upper()

    def load_from_file(self, filepath: str):
        """Load tile counts and starting tile from a configuration file."""
        tileset: Dict[str, int] = {}
        starting_tile: Optional[str] = None
        count = 0

        with open(filepath, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) < 2:
                    continue

                key = self._normalize_tile_name(parts[0])
                value = parts[1].strip()

                if key in ("STARTING_TILE", "START_TILE"):
                    starting_tile = self._normalize_tile_name(value)
                    continue

                try:
                    qty = int(value)
                except ValueError:
                    continue

                if qty <= 0:
                    continue

                tileset[key] = tileset.get(key, 0) + qty
                count += qty

        self.tileset = tileset
        self.count = count
        if starting_tile:
            self.starting_tile = starting_tile

    def getTile(self, name: str):
        """Draw a specific tile by name, if available."""
        name = self._normalize_tile_name(name)
        qty = self.tileset.get(name, 0)
        if qty <= 0:
            return None

        self.tileset[name] = qty - 1
        self.count -= 1
        return Tile(name)

    def generate_fixed_deck(self):
        """Generates and stores a fixed shuffle of the remaining tiles for determinism."""
        deck_list = []
        for t, c in self.tileset.items():
            deck_list.extend([t] * c)
        random.shuffle(deck_list)
        self.fixed_deck = deck_list

    def getRandomTile(self):
        """Draw a random tile from the remaining deck, or fixed deck if set."""
        if hasattr(self, 'fixed_deck') and self.fixed_deck is not None:
            if not self.fixed_deck:
                return None
            tile_name = self.fixed_deck.pop()
            self.tileset[tile_name] -= 1
            self.count -= 1
            return Tile(tile_name)

        if self.count <= 0:
            return None

        choices = [(t, c) for t, c in self.tileset.items() if c > 0]
        if not choices:
            return None

        tiles, weights = zip(*choices)
        tile_name = random.choices(tiles, weights=weights, k=1)[0]
        self.tileset[tile_name] -= 1
        self.count -= 1
        return Tile(tile_name)

    def getStartingTile(self):
        return Tile(self.starting_tile)
    
    def returnToTileDeck(self, tile : Tile):
        tile_name = tile.tile_type
        self.tileset[tile_name] += 1
        self.count += 1        
