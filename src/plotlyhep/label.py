"""Experiment labels, mirroring mplhep.label.exp_text / exp_label geometry.

mplhep (1.3): exp text = 1.3 x base font, secondary text = 1.0 x, lumi = 0.77 x;
loc 0: exp+text above the axes at the left, lumi above at the right;
loc 1: exp+text inside top-left on one line; loc 2: text below exp inside;
loc 3: exp above, text inside; loc 4 (ATLAS): inside, lumi below.
Inside padding equals the exp font size."""

from __future__ import annotations

import plotly.graph_objects as go

from ._units import pt2px

SCALE_EXP, SCALE_LUMI = 1.3, 1 / 1.3


def _lumi_line(year=None, lumi=None, lumi_format="{0}", com="13"):
    parts = []
    if year is not None:
        parts.append(str(year))
    if lumi is not None:
        parts.append(f"{lumi_format.format(lumi)} fb⁻¹")
    s = ", ".join(parts)
    if com is not None:
        s = f"{s} ({com} TeV)" if s else f"({com} TeV)"
    return s


def _tmpl(fig: go.Figure):
    t = fig.layout.template
    return t.layout if t is not None and not isinstance(t, str) else go.Layout()


def _font_px(fig: go.Figure) -> float:
    return fig.layout.font.size or _tmpl(fig).font.size or pt2px(26)


def _axis_px(fig: go.Figure, axis: str, part: str) -> float | None:
    lay = getattr(fig.layout, axis)
    tl = getattr(_tmpl(fig), axis)
    if part == "tick":
        return lay.tickfont.size or tl.tickfont.size
    return lay.title.font.size or tl.title.font.size


def exp_text(
    fig: go.Figure,
    exp: str = "",
    text: str = "",
    *,
    loc: int = 0,
    lumi: str | None = None,
    fontsize: float | None = None,
    xref="paper",
    yref="paper",
) -> go.Figure:
    """Experiment label in the mplhep style: bold experiment name, italic text, optional lumi line.

    loc follows mplhep: 0 above the axes (name left, lumi right), 1-3 inside the top-left corner
    with the text beside or below the name, 4 the ATLAS layout with the lumi line inside too.
    lumi is the finished string (use exp_label to build it from lumi/com/year)."""
    base_pt = _font_px(fig) / pt2px(1) if fontsize is None else fontsize
    fam = fig.layout.font.family
    exp_px, txt_px, lumi_px = pt2px(base_pt * SCALE_EXP), pt2px(base_pt), pt2px(base_pt * SCALE_LUMI)
    pad = exp_px  # mplhep: max(5 pt, exp font size)
    gap = 0.3 * exp_px  # space between "CMS" and "Preliminary"
    ann = []

    def A(txt, x, y, xa, ya, size, bold=False, italic=False, xs=0, ys=0):
        t = txt
        if bold:
            t = f"<b>{t}</b>"
        if italic:
            t = f"<i>{t}</i>"
        ann.append(
            dict(
                text=t,
                x=x,
                y=y,
                xref=xref,
                yref=yref,
                xanchor=xa,
                yanchor=ya,
                showarrow=False,
                font=dict(size=size, family=fam),
                xshift=xs,
                yshift=ys,
                align="left",
            )
        )

    exp_w = 0.72 * exp_px * len(exp)  # crude advance for appending text to the right
    if loc == 0:
        A(exp, 0, 1, "left", "bottom", exp_px, bold=True, ys=2)
        if text:
            A(text, 0, 1, "left", "bottom", txt_px, italic=True, xs=exp_w + gap, ys=2)
        if lumi:
            A(lumi, 1, 1, "right", "bottom", lumi_px, ys=2)
    elif loc == 1:
        A(exp, 0, 1, "left", "top", exp_px, bold=True, xs=pad, ys=-pad)
        if text:
            A(text, 0, 1, "left", "top", txt_px, italic=True, xs=pad + exp_w + gap, ys=-pad - (exp_px - txt_px) * 0.8)
        if lumi:
            A(lumi, 1, 1, "right", "bottom", lumi_px, ys=2)
    elif loc == 2:
        A(exp, 0, 1, "left", "top", exp_px, bold=True, xs=pad, ys=-pad)
        if text:
            A(text, 0, 1, "left", "top", txt_px, italic=True, xs=pad, ys=-pad - exp_px * 1.15)
        if lumi:
            A(lumi, 1, 1, "right", "bottom", lumi_px, ys=2)
    elif loc == 3:
        A(exp, 0, 1, "left", "bottom", exp_px, bold=True, ys=2)
        if text:
            A(text, 0, 1, "left", "top", txt_px, italic=True, xs=pad, ys=-pad)
        if lumi:
            A(lumi, 1, 1, "right", "bottom", lumi_px, ys=2)
    elif loc == 4:
        A(exp, 0, 1, "left", "top", exp_px, bold=True, xs=pad, ys=-pad)
        if text:
            A(text, 0, 1, "left", "top", txt_px, italic=True, xs=pad + exp_w + gap, ys=-pad - (exp_px - txt_px) * 0.8)
        if lumi:
            A(lumi, 0, 1, "left", "top", lumi_px, xs=pad, ys=-pad - exp_px * 1.15)
    else:
        raise ValueError(f"Invalid location: {loc}. Valid options are 0-4.")
    for a in ann:
        fig.add_annotation(**a)
    return fig


