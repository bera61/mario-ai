"""Canlı pencere: solda 100 Mario, sağda öndeki Mario'nun nöronları, altta gelişim grafiği."""

import numpy as np
import pygame

from mario_game.constants import SCREEN_H, SCREEN_W
from mario_game.renderer import Renderer

from .brain import N_HIDDEN, N_OUTPUTS
from .features import EXTRA_NAMES, MARIO_CELL, N_EXTRAS, WINDOW_COLS, WINDOW_ROWS

GAME_SCALE = 2
GAME_W = SCREEN_W * GAME_SCALE
GAME_H = SCREEN_H * GAME_SCALE
PANEL_W = 608
WINDOW_W = GAME_W + PANEL_W
WINDOW_H = 640

SURFACE = (20, 24, 31)
GRID_LINE = (44, 50, 60)
INK = (230, 232, 236)
MUTED = (150, 156, 166)
MID = (70, 76, 88)
NEGATIVE = (79, 163, 224)
POSITIVE = (232, 141, 58)
BEST_LINE = (60, 168, 110)
AVERAGE_LINE = (160, 124, 216)

ACTION_NAMES = ("bekle", "sağ", "sağ + zıpla", "koş", "koş + zıpla", "zıpla", "sol")
TOP_EDGES = 50  # sadece o an en çok etkisi olan bağlantılar çizilir
SPEEDS = {pygame.K_1: 1, pygame.K_2: 4, pygame.K_3: 16}
TURBO_CHUNK = 300


def value_color(value):
    t = float(np.clip(value, -1.0, 1.0))
    pole = POSITIVE if t >= 0 else NEGATIVE
    t = abs(t)
    return tuple(int(MID[i] + (pole[i] - MID[i]) * t) for i in range(3))


