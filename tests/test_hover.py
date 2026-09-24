"""Hover carries the physics: bin range and content ± error, and decorative traces stay silent."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import plotlyhep as php


def test_histplot_hover():
    fig = php.figure("CMS")
    bins = np.array([0.0, 10.0, 20.0])
    H = np.array([4.0, 9.0])
    php.histplot(fig, H, bins, yerr=True, label="Data", histtype="errorbar")
    (t,) = fig.data
    assert "customdata" in t and t.hovertemplate.startswith("<b>Data</b>")
    assert list(t.customdata[1]) == [10.0, 20.0, 9.0, 3.0]  # [lo, hi, content, sqrt(content)]


def test_step_outline_is_silent_and_carrier_answers():
    fig = php.figure("CMS")
    bins = np.array([0.0, 10.0, 20.0])
    H = np.array([4.0, 9.0])
    php.histplot(fig, H, bins, label="MC")
    outline, carrier = fig.data
    assert outline.hoverinfo == "skip" and carrier.hovertemplate and carrier.marker.size == 0.1


def test_from_mpl_hover():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import mplhep as hep

    fig, ax = plt.subplots()
    hep.histplot(np.array([4.0, 9.0]), np.array([0.0, 10.0, 20.0]), label="MC", ax=ax)
    ax.errorbar([5, 15], [4, 9], yerr=[2, 3], fmt="o", label="Data")
    p = php.convert.from_mpl(fig)
    kinds = {(t.name, t.hoverinfo, bool(t.hovertemplate)) for t in p.data}
    assert ("MC", "skip", False) in kinds  # the drawn outline is silent
    assert any(n == "MC" and tmpl for n, hi, tmpl in kinds)  # the carrier speaks
    data = [t for t in p.data if t.name == "Data"][0]
    assert "−%{customdata[1]" in data.hovertemplate and data.error_y.array is not None
