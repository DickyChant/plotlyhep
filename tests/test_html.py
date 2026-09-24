"""HTML embedding for slides: frozen figures, the edit chip, page-level template."""
from __future__ import annotations

import numpy as np

import plotlyhep as php
from helpers import BINS, MC1
from plotlyhep.html import PLOTLY_JS, SLIDE_CSS, embed, script_tag


def _fig():
    fig = php.figure("CMS")
    php.histplot(fig, MC1, BINS, label="MC")
    return fig


def test_script_tag_publishes_template():
    tag = script_tag("CMS")
    assert PLOTLY_JS in tag and "window.PLOTLYHEP_TEMPLATE" in tag and '"paper_bgcolor": "rgba(0,0,0,0)"' in tag
    assert "PLOTLYHEP_TEMPLATE" not in script_tag(None)


def test_embed_frozen_default():
    h = embed(_fig(), "plot-1")
    assert 'id="plot-1"' in h and "plotlyhep-chip" in h and "var editing = false;" in h
    assert '"editable": false' in h and '"scrollZoom": false' in h            # frozen config
    assert "plot-edits:" in h                                                  # persisted edits


def test_embed_options():
    assert 'class="plotlyhep-chip"' not in embed(_fig(), "p", editable=False)
    assert "var editing = true;" in embed(_fig(), "p", frozen=False)
    assert "localStorage" not in embed(_fig(), "p", persist=False)


def test_embed_inherits_page_template():
    h = embed(_fig(), "p", inherit_template=True)
    layout_js = h.split("var data")[1].split("var configEdit")[0]
    assert '"template"' not in layout_js                                        # dropped, so the page theme applies
    assert '"template"' in embed(_fig(), "p", inherit_template=False)


def test_embed_serialises_numpy():
    fig = php.figure("CMS")
    php.histplot(fig, np.array([1.0, 2.0]), np.array([0.0, 1.0, 2.0]))
    assert '"y": [0.0, 1.0, 2.0, 2.0, 0.0]' in embed(fig, "p")


def test_slide_css_targets_plotly_only():
    assert ".js-plotly-plot" in SLIDE_CSS and "<style>" in SLIDE_CSS
