"""Oyun mantığı. Pygame'e bağlı değildir ve tamamen deterministiktir:
aynı tuş dizisi her zaman aynı sonucu verir. Eğitim sırasında pencere açmadan
çok hızlı çalışabilmesinin sebebi budur.
"""

from .constants import (
    BIG,
    BTN_JUMP,
    BTN_LEFT,
    BTN_RIGHT,
    BTN_RUN,
    CLEAR,
    DEAD,
    DYING,
    FIRE,
    FLAG,
    PLAYING,
    SCREEN_H,
    SCREEN_W,
    SMALL,
    TILE,
)
from .level import BRICK, ENEMY_SPAWNS, HIDDEN, QUESTION, SOLID, USED, Level

EPS = 0.001

# Fizik değerleri piksel/kare cinsindendir ve NES oyununa yakındır.
WALK_MAX = 1.5625
RUN_MAX = 2.5625
WALK_ACCEL = 0.0371
RUN_ACCEL = 0.0557
RELEASE_DECEL = 0.0508
SKID_DECEL = 0.1016
MAX_FALL = 4.0
# (kalkış hızı üst sınırı, ilk hız, tuş basılıyken yerçekimi, normal yerçekimi)
JUMP_TABLE = (
    (1.0, -4.125, 0.125, 0.4375),
    (2.31, -4.125, 0.117, 0.375),
    (99.0, -5.0, 0.156, 0.5625),
)
ENEMY_GRAVITY = 0.25
GOOMBA_SPEED = 0.5
SHELL_SPEED = 3.5
START_TIME = 400
FRAMES_PER_TICK = 24
INVULN_FRAMES = 120
STAR_FRAMES = 600
DEATH_FRAMES = 90
SMALL_H = 16
BIG_H = 30


class Entity:
    def __init__(self, kind, x, y, w, h, vx=0.0):
        self.kind = kind
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vx = vx
        self.vy = 0.0
        self.on_ground = False
        self.state = "walk"
        self.timer = 0
        self.active = False

    def overlaps(self, other):
        return (
            self.x < other.x + other.w
            and other.x < self.x + self.w
            and self.y < other.y + other.h
            and other.y < self.y + self.h
        )


class Mario(Entity):
    def __init__(self, x, y):
        super().__init__("mario", x, y, 12, SMALL_H)
        self.power = SMALL
        self.facing = 1
        self.invuln = 0
        self.star = 0
        self.air_max = WALK_MAX
        self.jump_gravity = JUMP_TABLE[0][2]
        self.fall_gravity = JUMP_TABLE[0][3]
        self.walk_phase = 0.0
        self.skidding = False


