import os
import pickle

import pygame

from AI_agent.MCTS.mcts_player import MCTSPlayer
from AI_agent.minimax.minimax_player import MinimaxPlayer
from AI_agent.random.random_player import RandomPlayer
from settings import BASE_DIR
from src import GamePhase
from src.game import Game
from src.hud import HUD
from src.meeple import Meeple
from src.player import Player
from src.tiles import Tile


class MenuButton:
    def __init__(self, label, action, enabled=True):
        self.label = label
        self.action = action
        self.enabled = enabled
        self.rect = pygame.Rect(0, 0, 0, 0)


class Menu:
    SAVE_FILE = os.path.join(BASE_DIR, "save.pkl")
    AI_TYPES = ["MCTS", "Random", "Minimax"]
    AI_COLORS = ["red", "green", "yellow"]

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
            "ai_count": 2,
            "ai_type": "MCTS",
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
            return {
                "player": meeple.player,
                "center": meeple.rect.center,
            }

        def meeple_setstate(meeple, state):
            meeple.player = state.get("player")
            from src.assetloader import get_image

            meeple.image = get_image(meeple.player.color, "Meeple")
            meeple.rect = meeple.image.get_rect(center=state.get("center", (0, 0)))
            meeple.position = meeple.rect.center

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

            if isinstance(game_self.current_player, MCTSPlayer):
                return

            chooser = getattr(game_self.current_player, "choose_tile_action", None)
            if not callable(chooser):
                return

            if game_self.current_phase == GamePhase.PlaceTile:
                action = chooser(game_self)
                if action:
                    for _ in range(action.rotation):
                        game_self.current_tile.rotate()
                    if game_self.place_tile(action.tile_pos, game_self.current_tile):
                        game_self.addRegionScore()
                        game_self.changePhase()
            elif game_self.current_phase == GamePhase.PlaceMeeple:
                meeple_chooser = getattr(game_self.current_player, "choose_meeple_action", None)
                if callable(meeple_chooser):
                    meeple_chooser(game_self)
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
        players = [Player("Player", "blue")]
        ai_count = max(0, min(int(self.config.get("ai_count", 1)), len(self.AI_COLORS)))
        ai_type = self.config.get("ai_type", "MCTS")

        for index in range(ai_count):
            color = self.AI_COLORS[index % len(self.AI_COLORS)]
            if ai_type == "Random":
                players.append(RandomPlayer(f"AI {index + 1}", color))
            elif ai_type == "Minimax":
                players.append(MinimaxPlayer(f"AI {index + 1}", color, depth=3))
            else:
                players.append(MCTSPlayer(f"AI {index + 1}", color, iterations=1000))

        return players

    def _apply_configured_players(self, game):
        game.players = self._build_players()
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

    def _cycle_ai_count(self, step):
        current = int(self.config.get("ai_count", 1))
        current += step
        if current < 1:
            current = len(self.AI_COLORS)
        if current > len(self.AI_COLORS):
            current = 1
        self.config["ai_count"] = current

    def _cycle_ai_type(self, step):
        current = self.AI_TYPES.index(self.config.get("ai_type", "MCTS"))
        current = (current + step) % len(self.AI_TYPES)
        self.config["ai_type"] = self.AI_TYPES[current]

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
        return [
            MenuButton(f"AI Opponents: {self.config['ai_count']}", lambda: self._cycle_ai_count(1)),
            MenuButton(f"AI Type: {self.config['ai_type']}", lambda: self._cycle_ai_type(1)),
            MenuButton("Start Game", self._confirm_config),
            MenuButton("Back", self._back_to_main),
        ]

    def _build_buttons(self):
        if self.mode == "config":
            return self._config_menu_buttons()
        return self._main_menu_buttons()

    def _layout_buttons(self):
        buttons = self._build_buttons()
        width = min(460, max(320, self.screen.get_width() - 120))
        height = 54
        gap = 18

        total_height = len(buttons) * height + (len(buttons) - 1) * gap
        start_y = int(self.screen.get_height() * 0.32)
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
                    self._cycle_ai_count(-1)
                elif self.selected == 1:
                    self._cycle_ai_type(-1)
            elif event.key == pygame.K_RIGHT and self.mode == "config":
                if self.selected == 0:
                    self._cycle_ai_count(1)
                elif self.selected == 1:
                    self._cycle_ai_type(1)
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
        title_rect = title_surf.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 5))
        self.screen.blit(title_surf, title_rect)

        if subtitle:
            subtitle_surf = self.small_font.render(subtitle, True, (200, 200, 200))
            subtitle_rect = subtitle_surf.get_rect(center=(self.screen.get_width() // 2, title_rect.bottom + 26))
            self.screen.blit(subtitle_surf, subtitle_rect)

    def _draw_buttons(self, buttons):
        mouse_pos = pygame.mouse.get_pos()
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

            text_color = (245, 245, 245) if button.enabled else (140, 140, 140)
            label = self.font.render(button.label, True, text_color)
            label_rect = label.get_rect(center=button.rect.center)
            self.screen.blit(label, label_rect)

    def render(self):
        self.screen.fill((24, 24, 24))
        buttons = self._layout_buttons()

        if self.mode == "config":
            self._draw_title("Pre-game Config", "Configure opponents and AI type")
        elif self.paused_game and getattr(self.paused_game, "game_over", False):
            self._draw_title("Game Over", "Continue is disabled after the match ends")
        elif self.paused_game and not getattr(self.paused_game, "running", True):
            self._draw_title("Paused", "Press Continue to resume or save the current game")
        else:
            self._draw_title("Carcassonne AI", "Use arrow keys or click a button")

        self._draw_buttons(buttons)

        footer_lines = []
        if self.mode == "config":
            footer_lines.append("Left/Right adjust setting • ↑/↓ Navigate")
        footer_lines.append("ESC pauses the game when you are in play")
        if self.message:
            footer_lines.append(self.message)

        y = self.screen.get_height() - 72
        for line in footer_lines:
            footer = self.small_font.render(line, True, (210, 210, 210))
            footer_rect = footer.get_rect(center=(self.screen.get_width() // 2, y))
            self.screen.blit(footer, footer_rect)
            y += 22
