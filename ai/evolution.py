"""Evrim kuralları: kim başarılı, kim çoğalır, çocuk nasıl değişir. DERS 2, 3 ve 4 burada."""


def fitness(result):
    puan = result.max_x
    puan = puan - result.frames * 0.1
    if result.flag_get:
        puan = puan + 5000
    return puan


def mutate(brain, rng):
    child = brain.copy()
    child.w1 = child.w1 + rng.normal(0.0, 0.1, child.w1.shape)
    child.b1 = child.b1 + rng.normal(0.0, 0.1, child.b1.shape)
    child.w2 = child.w2 + rng.normal(0.0, 0.1, child.w2.shape)
    child.b2 = child.b2 + rng.normal(0.0, 0.1, child.b2.shape)
    return child


def next_generation(brains, scores, rng):
    sira = sorted(range(len(brains)), key = lambda i: scores[i], reverse =True)

    best_ones = [brains[i] for i in sira [:30]]
    new = [best_ones[0].copy()]

    while len(new) < len(brains):
        parent = best_ones[rng.integers(len(best_ones))]
        new.append(mutate(parent, rng))
    return new
