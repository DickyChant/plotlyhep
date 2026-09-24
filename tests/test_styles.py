"""Templates, mirroring mplhep/tests/test_styles.py."""

from __future__ import annotations

import plotly.io as pio
import pytest

import plotlyhep as php
from plotlyhep._units import PT
from plotlyhep.styles import ROOT_EM, template, template_json

CMS_CYCLE = ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"]


def test_templates_registered():
    assert "hep_cms" in pio.templates and "hep_atlas" in pio.templates


@pytest.mark.parametrize("exp", ["CMS", "ATLAS"])
def test_use_style(exp):
    php.style.use(exp)
    assert pio.templates.default == f"hep_{exp.lower()}"
    fig = php.figure()
    assert fig.layout.template.to_plotly_json() == pio.templates[f"hep_{exp.lower()}"].to_plotly_json()


def test_use_style_self_consistent():
    php.style.use("CMS")
    a = template("CMS").to_plotly_json()
    b = pio.templates["hep_cms"].to_plotly_json()
    assert a == b


def test_style_cms_values():
    L = template("CMS").layout
    assert list(L.colorway) == CMS_CYCLE
    assert L.font.size == pytest.approx(26 * PT)  # 26 pt at 100 dpi
    assert L.xaxis.ticks == "inside" and L.xaxis.mirror == "allticks" and L.xaxis.showgrid is False
    assert L.xaxis.ticklen == pytest.approx(12 * PT) and L.xaxis.minor.ticklen == pytest.approx(6 * PT)
    assert L.width == 1000 and L.height == 1000


def test_style_atlas_values():
    L = template("ATLAS").layout
    assert L.font.size == pytest.approx(14 * PT)
    assert L.width == 800 and L.height == 600
    assert L.xaxis.linewidth == pytest.approx(1 * PT)


def test_figsize():
    assert php.figsize_px("CMS") == (1000, 1000)
    assert php.figsize_px("ATLAS") == (800, 600)


def test_template_json_transparent():
    t = template_json("CMS", transparent=True)
    assert t["layout"]["paper_bgcolor"] == "rgba(0,0,0,0)" and t["layout"]["plot_bgcolor"] == "rgba(0,0,0,0)"
    assert template_json("CMS")["layout"]["paper_bgcolor"] == "white"


def test_root_template_geometry():
    t = php.root_template(800, 600, label_size=0.035, title_size=0.04, margins=(0.1, 0.1, 0.1, 0.1), tick_len=0.03).layout
    assert (t.margin.l, t.margin.r, t.margin.t, t.margin.b) == (80, 80, 60, 60)
    assert t.font.size == pytest.approx(ROOT_EM * 0.035 * 600)
    assert t.xaxis.mirror is True and t.xaxis.ticks == "inside"  # frame box, ticks bottom/left only
    assert t.xaxis.ticklen == pytest.approx(0.03 * 600 * 0.8)  # 3 % of the plot area height
    assert t.yaxis.ticklen == pytest.approx(0.03 * 800 * 0.8)


@pytest.mark.image_compare(tolerance=4)
def test_style_cms():
    php.style.use("CMS")
    fig = php.figure()
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 10])
    return fig


@pytest.mark.image_compare(tolerance=4)
def test_style_atlas():
    php.style.use("ATLAS")
    fig = php.figure()
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 10])
    return fig


@pytest.mark.image_compare(tolerance=4)
def test_style_root():
    import plotly.graph_objects as go

    fig = go.Figure(layout=dict(template=php.root_template(800, 600)))
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 10])
    return fig


def test_figure_scale_keeps_proportions():
    """a 500 px CMS figure has half the fonts, ticks and margins of the 1000 px one"""
    full = php.figure("CMS")
    half = php.figure("CMS", width=500, height=500)
    assert (half.layout.width, half.layout.height) == (500, 500)
    tf, th = full.layout.template.layout, half.layout.template.layout
    assert th.font.size == pytest.approx(tf.font.size / 2)
    assert th.xaxis.ticklen == pytest.approx(tf.xaxis.ticklen / 2)
    assert th.xaxis.tickfont.size == pytest.approx(tf.xaxis.tickfont.size / 2)
    assert th.margin.l == pytest.approx(tf.margin.l / 2)
    assert list(th.colorway) == list(tf.colorway)
    third = php.figure("CMS", scale=1 / 3)
    assert (third.layout.width, third.layout.height) == (333, 333)
