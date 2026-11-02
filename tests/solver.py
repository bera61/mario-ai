"""Bölümün oyunun kurallarıyla bitirilebildiğini kanıtlayan arama.
AI değildir: oyunu kopyalayıp geleceği deneyerek çözüm bulur, öğrenmez.
"""

import copy
import heapq
import itertools

from mario_game import Game
from mario_game.constants import BTN_JUMP, BTN_LEFT, BTN_RIGHT, BTN_RUN, PLAYING

CHUNK_FRAMES = 6
CHOICES = (
    BTN_RIGHT | BTN_RUN,
    BTN_RIGHT | BTN_RUN | BTN_JUMP,
    BTN_RIGHT,
    BTN_RIGHT | BTN_JUMP,
    BTN_LEFT,
    0,
)


def solve(max_nodes=40000):
    """Bayrağa ulaşan kare kare tuş listesini döner, bulamazsa None."""
    counter = itertools.count()
    start = Game()
    heap = [(0.0, next(counter), start, ())]
    seen = set()
    nodes = 0
    while heap and nodes < max_nodes:
        _, _, game, path = heapq.heappop(heap)
        for buttons in CHOICES:
            nodes += 1
            child = copy.deepcopy(game)
            for _ in range(CHUNK_FRAMES):
                child.step(buttons)
                if child.state != PLAYING:
                    break
            child_path = (path, buttons)
            if child.flag_get:
                return _flatten(child_path)
            if child.state != PLAYING:
                continue
            key = _state_key(child)
            if key in seen:
                continue
            seen.add(key)
            # En ileri gideni önce dene, geçen süre hafif ceza olsun
            priority = -child.mario.x + child.frame * 0.5
            heapq.heappush(heap, (priority, next(counter), child, child_path))
    return None


def _state_key(game):
    m = game.mario
    enemies = sum(1 for e in game.enemies if e.state == "walk")
    return (
        int(m.x // 4),
        int(m.y // 4),
        int(m.vx * 2),
        int(m.vy),
        m.on_ground,
        m.power,
        enemies,
        game.prev_buttons & BTN_JUMP,
    )


def _flatten(path):
    chunks = []
    while path:
        path, buttons = path
        chunks.append(buttons)
    frames = []
    for buttons in reversed(chunks):
        frames += [buttons] * CHUNK_FRAMES
    return frames
