"""Dersleri kontrol eder ve sıradaki adımı söyler: python check.py"""

import sys

import numpy as np

from ai import evolution
from ai.brain import N_HIDDEN, N_OUTPUTS, Brain
from ai.features import N_INPUTS
from ai.population import Result


def brain_arrays(brain):
    return (brain.w1, brain.b1, brain.w2, brain.b2)


def check_forward():
    rng = np.random.default_rng(1)
    brain = Brain(rng)
    inputs = rng.normal(size=N_INPUTS)
    outputs = brain.forward(inputs)
    hidden = np.tanh(brain.w1 @ inputs + brain.b1)
    assert np.array_equal(brain.inputs, inputs), "self.inputs kaydedilmemiş"
    assert brain.hidden.shape == (N_HIDDEN,), "self.hidden 16 değer olmalı"
    assert np.allclose(brain.hidden, hidden), "self.hidden yanlış hesaplanmış"
    assert np.allclose(brain.outputs, brain.w2 @ hidden + brain.b2), "self.outputs yanlış hesaplanmış"
    assert outputs is not None and np.shape(outputs) == (N_OUTPUTS,), "7 çıktı döndürülmeli"


def _result(max_x=500.0, frames=600, flag_get=False, died=True):
    return Result(max_x=max_x, frames=frames, flag_get=flag_get, died=died, coins=0, score=0)


def check_fitness():
    near, far = evolution.fitness(_result(max_x=200.0)), evolution.fitness(_result(max_x=1500.0))
    assert isinstance(far, (int, float, np.floating)), "puan bir sayı olmalı"
    assert far > near, "daha uzağa giden Mario daha yüksek puan almalı"
    winner = evolution.fitness(_result(max_x=3170.0, flag_get=True, died=False))
    almost = evolution.fitness(_result(max_x=3160.0))
    assert winner > almost, "bayrağa ulaşmak ulaşamamaktan iyi olmalı"


def check_mutate():
    rng = np.random.default_rng(2)
    brain = Brain(rng)
    before = [a.copy() for a in brain_arrays(brain)]
    child = evolution.mutate(brain, rng)
    assert isinstance(child, Brain), "mutate bir Brain döndürmeli"
    assert child is not brain, "kopya döndürülmeli"
    for old, now in zip(before, brain_arrays(brain)):
        assert np.array_equal(old, now), "asıl beyin değişmemeli, önce kopyala"
    for old, new in zip(before, brain_arrays(child)):
        assert old.shape == new.shape, "ağırlıkların şekli değişmemeli"
    names = ("w1", "b1", "w2", "b2")
    for name, old, new in zip(names, before, brain_arrays(child)):
        assert not np.array_equal(old, new), "çocuğun %s ağırlıkları değişmemiş" % name
    largest = max(np.abs(old - new).max() for old, new in zip(before, brain_arrays(child)))
    assert largest < 5, "mutasyon çok büyük, beyin tamamen bozuluyor"


def check_next_generation():
    rng = np.random.default_rng(3)
    brains = [Brain(rng) for _ in range(100)]
    scores = [float(i) for i in range(100)]
    children = evolution.next_generation(brains, scores, rng)
    assert len(children) == 100, "yeni nesil aynı sayıda olmalı"
    assert all(isinstance(c, Brain) for c in children), "yeni nesil Brain listesi olmalı"
    # Her çocuğa en çok benzeyen beyin büyük ihtimalle onun ebeveynidir
    parent_scores = []
    for child in children:
        distances = [np.abs(child.w1 - brain.w1).mean() for brain in brains]
        parent_scores.append(scores[int(np.argmin(distances))])
    assert np.mean(parent_scores) > 60, "yeni nesil çoğunlukla başarılı beyinlerden türemeli"
    assert len({id(c) for c in children}) == 100, "her çocuk ayrı bir kopya olmalı"


LESSONS = (
    ("Ders 1: Beyin düşünüyor (ai/brain.py, forward)", check_forward,
     "Şimdi python train.py ile nöronları canlı izleyebilirsin. Mario'lar henüz öğrenmiyor."),
    ("Ders 2: Başarı puanı (ai/evolution.py, fitness)", check_fitness, None),
    ("Ders 3: Mutasyon (ai/evolution.py, mutate)", check_mutate, None),
    ("Ders 4: Yeni nesil (ai/evolution.py, next_generation)", check_next_generation,
     "Evrim hazır! python train.py ile Mario'ların öğrenmesini izle."),
)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for name, check, reward in LESSONS:
        try:
            check()
        except NotImplementedError:
            print("[ ] %s\n    Sıradaki ders bu." % name)
            return
        except AssertionError as error:
            print("[X] %s\n    Sorun: %s" % (name, error))
            return
        except Exception as error:
            print("[X] %s\n    Kod hata verdi: %s: %s" % (name, type(error).__name__, error))
            return
        print("[OK] %s" % name)
        if reward:
            print("     %s" % reward)
    print("Bütün dersler tamam.")


if __name__ == "__main__":
    main()
