"""Çalıştırmak için: python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from solver import solve

from mario_game import ACTIONS, Game, MarioEnv
from mario_game.constants import (
    BIG,
    BTN_JUMP,
    BTN_LEFT,
    BTN_RIGHT,
    BTN_RUN,
    CLEAR,
    DEAD,
    DYING,
    PLAYING,
    SMALL,
    TILE,
)
from mario_game.env import CELL_MARIO, GRID_COLS, GRID_ROWS
from mario_game.level import HIDDEN, PITS, QUESTION, SOLID, USED


class PhysicsTests(unittest.TestCase):
    def test_mario_stands_on_ground(self):
        game = Game()
        for _ in range(30):
            game.step()
        self.assertTrue(game.mario.on_ground)
        self.assertEqual(game.mario.y + game.mario.h, 13 * TILE)

    def test_running_is_faster_than_walking(self):
        walk, run = Game(), Game()
        for _ in range(120):
            walk.step(BTN_RIGHT)
            run.step(BTN_RIGHT | BTN_RUN)
        self.assertGreater(run.mario.x, walk.mario.x)

    def test_jump_height_clears_tallest_pipe(self):
        game = Game()
        game.step()
        start = game.mario.y
        top = start
        for _ in range(60):
            game.step(BTN_JUMP)
            top = min(top, game.mario.y)
        self.assertGreaterEqual(start - top, 4 * TILE - 1)

    def test_holding_jump_does_not_rejump(self):
        game = Game()
        game.step()
        for _ in range(100):
            game.step(BTN_JUMP)
        self.assertTrue(game.mario.on_ground)
        self.assertEqual(game.mario.vy, 0)

    def test_camera_only_moves_forward(self):
        game = Game()
        for _ in range(200):
            game.step(BTN_RIGHT | BTN_RUN)
        cam = game.cam_x
        for _ in range(200):
            game.step(BTN_LEFT)
        self.assertEqual(game.cam_x, cam)
        self.assertGreaterEqual(game.mario.x, cam)


class LevelTests(unittest.TestCase):
    def test_pits_have_no_ground(self):
        tiles = Game().level.tiles
        for first, last in PITS:
            for col in range(first, last + 1):
                self.assertNotIn(tiles[13][col], SOLID)

    def test_falling_in_pit_kills(self):
        game = Game()
        game.mario.x = 69.2 * TILE
        game.cam_x = game.mario.x - 112
        for _ in range(120):
            game.step()
        self.assertIn(game.state, (DYING, DEAD))

    def test_hitting_question_block_gives_coin(self):
        game = Game()
        game.mario.x = 16 * TILE + 2
        game.cam_x = 100.0
        game.step()
        for _ in range(30):
            game.step(BTN_JUMP)
        self.assertEqual(game.coins, 1)
        self.assertEqual(game.level.tiles[9][16], USED)

    def test_hidden_block_only_solid_from_below(self):
        game = Game()
        self.assertEqual(game.level.tiles[8][64], HIDDEN)
        self.assertNotIn(HIDDEN, SOLID)
        self.assertEqual(game.level.tiles[9][21], QUESTION)


class EnemyTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.step()
        self.goomba = self.game.enemies[0]
        self.goomba.active = True

    def test_touching_goomba_kills_small_mario(self):
        m = self.game.mario
        self.goomba.x, self.goomba.y = m.x + 4, m.y
        self.game.step()
        self.assertEqual(self.game.state, DYING)

    def test_stomp_squishes_goomba(self):
        m = self.game.mario
        self.goomba.x, self.goomba.y = m.x, 13 * TILE - 16
        m.y = self.goomba.y - m.h - 2
        m.vy = 3.0
        for _ in range(2):
            self.game.step()
        self.assertEqual(self.goomba.state, "squished")
        self.assertEqual(self.game.state, PLAYING)

    def test_big_mario_shrinks_instead_of_dying(self):
        m = self.game.mario
        self.game._grow()
        self.assertEqual(m.power, BIG)
        self.goomba.x, self.goomba.y = m.x + 4, m.y + m.h - 16
        self.game.step()
        self.assertEqual(self.game.state, PLAYING)
        self.assertEqual(m.power, SMALL)
        self.assertGreater(m.invuln, 0)

    def test_stomped_koopa_becomes_kickable_shell(self):
        koopa = next(e for e in self.game.enemies if e.kind == "koopa")
        koopa.active = True
        m = self.game.mario
        koopa.x, koopa.y = m.x, 13 * TILE - koopa.h
        m.y = koopa.y - m.h - 2
        m.vy = 3.0
        for _ in range(2):
            self.game.step()
        self.assertEqual(koopa.state, "shell")
        self.game._kick(koopa)
        self.assertEqual(koopa.state, "slide")
        self.assertNotEqual(koopa.vx, 0)


class FullLevelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solution = solve()

    def test_level_can_be_finished(self):
        self.assertIsNotNone(self.solution, "arama bayrağa ulaşan bir yol bulamadı")
        game = Game()
        for buttons in self.solution:
            game.step(buttons)
        self.assertTrue(game.flag_get)
        for _ in range(1500):
            game.step()
            if game.state == CLEAR:
                break
        self.assertEqual(game.state, CLEAR)

    def test_game_is_deterministic(self):
        a, b = Game(), Game()
        for buttons in self.solution:
            a.step(buttons)
            b.step(buttons)
        self.assertEqual(
            (a.mario.x, a.mario.y, a.frame, a.score), (b.mario.x, b.mario.y, b.frame, b.score)
        )


class EnvTests(unittest.TestCase):
    def test_reset_and_step_shapes(self):
        env = MarioEnv()
        obs, info = env.reset()
        self.assertEqual(obs.shape, (GRID_ROWS, GRID_COLS))
        self.assertEqual((obs == CELL_MARIO).sum(), 1)
        self.assertEqual(info["dead"], False)
        result = env.step(1)
        self.assertEqual(len(result), 5)

    def test_moving_right_gives_positive_reward(self):
        env = MarioEnv()
        env.reset()
        total = 0.0
        for _ in range(20):
            total += env.step(3)[1]
        self.assertGreater(total, 0)

    def test_death_terminates_episode(self):
        env = MarioEnv()
        env.reset()
        env.game.mario.x = 69.2 * TILE
        env.game.cam_x = env.game.mario.x - 112
        done = False
        for _ in range(60):
            *_, terminated, truncated, info = env.step(0)
            if terminated:
                done = True
                break
        self.assertTrue(done)
        self.assertTrue(info["dead"])
        self.assertLess(info["max_x"] + 1, env.game.level.width)

    def test_stuck_episode_is_truncated(self):
        env = MarioEnv(stuck_limit=40)
        env.reset()
        truncated = False
        for _ in range(20):
            *_, terminated, truncated, _info = env.step(0)
            if truncated:
                break
        self.assertTrue(truncated)

    def test_all_actions_are_valid(self):
        env = MarioEnv()
        env.reset()
        for action in range(len(ACTIONS)):
            env.step(action)


if __name__ == "__main__":
    unittest.main()
