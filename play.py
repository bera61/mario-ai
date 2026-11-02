"""Bölümü klavyeyle oyna: python play.py"""

import pygame

from mario_game.constants import (
    BTN_JUMP,
    BTN_LEFT,
    BTN_RIGHT,
    BTN_RUN,
    CLEAR,
    DEAD,
    FPS,
    SCREEN_H,
    SCREEN_W,
)
from mario_game.engine import Game
from mario_game.renderer import Renderer

SCALE = 3


def read_buttons(keys):
    buttons = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        buttons |= BTN_LEFT
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        buttons |= BTN_RIGHT
    if keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_z]:
        buttons |= BTN_JUMP
    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_x]:
        buttons |= BTN_RUN
    return buttons


def main():
    pygame.init()
    window = pygame.display.set_mode((SCREEN_W * SCALE, SCREEN_H * SCALE))
    pygame.display.set_caption("Mario 1-1  |  Oklar: hareket, Space: zipla, Shift: kos/ates, R: yeniden")
    screen = pygame.Surface((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    renderer = Renderer()
    game = Game()
    game_over = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.new_game()
                    game_over = False

        if not game_over:
            game.step(read_buttons(pygame.key.get_pressed()))
            if game.state == DEAD:
                game.lives -= 1
                if game.lives <= 0:
                    game_over = True
                else:
                    game.reset_level()

        renderer.draw(screen, game)
        if game_over:
            renderer.center_text(screen, "GAME OVER - R")
        elif game.state == CLEAR:
            renderer.center_text(screen, "BOLUM BITTI! - R")

        pygame.transform.scale(screen, window.get_size(), window)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
