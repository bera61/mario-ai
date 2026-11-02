"""Oyunu pygame yüzeyine çizer. Oyun mantığına dokunmaz, sadece okur."""

import pygame

from . import level as lv
from . import sprites as sp
from .constants import DEAD, DYING, FIRE, SCREEN_H, SCREEN_W, SMALL, TILE

SKY = (92, 148, 252)
BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
BRICK_RED = (200, 76, 12)
BRICK_LIGHT = (252, 188, 176)
QUESTION_YELLOW = (252, 152, 56)
USED_BROWN = (136, 80, 16)
PIPE_GREEN = (0, 168, 0)
PIPE_LIGHT = (128, 208, 16)
PIPE_DARK = (0, 88, 0)
HILL_GREEN = (0, 168, 0)
BUSH_GREEN = (128, 208, 16)
GROUND_Y = 13 * TILE


class Renderer:
    def __init__(self):
        self.font = pygame.font.Font(None, 16)
        self.big_font = pygame.font.Font(None, 28)
        self.tile_images = _build_tiles()
        self.mario_sets = {
            "normal": _mario_frames(sp.MARIO_COLORS),
            "fire": _mario_frames(sp.FIRE_COLORS),
            "star": _mario_frames(sp.STAR_COLORS),
        }
        ec, ic = sp.ENEMY_COLORS, sp.ITEM_COLORS
        goomba = sp.make_sprite(sp.GOOMBA, ec)
        koopa = [sp.make_sprite(rows, ec) for rows in sp.KOOPA]
        self.goomba = [goomba, pygame.transform.flip(goomba, True, False)]
        self.goomba_squished = sp.make_sprite(sp.GOOMBA_SQUISHED, ec)
        self.koopa = koopa
        self.shell = sp.make_sprite(sp.SHELL, ec)
        self.items = {
            "mushroom": sp.make_sprite(sp.MUSHROOM, ic),
            "1up": sp.make_sprite(sp.MUSHROOM, {**ic, "R": (0, 168, 0)}),
            "flower": sp.make_sprite(sp.FLOWER, ic),
            "star": sp.make_sprite(sp.STAR, ic),
        }
        self.coin = sp.make_sprite(sp.COIN, ic)
        self.coin_small = pygame.transform.scale(self.coin, (8, 8))

    def draw(self, surface, game):
        cam = int(game.cam_x)
        surface.fill(SKY)
        self._draw_scenery(surface, game, cam)
        self._draw_castle(surface, game, cam)
        self._draw_flag(surface, game, cam)
        for item in game.items:
            if item.state == "rise":
                self._draw_item(surface, item, cam)
        self._draw_tiles(surface, game, cam)
        for item in game.items:
            if item.state != "rise":
                self._draw_item(surface, item, cam)
        self._draw_enemies(surface, game, cam)
        for ball in game.fireballs:
            center = (int(ball.x) - cam + 4, int(ball.y) + 4)
            pygame.draw.circle(surface, QUESTION_YELLOW, center, 4)
            pygame.draw.circle(surface, sp.ITEM_COLORS["R"], center, 2)
        self._draw_particles(surface, game, cam)
        self._draw_mario(surface, game, cam)
        self._draw_hud(surface, game)

    def center_text(self, surface, text):
        image = self.big_font.render(text, False, WHITE)
        shadow = self.big_font.render(text, False, BLACK)
        x = (SCREEN_W - image.get_width()) // 2
        y = (SCREEN_H - image.get_height()) // 2
        surface.blit(shadow, (x + 1, y + 1))
        surface.blit(image, (x, y))

    # ------------------------------------------------------------------ dekor
    def _draw_scenery(self, surface, game, cam):
        for kind, col, row in game.level.scenery:
            x = col * TILE - cam
            if x > SCREEN_W or x < -6 * TILE:
                continue
            if kind.startswith("hill"):
                big = kind == "hill_big"
                w, h = (5 * TILE, 3 * TILE) if big else (3 * TILE, 2 * TILE)
                self._hill(surface, x, w, h)
            elif kind.startswith("cloud"):
                self._puffs(surface, x, row * TILE + TILE, int(kind[-1]), WHITE)
            elif kind.startswith("bush"):
                self._puffs(surface, x, GROUND_Y, int(kind[-1]), BUSH_GREEN)

    def _hill(self, surface, x, w, h):
        rect = pygame.Rect(x, GROUND_Y - h, w, h * 2)
        pygame.draw.ellipse(surface, HILL_GREEN, rect)
        pygame.draw.ellipse(surface, PIPE_DARK, rect, 1)
        for dx, dy in ((w // 2, h // 3), (w // 3, h * 2 // 3), (w * 2 // 3, h * 2 // 3)):
            pygame.draw.rect(surface, PIPE_DARK, (x + dx - 2, GROUND_Y - h + dy, 3, 5))

    def _puffs(self, surface, x, bottom, count, color):
        for i in range(count + 1):
            rect = pygame.Rect(x + i * 14, bottom - 22, 22, 22)
            pygame.draw.ellipse(surface, color, rect)
        pygame.draw.rect(surface, color, (x + 8, bottom - 10, count * 14 + 8, 10))

    def _draw_castle(self, surface, game, cam):
        x = game.level.castle_col * TILE - cam
        if x > SCREEN_W or x < -6 * TILE:
            return
        wall = BRICK_RED
        base_h, top_h = 3 * TILE, 2 * TILE
        pygame.draw.rect(surface, wall, (x, GROUND_Y - base_h, 5 * TILE, base_h))
        pygame.draw.rect(surface, wall, (x + TILE, GROUND_Y - base_h - top_h, 3 * TILE, top_h))
        for i in range(5):
            pygame.draw.rect(surface, wall, (x + i * TILE + 2, GROUND_Y - base_h - 6, 10, 6))
        for i in range(3):
            pygame.draw.rect(
                surface, wall, (x + TILE + i * TILE + 2, GROUND_Y - base_h - top_h - 6, 10, 6)
            )
        pygame.draw.rect(surface, BLACK, (x + 2 * TILE, GROUND_Y - 2 * TILE, TILE, 2 * TILE))
        pygame.draw.rect(surface, BLACK, (x + TILE + 6, GROUND_Y - base_h - 20, 8, 12))
        pygame.draw.rect(surface, BLACK, (x + 3 * TILE + 2, GROUND_Y - base_h - 20, 8, 12))

    def _draw_flag(self, surface, game, cam):
        x = int(game.pole_x) - cam
        if x < -TILE or x > SCREEN_W + TILE:
            return
        pygame.draw.line(surface, PIPE_LIGHT, (x, 3 * TILE), (x, 12 * TILE))
        pygame.draw.circle(surface, PIPE_GREEN, (x, 3 * TILE - 2), 3)
        y = int(game.flag_y)
        pygame.draw.polygon(surface, WHITE, [(x - 1, y), (x - 15, y), (x - 1, y + 14)])

    # ---------------------------------------------------------------- bloklar
    def _draw_tiles(self, surface, game, cam):
        first = cam // TILE
        for row in range(game.level.rows):
            cells = game.level.tiles[row]
            for col in range(first, min(first + 18, game.level.cols)):
                tile = cells[col]
                if tile in (lv.EMPTY, lv.HIDDEN):
                    continue
                y = row * TILE
                bump = game.bumps.get((col, row))
                if bump:
                    y -= 4 - abs(bump - 4)
                if tile == lv.QUESTION:
                    image = self.tile_images["q%d" % ((game.frame // 16) % 3)]
                else:
                    image = self.tile_images[tile]
                surface.blit(image, (col * TILE - cam, y))

    def _draw_item(self, surface, item, cam):
        surface.blit(self.items[item.kind], (int(item.x) - cam, int(item.y)))

    def _draw_particles(self, surface, game, cam):
        for kind, x, y, *_ in game.particles:
            if kind == "coin":
                surface.blit(self.coin, (int(x) - cam, int(y)))
            else:
                pygame.draw.rect(surface, BRICK_RED, (int(x) - cam, int(y), 7, 7))

    # -------------------------------------------------------------- karakterler
    def _draw_enemies(self, surface, game, cam):
        for e in game.enemies:
            if not e.active:
                continue
            x, y = int(e.x) - cam, int(e.y)
            if e.kind == "goomba":
                if e.state == "squished":
                    image = self.goomba_squished
                else:
                    image = self.goomba[(game.frame // 12) % 2]
            elif e.state in ("shell", "slide") or e.h == 16:
                image = self.shell
            else:
                image = self.koopa[(game.frame // 12) % 2]
                if e.vx > 0:
                    image = pygame.transform.flip(image, True, False)
            if e.state == "flipped":
                image = pygame.transform.flip(image, False, True)
            surface.blit(image, (x, y))

    def _draw_mario(self, surface, game, cam):
        m = game.mario
        if m.invuln and game.frame % 4 < 2:
            return
        if m.star and game.frame % 8 < 4:
            frames = self.mario_sets["star"]
        elif m.power == FIRE:
            frames = self.mario_sets["fire"]
        else:
            frames = self.mario_sets["normal"]
        size = "small" if m.power == SMALL else "big"
        if game.state in (DYING, DEAD):
            image = frames["dead"]
            surface.blit(image, (int(m.x) - cam, int(m.y)))
            return
        if not m.on_ground:
            image = frames[size]["jump"]
        elif m.skidding and size == "small":
            image = frames[size]["skid"]
        elif abs(m.vx) > 0.1:
            image = frames[size]["run"][int(m.walk_phase / 6) % 3]
        else:
            image = frames[size]["stand"]
        if m.facing < 0:
            image = pygame.transform.flip(image, True, False)
        x = int(m.x + m.w / 2 - image.get_width() / 2) - cam
        y = int(m.y + m.h - _feet_offset(image))
        surface.blit(image, (x, y))

    # --------------------------------------------------------------------- HUD
    def _draw_hud(self, surface, game):
        def text(value, x, y):
            surface.blit(self.font.render(value, False, WHITE), (x, y))

        text("MARIO", 16, 6)
        text("%06d" % game.score, 16, 17)
        surface.blit(self.coin_small, (88, 18))
        text("x%02d" % game.coins, 98, 17)
        text("WORLD", 140, 6)
        text("1-1", 150, 17)
        text("TIME", 204, 6)
        text("%03d" % game.time_left, 208, 17)


def _feet_offset(image):
    """Sprite'ın altındaki boş satırları sayıp ayakların yerini bulur."""
    w, h = image.get_size()
    for y in range(h - 1, -1, -1):
        if any(image.get_at((x, y)).a for x in range(w)):
            return y + 1
    return h


def _mario_frames(colors):
    def make(rows):
        return sp.make_sprite(rows, colors)

    return {
        "small": {
            "stand": make(sp.SMALL_STAND),
            "run": [make(rows) for rows in sp.SMALL_RUN],
            "jump": make(sp.SMALL_JUMP),
            "skid": make(sp.SMALL_SKID),
        },
        "big": {
            "stand": make(sp.BIG_STAND),
            "run": [make(rows) for rows in sp.BIG_RUN],
            "jump": make(sp.BIG_JUMP),
        },
        "dead": make(sp.SMALL_DEAD),
    }


def _build_tiles():
    tiles = {
        lv.GROUND: _ground_tile(),
        lv.BRICK: _brick_tile(),
        lv.USED: _block_tile(USED_BROWN, BLACK),
        lv.HARD: _hard_tile(),
        lv.PIPE_TOP_L: _pipe_tile(True, True),
        lv.PIPE_TOP_R: _pipe_tile(True, False),
        lv.PIPE_BODY_L: _pipe_tile(False, True),
        lv.PIPE_BODY_R: _pipe_tile(False, False),
        "q0": _question_tile(QUESTION_YELLOW),
        "q1": _question_tile((228, 92, 16)),
        "q2": _question_tile((136, 80, 16)),
    }
    return tiles


def _ground_tile():
    s = pygame.Surface((TILE, TILE))
    s.fill(BRICK_RED)
    pygame.draw.line(s, BRICK_LIGHT, (0, 0), (15, 0))
    pygame.draw.line(s, BRICK_LIGHT, (0, 0), (0, 7))
    pygame.draw.line(s, BLACK, (15, 1), (15, 8))
    pygame.draw.line(s, BLACK, (0, 8), (15, 8))
    pygame.draw.line(s, BRICK_LIGHT, (0, 9), (7, 9))
    pygame.draw.line(s, BLACK, (8, 9), (8, 15))
    pygame.draw.line(s, BLACK, (0, 15), (15, 15))
    return s


def _brick_tile():
    s = pygame.Surface((TILE, TILE))
    s.fill(BRICK_RED)
    pygame.draw.line(s, BRICK_LIGHT, (0, 0), (15, 0))
    for y in (3, 7, 11, 15):
        pygame.draw.line(s, BLACK, (0, y), (15, y))
    for y, x in ((1, 7), (5, 3), (5, 11), (9, 7), (13, 3), (13, 11)):
        pygame.draw.line(s, BLACK, (x, y - 1), (x, y + 1))
    return s


def _block_tile(fill, edge):
    s = pygame.Surface((TILE, TILE))
    s.fill(fill)
    pygame.draw.rect(s, edge, (0, 0, TILE, TILE), 1)
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        s.set_at((x, y), BLACK)
    return s


def _hard_tile():
    s = pygame.Surface((TILE, TILE))
    s.fill(BRICK_RED)
    pygame.draw.polygon(s, BRICK_LIGHT, [(0, 0), (15, 0), (12, 3), (3, 3), (3, 12), (0, 15)])
    pygame.draw.polygon(s, BLACK, [(15, 15), (0, 15), (3, 12), (12, 12), (12, 3), (15, 0)])
    return s


def _question_tile(color):
    s = _block_tile(color, BLACK)
    pygame.draw.lines(s, WHITE, False, [(5, 5), (6, 3), (10, 3), (11, 5), (8, 8), (8, 10)], 2)
    pygame.draw.rect(s, WHITE, (7, 12, 2, 2))
    return s


def _pipe_tile(top, left):
    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    if top:
        s.fill(PIPE_GREEN)
        pygame.draw.rect(s, BLACK, (0, 0, TILE, TILE), 1)
        pygame.draw.line(s, BLACK, (0, 15), (15, 15))
        if left:
            pygame.draw.rect(s, PIPE_LIGHT, (3, 1, 4, 14))
            pygame.draw.line(s, (0, 0, 0, 0), (15, 1), (15, 14))
            pygame.draw.line(s, PIPE_GREEN, (15, 1), (15, 14))
        else:
            pygame.draw.line(s, PIPE_GREEN, (0, 1), (0, 14))
            pygame.draw.rect(s, PIPE_DARK, (11, 1, 4, 14))
    elif left:
        pygame.draw.rect(s, PIPE_GREEN, (2, 0, 14, TILE))
        pygame.draw.line(s, BLACK, (2, 0), (2, 15))
        pygame.draw.rect(s, PIPE_LIGHT, (5, 0, 4, TILE))
    else:
        pygame.draw.rect(s, PIPE_GREEN, (0, 0, 14, TILE))
        pygame.draw.line(s, BLACK, (13, 0), (13, 15))
        pygame.draw.rect(s, PIPE_DARK, (9, 0, 4, TILE))
    return s