def exp_label(fig, exp="", text="", *, loc=0, data=False, year=None, lumi=None, lumi_format="{0}", com="13", rlabel=None, fontsize=None):
    """exp_text with the lumi line built for you (like mplhep.cms.label): data=False adds "Simulation",
    year/lumi/com/lumi_format become "2018, 59.8 fb⁻¹ (13 TeV)", rlabel replaces the whole right label."""
    if rlabel is None:
        rlabel = _lumi_line(year=year, lumi=lumi, lumi_format=lumi_format, com=com)
    if not data and not text:
        text = "Simulation"
    return exp_text(fig, exp, text, loc=loc, lumi=rlabel or None, fontsize=fontsize)


class _Exp:
    def __init__(self, name):
        self.name = name

    def label(self, fig, text="", **kw):
        return exp_label(fig, self.name, text, **kw)

    def text(self, fig, text="", **kw):
        return exp_text(fig, self.name, text, **kw)


cms, atlas = _Exp("CMS"), _Exp("ATLAS")


def set_xlabel(fig: go.Figure, text: str, *, size_px: float | None = None) -> go.Figure:
    """mplhep puts the x label right-aligned at the axis end (xaxis.labellocation=right)."""
    tick_px = _axis_px(fig, "xaxis", "tick") or pt2px(21.67)
    pad = fig.layout.xaxis.title.standoff or pt2px(6)
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=1,
        y=0,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        yshift=-(pad + tick_px + pt2px(4)),
        font=dict(size=size_px or _axis_px(fig, "xaxis", "title") or pt2px(26)),
    )
    return fig


def set_ylabel(fig: go.Figure, text: str, *, size_px: float | None = None, ticklabel_chars: int = 4) -> go.Figure:
    """y label top-aligned at the axis end (yaxis.labellocation=top), rotated."""
    tick_px = _axis_px(fig, "yaxis", "tick") or pt2px(21.67)
    pad = fig.layout.yaxis.title.standoff or pt2px(6)
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=0,
        y=1,
        xanchor="center",
        yanchor="top",
        textangle=-90,
        showarrow=False,
        xshift=-(pad + 0.55 * tick_px * ticklabel_chars + pt2px(4) + (size_px or pt2px(26)) / 2),
        font=dict(size=size_px or _axis_px(fig, "yaxis", "title") or pt2px(26)),
    )
    return fig
