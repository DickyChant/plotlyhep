"""Plotly layout templates mirroring mplhep experiment styles.

The template is derived from mplhep's own rcParams dictionaries at import time
when mplhep is installed (so a new mplhep release propagates), otherwise from
the vendored snapshot below (mplhep 1.3.3)."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

from ._units import DPI, SUBPLOT, fontsize_pt, pt2px

_SNAPSHOT = {
    "CMS": {
        "font.sans-serif": ["TeX Gyre Heros", "Helvetica", "Arial"],
        "font.size": 26,
        "axes.labelsize": "medium",
        "axes.linewidth": 2,
        "axes.prop_cycle": ["#5790fc", "#f89c20", "#e42536", "#964a8b", "#9c9ca1", "#7a21dd"],
        "xtick.major.size": 12,
        "xtick.minor.size": 6,
        "ytick.major.size": 12,
        "ytick.minor.size": 6,
        "xtick.major.pad": 6,
        "xtick.labelsize": "small",
        "ytick.labelsize": "small",
        "legend.fontsize": "small",
        "figure.figsize": (10.0, 10.0),
    },
    "ATLAS": {
        "font.sans-serif": ["TeX Gyre Heros", "Helvetica", "Arial"],
        "font.size": 14,
        "axes.labelsize": "x-large",
        "axes.linewidth": 1,
        "lines.linewidth": 2,
        "axes.prop_cycle": ["#d55e00", "#56b4e9", "#e69f00", "#f0e442", "#009e73", "#cc79a7", "#0072b2"],
        "xtick.major.size": 5,
        "xtick.minor.size": 3,
        "ytick.major.size": 14,
        "ytick.minor.size": 7,
        "xtick.labelsize": "large",
        "ytick.labelsize": "large",
        "legend.fontsize": "medium",
        "figure.figsize": (8.0, 6.0),
    },
}


def _rc(exp: str) -> dict:
    """rcParams-like dict for an experiment: live from mplhep if present."""
    try:
        import mplhep

        rc = dict(getattr(mplhep.style, exp))
        cyc = rc.get("axes.prop_cycle")
        if cyc is not None and not isinstance(cyc, list):
            rc["axes.prop_cycle"] = [c["color"] for c in cyc]
        return rc
    except Exception:
        return dict(_SNAPSHOT[exp])


def figsize_px(exp: str = "CMS") -> tuple[int, int]:
    w, h = _rc(exp).get("figure.figsize", (10.0, 10.0))
    return int(round(w * DPI)), int(round(h * DPI))


def template(exp: str = "CMS") -> go.layout.Template:
    rc = _rc(exp)
    base = float(rc.get("font.size", 26))
    fam = ", ".join(rc.get("font.sans-serif", ["TeX Gyre Heros", "Helvetica", "Arial"]))
    lw = pt2px(rc.get("axes.linewidth", 2))
    tick_w = pt2px(0.8)  # matplotlib default xtick.major.width
    mtick_w = pt2px(0.6)
    label_px = pt2px(fontsize_pt(rc.get("axes.labelsize", "medium"), base))
    tick_px = pt2px(fontsize_pt(rc.get("xtick.labelsize", "small"), base))
    leg_px = pt2px(fontsize_pt(rc.get("legend.fontsize", "small"), base))
    pad_px = pt2px(rc.get("xtick.major.pad", 3.5))
    W, H = figsize_px(exp)
    axis = lambda major, minor: dict(
        showline=True,
        linecolor="black",
        linewidth=lw,
        mirror="allticks",
        ticks="inside",
        ticklen=pt2px(major),
        tickwidth=tick_w,
        tickcolor="black",
        minor=dict(ticks="inside", ticklen=pt2px(minor), tickwidth=mtick_w, showgrid=False),
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=tick_px),
        title=dict(font=dict(size=label_px), standoff=pad_px),
        ticklabelposition="outside",
        automargin=False,
    )
    layout = go.Layout(
        font=dict(family=fam, size=pt2px(base), color="black"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        colorway=list(rc.get("axes.prop_cycle", _SNAPSHOT["CMS"]["axes.prop_cycle"])),
        width=W,
        height=H,
        # +2 px: Plotly centres the axis line on the domain edge, matplotlib draws it inside (measured)
        margin=dict(
            l=int(SUBPLOT["left"] * W) + 2,
            r=int((1 - SUBPLOT["right"]) * W) + 2,
            t=int((1 - SUBPLOT["top"]) * H) + 2,
            b=int(SUBPLOT["bottom"] * H) - 1,
            pad=0,
        ),
        xaxis=axis(rc.get("xtick.major.size", 12), rc.get("xtick.minor.size", 6)),
        yaxis=axis(rc.get("ytick.major.size", 12), rc.get("ytick.minor.size", 6)),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=leg_px),
            x=0.98,
            y=0.98,
            xanchor="right",
            yanchor="top",
            itemsizing="constant",
            tracegroupgap=0,
            itemwidth=30,
        ),
        showlegend=False,
        hovermode="closest",
    )
    return go.layout.Template(layout=layout)


ROOT_EM = 0.90  # ROOT's SetTextSize(f) is not the em size: measured cap height = 0.65 f·H, so em ≈ 0.90 f·H


def root_template(
    width: int = 800,
    height: int = 600,
    *,
    label_size: float = 0.035,
    title_size: float = 0.04,
    margins=(0.10, 0.10, 0.10, 0.10),
    tick_len: float = 0.03,
    mirror_ticks: bool = False,
    frame_width: float = 1.0,
) -> go.layout.Template:
    """A ROOT gStyle-like template: Helvetica (font 42), text sizes as fractions of the pad
    height like ROOT's precision-2 fonts, ticks inside on the bottom/left only (unless
    mirror_ticks, i.e. gPad->SetTickx/y), a full frame box, no grid, margins as ROOT pad
    fractions (left, right, top, bottom). Sizes are absolute pixels for the given canvas."""
    l, r, t, b = margins
    lab = ROOT_EM * label_size * height
    tit = ROOT_EM * title_size * height
    pw, ph = width * (1 - l - r), height * (1 - t - b)  # ROOT tick length is a fraction of the plot area
    ax = lambda tl: dict(
        showline=True,
        linecolor="black",
        linewidth=frame_width,
        mirror="allticks" if mirror_ticks else True,
        ticks="inside",
        ticklen=tl,
        tickwidth=frame_width,
        tickcolor="black",
        minor=dict(ticks="inside", ticklen=tl / 2, tickwidth=frame_width, showgrid=False),
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=lab),
        automargin=False,
        title=dict(font=dict(size=tit)),
        ticklabelposition="outside",
    )
    layout = go.Layout(
        font=dict(family="Helvetica, 'TeX Gyre Heros', Arial, sans-serif", size=lab, color="black"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        width=width,
        height=height,
        margin=dict(l=int(l * width), r=int(r * width), t=int(t * height), b=int(b * height), pad=0),
        xaxis=ax(tick_len * ph),
        yaxis=ax(tick_len * pw),
        showlegend=False,
        hovermode="closest",
        colorway=["#000099", "#009900", "#990000"],
    )
    return go.layout.Template(layout=layout)


def template_json(exp: str = "CMS", *, transparent: bool = False) -> dict:
    """The template as plain JSON — usable from JavaScript: Plotly.newPlot(gd, data, {template: T})."""
    t = template(exp).to_plotly_json()
    if transparent:  # on a slide the skin's ground shows through
        t["layout"]["paper_bgcolor"] = "rgba(0,0,0,0)"
        t["layout"]["plot_bgcolor"] = "rgba(0,0,0,0)"
    return t


def register() -> None:
    for exp in ("CMS", "ATLAS"):
        pio.templates[f"hep_{exp.lower()}"] = template(exp)


def use(exp: str = "CMS") -> None:
    """Make an experiment style the default for new figures (like mplhep.style.use)."""
    register()
    pio.templates.default = f"hep_{exp.lower()}"


register()
