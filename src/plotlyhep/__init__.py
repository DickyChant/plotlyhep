"""plotlyhep — mplhep, mirrored for Plotly.

import plotlyhep as php
php.style.use("CMS")                 # default template for new figures
fig = php.figure()                   # go.Figure at the mplhep figure size
php.histplot(fig, H, bins, yerr=True, label="Data", histtype="errorbar")
php.cms.label(fig, "Preliminary", lumi=138, com=13.6, loc=0)
php.set_xlabel(fig, "m<sub>jj</sub> [GeV]"); php.set_ylabel(fig, "Events")
"""

import plotly.graph_objects as go
import plotly.io as pio

from . import convert, html
from . import styles as style
from .label import atlas, cms, exp_label, exp_text, set_xlabel, set_ylabel
from .plot import hist2dplot, histplot
from .ratio import gridspec_domains, ratio_figure, ratioplot
from .styles import figsize_px, root_template, template


def figure(exp: str | None = None, *, scale: float | None = None, **layout) -> go.Figure:
    """A figure using the experiment template (or the current default), at mplhep's figure size.

    width/height or scale draw the figure at another size with the same proportions: fonts, ticks,
    line widths and margins scale together (scale defaults to min(width/W, height/H) against the
    style's native size, and width/height default to the native size times scale)."""
    name = f"hep_{exp.lower()}" if exp else str(pio.templates.default)
    exp_name = name.removeprefix("hep_").upper()
    W, H = figsize_px(exp_name)
    w, h = layout.get("width"), layout.get("height")
    if scale is None:
        scale = min(w / W if w else 9e9, h / H if h else 9e9) if (w or h) else 1.0
    if scale != 1.0:
        layout.setdefault("width", round(W * scale))
        layout.setdefault("height", round(H * scale))
        return go.Figure(layout=dict(template=template(exp_name, scale=scale), **layout))
    return go.Figure(layout=dict(template=name, **layout))


__all__ = [
    "atlas",
    "cms",
    "convert",
    "exp_label",
    "exp_text",
    "figsize_px",
    "figure",
    "gridspec_domains",
    "hist2dplot",
    "histplot",
    "html",
    "ratio_figure",
    "ratioplot",
    "root_template",
    "set_xlabel",
    "set_ylabel",
    "style",
    "template",
]
__version__ = "0.2.0"
