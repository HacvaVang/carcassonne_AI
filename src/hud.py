import pygame
class HUD:
    """Heads-Up Display for showing game info like scores, turn order, etc."""
    def __init__(self):
        self.font = pygame.font.SysFont(None, 36)

    def render(self, screen, game):
        """Draw the HUD elements onto the screen."""
        # show all player names and scores in a vertical list on the left
        y = 10
        for idx, player in enumerate(game.players):
            prefix = "-> " if idx == getattr(game, 'current_player', 0) else "   "
            text_str = f"{prefix}{player.name}: {player.score} / ({player.meeples})"
            text = self.font.render(text_str, True, player.color)
            screen.blit(text, (10, y))
            y += 30

        # show any transient score events
        if hasattr(game, "score_events") and game.score_events:
            y += 10
            for event in game.score_events:
                # fade the text as it expires
                alpha = int(255 * (event["remaining"] / event["duration"]))
                text_surf = self.font.render(event["text"], True, (255, 255, 255))
                text_surf.set_alpha(alpha)
                screen.blit(text_surf, (10, y))
                y += 25

        # optional: could display additional info such as remaining tiles
        if not game.players:
            text = self.font.render("No players", True, (255, 255, 255))
            screen.blit(text, (10, 10))

        # When the game is over, show a simple overlay with instructions.
        if getattr(game, "game_over", False):
            overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            title = self.font.render("GAME OVER", True, (255, 0, 0))
            rect = title.get_rect(center=(screen.get_width() // 2, 80))
            screen.blit(title, rect)

            hint = self.font.render("Press ESC to return to menu", True, (255, 255, 255))
            hint_rect = hint.get_rect(center=(screen.get_width() // 2, 120))
            screen.blit(hint, hint_rect)
