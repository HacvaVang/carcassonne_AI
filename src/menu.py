import os
import pickle

import pygame

from AI_agent.MCTS.mcts_player import MCTSPlayer
from AI_agent.minimax.minimax_player import MinimaxPlayer
from AI_agent.random.random_player import RandomPlayer
from settings import BASE_DIR
from src import GamePhase, Color
from src.game import Game
from src.hud import HUD
from src.meeple import Meeple
from src.player import Player
from src.tiles import Tile


class MenuButton:
    def __init__(self, label, action, enabled=True, text_color=None):
        self.label = label
        self.action = action
        self.enabled = enabled
        self.text_color = text_color
        self.rect = pygame.Rect(0, 0, 0, 0)


class Menu:
    SAVE_FILE = os.path.join(BASE_DIR, "save.pkl")
    PLAYER_TYPES = ["Player", "Random bot", "Minimax bot", "MCTS bot"]
    PLAYER_COLORS = ["blue", "red", "green", "yellow", "black"]

    _runtime_patched = False
    _active_menu = None
    _active_game = None
    _pending_config = None
    _pending_loaded_game = None
    _original_game_start = None
    _original_game_update = None
    _original_game_handle_event = None

    def __init__(self, screen, start_callback=None):
        self.screen = screen
        self.start_callback = start_callback

        self.title_font = pygame.font.SysFont(None, 72)
        self.font = pygame.font.SysFont(None, 42)
        self.small_font = pygame.font.SysFont(None, 28)

        self.mode = "main"
        self.selected = 0
        self.message = ""
        self.message_timer = 0.0

        self.config = {
            "total_players": 3,
            "player_kinds": ["Player", "MCTS bot", "MCTS bot", "MCTS bot", "MCTS bot"],
        }

        self.active_game = None
        self.paused_game = None

        os.makedirs(os.path.dirname(self.SAVE_FILE), exist_ok=True)
        Menu._active_menu = self
        self._patch_runtime()

    def _patch_runtime(self):
        if Menu._runtime_patched:
            return

        Menu._runtime_patched = True

        def tile_getstate(tile):
            return {
                "tile_type": tile.tile_type,
                "rotate_count": tile.rotate_count,
            }

        def tile_setstate(tile, state):
            tile.__init__(state.get("tile_type"))
            for _ in range(state.get("rotate_count", 0) % 4):
                tile.rotate()

        def meeple_getstate(meeple):
            center = getattr(meeple, "pos", None)
            if center is None:
                rect = getattr(meeple, "rect", None)
                center = rect.center if rect is not None else (0, 0)
            return {
                "player": meeple.player,
                "center": center,
            }

        def meeple_setstate(meeple, state):
            meeple.player = state.get("player")
            center = state.get("center", state.get("pos", (0, 0)))
            meeple.pos = center
            from src.assetloader import get_image

            if meeple.player is not None:
                meeple.image = get_image(meeple.player.color, "Meeple")
            else:
                meeple.image = None

        def hud_getstate(hud):
            return {}

        def hud_setstate(hud, state):
            hud.font = pygame.font.SysFont(None, 36)

        def game_getstate(game):
            state = dict(game.__dict__)
            state.pop("screen", None)
            return state

        def game_setstate(game, state):
            game.__dict__.update(state)
            game.screen = None
            if getattr(game, "hud", None) is None:
                game.hud = HUD()

        Tile.__getstate__ = tile_getstate
        Tile.__setstate__ = tile_setstate
        Meeple.__getstate__ = meeple_getstate
        Meeple.__setstate__ = meeple_setstate
        HUD.__getstate__ = hud_getstate
        HUD.__setstate__ = hud_setstate
        Game.__getstate__ = game_getstate
        Game.__setstate__ = game_setstate

        Menu._original_game_start = Game.start
        Menu._original_game_update = Game.update
        Menu._original_game_handle_event = Game.handle_event

        def patched_start(game_self):
            Menu._original_game_start(game_self)
            menu = Menu._active_menu
            if not menu:
                return

            menu._set_active_game(game_self)
            menu._apply_configured_players(game_self)

            if Menu._pending_loaded_game is not None:
                menu._apply_loaded_game(game_self, Menu._pending_loaded_game)
                Menu._pending_loaded_game = None

            if game_self.running:
                menu.mode = "main"

        def patched_update(game_self, dt):
            Menu._original_game_update(game_self, dt)

            if not game_self.running or getattr(game_self, "game_over", False):
                return

            current_player = None
            if getattr(game_self, "players", None):
                current_index = getattr(game_self, "current_player_index", 0)
                if 0 <= current_index < len(game_self.players):
                    current_player = game_self.players[current_index]
                    game_self.current_player = current_player

            if current_player is None or isinstance(current_player, MCTSPlayer):
                return

            chooser = getattr(current_player, "choose_action", None)
            if not callable(chooser):
                return

            action = chooser(game_self)
            if not action:
                return

            if game_self.current_phase == GamePhase.PlaceTile:
                for _ in range(action.rotation):
                    game_self.current_tile.rotate()
                if game_self.place_tile(action.tile_pos, game_self.current_tile):
                    game_self.addRegionScore()
                    game_self.changePhase()
            elif game_self.current_phase == GamePhase.PlaceMeeple:
                game_self.changePhase()

        def patched_handle_event(game_self, event):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if getattr(game_self, "game_over", False):
                    game_self.running = False
                else:
                    game_self.running = False
                    menu = Menu._active_menu
                    if menu:
                        menu._set_active_game(game_self)
                return
            Menu._original_game_handle_event(game_self, event)

        Game.start = patched_start
        Game.update = patched_update
        Game.handle_event = patched_handle_event

    def _get_save_path(self):
        return self.SAVE_FILE

    def _set_message(self, text, duration=2.0):
        self.message = text
        self.message_timer = duration

    def _set_active_game(self, game):
        self.active_game = game
        if game:
            self.paused_game = game
        Menu._active_game = game

    def _build_players(self):
        players = []
        total_players = int(self.config.get("total_players", 3))
        total_players = max(2, min(total_players, len(self.PLAYER_COLORS)))

        kinds = self._normalized_player_kinds(total_players)

        for index in range(total_players):
            color = self.PLAYER_COLORS[index]
            kind = kinds[index]
            players.append(self._create_player(kind, index, color))

        return players

    def _normalized_player_kinds(self, total_players):
        kinds = list(self.config.get("player_kinds", []))
        if len(kinds) < len(self.PLAYER_COLORS):
            kinds.extend(["MCTS bot"] * (len(self.PLAYER_COLORS) - len(kinds)))

        kinds = kinds[:len(self.PLAYER_COLORS)]
        if kinds:
            kinds[0] = kinds[0] if kinds[0] in self.PLAYER_TYPES else "Player"

        for index in range(total_players):
            if kinds[index] not in self.PLAYER_TYPES:
                kinds[index] = "MCTS bot"

        return kinds

    def _create_player(self, kind, index, color):
        name = "Player" if index == 0 and kind == "Player" else f"Player {index + 1}"

        if kind == "Player":
            return Player(name, color)
        if kind == "Random bot":
            return RandomPlayer(f"AI {index + 1}", color)
        if kind == "Minimax bot":
            return MinimaxPlayer(f"AI {index + 1}", color, depth=2)
        return MCTSPlayer(f"AI {index + 1}", color, iterations=1000)

    def _apply_configured_players(self, game):
        game.players = self._build_players()
        game.current_player_index = 0
        game.current_player = game.players[0] if game.players else None
        if game.current_tile is not None:
            game.current_phase = GamePhase.PlaceTile

    def _apply_loaded_game(self, target_game, loaded_game):
        target_game.__dict__.clear()
        target_game.__dict__.update(loaded_game.__dict__)
        target_game.screen = self.screen
        if getattr(target_game, "hud", None) is None:
            target_game.hud = HUD()
        target_game.running = False
        self._set_active_game(target_game)

    def _save_game(self):
        game = self.paused_game or self.active_game
        if not game:
            self._set_message("No game to save.")
            return

        try:
            with open(self._get_save_path(), "wb") as handle:
                pickle.dump(game, handle)
            self._set_message("Game saved.")
        except Exception as error:
            self._set_message(f"Save failed: {error}")

    def _load_saved_game(self):
        save_path = self._get_save_path()
        if not os.path.exists(save_path):
            self._set_message("No save file found.")
            return

        try:
            with open(save_path, "rb") as handle:
                saved_game = pickle.load(handle)
        except Exception as error:
            self._set_message(f"Load failed: {error}")
            return

        if self.active_game and not self.active_game.running:
            self._apply_loaded_game(self.active_game, saved_game)
            self._set_message("Game loaded.")
            return

        Menu._pending_loaded_game = saved_game
        if self.start_callback:
            self.start_callback()
            self._set_message("Game loaded.")
        else:
            self._set_message("Cannot load without a start callback.")

    def _start_new_game(self):
        Menu._pending_loaded_game = None
        if self.start_callback:
            self.start_callback()

    def _continue_game(self):
        game = self.paused_game or self.active_game
        if not game:
            self._set_message("No paused game to continue.")
            return
        if getattr(game, "game_over", False):
            self._set_message("Game over cannot be continued.")
            return

        game.running = True
        self._set_active_game(game)

    def _cycle_total_players(self, step):
        current = int(self.config.get("total_players", 3))
        current += step
        if current < 2:
            current = len(self.PLAYER_COLORS)
        if current > len(self.PLAYER_COLORS):
            current = 2
        self.config["total_players"] = current

    def _cycle_player_kind(self, player_index, step=1):
        if player_index < 0:
            return

        total_players = int(self.config.get("total_players", 3))
        if player_index >= total_players:
            return
        kinds = self._normalized_player_kinds(total_players)
        current = kinds[player_index]
        current_index = self.PLAYER_TYPES.index(current) if current in self.PLAYER_TYPES else 0
        kinds[player_index] = self.PLAYER_TYPES[(current_index + step) % len(self.PLAYER_TYPES)]
        self.config["player_kinds"] = kinds

    def _main_menu_buttons(self):
        can_continue = bool(self.paused_game and not getattr(self.paused_game, "game_over", False))
        can_save = bool(self.paused_game)
        can_load = os.path.exists(self._get_save_path())
        return [
            MenuButton("Continue", self._continue_game, enabled=can_continue),
            MenuButton("New Game", self._go_config),
            MenuButton("Load Game", self._load_saved_game, enabled=can_load),
            MenuButton("Save Game", self._save_game, enabled=can_save),
            MenuButton("Quit", self._quit),
        ]

    def _config_menu_buttons(self):
        buttons = [
            MenuButton(f"Total Players: {self.config['total_players']}", lambda: self._cycle_total_players(1)),
        ]

        total_players = int(self.config.get("total_players", 3))
        kinds = self._normalized_player_kinds(total_players)

        for idx in range(total_players):
            role = kinds[idx]
            color_name = self.PLAYER_COLORS[idx].capitalize()
            base_rgb = Color.color.get(self.PLAYER_COLORS[idx], (220, 220, 220))
            slot_rgb = tuple(min(255, c + 35) for c in base_rgb)
            buttons.append(
                MenuButton(
                    f"Slot {idx + 1} ({color_name}): {role}",
                    lambda p=idx: self._cycle_player_kind(p, 1),
                    text_color=slot_rgb,
                )
            )

        buttons.extend([
            MenuButton("Start Game", self._confirm_config),
            MenuButton("Back", self._back_to_main),
        ])
        return buttons

    def _build_buttons(self):
        if self.mode == "config":
            return self._config_menu_buttons()
        return self._main_menu_buttons()

    def _layout_buttons(self):
        buttons = self._build_buttons()
        width = min(460, max(320, self.screen.get_width() - 120))
        base_height = 54
        base_gap = 18

        # Reserve space for title/subtitle and footer, then fit buttons in between.
        title_block_h = self.title_font.get_height() + self.small_font.get_height() + 56
        footer_block_h = 110
        top_y = 30 + title_block_h
        bottom_y = self.screen.get_height() - footer_block_h
        available_h = max(180, bottom_y - top_y)

        height = base_height
        gap = base_gap
        total_height = len(buttons) * height + (len(buttons) - 1) * gap

        if total_height > available_h and total_height > 0:
            scale = available_h / total_height
            height = max(42, int(base_height * scale))
            gap = max(8, int(base_gap * scale))
            total_height = len(buttons) * height + (len(buttons) - 1) * gap

        start_y = self.screen.get_height()*0.23
        start_x = self.screen.get_width() // 2 - width // 2

        for index, button in enumerate(buttons):
            button.rect = pygame.Rect(start_x, start_y + index * (height + gap), width, height)

        return buttons

    def _go_config(self):
        self.mode = "config"
        self.selected = 0

    def _back_to_main(self):
        self.mode = "main"
        self.selected = 0

    def _confirm_config(self):
        self.mode = "main"
        self.selected = 0
        self._start_new_game()

    def _quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _activate_index(self, index):
        buttons = self._layout_buttons()
        if not buttons:
            return
        index = max(0, min(index, len(buttons) - 1))
        button = buttons[index]
        if not button.enabled:
            if "Continue" in button.label:
                self._set_message("No paused game available", duration=3.0)
            elif "Load" in button.label:
                self._set_message("No save files found", duration=3.0)
            elif "Save" in button.label:
                self._set_message("Pause a game first to save", duration=3.0)
            else:
                self._set_message("That option is not available.", duration=3.0)
            return
        button.action()

    def handle_event(self, event):
        buttons = self._layout_buttons()
        if self.selected >= len(buttons):
            self.selected = max(0, len(buttons) - 1)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(buttons)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(buttons)
            elif event.key == pygame.K_LEFT and self.mode == "config":
                if self.selected == 0:
                    self._cycle_total_players(-1)
                elif 0 < self.selected < len(buttons) - 2:
                    self._cycle_player_kind(self.selected, -1)
            elif event.key == pygame.K_RIGHT and self.mode == "config":
                if self.selected == 0:
                    self._cycle_total_players(1)
                elif 0 < self.selected < len(buttons) - 2:
                    self._cycle_player_kind(self.selected, 1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_index(self.selected)
            elif event.key == pygame.K_ESCAPE and self.mode == "config":
                self._back_to_main()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, button in enumerate(buttons):
                if button.rect.collidepoint(event.pos):
                    self.selected = index
                    self._activate_index(index)
                    break

    def update(self, dt):
        buttons = self._layout_buttons()
        if self.selected >= len(buttons):
            self.selected = max(0, len(buttons) - 1)

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    def _draw_title(self, title, subtitle=None):
        title_surf = self.title_font.render(title, True, (240, 240, 240))
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 8))
        self.screen.blit(title_surf, title_rect)

        if subtitle:
            subtitle_surf = self.small_font.render(subtitle, True, (200, 200, 200))
            subtitle_rect = subtitle_surf.get_rect(center=(self.screen.get_width() // 2, title_rect.bottom + 26))
            self.screen.blit(subtitle_surf, subtitle_rect)

    def _draw_buttons(self, buttons):
        mouse_pos = pygame.mouse.get_pos()
        # In config mode with many rows, use a slightly smaller font to keep labels clean.
        label_font = self.small_font if self.mode == "config" and len(buttons) >= 7 else self.font
        for index, button in enumerate(buttons):
            hovered = button.rect.collidepoint(mouse_pos)
            selected = index == self.selected
            base_color = (70, 70, 70)
            if not button.enabled:
                base_color = (35, 35, 35)
            elif hovered or selected:
                base_color = (110, 110, 110)

            pygame.draw.rect(self.screen, base_color, button.rect, border_radius=8)
            pygame.draw.rect(self.screen, (170, 170, 170), button.rect, 2, border_radius=8)

            if button.enabled and button.text_color is not None:
                text_color = button.text_color
            else:
                text_color = (245, 245, 245) if button.enabled else (140, 140, 140)
            label = label_font.render(button.label, True, text_color)
            label_rect = label.get_rect(center=button.rect.center)
            self.screen.blit(label, label_rect)

    def render(self):
        self.screen.fill((24, 24, 24))
        buttons = self._layout_buttons()

        if self.mode == "config":
            self._draw_title("Pre-game Config", "Choose a role for each slot")
        elif self.paused_game and getattr(self.paused_game, "game_over", False):
            self._draw_title("Game Over", "Continue is disabled after the match ends")
        elif self.paused_game and not getattr(self.paused_game, "running", True):
            self._draw_title("Paused", "Press Continue to resume or save the current game")
        else:
            self._draw_title("Carcassonne AI", "Use arrow keys or click a button")

        self._draw_buttons(buttons)

        footer_lines = []
        if self.mode == "config":
            footer_lines.append("Left/Right cycle role • ↑/↓ Navigate")
        footer_lines.append("ESC pauses the game when you are in play")
        if self.message:
            footer_lines.append(self.message)

        y = self.screen.get_height() - 72
        for line in footer_lines:
            footer = self.small_font.render(line, True, (210, 210, 210))
            footer_rect = footer.get_rect(center=(self.screen.get_width() // 2, y))
            self.screen.blit(footer, footer_rect)
            y += 22
