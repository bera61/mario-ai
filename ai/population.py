"""100 Mario'yu aynı anda oynatır ve nesilleri yönetir."""

from dataclasses import dataclass

import numpy as np

from mario_game import ACTIONS, Game
from mario_game.constants import DEAD, DYING, PLAYING

from . import evolution
from .brain import Brain
from .features import read_features

POPULATION_SIZE = 100
DECISION_FRAMES = 4  # Mario 4 karede bir karar verir
STUCK_FRAMES = 180  # 3 saniye ilerleyemeyen Mario elenir


@dataclass
class Result:
    max_x: float
    frames: int
    flag_get: bool
    died: bool
    coins: int
    score: int


class Agent:
    def __init__(self, brain):
        self.brain = brain
        self.game = Game()
        self.alive = True
        self.buttons = 0
        self.action = 0
        self.best_x = self.game.mario.x
        self.stuck = 0

    def step(self):
        game = self.game
        if game.frame % DECISION_FRAMES == 0:
            self.action = self.brain.decide(read_features(game))
            self.buttons = ACTIONS[self.action][1]
        game.step(self.buttons)

        if game.mario.x > self.best_x:
            self.best_x = game.mario.x
            self.stuck = 0
        else:
            self.stuck += 1
        if game.state != PLAYING or self.stuck >= STUCK_FRAMES:
            self.alive = False

    def result(self):
        game = self.game
        return Result(
            max_x=game.max_x,
            frames=game.frame,
            flag_get=game.flag_get,
            died=game.state in (DYING, DEAD),
            coins=game.coins,
            score=game.score,
        )


class Population:
    def __init__(self, seed=None, size=POPULATION_SIZE):
        self.rng = np.random.default_rng(seed)
        self.generation = 1
        self.history = []  # her nesil için (en iyi, ortalama) ilerleme yüzdesi
        self.best_score = None
        self.best_brain = None
        self.flag_count = 0
        self.evolving = True
        self.brains = [Brain(self.rng) for _ in range(size)]
        self._start_agents()

    def _start_agents(self):
        self.agents = [Agent(brain) for brain in self.brains]
        self.flag_x = self.agents[0].game.pole_x

    @property
    def finished(self):
        return not any(a.alive for a in self.agents)

    @property
    def alive_count(self):
        return sum(a.alive for a in self.agents)

    def step(self):
        for agent in self.agents:
            if agent.alive:
                agent.step()

    def leader(self):
        """En önde giden Mario. Hepsi elendiyse en uzağa gitmiş olan."""
        alive = [a for a in self.agents if a.alive]
        pool = alive or self.agents
        return max(pool, key=lambda a: a.game.mario.x)

    def next_generation(self):
        results = [agent.result() for agent in self.agents]
        scores = self._score(results)
        progress = [min(1.0, r.max_x / self.flag_x) * 100 for r in results]
        self.history.append((max(progress), sum(progress) / len(progress)))
        self.flag_count = sum(r.flag_get for r in results)

        best = int(np.argmax(scores))
        if self.best_score is None or scores[best] > self.best_score:
            self.best_score = scores[best]
            self.best_brain = self.brains[best].copy()

        try:
            brains = evolution.next_generation(self.brains, scores, self.rng)
            self.evolving = True
        except NotImplementedError:
            brains = [Brain(self.rng) for _ in self.brains]
            self.evolving = False
        self.brains = brains
        self.generation += 1
        self._start_agents()

    def _score(self, results):
        try:
            return [evolution.fitness(r) for r in results]
        except NotImplementedError:
            return [r.max_x for r in results]
