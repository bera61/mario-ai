# Mario 1-1 AI

Mario'nun deneye deneye World 1-1'i bitirmeyi öğreneceği proje. Oyun tamamen Python ile
yazıldı, ROM veya dışarıdan resim dosyası gerekmez.

## AI: 100 Mario ile evrim

Her Mario'nun küçük bir beyni var (67 girdi, 16 gizli nöron, 7 çıktı). En iyiler seçilip
mutasyonla çoğalır. Çekirdeği dersler halinde kendimiz yazıyoruz:

```bash
python check.py
```

Bu komut hangi dersin tamam olduğunu ve sıradakini söyler.

| Ders | Dosya | Konu |
| --- | --- | --- |
| 1 | `ai/brain.py` | Beynin hesabı (`forward`) |
| 2 | `ai/evolution.py` | Başarı puanı (`fitness`) |
| 3 | `ai/evolution.py` | Mutasyon (`mutate`) |
| 4 | `ai/evolution.py` | Yeni nesil (`next_generation`) |

Ders 1 bitince canlı nöron penceresi açılabilir:

```bash
python train.py
```

En iyi beyni izlemek için: `python train.py --watch`

## Oynamak

```bash
python play.py
```

| Tuş | Görev |
| --- | --- |
| Ok tuşları veya A/D | Hareket |
| Space, Yukarı, W veya Z | Zıplama (basılı tutunca daha yükseğe) |
| Shift veya X | Koşma, ateş gücü varken ateş |
| R | Yeniden başlatma |
| Esc | Çıkış |

## Genel AI arayüzü

Başka yöntemleri denemek için Gymnasium benzeri ortam da var:

```python
from mario_game import MarioEnv

env = MarioEnv(frame_skip=4)
obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(3)  # 3 = right_run
env.render()  # isteğe bağlı, eğitimde çağırma
```

- **Gözlem:** 15x16 tablo. 0 boş, 1 katı blok, 2 Mario, 3 düşman, 4 eşya.
- **Aksiyonlar:** `ACTIONS` listesindeki 7 tuş kombinasyonu.
- **Ödül:** `default_reward` geçicidir. `MarioEnv(reward_fn=...)` ile değiştirilebilir.
- **Bitiş:** ölüm veya bayrak `terminated`, uzun süre ilerleyememek `truncated` verir.
- **Zıplama:** yerdeyken tuşa yeni basmak gerekir, basılı tutmak tekrar zıplatmaz.

Oyun deterministiktir: aynı tuş dizisi her zaman aynı sonucu verir.

## Dosyalar

- `mario_game/engine.py`: fizik ve oyun kuralları (pygame kullanmaz)
- `mario_game/level.py`: 1-1 haritası
- `mario_game/env.py`: AI ortamı
- `mario_game/renderer.py`, `sprites.py`: çizim
- `tests/solver.py`: bölümün bitirilebildiğini kanıtlayan arama (AI değildir)

## Testler

```bash
python -m unittest discover tests
```

## Yasal not

Bu proje resmi değildir ve ticari amaç taşımaz; yalnızca eğitim amaçlıdır. Nintendo ile
bağlantısı yoktur, Nintendo tarafından desteklenmez. Super Mario ve ilgili karakterler
Nintendo'nun markası ve fikri mülkiyetidir. Depoda ROM veya orijinal oyun dosyası yoktur.
