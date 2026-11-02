"""AI için ortam. Arayüz Gymnasium'a benzer: reset() ve step(action).

Gözlem, ekran piksellerinin sadeleştirilmiş hali olan 15x16'lık bir tablodur.
Her hücre CELL_* değerlerinden birini alır.
"""

import numpy as np

from .constants import (
    BTN_JUMP,
    BTN_LEFT,
    BTN_RIGHT,
    BTN_RUN,
    DEAD,
    DYING,
    FPS,
    PLAYING,
    SCREEN_H,
    SCREEN_W,
    TILE,
)
from .engine import Game
from .level import SOLID

CELL_EMPTY = 0
CELL_SOLID = 1
CELL_MARIO = 2
CELL_ENEMY = 3
CELL_ITEM = 4

GRID_ROWS = SCREEN_H // TILE
GRID_COLS = SCREEN_W // TILE

ACTIONS = (
    ("noop", 0),
    ("right", BTN_RIGHT),
    ("right_jump", BTN_RIGHT | BTN_JUMP),
    ("right_run", BTN_RIGHT | BTN_RUN),
    ("right_run_jump", BTN_RIGHT | BTN_RUN | BTN_JUMP),
    ("jump", BTN_JUMP),
    ("left", BTN_LEFT),
)


def default_reward(prev_info, info):
    """Geçici ödül: ilerleme ödüllenir, ölüm cezalandırılır. AI aşamasında birlikte
    yeniden tasarlayacağız; MarioEnv(reward_fn=...) ile kolayca değiştirilebilir."""
    reward = (info["max_x"] - prev_info["max_x"]) * 0.1
    if info["dead"]:
        reward -= 15.0
    if info["flag_get"]:
        reward += 50.0
    return reward


class MarioEnv:
    def __init__(self, frame_skip=4, stuck_limit=600, reward_fn=default_reward):
        self.frame_skip = frame_skip
        self.stuck_limit = stuck_limit  # bu kadar kare ilerleme olmazsa bölüm kesilir
        self.reward_fn = reward_fn
        self.action_count = len(ACTIONS)
        self.game = Game()
        self._stuck_frames = 0
        self._window = None
        self._screen = None
        self._renderer = None
        self._clock = None

    def reset(self):
        self.game.new_game()
        self._stuck_frames = 0
        return self.observation(), self.info()

    def step(self, action):
        game = self.game
        prev_info = self.info()
        buttons = ACTIONS[action][1]
        for _ in range(self.frame_skip):
            game.step(buttons)
            if game.state != PLAYING:
                break

        info = self.info()
        if info["max_x"] > prev_info["max_x"]:
            self._stuck_frames = 0
        else:
            self._stuck_frames += self.frame_skip

        terminated = info["dead"] or info["flag_get"]
        truncated = not terminated and self._stuck_frames >= self.stuck_limit
        reward = self.reward_fn(prev_info, info)
        return self.observation(), reward, terminated, truncated, info

    def info(self):
        game = self.game
        return {
            "x_pos": game.mario.x,
            "max_x": game.max_x,
            "y_pos": game.mario.y,
            "score": game.score,
            "coins": game.coins,
            "time": game.time_left,
            "power": game.mario.power,
            "dead": game.state in (DYING, DEAD),
            "flag_get": game.flag_get,
        }

    def observation(self):
        game = self.game
        grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.int8)
        tiles = game.level.tiles
        first_col = int((game.cam_x + TILE / 2) // TILE)
        last = game.level.cols - first_col
        for row in range(GRID_ROWS):
            cells = tiles[row]
            for c in range(min(GRID_COLS, last)):
                if cells[first_col + c] in SOLID:
                    grid[row, c] = CELL_SOLID
        for item in game.items:
            self._mark(grid, item, CELL_ITEM)
        for enemy in game.enemies:
            if enemy.active and enemy.state not in ("squished", "flipped"):
                self._mark(grid, enemy, CELL_ENEMY)
        self._mark(grid, game.mario, CELL_MARIO)
        return grid

    def _mark(self, grid, entity, value):
        col = int((entity.x + entity.w / 2 - self.game.cam_x) // TILE)
        row = int((entity.y + entity.h / 2) // TILE)
        if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS:
            grid[row, col] = value

    def render(self, scale=3, fps=FPS):
        """İzlemek için pencereye çizer. Eğitimde çağrılmadığı sürece pygame açılmaz."""
        import pygame

        from .renderer import Renderer

        if self._window is None:
            pygame.init()
            self._window = pygame.display.set_mode((SCREEN_W * scale, SCREEN_H * scale))
            pygame.display.set_caption("Mario AI")
            self._screen = pygame.Surface((SCREEN_W, SCREEN_H))
            self._renderer = Renderer()
            self._clock = pygame.time.Clock()
        pygame.event.pump()
        self._renderer.draw(self._screen, self.game)
        pygame.transform.scale(self._screen, self._window.get_size(), self._window)
        pygame.display.flip()
        if fps:
            self._clock.tick(fps / self.frame_skip)

    def close(self):
        if self._window is not None:
            import pygame

            pygame.quit()
            self._window = None
