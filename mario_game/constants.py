"""Oyunun her yerinde kullanılan sabitler."""

TILE = 16
SCREEN_W = 256
SCREEN_H = 240
FPS = 60

# Tuşlar bit bayrağı olarak tutulur: BTN_RIGHT | BTN_JUMP gibi birleştirilebilir.
BTN_LEFT = 1
BTN_RIGHT = 2
BTN_JUMP = 4
BTN_RUN = 8

# Oyun durumları
PLAYING = "playing"
DYING = "dying"  # ölüm animasyonu oynuyor
DEAD = "dead"  # animasyon bitti, can düşülebilir
FLAG = "flag"  # bayrağa tutundu, kaleye yürüyor
CLEAR = "clear"  # bölüm bitti

# Mario'nun güç seviyeleri
SMALL = 0
BIG = 1
FIRE = 2
