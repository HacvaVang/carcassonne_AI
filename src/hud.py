import pygame

# class ScoreBox():
#     def __init__(self, name, point, meeple):
#         self.name = name
#         self.point = point
#         self.meeple = meeple
        
        
#     def render(font):


class HUD:
    """Heads-Up Display for showing game info like scores, turn order, etc."""
    def __init__(self):
        self.font = pygame.font.Font("assets/font/Squares.otf" , 30)
        self.score_font = pygame.font.Font("assets/font/Squares.otf", 60)
        self.player_font = None

    def render(self, screen, game):
        """Draw the HUD elements onto the screen."""
        if game.players:
            screen_width = screen.get_width()
            box_height = 80
            box_y = 10
            num_players = len(game.players)
            box_spacing = screen_width / (num_players + 1)
            
            # Get current player index
            current_player_idx = game.current_player_index if hasattr(game, 'current_player_index') else -1
            
            for idx, player in enumerate(game.players):
                # Render texts separately
                score_text = self.score_font.render(str(player.score), True, player.color)
                name_text = self.font.render(player.name, True, player.color)
                meeples_text = self.font.render(f"{player.meeples}", True, player.color)
                
                # Calculate scalable box width for the score alone
                score_pad_x = 20
                score_box_width = score_text.get_width() + score_pad_x * 2
                
                # Calculate total width to keep the player info centered
                right_text_width = max(name_text.get_width(), meeples_text.get_width())
                total_block_width = score_box_width + 15 + right_text_width
                
                block_x = (idx + 1) * box_spacing - total_block_width / 2
                
                # Draw rounded box ONLY around score
                score_box_rect = pygame.Rect(block_x, box_y, score_box_width, box_height)
                is_current = idx == current_player_idx
                
                # Highlight current player
                if is_current:
                    pygame.draw.rect(screen, (100, 100, 0), score_box_rect, width=0, border_radius=5)
                    pygame.draw.rect(screen, player.color, score_box_rect, width=4, border_radius=5)
                else:
                    pygame.draw.rect(screen, (255, 255, 255, 75), score_box_rect, width=0, border_radius=5)
                    pygame.draw.rect(screen, (0, 0, 0), score_box_rect, width=4, border_radius=5)
                
                # Layout: Score centered inside its box
                score_x = block_x + score_pad_x
                score_y = box_y + (box_height - score_text.get_height()) // 2
                screen.blit(score_text, (score_x, score_y))
                
                # Layout: Name and meeples on the right side of the score box
                text_col_x = block_x + score_box_width + 15
                name_y = box_y + 10
                meeples_y = box_y + 45
                
                screen.blit(name_text, (text_col_x, name_y))
                screen.blit(meeples_text, (text_col_x, meeples_y))

        # Show currently playing tile with remaining count
        if hasattr(game, 'current_tile') and game.current_tile:
            screen_width = screen.get_width()
            screen_height = screen.get_height()
            
            # Position tile display on the right side
            tile_display_x = screen_width - 150
            tile_display_y = 100
            
            # Draw tile image
            tile_image = game.current_tile.image
            if tile_image:
                # Scale tile image for display (smaller than board size)
                tile_size = 80
                scaled_tile = pygame.transform.scale(tile_image, (tile_size, tile_size))
                # Rotate based on current rotation
                rotated_tile = pygame.transform.rotate(scaled_tile, -90 * game.current_tile.rotate_count)
                
                # Draw background box for tile
                tile_box = rotated_tile.get_rect(center=(tile_display_x, tile_display_y))
                pygame.draw.rect(screen, (50, 50, 50), tile_box.inflate(10, 10), width=0, border_radius=5)
                pygame.draw.rect(screen, (200, 150, 100), tile_box.inflate(10, 10), width=2, border_radius=5)
                
                screen.blit(rotated_tile, tile_box)
            
            # Show tiles remaining
            tiles_left = getattr(game.tile_deck, 'count', 0) if hasattr(game, 'tile_deck') else 0
            tiles_text = f"Tiles: {tiles_left}"
            tiles_surf = self.font.render(tiles_text, True, (255, 255, 255))
            
            # Display below the tile
            tiles_x = tile_display_x - tiles_surf.get_width() // 2
            tiles_y = tile_display_y + 60
            
            # Draw background box for tiles text
            tiles_rect = tiles_surf.get_rect(topleft=(tiles_x - 8, tiles_y - 5))
            tiles_rect.width += 16
            tiles_rect.height += 10
            pygame.draw.rect(screen, (50, 50, 50), tiles_rect, width=0, border_radius=5)
            pygame.draw.rect(screen, (100, 200, 255), tiles_rect, width=2, border_radius=5)
            
            screen.blit(tiles_surf, (tiles_x, tiles_y))

        # show any transient score events
        if hasattr(game, "score_events") and game.score_events:
            y = 75
            for event in game.score_events:
                # fade the text as it expires
                alpha = int(255 * (event["remaining"] / event["duration"]))
                text_surf = self.font.render(event["text"], True, (255, 255, 255))
                text_surf.set_alpha(alpha)
                screen.blit(text_surf, (10, y))
                y += 25

        # Show AI thinking message
        if hasattr(game, 'ai_thinking') and game.ai_thinking:
            thinking_text = self.font.render("The AI is thinking...", True, (255, 255, 255))
            screen.blit(thinking_text, (screen.get_width() // 2 - thinking_text.get_width() // 2, screen.get_height() // 2))

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
            
        # if game.current
