import sys
import pygame
from src.menu import Menu
from src.tiles import AssetLoader
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Carcassonne AI")
    clock = pygame.time.Clock()

    game = None

    def start_game():
        nonlocal game
        from src.game import Game
        game = Game(screen)
        game.start()

    menu = Menu(screen, start_callback=start_game)
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                if game and game.running:
                    game.handle_event(event)
                else:
                    menu.handle_event(event)

        if game and game.running:
            game.update(dt)
        else:
            menu.update(dt)

        screen.fill((30, 30, 30))
        if game and game.running:
            game.render()
        else:
            menu.render()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
