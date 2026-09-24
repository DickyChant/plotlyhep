"""Ratio panels and gridspec geometry, mirroring mplhep's test_layouts / test_styles_ratio_plot."""

from __future__ import annotations

import numpy as np
import pytest

import plotlyhep as php
from helpers import BINS, DATA, MC1, traces


@pytest.mark.parametrize("ratios,hspace", [((3, 1), 0.05), ((3, 1), 0.2), ((2, 1, 1), 0.1)])
def test_gridspec_domains_match_matplotlib(ratios, hspace):
    """our domains are matplotlib's GridSpec positions, expressed in the plot area"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from plotlyhep._units import SUBPLOT

    fig, axes = plt.subplots(len(ratios), 1, gridspec_kw={"height_ratios": list(ratios), "hspace": hspace})
    doms = php.gridspec_domains(ratios, hspace)
    total = SUBPLOT["top"] - SUBPLOT["bottom"]
    for ax, (lo, hi) in zip(axes, doms):
        pos = ax.get_position()
        assert lo == pytest.approx((pos.y0 - SUBPLOT["bottom"]) / total, abs=1e-6)
        assert hi == pytest.approx((pos.y1 - SUBPLOT["bottom"]) / total, abs=1e-6)
    plt.close(fig)


def test_ratio_figure_axes():
    fig = php.ratio_figure("CMS", ratio_range=(0.5, 1.5), ratio_title="Data / MC")
    L = fig.layout
    assert L.xaxis.showticklabels is False and L.xaxis.matches == "x2"  # shared x, labels only below
    assert L.yaxis.domain[0] > L.yaxis2.domain[1]  # main panel above the ratio panel
    assert list(L.yaxis2.range) == [0.5, 1.5] and L.yaxis2.title.text == "Data / MC"
    assert any(s.type == "line" and s.y0 == 1 for s in L.shapes)  # reference line at 1


def test_ratioplot_values():
    fig = php.ratio_figure("CMS")
    mc = MC1.copy()
    mc[3] = 0.0  # an empty denominator bin
    php.ratioplot(fig, DATA, mc, BINS, den_w2=mc, band=True)
    pts = traces(fig, mode="markers", yaxis="y2")[0]
    r = np.asarray(pts.y, float)
    ok = mc > 0
    np.testing.assert_allclose(r[ok], DATA[ok] / mc[ok])
    assert np.isnan(r[~ok]).all()
    np.testing.assert_allclose(np.asarray(pts.error_y.array, float)[ok], np.sqrt(DATA[ok]) / mc[ok])
    band = [t for t in fig.data if t.fill == "tonexty"]
    assert len(band) == 1 and band[0].yaxis == "y2"


@pytest.mark.image_compare(tolerance=4)
def test_ratio_panel():
    fig = php.ratio_figure("CMS", height_ratios=(3, 1), hspace=0.05)
    php.histplot(fig, MC1, BINS, label="MC")
    php.histplot(fig, DATA, BINS, yerr=True, histtype="errorbar", color="black", label="Data")
    php.ratioplot(fig, DATA, MC1, BINS, den_w2=MC1)
    fig.update_xaxes(range=[0, 200])
    return fig
