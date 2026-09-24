"""Experiment labels, mirroring mplhep/tests/test_labels.py."""
from __future__ import annotations

import pytest

import plotlyhep as php
from helpers import annotation_texts
from plotlyhep.label import SCALE_EXP, SCALE_LUMI, _lumi_line, exp_label, exp_text


@pytest.fixture
def fig():
    php.style.use("CMS")
    return php.figure()


def test_lumi_line_variants():
    assert _lumi_line(lumi=138, com=13.6) == "138 fb⁻¹ (13.6 TeV)"
    assert _lumi_line(year=2018, lumi=59.8, com=13) == "2018, 59.8 fb⁻¹ (13 TeV)"
    assert _lumi_line(com=13.6) == "(13.6 TeV)"
    assert _lumi_line(lumi=139, lumi_format="{0:.0f}", com=None) == "139 fb⁻¹"
    assert _lumi_line() == "(13 TeV)"          # mplhep's default com
    assert _lumi_line(com=None) == ""


@pytest.mark.parametrize("loc", [0, 1, 2, 3, 4])
def test_exp_text_loc(fig, loc):
    exp_text(fig, "CMS", "Preliminary", loc=loc, lumi="138 fb⁻¹ (13.6 TeV)")
    texts = annotation_texts(fig)
    assert "<b>CMS</b>" in texts and "<i>Preliminary</i>" in texts and "138 fb⁻¹ (13.6 TeV)" in texts
    exp = next(a for a in fig.layout.annotations if a.text == "<b>CMS</b>")
    txt = next(a for a in fig.layout.annotations if a.text == "<i>Preliminary</i>")
    lumi = next(a for a in fig.layout.annotations if "fb" in a.text)
    # mplhep size ratios: exp 1.3x, text 1x, lumi 0.77x
    assert exp.font.size / txt.font.size == pytest.approx(SCALE_EXP)
    assert lumi.font.size / txt.font.size == pytest.approx(SCALE_LUMI)
    if loc == 0:
        assert exp.yanchor == "bottom" and exp.y == 1 and lumi.xanchor == "right"      # above the axes
    if loc in (1, 2, 4):
        assert exp.yanchor == "top" and exp.xshift > 0 and exp.yshift < 0                # inside, padded
    if loc == 4:
        assert lumi.xanchor == "left" and lumi.yanchor == "top"                          # ATLAS style: lumi below


def test_exp_text_invalid_loc(fig):
    with pytest.raises(ValueError, match="Invalid location"):
        exp_text(fig, "CMS", loc=7)


def test_exp_label_simulation_default(fig):
    exp_label(fig, "CMS", data=False, com=13.6)
    assert "<i>Simulation</i>" in annotation_texts(fig)


def test_exp_label_rlabel_overrides(fig):
    exp_label(fig, "CMS", "Preliminary", data=True, lumi=138, com=13.6, rlabel="my label")
    assert "my label" in annotation_texts(fig) and not any("138" in t for t in annotation_texts(fig))


def test_namespaces(fig):
    php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6)
    php.atlas.text(fig, "Internal", loc=1)
    texts = annotation_texts(fig)
    assert "<b>CMS</b>" in texts and "<b>ATLAS</b>" in texts


def test_axis_label_helpers(fig):
    php.set_xlabel(fig, "m<sub>jj</sub> [GeV]")
    php.set_ylabel(fig, "Events")
    x = next(a for a in fig.layout.annotations if "jj" in a.text)
    y = next(a for a in fig.layout.annotations if a.text == "Events")
    assert (x.xanchor, x.yanchor, x.x, x.y) == ("right", "top", 1, 0) and x.yshift < 0     # right end, below the axis
    assert y.textangle == -90 and y.y == 1 and y.xshift < 0                              # top end, left of the axis


@pytest.mark.image_compare(tolerance=6, remove_text=False)
def test_labeltext_loc0(fig):
    fig.update_xaxes(range=[0, 10]); fig.update_yaxes(range=[0, 10])
    php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6, loc=0)
    return fig


@pytest.mark.image_compare(tolerance=6, remove_text=False)
def test_labeltext_loc2(fig):
    fig.update_xaxes(range=[0, 10]); fig.update_yaxes(range=[0, 10])
    php.cms.label(fig, "Simulation", data=False, com=13.6, loc=2)
    return fig
