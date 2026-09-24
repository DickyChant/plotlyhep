"""Shared inputs for the tests (deterministic), like mplhep/tests/helpers.py."""
from __future__ import annotations

import numpy as np

RNG = np.random.default_rng(42)
BINS = np.linspace(0, 200, 41)
CENTERS = 0.5 * (BINS[1:] + BINS[:-1])
DATA = np.histogram(RNG.normal(90, 25, 4000), BINS)[0].astype(float)
MC1 = np.histogram(RNG.normal(90, 25, 3000), BINS)[0] * 1.3
MC2 = np.histogram(RNG.exponential(60, 3000), BINS)[0] * 0.5
H2D, XE, YE = np.histogram2d(RNG.normal(0, 1, 5000), RNG.normal(0, 1, 5000), bins=[20, 15])


def traces(fig, **match):
    """Traces of a figure matching all given attributes (e.g. mode='markers', yaxis='y2')."""
    return [t for t in fig.data if all(getattr(t, k, None) == v for k, v in match.items())]


def annotation_texts(fig):
    return [a.text for a in fig.layout.annotations]