class Viewer:
    def __init__(self, population, on_finished, title="Mario AI"):
        pygame.init()
        self.population = population
        self.on_finished = on_finished
        self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption(title)
        self.game_surface = pygame.Surface((SCREEN_W, SCREEN_H))
        self.edge_layer = pygame.Surface((PANEL_W, WINDOW_H), pygame.SRCALPHA)
        self.renderer = Renderer()
        self.font = pygame.font.SysFont("segoeui", 13)
        self.title_font = pygame.font.SysFont("segoeui", 15, bold=True)
        self.big_font = pygame.font.SysFont("segoeui", 22, bold=True)
        self.clock = pygame.time.Clock()
        self.speed = 1
        self.turbo = False
        self.paused = False
        small = self.renderer.mario_sets["normal"]["small"]["stand"].copy()
        small.set_alpha(110)
        self.ghost = small
        self._layout()

    def _layout(self):
        self.cell = 26
        self.grid_x, self.grid_y = 24, 56
        points = []
        for r in range(WINDOW_ROWS):
            for c in range(WINDOW_COLS):
                points.append(
                    (self.grid_x + c * self.cell + 13, self.grid_y + r * self.cell + 13)
                )
        self.extras_y = self.grid_y + WINDOW_ROWS * self.cell + 18
        for i in range(N_EXTRAS):
            points.append((self.grid_x + 13, self.extras_y + i * 28 + 13))
        self.input_points = points
        self.hidden_points = [(330, 64 + i * 32) for i in range(N_HIDDEN)]
        self.output_points = [(470, 90 + i * 66) for i in range(N_OUTPUTS)]

    # -------------------------------------------------------------------- döngü
    def run(self):
        running = True
        while running:
            running = self._handle_events()
            if not self.paused:
                self._advance()
            self.draw()
            pygame.display.flip()
            self.clock.tick(0 if self.turbo else 60)
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_t:
                    self.turbo = not self.turbo
                elif event.key in SPEEDS:
                    self.speed = SPEEDS[event.key]
                    self.turbo = False
        return True

    def _advance(self):
        for _ in range(TURBO_CHUNK if self.turbo else self.speed):
            self.population.step()
            if self.population.finished:
                self.on_finished(self.population)
                break

    # --------------------------------------------------------------------- çizim
    def draw(self):
        self.window.fill(SURFACE)
        leader = self.population.leader()
        self._draw_game(leader)
        self._draw_network(leader)
        self._draw_stats()
        self._draw_chart()

    def _draw_game(self, leader):
        game = leader.game
        surface = self.game_surface
        self.renderer.draw(surface, game)
        cam = int(game.cam_x)
        ghost_h = self.ghost.get_height()
        for agent in self.population.agents:
            if agent.alive and agent is not leader:
                m = agent.game.mario
                surface.blit(self.ghost, (int(m.x) - cam, int(m.y + m.h) - ghost_h))
        pygame.transform.scale(surface, (GAME_W, GAME_H), self.window.subsurface((0, 0, GAME_W, GAME_H)))

    def _text(self, text, x, y, color=INK, font=None):
        image = (font or self.font).render(text, True, color)
        self.window.blit(image, (x, y))
        return image.get_width()

    def _draw_network(self, leader):
        brain = leader.brain
        ox = GAME_W
        self._text("Gördüğü", ox + self.grid_x, 22, INK, self.title_font)
        self._text("Gizli nöronlar", ox + 282, 22, INK, self.title_font)
        self._text("Kararı", ox + 452, 22, INK, self.title_font)

        self._draw_edges(brain, ox)
        self._draw_inputs(brain, ox)
        for i, (x, y) in enumerate(self.hidden_points):
            pygame.draw.circle(self.window, value_color(brain.hidden[i]), (ox + x, y), 10)
            pygame.draw.circle(self.window, GRID_LINE, (ox + x, y), 10, 1)
        self._draw_outputs(brain, leader.action, ox)

        y = WINDOW_H - 62
        pygame.draw.rect(self.window, POSITIVE, (ox + 24, y + 3, 12, 12))
        self._text("artı: blok / aktif nöron", ox + 42, y)
        pygame.draw.rect(self.window, NEGATIVE, (ox + 24, y + 23, 12, 12))
        self._text("eksi: düşman / baskılanan nöron", ox + 42, y + 20)
        self._text("Boşluk: duraklat   1 2 3: hız   T: turbo   Esc: çıkış", ox + 290, y + 20, MUTED)

    def _draw_inputs(self, brain, ox):
        for r in range(WINDOW_ROWS):
            for c in range(WINDOW_COLS):
                value = brain.inputs[r * WINDOW_COLS + c]
                rect = (ox + self.grid_x + c * self.cell, self.grid_y + r * self.cell, self.cell - 2, self.cell - 2)
                color = value_color(value) if value else (32, 37, 46)
                pygame.draw.rect(self.window, color, rect, border_radius=3)
                if (r, c) == MARIO_CELL:
                    pygame.draw.rect(self.window, INK, rect, 2, border_radius=3)
        base = WINDOW_ROWS * WINDOW_COLS
        for i, name in enumerate(EXTRA_NAMES):
            y = self.extras_y + i * 28
            rect = (ox + self.grid_x, y, self.cell - 2, self.cell - 2)
            pygame.draw.rect(self.window, value_color(brain.inputs[base + i]), rect, border_radius=3)
            self._text(name, ox + self.grid_x + 32, y + 4, MUTED)

    def _draw_outputs(self, brain, action, ox):
        for i, (x, y) in enumerate(self.output_points):
            chosen = i == action
            pygame.draw.circle(self.window, value_color(brain.outputs[i] / 3), (ox + x, y), 12)
            pygame.draw.circle(self.window, INK if chosen else GRID_LINE, (ox + x, y), 12, 2 if chosen else 1)
            font = self.title_font if chosen else self.font
            self._text(ACTION_NAMES[i], ox + x + 18, y - 9, INK if chosen else MUTED, font)
            self._text("%+.1f" % brain.outputs[i], ox + x + 18, y + 9, MUTED)

    def _draw_edges(self, brain, ox):
        layer = self.edge_layer
        layer.fill((0, 0, 0, 0))
        self._edge_group(layer, brain.w1 * brain.inputs, self.input_points, self.hidden_points)
        self._edge_group(layer, brain.w2 * brain.hidden, self.hidden_points, self.output_points)
        self.window.blit(layer, (ox, 0))

    def _edge_group(self, layer, effects, starts, ends):
        strengths = np.abs(effects).ravel()
        peak = strengths.max()
        if peak <= 0:
            return
        count = min(TOP_EDGES, strengths.size)
        for index in np.argpartition(strengths, -count)[-count:]:
            if strengths[index] <= 0:
                continue
            end, start = np.unravel_index(index, effects.shape)
            pole = POSITIVE if effects[end, start] > 0 else NEGATIVE
            alpha = int(40 + 180 * strengths[index] / peak)
            pygame.draw.line(layer, (*pole, alpha), starts[start], ends[end])

    def _draw_stats(self):
        pop = self.population
        x, y = 14, GAME_H + 10
        self._text("Nesil %d" % pop.generation, x, y, INK, self.big_font)
        self._text("Yaşayan: %d / %d" % (pop.alive_count, len(pop.agents)), x, y + 34)
        self._text("Bayrağa ulaşan: %d" % pop.flag_count, x, y + 54)
        if self.paused:
            mode = "duraklatıldı"
        elif self.turbo:
            mode = "turbo"
        else:
            mode = "%dx" % self.speed
        self._text("Hız: %s" % mode, x, y + 74)
        if not pop.evolving:
            self._text("Evrim yok: python check.py", x, y + 96, MUTED)

    def _draw_chart(self):
        left, right, top, bottom = 196, GAME_W - 76, GAME_H + 32, WINDOW_H - 24
        self._text("Bölümde ilerleme (%)", left, GAME_H + 8, INK, self.title_font)
        for percent in (0, 50, 100):
            y = bottom - (bottom - top) * percent // 100
            pygame.draw.line(self.window, GRID_LINE, (left, y), (right, y))
            self._text(str(percent), left - 24, y - 9, MUTED)

        history = self.population.history
        if not history:
            self._text("İlk nesil bitince çizilecek", left + 60, top + 36, MUTED)
            return
        self._text("nesil %d" % len(history), right - 40, bottom + 2, MUTED)
        x_step = (right - left) / max(1, len(history) - 1)
        for series, color, name in ((1, AVERAGE_LINE, "ort."), (0, BEST_LINE, "en iyi")):
            points = [
                (left + i * x_step, bottom - (bottom - top) * row[series] / 100)
                for i, row in enumerate(history)
            ]
            if len(points) > 1:
                pygame.draw.lines(self.window, color, False, points, 2)
            pygame.draw.circle(self.window, color, points[-1], 4)
            label_y = points[-1][1] - 9
            # İki değer birbirine yakınsa etiketler üst üste binmesin
            if series == 1 and history[-1][0] - history[-1][1] < 14:
                label_y += 16
            self._text("%s %.0f" % (name, history[-1][series]), right + 8, label_y)
