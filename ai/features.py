"""Oyunu beynin okuyabileceği sayılara çevirir: Mario'nun çevresindeki 8x8'lik pencere.

Pencere Mario ile birlikte hareket eder, bu yüzden aynı engel bölümün neresinde
olursa olsun beyne aynı görünür.
"""

import numpy as np

from mario_game.constants import TILE
from mario_game.level import SOLID

WINDOW_ROWS = 8
WINDOW_COLS = 8
ROWS_ABOVE = 4  # Mario'nun ayak satırının üstünde kaç satır görülür
COLS_BEHIND = 1  # Mario'nun arkasında kaç sütun görülür
MARIO_CELL = (ROWS_ABOVE, COLS_BEHIND)
N_EXTRAS = 3  # yerde mi, yatay hız, dikey hız
N_INPUTS = WINDOW_ROWS * WINDOW_COLS + N_EXTRAS
EXTRA_NAMES = ("yerde", "hız x", "hız y")

CELL_BLOCK = 1.0
CELL_ENEMY = -1.0


def read_features(game):
    m = game.mario
    feet_row = int((m.y + m.h - 1) // TILE)
    center_col = int((m.x + m.w / 2) // TILE)
    top_row = feet_row - ROWS_ABOVE
    left_col = center_col - COLS_BEHIND

    values = np.zeros(N_INPUTS)
    tiles = game.level.tiles
    rows, cols = game.level.rows, game.level.cols
    for r in range(WINDOW_ROWS):
        row = top_row + r
        if 0 <= row < rows:
            cells = tiles[row]
            for c in range(WINDOW_COLS):
                col = left_col + c
                if 0 <= col < cols and cells[col] in SOLID:
                    values[r * WINDOW_COLS + c] = CELL_BLOCK

    for e in game.enemies:
        if e.active and e.state not in ("squished", "flipped"):
            r = int((e.y + e.h / 2) // TILE) - top_row
            c = int((e.x + e.w / 2) // TILE) - left_col
            if 0 <= r < WINDOW_ROWS and 0 <= c < WINDOW_COLS:
                values[r * WINDOW_COLS + c] = CELL_ENEMY

    base = WINDOW_ROWS * WINDOW_COLS
    values[base] = 1.0 if m.on_ground else 0.0
    values[base + 1] = m.vx / 2.5625
    values[base + 2] = m.vy / 4.0
    return values
