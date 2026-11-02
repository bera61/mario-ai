"""Mario'nun beyni: girdi -> gizli katman -> çıktı. DERS 1 burada."""

import numpy as np

from mario_game import ACTIONS

from .features import N_INPUTS

N_HIDDEN = 16
N_OUTPUTS = len(ACTIONS)
WEIGHT_SCALE = 0.5


class Brain:
    def __init__(self, rng):
        # w1: girdiden gizli katmana bağlantılar, şekli (16, 67)
        # w2: gizli katmandan çıktıya bağlantılar, şekli (7, 16)
        # b1, b2: her nöronun kendi eğilimi (bias)
        self.w1 = rng.normal(0.0, WEIGHT_SCALE, (N_HIDDEN, N_INPUTS))
        self.b1 = rng.normal(0.0, WEIGHT_SCALE, N_HIDDEN)
        self.w2 = rng.normal(0.0, WEIGHT_SCALE, (N_OUTPUTS, N_HIDDEN))
        self.b2 = rng.normal(0.0, WEIGHT_SCALE, N_OUTPUTS)
        # Nöron penceresi bu son değerleri okuyup çizer
        self.inputs = np.zeros(N_INPUTS)
        self.hidden = np.zeros(N_HIDDEN)
        self.outputs = np.zeros(N_OUTPUTS)

    def forward(self, inputs):
        self.inputs = inputs
        toplam = self.w1 @ inputs
        toplam = toplam + self.b1
        self.hidden = np.tanh(toplam)

        zbab = self.w2 @ self.hidden
        zbab = zbab + self.b2
        self.outputs = zbab
        return self.outputs


    def decide(self, inputs):
        """En yüksek çıktıya sahip aksiyonun numarasını döner."""
        return int(np.argmax(self.forward(inputs)))

    def copy(self):
        twin = Brain.__new__(Brain)
        for name, value in vars(self).items():
            setattr(twin, name, value.copy())
        return twin

    def save(self, path):
        np.savez(path, w1=self.w1, b1=self.b1, w2=self.w2, b2=self.b2)

    @classmethod
    def load(cls, path):
        brain = cls(np.random.default_rng(0))
        with np.load(path) as data:
            brain.w1, brain.b1 = data["w1"], data["b1"]
            brain.w2, brain.b2 = data["w2"], data["b2"]
        return brain
