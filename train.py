"""Mario'ları eğit ve nöronlarını canlı izle: python train.py
En iyi beyni tekrar izlemek için: python train.py --watch
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from ai.brain import Brain
from ai.features import N_INPUTS
from ai.population import Population
from ai.viewer import Viewer

BEST_PATH = Path(__file__).parent / "best_brain.npz"


def forward_is_ready():
    try:
        Brain(np.random.default_rng(0)).forward(np.zeros(N_INPUTS))
    except NotImplementedError:
        return False
    return True


def train(seed):
    population = Population(seed=seed)
    saved = [None]

    def on_finished(pop):
        pop.next_generation()
        best, average = pop.history[-1]
        print("Nesil %3d | en iyi %%%5.1f | ortalama %%%5.1f | bayrak %d" % (len(pop.history), best, average, pop.flag_count))
        if pop.best_brain is not saved[0] and pop.evolving:
            pop.best_brain.save(BEST_PATH)
            saved[0] = pop.best_brain

    Viewer(population, on_finished).run()


def watch():
    if not BEST_PATH.exists():
        print("Henüz kayıtlı beyin yok. Önce: python train.py")
        return
    population = Population(size=1)
    population.brains = [Brain.load(BEST_PATH)]
    population._start_agents()
    Viewer(population, lambda pop: pop._start_agents(), "Mario AI - en iyi beyin").run()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="kayıtlı en iyi beyni izle")
    parser.add_argument("--seed", type=int, default=None, help="tekrarlanabilir çalışma için")
    args = parser.parse_args()

    if not forward_is_ready():
        print("Beyin henüz düşünemiyor. Önce Ders 1'i bitir: ai/brain.py, sonra python check.py")
        return
    if args.watch:
        watch()
    else:
        train(args.seed)


if __name__ == "__main__":
    main()
