"""histplot / hist2dplot, mirroring mplhep/tests/test_basic.py."""
from __future__ import annotations

import numpy as np
import pytest

import plotlyhep as php
from helpers import BINS, DATA, H2D, MC1, MC2, XE, YE, traces


@pytest.fixture(autouse=True)
def _cms_default():
    php.style.use("CMS")


def test_simple():
    fig = php.figure()
    php.histplot(fig, MC1, BINS)
    outline, carrier = fig.data
    assert outline.line.shape == "hv" and outline.hoverinfo == "skip"
    # stairs with edges down to zero: first and last y are 0, plateau values are the bins
    assert outline.y[0] == 0 and outline.y[-1] == 0
    np.testing.assert_allclose(np.asarray(outline.y[1:-2]), MC1)
    assert len(carrier.x) == len(MC1) and carrier.marker.size == 0.1


@pytest.mark.image_compare(tolerance=4)
def test_histplot_step():
    fig = php.figure()
    php.histplot(fig, [MC1, MC2], BINS, label=["a", "b"])
    fig.update_xaxes(range=[0, 200])
    return fig


@pytest.mark.image_compare(tolerance=4)
def test_histplot_fill():
    fig = php.figure()
    php.histplot(fig, MC1, BINS, histtype="fill", color="rgba(87,144,252,0.5)")
    return fig


@pytest.mark.image_compare(tolerance=4)
def test_histplot_errorbar():
    fig = php.figure()
    php.histplot(fig, DATA, BINS, yerr=True, histtype="errorbar", color="black")
    return fig


def test_histplot_errorbar_values():
    fig = php.figure()
    php.histplot(fig, DATA, BINS, yerr=True, histtype="errorbar")
    (t,) = fig.data
    np.testing.assert_allclose(np.asarray(t.error_y.array), np.sqrt(DATA))
    np.testing.assert_allclose(np.asarray(t.x), 0.5 * (BINS[1:] + BINS[:-1]))


def test_histplot_stack():
    fig = php.figure()
    php.histplot(fig, [MC1, MC2], BINS, stack=True, label=["a", "b"])
    outlines = traces(fig, hoverinfo="skip")
    assert len(outlines) == 2
    top = np.asarray(outlines[1].y[1:-2]) if outlines[1].name == "b" else np.asarray(outlines[0].y[1:-2])
    np.testing.assert_allclose(top, MC1 + MC2)


@pytest.mark.image_compare(tolerance=4)
def test_histplot_stack_fill():
    """stacked fills must paint top-down so every layer stays visible"""
    fig = php.figure()
    php.histplot(fig, [MC2, MC1], BINS, stack=True, histtype="fill", color=["#f89c20", "#5790fc"], label=["b", "a"])
    return fig


def test_histplot_stack_fill_order():
    fig = php.figure()
    php.histplot(fig, [MC2, MC1], BINS, stack=True, histtype="fill", label=["b", "a"])
    fills = [t for t in fig.data if t.fill == "tozeroy"]
    # first drawn = tallest (the full stack), so it is covered by the later, lower layer
    assert np.nanmax(np.asarray(fills[0].y, float)) >= np.nanmax(np.asarray(fills[1].y, float))
    assert fills[0].legendrank > fills[1].legendrank  # legend keeps the given order, not the draw order


def test_histplot_density():
    fig = php.figure()
    php.histplot(fig, MC1, BINS, density=True)
    y = np.asarray(fig.data[0].y[1:-2])
    np.testing.assert_allclose((y * np.diff(BINS)).sum(), 1.0)


def test_histplot_no_edges():
    fig = php.figure()
    php.histplot(fig, MC1, BINS, edges=False)
    assert len(fig.data[0].x) == len(BINS)


def test_histplot_row_targets_panel():
    fig = php.ratio_figure("CMS")
    php.histplot(fig, MC1, BINS, row=2)
    assert all(t.xaxis == "x2" and t.yaxis == "y2" for t in fig.data)


def test_histplot_legend_shows_when_labelled():
    fig = php.figure()
    php.histplot(fig, MC1, BINS)
    assert fig.layout.showlegend is None or fig.layout.showlegend is False
    php.histplot(fig, MC2, BINS, label="b")
    assert fig.layout.showlegend is True


@pytest.mark.image_compare(tolerance=4)
def test_hist2dplot():
    fig = php.figure()
    php.hist2dplot(fig, H2D, XE, YE)
    return fig


def test_hist2dplot_values():
    fig = php.figure()
    t = php.hist2dplot(fig, H2D, XE, YE)
    assert t.type == "heatmap"
    np.testing.assert_allclose(np.asarray(t.z), H2D.T)
    assert len(t.x) == len(XE) - 1 and len(t.y) == len(YE) - 1


def test_bad_bins_raises():
    fig = php.figure()
    with pytest.raises(AssertionError):
        php.histplot(fig, MC1, BINS[:-3])