class Game:
    def __init__(self):
        self.lives = 3
        self.new_game()

    def new_game(self):
        self.lives = 3
        self.score = 0
        self.coins = 0
        self.reset_level()

    def reset_level(self):
        """Bölümü baştan başlatır. Skor, para ve can korunur."""
        self.level = Level()
        self.mario = Mario(40.0, 13 * TILE - SMALL_H)
        self.mario.on_ground = True
        self.enemies = [self._spawn_enemy(*spawn) for spawn in ENEMY_SPAWNS]
        self.items = []
        self.fireballs = []
        self.particles = []
        self.bumps = {}
        self.cam_x = 0.0
        self.time_left = START_TIME
        self.frame = 0
        self.state = PLAYING
        self.flag_get = False
        self.prev_buttons = 0
        self.dying_timer = 0
        self.pole_x = self.level.flag_col * TILE + TILE / 2
        self.flag_y = 3 * TILE + 2.0
        self.flag_sliding = False
        self.max_x = self.mario.x

    def _spawn_enemy(self, kind, col, row):
        h = 24 if kind == "koopa" else 16
        enemy = Entity(kind, col * TILE, (row + 1) * TILE - h, 16, h, -GOOMBA_SPEED)
        return enemy

    # ------------------------------------------------------------- ana döngü
    def step(self, buttons=0):
        """Oyunu bir kare ilerletir."""
        self.frame += 1
        pressed = buttons & ~self.prev_buttons
        self.prev_buttons = buttons

        if self.state == PLAYING:
            self._update_mario(buttons, pressed)
            if self.state == PLAYING:
                self._update_items()
                self._update_enemies()
                self._update_fireballs()
                self._mario_vs_enemies()
                self._mario_vs_items()
                self._update_timer()
        elif self.state == DYING:
            self._update_dying()
        elif self.state == FLAG:
            self._update_flag()

        self._update_bumps()
        self._update_particles()
        self._update_camera()

    # ------------------------------------------------------------ tile çarpışma
    def _tile(self, col, row):
        if 0 <= row < self.level.rows and 0 <= col < self.level.cols:
            return self.level.tiles[row][col]
        return 0

    def _solid(self, col, row):
        if col < 0 or col >= self.level.cols:
            return True
        return self._tile(col, row) in SOLID

    def _move_x(self, e):
        """Yatay hareket. Duvara çarptıysa True döner."""
        e.x += e.vx
        if e.vx == 0:
            return False
        col = int((e.x + e.w - EPS) // TILE) if e.vx > 0 else int(e.x // TILE)
        top = int(e.y // TILE)
        bottom = int((e.y + e.h - EPS) // TILE)
        for row in range(top, bottom + 1):
            if self._solid(col, row):
                e.x = col * TILE - e.w if e.vx > 0 else (col + 1) * TILE
                return True
        return False

    def _move_y(self, e):
        """Dikey hareket. Tavana çarpan sütunların listesini ve satırı döner."""
        prev_y = e.y
        e.y += e.vy
        e.on_ground = False
        left = int(e.x // TILE)
        right = int((e.x + e.w - EPS) // TILE)
        if e.vy > 0:
            row = int((e.y + e.h - EPS) // TILE)
            for col in range(left, right + 1):
                if self._solid(col, row):
                    e.y = row * TILE - e.h
                    e.vy = 0.0
                    e.on_ground = True
                    break
        elif e.vy < 0:
            row = int(e.y // TILE)
            hits = []
            for col in range(left, right + 1):
                tile = self._tile(col, row)
                hidden = (
                    e is self.mario and tile == HIDDEN and prev_y >= (row + 1) * TILE
                )
                if tile in SOLID or hidden:
                    hits.append(col)
            if hits:
                e.y = (row + 1) * TILE
                e.vy = 0.0
                return hits, row
        return [], 0

    # -------------------------------------------------------------------- Mario
    def _update_mario(self, buttons, pressed):
        m = self.mario
        direction = bool(buttons & BTN_RIGHT) - bool(buttons & BTN_LEFT)
        running = bool(buttons & BTN_RUN)

        self._apply_horizontal(m, direction, running)

        if pressed & BTN_JUMP and m.on_ground:
            speed = abs(m.vx)
            for limit, start_vy, hold, fall in JUMP_TABLE:
                if speed < limit:
                    m.vy = start_vy
                    m.jump_gravity = hold
                    m.fall_gravity = fall
                    break
            m.air_max = RUN_MAX if speed > WALK_MAX else WALK_MAX
            m.on_ground = False

        if pressed & BTN_RUN and m.power == FIRE:
            self._shoot_fireball()

        rising_with_jump = m.vy < 0 and buttons & BTN_JUMP
        m.vy = min(m.vy + (m.jump_gravity if rising_with_jump else m.fall_gravity), MAX_FALL)

        if self._move_x(m):
            m.vx = 0.0
        if m.x < self.cam_x:
            m.x = self.cam_x
            m.vx = max(m.vx, 0.0)

        was_rising = m.vy < 0
        hits, row = self._move_y(m)
        if was_rising and hits:
            center = m.x + m.w / 2
            col = min(hits, key=lambda c: abs(c * TILE + TILE / 2 - center))
            self._hit_block(col, row)

        m.walk_phase += abs(m.vx)
        m.invuln = max(0, m.invuln - 1)
        m.star = max(0, m.star - 1)
        self.max_x = max(self.max_x, m.x)

        if m.y > SCREEN_H:
            self._die()
        elif m.x + m.w >= self.pole_x:
            self._grab_flag()

    def _apply_horizontal(self, m, direction, running):
        m.skidding = False
        if m.on_ground:
            limit = RUN_MAX if running else WALK_MAX
            if direction:
                m.facing = direction
                if m.vx * direction < 0:
                    m.vx += direction * SKID_DECEL
                    m.skidding = True
                else:
                    m.vx += direction * (RUN_ACCEL if running else WALK_ACCEL)
            else:
                m.vx = _toward_zero(m.vx, RELEASE_DECEL)
            if abs(m.vx) > limit:
                m.vx = _clamp_down(m.vx, limit, RELEASE_DECEL)
        elif direction:
            fast = abs(m.vx) >= WALK_MAX
            if m.vx * direction >= 0:
                m.vx += direction * (RUN_ACCEL if fast else WALK_ACCEL)
            else:
                m.vx += direction * (SKID_DECEL if fast else RUN_ACCEL)
            m.vx = max(-m.air_max, min(m.air_max, m.vx))

    def _shoot_fireball(self):
        if len(self.fireballs) >= 2:
            return
        m = self.mario
        x = m.x + m.w if m.facing > 0 else m.x - 8
        ball = Entity("fireball", x, m.y + 8, 8, 8, 4.0 * m.facing)
        ball.vy = 1.0
        self.fireballs.append(ball)

    def _hurt(self):
        m = self.mario
        if m.power == SMALL:
            self._die()
            return
        m.power = SMALL
        m.y += BIG_H - SMALL_H
        m.h = SMALL_H
        m.invuln = INVULN_FRAMES

    def _die(self):
        m = self.mario
        fell = m.y > SCREEN_H
        self.state = DYING
        self.dying_timer = DEATH_FRAMES
        m.vx = 0.0
        m.vy = 0.0 if fell else -5.0

    def _update_dying(self):
        m = self.mario
        if self.dying_timer < DEATH_FRAMES - 20:
            m.vy = min(m.vy + 0.25, MAX_FALL)
            m.y += m.vy
        self.dying_timer -= 1
        if self.dying_timer <= 0:
            self.state = DEAD

    def _grab_flag(self):
        m = self.mario
        self.state = FLAG
        self.flag_get = True
        self.flag_sliding = True
        height_points = (192 - (m.y + m.h)) / (192 - 3 * TILE)
        self.score += 100 + int(max(0.0, min(1.0, height_points)) * 49) * 100
        m.x = self.pole_x - m.w
        m.vx = 0.0
        m.vy = 0.0

    def _update_flag(self):
        m = self.mario
        base = 12 * TILE
        if self.flag_sliding:
            self.flag_y = min(self.flag_y + 2.0, base - 16)
            if m.y + m.h < base:
                m.y = min(m.y + 2.0, base - m.h)
            elif self.flag_y >= base - 16:
                self.flag_sliding = False
                m.x = self.pole_x + 2
                m.facing = 1
            return
        m.vx = 1.25
        m.vy = min(m.vy + m.fall_gravity, MAX_FALL)
        self._move_x(m)
        self._move_y(m)
        m.walk_phase += m.vx
        if m.x >= (self.level.castle_col + 2) * TILE:
            self.score += self.time_left * 50
            self.state = CLEAR

    def _update_timer(self):
        if self.frame % FRAMES_PER_TICK == 0:
            self.time_left -= 1
            if self.time_left <= 0:
                self.time_left = 0
                self._die()

    # ------------------------------------------------------------------ bloklar
    def _hit_block(self, col, row):
        tile = self.level.tiles[row][col]
        content = self.level.contents.get((col, row))
        if tile in (QUESTION, HIDDEN) or (tile == BRICK and content):
            self.bumps[(col, row)] = 8
            self._release(col, row, content)
            if content == "multicoin":
                self.level.contents[(col, row)] = "multicoin_1"
                self.multicoin_left = 9
            elif content == "multicoin_1":
                self.multicoin_left -= 1
                if self.multicoin_left <= 0:
                    self.level.tiles[row][col] = USED
                    del self.level.contents[(col, row)]
            else:
                self.level.tiles[row][col] = USED
                self.level.contents.pop((col, row), None)
        elif tile == BRICK:
            if self.mario.power == SMALL:
                self.bumps[(col, row)] = 8
            else:
                self.level.tiles[row][col] = 0
                self.score += 50
                self._add_brick_particles(col, row)
        else:
            return
        self._kill_enemies_on_block(col, row)

    def _release(self, col, row, content):
        if content in ("coin", "multicoin", "multicoin_1"):
            self.coins += 1
            self.score += 200
            if self.coins >= 100:
                self.coins -= 100
                self.lives += 1
            self.particles.append(["coin", col * TILE, (row - 1) * TILE, 0.0, -3.5, 24])
            return
        if content == "mushroom" and self.mario.power != SMALL:
            content = "flower"
        item = Entity(content, col * TILE, row * TILE, 16, 16)
        item.state = "rise"
        item.timer = 32
        self.items.append(item)

    def _add_brick_particles(self, col, row):
        x, y = col * TILE, row * TILE
        for dx, dy, vx, vy in ((0, 0, -1, -5), (8, 0, 1, -5), (0, 8, -1, -3), (8, 8, 1, -3)):
            self.particles.append(["brick", x + dx, y + dy, float(vx), float(vy), 60])

    def _kill_enemies_on_block(self, col, row):
        left, right, top = col * TILE, (col + 1) * TILE, row * TILE
        for e in self.enemies:
            if e.active and _alive(e) and e.x < right and left < e.x + e.w:
                if abs(e.y + e.h - top) <= 2:
                    self._kill_enemy(e, 1 if e.x + e.w / 2 >= left + TILE / 2 else -1)

    def _update_bumps(self):
        for key in list(self.bumps):
            self.bumps[key] -= 1
            if self.bumps[key] <= 0:
                del self.bumps[key]

    # ------------------------------------------------------------------ eşyalar
    def _update_items(self):
        for item in self.items[:]:
            if item.state == "rise":
                item.y -= 0.5
                item.timer -= 1
                if item.timer <= 0:
                    item.state = "move"
                    if item.kind in ("mushroom", "1up"):
                        item.vx = 1.0
                    elif item.kind == "star":
                        item.vx = 1.5
                        item.vy = -4.0
                continue
            if item.kind == "flower":
                continue
            item.vy = min(item.vy + ENEMY_GRAVITY, MAX_FALL)
            if self._move_x(item):
                item.vx = -item.vx
            self._move_y(item)
            if item.kind == "star" and item.on_ground:
                item.vy = -4.0
            if item.y > SCREEN_H or item.x + item.w < self.cam_x - 32:
                self.items.remove(item)

    def _mario_vs_items(self):
        m = self.mario
        for item in self.items[:]:
            if m.overlaps(item):
                self.items.remove(item)
                self._collect(item.kind)

    def _collect(self, kind):
        m = self.mario
        if kind == "1up":
            self.lives += 1
            return
        self.score += 1000
        if kind == "star":
            m.star = STAR_FRAMES
        elif kind == "flower":
            if m.power == SMALL:
                self._grow()
            else:
                m.power = FIRE
        elif m.power == SMALL:
            self._grow()

    def _grow(self):
        m = self.mario
        m.power = BIG
        m.y -= BIG_H - SMALL_H
        m.h = BIG_H

    # ---------------------------------------------------------------- düşmanlar
    def _update_enemies(self):
        for e in self.enemies[:]:
            if not e.active:
                if e.x < self.cam_x + SCREEN_W + 8:
                    e.active = True
                else:
                    continue
            if e.state == "squished":
                e.timer -= 1
                if e.timer <= 0:
                    self.enemies.remove(e)
                continue
            if e.state == "flipped":
                e.vy += ENEMY_GRAVITY
                e.x += e.vx
                e.y += e.vy
                if e.y > SCREEN_H + 16:
                    self.enemies.remove(e)
                continue
            e.timer = max(0, e.timer - 1)
            e.vy = min(e.vy + ENEMY_GRAVITY, MAX_FALL)
            if self._move_x(e):
                e.vx = -e.vx
            self._move_y(e)
            behind = e.x + e.w < self.cam_x - 48
            ahead_shell = e.state == "slide" and e.x > self.cam_x + SCREEN_W + 48
            if e.y > SCREEN_H or behind or ahead_shell:
                self.enemies.remove(e)
        self._enemies_vs_enemies()

    def _enemies_vs_enemies(self):
        alive = [e for e in self.enemies if e.active and _alive(e)]
        for i, a in enumerate(alive):
            for b in alive[i + 1 :]:
                if not a.overlaps(b) or not _alive(a) or not _alive(b):
                    continue
                if a.state == "slide":
                    self._kill_enemy(b, 1 if a.vx > 0 else -1)
                elif b.state == "slide":
                    self._kill_enemy(a, 1 if b.vx > 0 else -1)
                else:
                    left, right = (a, b) if a.x <= b.x else (b, a)
                    left.vx = -abs(left.vx)
                    right.vx = abs(right.vx)

    def _kill_enemy(self, e, direction):
        e.state = "flipped"
        e.vx = float(direction)
        e.vy = -3.5
        self.score += 100

    def _mario_vs_enemies(self):
        m = self.mario
        for e in self.enemies:
            if not e.active or not _alive(e) or not m.overlaps(e):
                continue
            if m.star > 0:
                self._kill_enemy(e, m.facing)
            elif m.vy > 0 and m.y + m.h <= e.y + 10:
                self._stomp(e)
            elif e.state == "shell":
                self._kick(e)
            elif m.invuln == 0 and not (e.state == "slide" and e.timer > 0):
                self._hurt()
                if self.state != PLAYING:
                    return

    def _stomp(self, e):
        m = self.mario
        m.vy = -4.0
        m.y = e.y - m.h
        self.score += 100
        if e.kind == "goomba":
            e.state = "squished"
            e.timer = 30
            e.vx = 0.0
        elif e.state == "walk":
            e.state = "shell"
            e.y += e.h - 16
            e.h = 16
            e.vx = 0.0
        elif e.state == "slide":
            e.state = "shell"
            e.vx = 0.0
        else:
            self._kick(e)

    def _kick(self, e):
        m = self.mario
        direction = 1 if m.x + m.w / 2 < e.x + e.w / 2 else -1
        e.state = "slide"
        e.vx = SHELL_SPEED * direction
        e.timer = 12  # tekmeleyen Mario hemen canından olmasın
        self.score += 100

    # ---------------------------------------------------------------- ateş topu
    def _update_fireballs(self):
        for ball in self.fireballs[:]:
            ball.vy = min(ball.vy + 0.35, MAX_FALL)
            hit_wall = self._move_x(ball)
            self._move_y(ball)
            if ball.on_ground:
                ball.vy = -2.5
            hit_enemy = None
            for e in self.enemies:
                if e.active and _alive(e) and ball.overlaps(e):
                    hit_enemy = e
                    break
            if hit_enemy:
                self._kill_enemy(hit_enemy, 1 if ball.vx > 0 else -1)
            off_screen = (
                ball.x > self.cam_x + SCREEN_W or ball.x + ball.w < self.cam_x or ball.y > SCREEN_H
            )
            if hit_wall or hit_enemy or off_screen:
                self.fireballs.remove(ball)

    # ---------------------------------------------------------------- görsellik
    def _update_particles(self):
        for p in self.particles[:]:
            p[4] += 0.25
            p[1] += p[3]
            p[2] += p[4]
            p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)

    def _update_camera(self):
        target = self.mario.x - 112
        limit = self.level.width - SCREEN_W
        self.cam_x = max(self.cam_x, min(target, limit))


def _alive(e):
    return e.state not in ("squished", "flipped")


def _toward_zero(value, amount):
    if value > 0:
        return max(0.0, value - amount)
    return min(0.0, value + amount)


def _clamp_down(value, limit, amount):
    if value > 0:
        return max(limit, value - amount)
    return min(-limit, value + amount)
