"""plotlyhep — mplhep, mirrored for Plotly.

    import plotlyhep as php
    php.style.use("CMS")                 # default template for new figures
    fig = php.figure()                   # go.Figure at the mplhep figure size
    php.histplot(fig, H, bins, yerr=True, label="Data", histtype="errorbar")
    php.cms.label(fig, "Preliminary", lumi=138, com=13.6, loc=0)
    php.set_xlabel(fig, "m<sub>jj</sub> [GeV]"); php.set_ylabel(fig, "Events")
"""
from . import styles as style
from .styles import template, figsize_px, root_template
from .label import exp_text, exp_label, cms, atlas, set_xlabel, set_ylabel
from .plot import histplot, hist2dplot
from . import convert, html
import plotly.graph_objects as go
import plotly.io as pio

def figure(exp: str | None = None, **layout) -> go.Figure:
    """A figure using the experiment template (or the current default)."""
    tmpl = f"hep_{exp.lower()}" if exp else pio.templates.default
    fig = go.Figure(layout=dict(template=tmpl, **layout))
    return fig

__all__ = ["style", "template", "figsize_px", "root_template", "figure", "exp_text", "exp_label", "cms", "atlas",
           "set_xlabel", "set_ylabel", "histplot", "hist2dplot", "convert", "html"]
__version__ = "0.1.0"
