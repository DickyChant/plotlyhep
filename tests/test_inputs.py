"""Input handling, mirroring mplhep/tests/test_inputs.py."""

from __future__ import annotations

import numpy as np
import pytest

import plotlyhep as php
from helpers import BINS, MC1


def test_list_input():
    fig = php.figure("CMS")
    php.histplot(fig, list(MC1), list(BINS))
    np.testing.assert_allclose(np.asarray(fig.data[0].y[1:-2]), MC1)


def test_default_bins():
    fig = php.figure("CMS")
    php.histplot(fig, [1, 2, 3])
    np.testing.assert_allclose(np.asarray(fig.data[0].x), [0, 0, 1, 2, 3, 3])


def test_yerr_array_and_list_of_arrays():
    fig = php.figure("CMS")
    php.histplot(fig, [MC1, MC1], BINS, yerr=[np.ones(40), 2 * np.ones(40)])
    carriers = [t for t in fig.data if t.error_y.array is not None]
    assert [float(c.error_y.array[0]) for c in carriers] == [1.0, 2.0]


def test_labels_per_histogram():
    fig = php.figure("CMS")
    php.histplot(fig, [MC1, MC1], BINS, label=["a", "b"])
    assert [t.name for t in fig.data if t.showlegend] == ["a", "b"]


def test_unknown_histtype():
    fig = php.figure("CMS")
    with pytest.raises(ValueError, match="histtype"):
        php.histplot(fig, MC1, BINS, histtype="bar")
