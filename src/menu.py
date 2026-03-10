import pygame

class Menu:
    def __init__(self, screen, start_callback=None):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 48)
        self.options = ["Start Game", "Quit"]
        self.selected = 0
        self.start_callback = start_callback

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self.activate()

    def activate(self):
        choice = self.options[self.selected]
        if choice == "Quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif choice == "Start Game":
            if self.start_callback:
                self.start_callback()

    def update(self, dt):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))
        for idx, text in enumerate(self.options):
            color = (255, 255, 0) if idx == self.selected else (255, 255, 255)
            label = self.font.render(text, True, color)
            rect = label.get_rect(center=(self.screen.get_width() // 2,
                                          self.screen.get_height() // 2 + idx * 60))
            self.screen.blit(label, rect)
