"""World 1-1 haritası. Satır 0 en üstte, zemin 13-14. satırlarda."""

from .constants import TILE

EMPTY = 0
GROUND = 1
BRICK = 2
QUESTION = 3
USED = 4
HARD = 5
PIPE_TOP_L = 6
PIPE_TOP_R = 7
PIPE_BODY_L = 8
PIPE_BODY_R = 9
HIDDEN = 10  # görünmez blok: sadece alttan vurulunca ortaya çıkar

SOLID = frozenset(
    {GROUND, BRICK, QUESTION, USED, HARD, PIPE_TOP_L, PIPE_TOP_R, PIPE_BODY_L, PIPE_BODY_R}
)

LEVEL_COLS = 212
LEVEL_ROWS = 15
PITS = ((69, 70), (86, 88), (153, 154))
FLAG_COL = 198
CASTLE_COL = 202

# (sütun, yükseklik)
PIPES = ((28, 2), (38, 3), (46, 4), (57, 4), (163, 2), (179, 2))

# (tür, sütun, satır) - satır, düşmanın ayaklarının bulunduğu satırdır
ENEMY_SPAWNS = (
    ("goomba", 22, 12),
    ("goomba", 40, 12),
    ("goomba", 51, 12),
    ("goomba", 52.5, 12),
    ("goomba", 80, 4),
    ("goomba", 82, 4),
    ("goomba", 97, 12),
    ("goomba", 98.5, 12),
    ("koopa", 107, 12),
    ("goomba", 114, 12),
    ("goomba", 115.5, 12),
    ("goomba", 124, 12),
    ("goomba", 125.5, 12),
    ("goomba", 128, 12),
    ("goomba", 129.5, 12),
    ("goomba", 174, 12),
    ("goomba", 175.5, 12),
)


class Level:
    def __init__(self):
        self.cols = LEVEL_COLS
        self.rows = LEVEL_ROWS
        self.width = LEVEL_COLS * TILE
        self.tiles = [[EMPTY] * LEVEL_COLS for _ in range(LEVEL_ROWS)]
        self.contents = {}  # (sütun, satır) -> blok içeriği
        self.flag_col = FLAG_COL
        self.castle_col = CASTLE_COL
        self.scenery = _build_scenery()
        self._build()

    def _put(self, col, row, tile, content=None):
        self.tiles[row][col] = tile
        if content:
            self.contents[(col, row)] = content

    def _bricks(self, first, last, row):
        for col in range(first, last + 1):
            self._put(col, row, BRICK)

    def _pillar(self, col, height):
        for row in range(13 - height, 13):
            self._put(col, row, HARD)

    def _build(self):
        pit_cols = {c for first, last in PITS for c in range(first, last + 1)}
        for col in range(LEVEL_COLS):
            if col not in pit_cols:
                self.tiles[13][col] = GROUND
                self.tiles[14][col] = GROUND

        for col, height in PIPES:
            top = 13 - height
            self._put(col, top, PIPE_TOP_L)
            self._put(col + 1, top, PIPE_TOP_R)
            for row in range(top + 1, 13):
                self._put(col, row, PIPE_BODY_L)
                self._put(col + 1, row, PIPE_BODY_R)

        self._put(16, 9, QUESTION, "coin")
        self._put(20, 9, BRICK)
        self._put(21, 9, QUESTION, "mushroom")
        self._put(22, 9, BRICK)
        self._put(23, 9, QUESTION, "coin")
        self._put(24, 9, BRICK)
        self._put(22, 5, QUESTION, "coin")

        self._put(64, 8, HIDDEN, "1up")

        self._put(77, 9, BRICK)
        self._put(78, 9, QUESTION, "mushroom")
        self._put(79, 9, BRICK)
        self._bricks(80, 87, 5)

        self._bricks(91, 93, 5)
        self._put(94, 5, QUESTION, "coin")
        self._put(94, 9, BRICK, "multicoin")

        self._put(100, 9, BRICK)
        self._put(101, 9, BRICK, "star")

        self._put(106, 9, QUESTION, "coin")
        self._put(109, 9, QUESTION, "coin")
        self._put(109, 5, QUESTION, "mushroom")
        self._put(112, 9, QUESTION, "coin")

        self._put(118, 9, BRICK)
        self._bricks(121, 123, 5)

        self._put(128, 5, BRICK)
        self._put(129, 5, QUESTION, "coin")
        self._put(130, 5, QUESTION, "coin")
        self._put(131, 5, BRICK)
        self._bricks(129, 130, 9)

        # Merdivenler
        for i in range(4):
            self._pillar(134 + i, i + 1)
            self._pillar(143 - i, i + 1)
            self._pillar(148 + i, i + 1)
            self._pillar(158 - i, i + 1)
        self._pillar(152, 4)

        self._bricks(168, 169, 9)
        self._put(170, 9, QUESTION, "coin")
        self._put(171, 9, BRICK)

        # Son merdiven ve bayrak
        for i in range(8):
            self._pillar(181 + i, i + 1)
        self._pillar(189, 8)
        self._put(FLAG_COL, 12, HARD)


def _build_scenery():
    """Sadece görsel öğeler. Orijinaldeki gibi 48 sütunda bir tekrar eder."""
    scenery = []
    for base in range(0, LEVEL_COLS, 48):
        scenery += [
            ("hill_big", base, 0),
            ("hill_small", base + 16, 0),
            ("cloud1", base + 8, 3),
            ("cloud1", base + 19, 2),
            ("cloud3", base + 27, 3),
            ("cloud2", base + 36, 2),
            ("bush3", base + 11, 0),
            ("bush1", base + 23, 0),
            ("bush2", base + 41, 0),
        ]
    return scenery
