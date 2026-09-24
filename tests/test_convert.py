"""matplotlib <-> Plotly conversion."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from helpers import BINS, DATA, MC1
from plotlyhep.convert import from_mpl, html_to_mathtext, mathtext_to_html, to_mpl


def test_mathtext_to_html():
    assert mathtext_to_html("m$_{jj}$ [GeV]") == "m<sub>jj</sub> [GeV]"
    assert mathtext_to_html("$x^{2}$ and $E_T$") == "x<sup>2</sup> and E<sub>T</sub>"
    assert mathtext_to_html(r"$\mathrm{p}_{\mathrm{T}}$") == "p<sub>T</sub>"


def test_html_to_mathtext():
    assert html_to_mathtext("m<sub>jj</sub> [GeV]") == "m$_{jj}$ [GeV]"
    assert html_to_mathtext("<b>CMS</b> <i>x</i>") == "CMS x"


@pytest.fixture
def mpl_figure():
    import mplhep as hep

    hep.style.use("CMS")
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
    hep.histplot(MC1, BINS, label="MC", ax=ax)
    ax.errorbar(0.5 * (BINS[1:] + BINS[:-1]), DATA, yerr=np.sqrt(DATA), fmt=".", color="black", label="Data")
    ax.plot([0, 200], [100, 300], "--", color="red", label="line")
    ax.annotate("peak", xy=(90, 340), xytext=(140, 400), arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 450)
    ax.set_xlabel("m$_{jj}$ [GeV]")
    ax.set_ylabel("Events")
    ax.legend()
    yield fig
    plt.close(fig)


def test_from_mpl_traces(mpl_figure):
    p = from_mpl(mpl_figure)
    names = [t.name for t in p.data if t.showlegend]
    assert set(names) == {"MC", "Data", "line"}
    step = [t for t in p.data if t.name == "MC" and t.hoverinfo == "skip"][0]
    assert step.line.shape == "hv"
    data = [t for t in p.data if t.name == "Data"][0]
    assert data.error_y.array is not None and data.mode == "markers"
    np.testing.assert_allclose(np.asarray(data.error_y.array), np.sqrt(DATA))
    line = [t for t in p.data if t.name == "line"][0]
    assert line.line.dash == "dash"


def test_from_mpl_axes_and_texts(mpl_figure):
    p = from_mpl(mpl_figure)
    assert list(p.layout.xaxis.range) == [0, 200] and list(p.layout.yaxis.range) == [0, 450]
    assert p.layout.xaxis.tickmode == "array" and "100" in list(p.layout.xaxis.ticktext)
    texts = [a.text for a in p.layout.annotations]
    assert "m<sub>jj</sub> [GeV]" in texts and "Events" in texts
    arrow = [a for a in p.layout.annotations if a.text == "peak"][0]
    assert arrow.showarrow and arrow.ax != 0
    assert p.layout.showlegend and p.layout.legend.font.size > 0


def test_legend_order_preserved(mpl_figure):
    p = from_mpl(mpl_figure)
    ranked = sorted([t for t in p.data if t.showlegend], key=lambda t: t.legendrank)
    drawn = [t.get_text() for t in mpl_figure.axes[0].get_legend().get_texts()]
    assert [t.name for t in ranked] == drawn


def test_roundtrip_data(mpl_figure):
    p = from_mpl(mpl_figure)
    f2 = to_mpl(p)
    ax2 = f2.axes[0]
    assert ax2.get_xlim() == (0, 200) and ax2.get_ylim() == (0, 450)
    lines = [l for l in ax2.lines if l.get_label() == "line"]
    assert lines and lines[0].get_linestyle() == "--"
    plt.close(f2)


def test_to_mpl_bar_and_heatmap():
    import plotly.graph_objects as go

    p = go.Figure(layout=dict(width=600, height=400, xaxis=dict(range=[0, 3]), yaxis=dict(range=[0, 5])))
    p.add_trace(go.Bar(x=[0.5, 1.5, 2.5], y=[1, 4, 2], width=[1, 1, 1], marker=dict(color="rgba(0,0,255,1)")))
    p.add_trace(go.Heatmap(x=[0.5, 1.5, 2.5], y=[0.5, 1.5], z=[[1, 2, 3], [4, 5, 6]]))
    f = to_mpl(p)
    ax = f.axes[0]
    assert len(ax.patches) == 3 and len(ax.collections) == 1
    plt.close(f)
