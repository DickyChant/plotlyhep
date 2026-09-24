"""ROOT <-> Plotly.

from_root(obj) turns a TCanvas / TPad (with everything drawn on it: TH1, TH2, TGraph*, TMultiGraph,
THStack, TF1, TLegend, TLatex / TText, TLine / TBox / TArrow, TPaveText title, TPaveStats, sub-pads
from Divide) or a single ROOT object into a go.Figure that looks like ROOT's own rendering: same
pad margins, the frame with inside ticks, text sizes as fractions of the pad height, marker and
line styles, the colour table and the current palette. Objects read with uproot convert too (no
ROOT needed); colours then come from a snapshot of ROOT's colour table.

to_root(fig) builds a TCanvas from a Plotly figure: hv steps become TH1D, markers with error bars
TGraphErrors / TGraphAsymmErrors, lines TGraph, heatmaps TH2D, annotations TLatex, line shapes
TLine, the legend a TLegend. It returns the canvas with the objects kept alive on it.

Coordinates: the figure keeps zero margins and puts the axes in a domain equal to the pad's frame,
so Plotly's paper fractions ARE ROOT's NDC. That makes every NDC-positioned object (legend, latex,
paves) a direct copy.
"""

from __future__ import annotations

import json
import math
import os
import re
from typing import Any

import numpy as np
import plotly.graph_objects as go

from .styles import ROOT_EM

# --------------------------------------------------------------------------- tables
_COLORS: dict[str, str] = json.load(open(os.path.join(os.path.dirname(__file__), "_root_colors.json")))

# ROOT's default palette (kBird, 255 colours) sampled at 9 stops, for uproot-read TH2 without ROOT
_KBIRD = ["#352a86", "#343dae", "#0262e0", "#1389d2", "#07a9c2", "#2db7a3", "#68c979", "#b6cf2a", "#f9f90e"]

_MARKER = {
    1: ("circle", 0.25),
    2: ("cross-thin", 1.0),
    3: ("asterisk", 1.0),
    4: ("circle-open", 1.0),
    5: ("x-thin", 1.0),
    6: ("circle", 0.4),
    7: ("circle", 0.5),
    8: ("circle", 1.0),
    20: ("circle", 1.0),
    21: ("square", 1.0),
    22: ("triangle-up", 1.0),
    23: ("triangle-down", 1.0),
    24: ("circle-open", 1.0),
    25: ("square-open", 1.0),
    26: ("triangle-up-open", 1.0),
    27: ("diamond-open", 1.0),
    28: ("cross-open", 1.0),
    29: ("star", 1.2),
    30: ("star-open", 1.2),
    31: ("asterisk", 1.0),
    32: ("triangle-down-open", 1.0),
    33: ("diamond", 1.2),
    34: ("cross", 1.0),
    35: ("diamond-open", 1.2),
    36: ("square-open", 1.0),
    37: ("star-triangle-up-open", 1.0),
    38: ("hexagon", 1.0),
    39: ("star", 1.0),
    40: ("star-diamond", 1.0),
    41: ("star-open", 1.0),
    42: ("star", 1.0),
    43: ("star", 1.0),
    44: ("star-open", 1.0),
    45: ("star-diamond-open", 1.0),
    46: ("star-square", 1.0),
    47: ("star-square-open", 1.0),
    48: ("star", 1.0),
    49: ("star", 1.0),
}
_MARKER_INV = {
    "circle": 20,
    "square": 21,
    "triangle-up": 22,
    "triangle-down": 23,
    "circle-open": 24,
    "square-open": 25,
    "triangle-up-open": 26,
    "diamond-open": 27,
    "cross-open": 28,
    "star": 29,
    "star-open": 30,
    "diamond": 33,
    "cross": 34,
    "cross-thin": 2,
    "asterisk": 3,
    "x-thin": 5,
    "x": 5,
}
MARKER_PX = 8.0  # ROOT marker size 1 is 8 pixels
_DASH = {
    1: "solid",
    2: "dash",
    3: "dot",
    4: "dashdot",
    5: "longdash",
    6: "longdashdot",
    7: "dash",
    8: "dashdot",
    9: "longdash",
    10: "longdashdot",
}
_DASH_INV = {"solid": 1, "dash": 2, "dot": 3, "dashdot": 4, "longdash": 5, "longdashdot": 6}
_HATCH = {
    3001: ".",
    3002: ".",
    3003: ".",
    3004: "/",
    3005: "\\",
    3006: "|",
    3007: "-",
    3008: "x",
    3009: "+",
    3010: "x",
    3011: ".",
    3012: "+",
    3013: "x",
    3014: "-",
    3015: "+",
    3016: "|",
    3017: "/",
    3018: "\\",
    3019: "x",
    3020: "x",
    3021: ".",
    3022: "x",
    3023: "+",
    3024: "/",
    3025: "\\",
}
_HALIGN = {1: "left", 2: "center", 3: "right"}
_VALIGN = {1: "bottom", 2: "middle", 3: "top"}
DESC = 0.22  # ROOT anchors text at the baseline, Plotly at the box bottom: descender ~0.22 em

_GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "zeta": "ζ",
    "eta": "η",
    "theta": "θ",
    "iota": "ι",
    "kappa": "κ",
    "lambda": "λ",
    "mu": "μ",
    "nu": "ν",
    "xi": "ξ",
    "omicron": "ο",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "upsilon": "υ",
    "phi": "φ",
    "chi": "χ",
    "psi": "ψ",
    "omega": "ω",
    "varphi": "ϕ",
    "Alpha": "Α",
    "Beta": "Β",
    "Gamma": "Γ",
    "Delta": "Δ",
    "Epsilon": "Ε",
    "Zeta": "Ζ",
    "Eta": "Η",
    "Theta": "Θ",
    "Iota": "Ι",
    "Kappa": "Κ",
    "Lambda": "Λ",
    "Mu": "Μ",
    "Nu": "Ν",
    "Xi": "Ξ",
    "Omicron": "Ο",
    "Pi": "Π",
    "Rho": "Ρ",
    "Sigma": "Σ",
    "Tau": "Τ",
    "Upsilon": "Υ",
    "Phi": "Φ",
    "Chi": "Χ",
    "Psi": "Ψ",
    "Omega": "Ω",
    "pm": "±",
    "mp": "∓",
    "times": "×",
    "cdot": "·",
    "rightarrow": "→",
    "leftarrow": "←",
    "Rightarrow": "⇒",
    "Leftarrow": "⇐",
    "leftrightarrow": "↔",
    "uparrow": "↑",
    "downarrow": "↓",
    "geq": "≥",
    "leq": "≤",
    "neq": "≠",
    "approx": "≈",
    "equiv": "≡",
    "sim": "∼",
    "propto": "∝",
    "infty": "∞",
    "sum": "∑",
    "int": "∫",
    "partial": "∂",
    "nabla": "∇",
    "circ": "°",
    "degree": "°",
    "prime": "′",
    "perp": "⊥",
    "parallel": "∥",
    "in": "∈",
    "notin": "∉",
    "cap": "∩",
    "cup": "∪",
    "forall": "∀",
    "exists": "∃",
    "hbar": "ℏ",
    "ell": "ℓ",
    "angle": "∠",
    "ldots": "…",
    "bullet": "•",
    "diamond": "◊",
    "star": "★",
    "void": "",
    "3dots": "…",
    "GeV": "GeV",
    "minus": "−",
    "plus": "+",
    "slash": "/",
    "backslash": "\\",
    "upoint": "·",
    "surd": "√",
    "lbar": "|",
    "dagger": "†",
    "aleph": "ℵ",
    "oslash": "⊘",
    "otimes": "⊗",
    "oplus": "⊕",
    "wedge": "∧",
    "vee": "∨",
    "supset": "⊃",
    "subset": "⊂",
    "supseteq": "⊇",
    "subseteq": "⊆",
    "doublequote": '"',
    "copyright": "©",
    "trademark": "™",
    "AA": "Å",
    "aa": "å",
}
_GREEK_INV = {v: k for k, v in _GREEK.items() if len(v) == 1 and v not in '"+/\\|'}
_ACCENT = {"bar": "̄", "hat": "̂", "tilde": "̃", "vec": "⃗", "dot": "̇", "ddot": "̈", "acute": "́", "grave": "̀", "check": "̌"}


def rootlatex_to_html(s: str) -> str:
    """ROOT TLatex markup to the HTML Plotly renders: #it{} #bf{} -> <i> <b>, _{} ^{} -> <sub> <sup>,
    #sqrt{x} -> √x, #alpha ... #pm -> Unicode, accents (#bar{x}) -> combining marks, #scale/#color/#font dropped."""
    if not s:
        return ""
    out = s
    for _ in range(20):  # innermost braces first, repeat for nesting
        new = re.sub(r"#it\{([^{}]*)\}", r"<i>\1</i>", out)
        new = re.sub(r"#bf\{([^{}]*)\}", r"<b>\1</b>", new)
        new = re.sub(r"#sqrt\{([^{}]*)\}", r"√\1", new)
        new = re.sub(r"#(bar|hat|tilde|vec|dot|ddot|acute|grave|check)\{([^{}]*)\}", lambda m: m.group(2) + _ACCENT[m.group(1)], new)
        new = re.sub(r"#(scale|color|font)\[[^\]]*\]\{([^{}]*)\}", r"\2", new)
        new = re.sub(r"#(mbox|text|rm)\{([^{}]*)\}", r"\2", new)
        new = re.sub(r"#frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", new)
        new = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", new)
        new = re.sub(r"\^\{([^{}]*)\}", r"<sup>\1</sup>", new)
        if new == out:
            break
        out = new
    out = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", out)
    out = re.sub(r"\^([A-Za-z0-9])", r"<sup>\1</sup>", out)
    out = re.sub(r"#([A-Za-z]+)", lambda m: _GREEK.get(m.group(1), m.group(0)), out)
    out = out.replace("{", "").replace("}", "")
    return out


def html_to_rootlatex(s: str) -> str:
    """Inverse of rootlatex_to_html for the tags plotlyhep produces."""
    if not s:
        return ""
    out = s.replace("<br>", " ")
    out = re.sub(r"<i>(.*?)</i>", r"#it{\1}", out)
    out = re.sub(r"<b>(.*?)</b>", r"#bf{\1}", out)
    out = re.sub(r"<sub>(.*?)</sub>", r"_{\1}", out)
    out = re.sub(r"<sup>(.*?)</sup>", r"^{\1}", out)
    out = re.sub(r"<[^>]+>", "", out)
    out = out.replace("√", "#sqrt").replace("⁻¹", "^{-1}")
    return "".join(f"#{_GREEK_INV[ch]}" if ch in _GREEK_INV else ch for ch in out)


# --------------------------------------------------------------------------- small helpers
def _root():
    import ROOT

    ROOT.gROOT.SetBatch(True)
    return ROOT


def _is_root(obj) -> bool:
    return hasattr(obj, "ClassName") and hasattr(obj, "InheritsFrom")


def _is_uproot(obj) -> bool:
    return hasattr(obj, "classname") and hasattr(obj, "member")


def _addr(obj) -> int:
    try:
        import cppyy

        return int(cppyy.addressof(obj))
    except Exception:
        return id(obj)


def root_color(index: int | None, alpha: float | None = None, *, ROOT=None) -> str:
    """ROOT colour index -> CSS colour (live TColor when ROOT is loaded, the snapshot table otherwise)."""
    if index is None:
        return "black"
    index = int(index)
    hexs: str | None = None
    a = 1.0
    if ROOT is not None:
        c = ROOT.gROOT.GetColor(index)
        if c:
            hexs, a = c.AsHexString(), float(c.GetAlpha())
    if hexs is None:
        hexs = _COLORS.get(str(index))
        if hexs is None:
            return "black"
    if alpha is not None:
        a = alpha
    if a < 1.0:
        r, g, b = int(hexs[1:3], 16), int(hexs[3:5], 16), int(hexs[5:7], 16)
        return f"rgba({r},{g},{b},{a:.3f})"
    return hexs


def _text_px(size: float, font: int, pad_h: float) -> float:
    """ROOT text size -> pixels: precision-3 fonts (x3) are in pixels, the rest fractions of the pad height."""
    if size <= 0:
        return ROOT_EM * 0.035 * pad_h
    return float(size) if font % 10 == 3 else ROOT_EM * float(size) * pad_h


def _font_style(font: int) -> tuple[bool, bool]:
    """(bold, italic) from the ROOT font code's family digit."""
    fam = font // 10
    return fam in (6, 7, 10), fam in (5, 7, 12)


def _wrap_style(text: str, font: int) -> str:
    bold, italic = _font_style(font)
    if bold:
        text = f"<b>{text}</b>"
    if italic:
        text = f"<i>{text}</i>"
    return text


def _mark(style: int, size: float, color: str) -> dict:
    sym, f = _MARKER.get(int(style), ("circle", 1.0))
    return dict(symbol=sym, size=MARKER_PX * float(size) * f, color=color, line=dict(color=color, width=1))


def _hist1d_arrays(h):
    n = h.GetNbinsX()
    ax = h.GetXaxis()
    edges = np.array([ax.GetBinLowEdge(i) for i in range(1, n + 1)] + [ax.GetBinUpEdge(n)], float)
    vals = np.array([h.GetBinContent(i) for i in range(1, n + 1)], float)
    errs = np.array([h.GetBinError(i) for i in range(1, n + 1)], float)
    return edges, vals, errs


def _step_xy(edges, vals):
    x = np.concatenate([[edges[0]], edges, [edges[-1]]])
    y = np.concatenate([[0.0], vals, [vals[-1], 0.0]])
    return x, y


# --------------------------------------------------------------------------- object -> traces
class _Ctx:
    """Where things go: which axes, the pad geometry, the ROOT module (or None for uproot)."""

    def __init__(self, ROOT, pad_h: float, xaxis="x", yaxis="y", rect=(0.0, 0.0, 1.0, 1.0), logx=False, logy=False):
        self.ROOT, self.pad_h, self.xaxis, self.yaxis, self.rect, self.logx, self.logy = ROOT, pad_h, xaxis, yaxis, rect, logx, logy
        self.traces: list = []
        self.owners: list = []  # parallel to traces: address of the ROOT object each trace came from
        self.annotations: list = []
        self.shapes: list = []
        self.legend: dict | None = None
        self.title: dict | None = None

    def add(self, trace, owner=None):
        trace.update(xaxis=self.xaxis, yaxis=self.yaxis)
        self.traces.append(trace)
        self.owners.append(_addr(owner) if owner is not None else None)
        return trace

    def paper(self, x, y):
        """pad NDC -> figure paper (identity for a top-level pad, the pad rect for a sub-pad)."""
        x0, y0, w, h = self.rect
        return x0 + w * x, y0 + h * y

    def color(self, idx, alpha=None):
        return root_color(idx, alpha, ROOT=self.ROOT)


def _add_th1(ctx: _Ctx, h, opt: str, *, name: str | None = None, stacked_base=None):
    o = opt.upper()
    edges, vals, errs = _hist1d_arrays(h)
    if stacked_base is not None:
        vals = vals + stacked_base
    lc = ctx.color(h.GetLineColor())
    lw = float(h.GetLineWidth())
    dash = _DASH.get(int(h.GetLineStyle()), "solid")
    fc_idx, fs = int(h.GetFillColor()), int(h.GetFillStyle())
    mc = ctx.color(h.GetMarkerColor())
    label = name if name is not None else rootlatex_to_html(h.GetTitle()) or h.GetName()
    centers = 0.5 * (edges[1:] + edges[:-1])
    half = 0.5 * np.diff(edges)
    err_mode = ("E" in o and "HIST" not in o) or ("P" in o and "E" in o)
    if err_mode or ("P" in o and "HIST" not in o):
        ms, msz = int(h.GetMarkerStyle()), float(h.GetMarkerSize())
        marker = _mark(ms, msz, mc)
        t = go.Scatter(x=centers, y=vals, mode="markers", name=label, marker=marker, showlegend=False)
        if err_mode:
            cap = 0.0
            if "E1" in o:
                cap = 0.5 * MARKER_PX
            t.update(error_y=dict(type="data", array=errs, color=lc, thickness=lw, width=cap))
            if "X0" not in o and ctx.ROOT is not None and ctx.ROOT.gStyle.GetErrorX() > 0:
                t.update(error_x=dict(type="data", array=half * 2 * ctx.ROOT.gStyle.GetErrorX(), color=lc, thickness=lw, width=0))
            elif "X0" not in o and ctx.ROOT is None:
                t.update(error_x=dict(type="data", array=half, color=lc, thickness=lw, width=0))
        ctx.add(t, h)
        if "HIST" in o or "L" in o or "C" in o:
            x, y = _step_xy(edges, vals)
            ctx.add(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    line=dict(shape="hv", color=lc, width=lw, dash=dash),
                    showlegend=False,
                    name=label,
                    hoverinfo="skip",
                ),
                h,
            )
        return
    if ("B" in o and "BAR" in o) or o.strip() == "B":
        ctx.add(
            go.Bar(
                x=centers,
                y=vals,
                width=2 * half,
                name=label,
                marker=dict(color=ctx.color(fc_idx) if fc_idx else lc, line=dict(color=lc, width=lw)),
                showlegend=False,
            ),
            h,
        )
        return
    if "L" in o or "C" in o:  # polyline through the bin centres
        ctx.add(
            go.Scatter(
                x=centers,
                y=vals,
                mode="lines",
                name=label,
                line=dict(color=lc, width=lw, dash=dash, shape="spline" if "C" in o else "linear"),
                showlegend=False,
            ),
            h,
        )
        return
    x, y = _step_xy(edges, vals)
    t = go.Scatter(x=x, y=y, mode="lines", name=label, line=dict(shape="hv", color=lc, width=lw, dash=dash), showlegend=False)
    if fc_idx > 0 and fs != 0 and stacked_base is None:
        fill = ctx.color(fc_idx)
        if fs in _HATCH:
            t.update(
                fill="tozeroy",
                fillcolor="rgba(0,0,0,0)",
                fillpattern=dict(shape=_HATCH[fs], fgcolor=fill, bgcolor="rgba(0,0,0,0)", size=6, solidity=0.4),
            )
        elif fs == 1001 or fs == 0 or fs > 4000:
            t.update(fill="tozeroy", fillcolor=fill)
        else:
            t.update(fill="tozeroy", fillcolor=fill)
    elif stacked_base is not None:
        fill = ctx.color(fc_idx) if fc_idx > 0 else lc
        t.update(fill="tozeroy", fillcolor=fill)
    ctx.add(t, h)


def _add_th2(ctx: _Ctx, h, opt: str):
    o = opt.upper()
    nx, ny = h.GetNbinsX(), h.GetNbinsY()
    xa, ya = h.GetXaxis(), h.GetYaxis()
    xe = np.array([xa.GetBinLowEdge(i) for i in range(1, nx + 1)] + [xa.GetBinUpEdge(nx)], float)
    ye = np.array([ya.GetBinLowEdge(j) for j in range(1, ny + 1)] + [ya.GetBinUpEdge(ny)], float)
    z = np.array([[h.GetBinContent(i, j) for i in range(1, nx + 1)] for j in range(1, ny + 1)], float)
    zshow = np.where(z == 0, np.nan, z) if "COL0" not in o and "0" not in o.replace("COL", "") else z
    if ctx.ROOT is not None:
        pal = ctx.ROOT.TColor.GetPalette()
        n = pal.GetSize()
        scale = [[k / 8, ctx.ROOT.gROOT.GetColor(pal[int(round(k / 8 * (n - 1)))]).AsHexString()] for k in range(9)]
    else:
        scale = [[k / 8, c] for k, c in enumerate(_KBIRD)]
    t = go.Heatmap(
        x=0.5 * (xe[1:] + xe[:-1]),
        y=0.5 * (ye[1:] + ye[:-1]),
        z=zshow,
        colorscale=scale,
        showscale="Z" in o,
        xgap=0,
        ygap=0,
        name=rootlatex_to_html(h.GetTitle()),
        zmin=float(np.nanmin(z)) if "COL0" in o else None,
        zmax=float(np.nanmax(z)),
        colorbar=dict(
            x=1.0 + 0.01,
            xanchor="left",
            len=1.0,
            thickness=0.05 * ctx.pad_h,
            tickfont=dict(size=_text_px(xa.GetLabelSize(), xa.GetLabelFont(), ctx.pad_h)),
            outlinewidth=0,
        ),
    )
    if "Z" in o:
        x0, y0, w, hh = ctx.rect
        t.update(
            colorbar=dict(x=x0 + w * 1.0 + 0.005, y=y0 + hh * 0.5, xanchor="left", yanchor="middle", len=hh, thickness=0.03 * w * 1000 / 10)
        )
    ctx.add(t, h)


def _graph_arrays(g):
    n = g.GetN()
    x = np.asarray(g.GetX(), dtype=float)[:n].copy()
    y = np.asarray(g.GetY(), dtype=float)[:n].copy()
    ex = ey = exl = exh = eyl = eyh = None
    if g.InheritsFrom("TGraphAsymmErrors"):
        exl, exh = np.asarray(g.GetEXlow(), float)[:n].copy(), np.asarray(g.GetEXhigh(), float)[:n].copy()
        eyl, eyh = np.asarray(g.GetEYlow(), float)[:n].copy(), np.asarray(g.GetEYhigh(), float)[:n].copy()
    elif g.InheritsFrom("TGraphErrors"):
        ex, ey = np.asarray(g.GetEX(), float)[:n].copy(), np.asarray(g.GetEY(), float)[:n].copy()
    return x, y, ex, ey, exl, exh, eyl, eyh


def _add_tgraph(ctx: _Ctx, g, opt: str, *, name: str | None = None):
    o = opt.upper().replace("SAME", "")
    x, y, ex, ey, exl, exh, eyl, eyh = _graph_arrays(g)
    lc, mc = ctx.color(g.GetLineColor()), ctx.color(g.GetMarkerColor())
    lw, dash = float(g.GetLineWidth()), _DASH.get(int(g.GetLineStyle()), "solid")
    label = name if name is not None else rootlatex_to_html(g.GetTitle()) or g.GetName()
    modes = []
    if "P" in o or "*" in o:
        modes.append("markers")
    if "L" in o or "C" in o or (not modes and "3" not in o and "F" not in o and "B" not in o):
        modes.append("lines")
    if "3" in o and (ey is not None or eyl is not None):  # band between y-err and y+err
        lo = y - (eyl if eyl is not None else ey)
        hi = y + (eyh if eyh is not None else ey)
        fc = ctx.color(g.GetFillColor()) if g.GetFillColor() > 0 else lc
        ctx.add(go.Scatter(x=x, y=hi, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip", name=label), g)
        ctx.add(go.Scatter(x=x, y=lo, mode="lines", line=dict(width=0), fill="tonexty", fillcolor=fc, showlegend=False, name=label), g)
        if "L" in o or "C" in o:
            ctx.add(go.Scatter(x=x, y=y, mode="lines", line=dict(color=lc, width=lw, dash=dash), name=label, showlegend=False), g)
        return
    if "B" in o and "P" not in o and "L" not in o:
        ctx.add(
            go.Bar(x=x, y=y, name=label, marker=dict(color=ctx.color(g.GetFillColor()) if g.GetFillColor() > 0 else lc), showlegend=False),
            g,
        )
        return
    t = go.Scatter(
        x=x,
        y=y,
        mode="+".join(modes) if modes else "lines",
        name=label,
        showlegend=False,
        line=dict(color=lc, width=lw, dash=dash, shape="spline" if "C" in o else "linear"),
        marker=_mark(int(g.GetMarkerStyle()) if "*" not in o else 3, float(g.GetMarkerSize()), mc),
    )
    if "F" in o:
        t.update(fill="tozeroy", fillcolor=ctx.color(g.GetFillColor()) if g.GetFillColor() > 0 else lc)
    if "X" not in o:
        cap = 0.0 if "Z" in o else 0.5 * MARKER_PX
        if eyl is not None:
            t.update(error_y=dict(type="data", array=eyh, arrayminus=eyl, color=lc, thickness=lw, width=cap))
        elif ey is not None:
            t.update(error_y=dict(type="data", array=ey, color=lc, thickness=lw, width=cap))
        if exl is not None:
            t.update(error_x=dict(type="data", array=exh, arrayminus=exl, color=lc, thickness=lw, width=cap))
        elif ex is not None and (ctx.ROOT is None or ctx.ROOT.gStyle.GetErrorX() > 0):
            t.update(error_x=dict(type="data", array=ex, color=lc, thickness=lw, width=cap))
    ctx.add(t, g)


def _add_tf1(ctx: _Ctx, f, opt: str):
    xmin, xmax = f.GetXmin(), f.GetXmax()
    npx = max(int(f.GetNpx()), 2)
    xs = np.logspace(np.log10(xmin), np.log10(xmax), npx + 1) if ctx.logx and xmin > 0 else np.linspace(xmin, xmax, npx + 1)
    ys = np.array([f.Eval(float(v)) for v in xs])
    ctx.add(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            name=rootlatex_to_html(f.GetTitle()) or f.GetName(),
            showlegend=False,
            line=dict(color=ctx.color(f.GetLineColor()), width=float(f.GetLineWidth()), dash=_DASH.get(int(f.GetLineStyle()), "solid")),
        ),
        f,
    )


def _add_text(ctx: _Ctx, t, *, pad_h: float):
    ROOT = ctx.ROOT
    ndc = t.TestBit(ROOT.TText.kTextNDC) if ROOT is not None else True
    align = int(t.GetTextAlign()) or 11
    ha, va = _HALIGN.get(align // 10, "left"), _VALIGN.get(align % 10, "bottom")
    px = _text_px(t.GetTextSize(), int(t.GetTextFont()), pad_h)
    text = _wrap_style(rootlatex_to_html(t.GetTitle()), int(t.GetTextFont()))
    a = dict(
        text=text,
        showarrow=False,
        font=dict(size=px, color=ctx.color(t.GetTextColor())),
        xanchor=ha,
        yanchor=va,
        textangle=-float(t.GetTextAngle()) if t.GetTextAngle() else 0,
        yshift=-DESC * px if va == "bottom" else 0,
    )
    if ndc:
        x, y = ctx.paper(t.GetX(), t.GetY())
        a.update(x=x, y=y, xref="paper", yref="paper")
    else:
        x, y = t.GetX(), t.GetY()
        a.update(x=math.log10(x) if ctx.logx and x > 0 else x, y=math.log10(y) if ctx.logy and y > 0 else y, xref=ctx.xaxis, yref=ctx.yaxis)
    ctx.annotations.append(a)


def _add_line(ctx: _Ctx, ln, cls: str):
    ROOT = ctx.ROOT
    ndc = ROOT is not None and cls == "TLine" and ln.TestBit(ROOT.TLine.kLineNDC)
    x1, y1, x2, y2 = ln.GetX1(), ln.GetY1(), ln.GetX2(), ln.GetY2()
    if ndc:
        (x1, y1), (x2, y2) = ctx.paper(x1, y1), ctx.paper(x2, y2)
        ref = dict(xref="paper", yref="paper")
    else:
        if ctx.logx:
            x1, x2 = (math.log10(v) if v > 0 else v for v in (x1, x2))
        if ctx.logy:
            y1, y2 = (math.log10(v) if v > 0 else v for v in (y1, y2))
        ref = dict(xref=ctx.xaxis, yref=ctx.yaxis)
    line = dict(color=ctx.color(ln.GetLineColor()), width=float(ln.GetLineWidth()), dash=_DASH.get(int(ln.GetLineStyle()), "solid"))
    if cls == "TBox":
        fc = int(ln.GetFillColor())
        ctx.shapes.append(
            dict(
                type="rect",
                x0=x1,
                y0=y1,
                x1=x2,
                y1=y2,
                line=line,
                fillcolor=ctx.color(fc) if fc > 0 and ln.GetFillStyle() else "rgba(0,0,0,0)",
                **ref,
            )
        )
    elif cls == "TEllipse":
        ctx.shapes.append(
            dict(
                type="circle",
                x0=ln.GetX1() - ln.GetR1(),
                x1=ln.GetX1() + ln.GetR1(),
                y0=ln.GetY1() - ln.GetR2(),
                y1=ln.GetY1() + ln.GetR2(),
                line=line,
                **ref,
            )
        )
    elif cls == "TArrow":
        ctx.annotations.append(
            dict(
                x=x2,
                y=y2,
                ax=x1,
                ay=y1,
                axref=ref["xref"],
                ayref=ref["yref"],
                xref=ref["xref"],
                yref=ref["yref"],
                showarrow=True,
                arrowhead=2,
                arrowsize=1.5 * ln.GetArrowSize() * 10,
                arrowwidth=line["width"],
                arrowcolor=line["color"],
                text="",
            )
        )
    else:
        ctx.shapes.append(dict(type="line", x0=x1, y0=y1, x1=x2, y1=y2, line=line, **ref))


def _add_pave(ctx: _Ctx, p, *, pad_h: float):
    """TPaveText (the histogram title box), TPaveStats, TPaveLabel -> one annotation box."""
    x1, y1, x2, y2 = p.GetX1NDC(), p.GetY1NDC(), p.GetX2NDC(), p.GetY2NDC()
    lines = (
        [rootlatex_to_html(ln.GetTitle()) for ln in p.GetListOfLines()]
        if hasattr(p, "GetListOfLines")
        else [rootlatex_to_html(p.GetLabel())]
    )
    nl = max(len(lines), 1)
    box_h = (y2 - y1) * pad_h
    size = p.GetTextSize()
    px = _text_px(size, int(p.GetTextFont()), pad_h) if size > 0 else min(0.7 * box_h / nl, ROOT_EM * 0.05 * pad_h)
    font = int(p.GetTextFont())
    if p.GetName() == "title" or p.ClassName() == "TPaveLabel":
        cx, cy = ctx.paper(0.5 * (x1 + x2), 0.5 * (y1 + y2))
        ctx.annotations.append(
            dict(
                text=_wrap_style("<br>".join(lines), font),
                x=cx,
                y=cy,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="middle",
                showarrow=False,
                font=dict(size=px, color=ctx.color(p.GetTextColor())),
                bordercolor="black" if p.GetBorderSize() > 0 else "rgba(0,0,0,0)",
                borderwidth=1 if p.GetBorderSize() > 0 else 0,
                bgcolor=ctx.color(p.GetFillColor()) if p.GetFillStyle() else "rgba(0,0,0,0)",
            )
        )
        return
    # stats-like: left-aligned lines in a bordered box anchored at its top-right corner
    align = int(p.GetTextAlign()) or 12
    tx, ty = ctx.paper(x2, y2)
    ctx.annotations.append(
        dict(
            text="<br>".join(ln.replace("  ", "&nbsp;&nbsp;") for ln in lines),
            x=tx,
            y=ty,
            xref="paper",
            yref="paper",
            xanchor="right",
            yanchor="top",
            align=_HALIGN.get(align // 10, "left"),
            showarrow=False,
            font=dict(size=px, color=ctx.color(p.GetTextColor())),
            bordercolor="black" if p.GetBorderSize() > 0 else "rgba(0,0,0,0)",
            borderwidth=1 if p.GetBorderSize() > 0 else 0,
            borderpad=0.3 * px,
            bgcolor=ctx.color(p.GetFillColor()) if p.GetFillStyle() else "rgba(0,0,0,0)",
        )
    )


def _apply_legend(ctx: _Ctx, leg, *, pad_h: float):
    x1, y1, _x2, y2 = leg.GetX1NDC(), leg.GetY1NDC(), leg.GetX2NDC(), leg.GetY2NDC()
    entries = list(leg.GetListOfPrimitives())
    nrows = max(math.ceil(len(entries) / max(leg.GetNColumns(), 1)), 1)
    size = leg.GetTextSize()
    if size > 0:
        px = _text_px(size, int(leg.GetTextFont()), pad_h)
    else:  # ROOT's automatic size: the entry row height less the entry separation
        px = min(0.72 * (y2 - y1) * pad_h / nrows, ROOT_EM * 0.06 * pad_h)
    used = set()
    for e in entries:
        obj = e.GetObject()
        label = rootlatex_to_html(e.GetLabel())
        if obj is None or not obj:
            continue
        a = _addr(obj)
        for t, owner in zip(ctx.traces, ctx.owners):
            if owner == a and a not in used:
                t.update(name=label, showlegend=True)
                used.add(a)
                break
    lx, ly = ctx.paper(x1, y2)
    ctx.legend = dict(
        x=lx,
        y=ly,
        xanchor="left",
        yanchor="top",
        font=dict(size=px),
        itemsizing="constant",
        bordercolor="black" if leg.GetBorderSize() > 0 else "rgba(0,0,0,0)",
        borderwidth=1 if leg.GetBorderSize() > 0 else 0,
        bgcolor=ctx.color(leg.GetFillColor()) if leg.GetFillStyle() else "rgba(0,0,0,0)",
        tracegroupgap=0,
        orientation="h" if leg.GetNColumns() > 1 else "v",
    )


# --------------------------------------------------------------------------- pad -> layout
def _axis_layout(
    ctx: _Ctx,
    pad,
    ax,
    *,
    which: str,
    lo: float,
    hi: float,
    log: bool,
    frame_px: tuple[float, float],
    grid: bool,
    tick_both: bool,
    pad_h: float,
):
    fw, fh = frame_px
    x0, y0, w, h = ctx.rect
    dom = (
        [x0 + w * pad.GetLeftMargin(), x0 + w * (1 - pad.GetRightMargin())]
        if which == "x"
        else [y0 + h * pad.GetBottomMargin(), y0 + h * (1 - pad.GetTopMargin())]
    )
    lab_px = _text_px(ax.GetLabelSize(), int(ax.GetLabelFont()), pad_h) if ax is not None else ROOT_EM * 0.035 * pad_h
    ndiv = int(ax.GetNdivisions()) if ax is not None else 510
    n1 = abs(ndiv) % 100
    tl = (ax.GetTickLength() if ax is not None else 0.03) * (fh if which == "x" else fw)
    d: dict[str, Any] = dict(
        domain=dom,
        range=[lo, hi],
        type="log" if log else "linear",
        showline=True,
        linecolor="black",
        linewidth=1,
        mirror="ticks" if tick_both else True,
        ticks="inside",
        ticklen=tl,
        tickwidth=1,
        tickcolor="black",
        tickfont=dict(size=lab_px, color=ctx.color(ax.GetLabelColor()) if ax is not None else "black"),
        showgrid=grid,
        gridcolor="rgba(0,0,0,0.35)",
        griddash="dot",
        gridwidth=1,
        zeroline=False,
        automargin=False,
        nticks=n1 + 1 if n1 else 0,
        minor=dict(ticks="inside", ticklen=tl / 2, tickwidth=1, showgrid=False),
        anchor=ctx.yaxis if which == "x" else ctx.xaxis,
        title=dict(text=""),
    )
    if log:
        d.update(
            dtick=1,
            minor=dict(ticks="inside", ticklen=tl / 2, tickwidth=1, showgrid=False, dtick="D1"),
            exponentformat="power",
            nticks=None,
        )
    return d


def _axis_title(ctx: _Ctx, ax, *, which: str, dom_x, dom_y, pad_h: float, hi: float = 0.0):
    """ROOT axis titles sit at the END of the axis (right / top) unless CenterTitle; drawn as annotations.
    The distance from the axis is the label height (x) or the label width (y) plus offset x 1.6 x title size, as TGaxis does."""
    if ax is None or not ax.GetTitle():
        return
    px = _text_px(ax.GetTitleSize(), int(ax.GetTitleFont()), pad_h)
    lab_px = _text_px(ax.GetLabelSize(), int(ax.GetLabelFont()), pad_h)
    off = float(ax.GetTitleOffset() or 1.0)
    text = _wrap_style(rootlatex_to_html(ax.GetTitle()), int(ax.GetTitleFont()))
    centered = bool(ax.GetCenterTitle())
    col = ctx.color(ax.GetTitleColor())
    if which == "x":
        x = 0.5 * (dom_x[0] + dom_x[1]) if centered else dom_x[1]
        ctx.annotations.append(
            dict(
                text=text,
                x=x,
                y=dom_y[0],
                xref="paper",
                yref="paper",
                xanchor="center" if centered else "right",
                yanchor="top",
                yshift=-(1.15 * lab_px + (off - 1.0) * 1.6 * px + 0.15 * px),
                showarrow=False,
                font=dict(size=px, color=col),
            )
        )
    else:
        step = 10 ** math.floor(math.log10(abs(hi) or 1.0))  # the widest tick label ROOT will draw, e.g. "30" for a 0-31.5 axis
        nchar = min(max(len(f"{math.floor(hi / step) * step:g}"), 2), 7)
        label_w = 0.55 * lab_px * nchar
        y = 0.5 * (dom_y[0] + dom_y[1]) if centered else dom_y[1]
        ctx.annotations.append(
            dict(
                text=text,
                x=dom_x[0],
                y=y,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="middle" if centered else "top",
                textangle=-90,
                xshift=-(label_w + off * 1.6 * px),
                showarrow=False,
                font=dict(size=px, color=col),
            )
        )


def _first_axes(prims):
    for obj, _opt in prims:
        for cls in ("TH1", "TGraph", "TF1", "TMultiGraph", "THStack", "TH2"):
            if obj.InheritsFrom(cls):
                try:
                    xa, ya = obj.GetXaxis(), obj.GetYaxis()
                    if xa:
                        return xa, ya
                except Exception:
                    pass
    return None, None


def _primitives(pad):
    out = []
    lnk = pad.GetListOfPrimitives().FirstLink()
    while lnk:
        out.append((lnk.GetObject(), str(lnk.GetOption() or "")))
        lnk = lnk.Next()
    return out


def _convert_pad(fig: go.Figure, pad, ROOT, *, rect, canvas_px: tuple[float, float], index: int) -> int:
    """Draw one pad's content into fig on axes number `index`; returns the next free axes index."""
    W, H = canvas_px
    x0, y0, w, h = rect
    pad_w, pad_h = w * W, h * H
    xaxis, yaxis = ("x", "y") if index == 1 else (f"x{index}", f"y{index}")
    prims = _primitives(pad)
    subpads = [(o, opt) for o, opt in prims if o.InheritsFrom("TPad")]
    if subpads:
        nxt = index
        for sp, _ in subpads:
            srect = (x0 + w * sp.GetXlowNDC(), y0 + h * sp.GetYlowNDC(), w * sp.GetWNDC(), h * sp.GetHNDC())
            nxt = _convert_pad(fig, sp, ROOT, rect=srect, canvas_px=canvas_px, index=nxt)
        return nxt
    pad.Update()
    logx, logy = bool(pad.GetLogx()), bool(pad.GetLogy())
    ctx = _Ctx(ROOT, pad_h, xaxis, yaxis, rect, logx, logy)
    stacks_seen = 0
    for obj, opt in prims:
        cls = obj.ClassName()
        if obj.InheritsFrom("TFrame") or (obj.InheritsFrom("TH1") and obj.GetName() == "hframe"):
            continue  # DrawFrame's empty 1000-bin histogram only carries the axes
        if obj.InheritsFrom("TH2"):
            _add_th2(ctx, obj, opt)
        elif obj.InheritsFrom("TH1"):
            _add_th1(ctx, obj, opt)
            for f in obj.GetListOfFunctions():
                if f.InheritsFrom("TF1"):
                    _add_tf1(ctx, f, "")
                elif f.InheritsFrom("TPaveStats") and ROOT.gStyle.GetOptStat():
                    _add_pave(ctx, f, pad_h=pad_h)
        elif obj.InheritsFrom("THStack"):
            hs = list(obj.GetHists())
            if "NOSTACK" in opt.upper():
                for hh in hs:
                    _add_th1(ctx, hh, opt.upper().replace("NOSTACK", ""))
            else:
                base = None
                built = []
                for hh in hs:
                    _e, vals, _ = _hist1d_arrays(hh)
                    built.append((hh, base.copy() if base is not None else np.zeros_like(vals)))
                    base = vals + (base if base is not None else 0)
                for hh, b in reversed(built):  # tallest first so lower layers cover it
                    _add_th1(ctx, hh, "HIST", stacked_base=b)
            stacks_seen += 1
        elif obj.InheritsFrom("TMultiGraph"):
            for g in obj.GetListOfGraphs():
                _add_tgraph(ctx, g, (g.GetDrawOption() or opt).replace("A", ""))
        elif obj.InheritsFrom("TGraph"):
            _add_tgraph(ctx, obj, opt)
        elif obj.InheritsFrom("TF1"):
            _add_tf1(ctx, obj, opt)
        elif obj.InheritsFrom("TLegend"):
            _apply_legend(ctx, obj, pad_h=pad_h)
        elif obj.InheritsFrom("TPaveStats") or obj.InheritsFrom("TPaveText") or obj.InheritsFrom("TPaveLabel"):
            _add_pave(ctx, obj, pad_h=pad_h)
        elif obj.InheritsFrom("TLatex") or obj.InheritsFrom("TText"):
            _add_text(ctx, obj, pad_h=pad_h)
        elif cls in ("TLine", "TBox", "TArrow", "TEllipse"):
            _add_line(ctx, obj, cls)
    # axes from the pad's frame (user coordinates; log10 already in log pads)
    xa, ya = _first_axes(prims)
    lo_x, hi_x, lo_y, hi_y = pad.GetUxmin(), pad.GetUxmax(), pad.GetUymin(), pad.GetUymax()
    if lo_x == hi_x:
        lo_x, hi_x = (xa.GetXmin(), xa.GetXmax()) if xa is not None else (0, 1)
    if lo_y == hi_y:
        lo_y, hi_y = (ya.GetXmin(), ya.GetXmax()) if ya is not None else (0, 1)
    fw, fh = pad_w * (1 - pad.GetLeftMargin() - pad.GetRightMargin()), pad_h * (1 - pad.GetTopMargin() - pad.GetBottomMargin())
    xl = _axis_layout(
        ctx,
        pad,
        xa,
        which="x",
        lo=lo_x,
        hi=hi_x,
        log=logx,
        frame_px=(fw, fh),
        grid=bool(pad.GetGridx()),
        tick_both=bool(pad.GetTickx()),
        pad_h=pad_h,
    )
    yl = _axis_layout(
        ctx,
        pad,
        ya,
        which="y",
        lo=lo_y,
        hi=hi_y,
        log=logy,
        frame_px=(fw, fh),
        grid=bool(pad.GetGridy()),
        tick_both=bool(pad.GetTicky()),
        pad_h=pad_h,
    )
    fig.layout[f"xaxis{'' if index == 1 else index}"] = xl
    fig.layout[f"yaxis{'' if index == 1 else index}"] = yl
    _axis_title(ctx, xa, which="x", dom_x=xl["domain"], dom_y=yl["domain"], pad_h=pad_h)
    _axis_title(ctx, ya, which="y", dom_x=xl["domain"], dom_y=yl["domain"], pad_h=pad_h, hi=hi_y)
    for t in ctx.traces:
        fig.add_trace(t)
    fig.layout.annotations = list(fig.layout.annotations) + ctx.annotations
    fig.layout.shapes = list(fig.layout.shapes) + ctx.shapes
    if ctx.legend is not None:
        fig.update_layout(legend=ctx.legend, showlegend=True)
    return index + 1


def _pad_to_figure(pad, ROOT, *, width=None, height=None) -> go.Figure:
    W = width or (pad.GetWw() if pad.InheritsFrom("TCanvas") else 700)
    H = height or (pad.GetWh() if pad.InheritsFrom("TCanvas") else 500)
    fig = go.Figure(
        layout=dict(
            width=W,
            height=H,
            margin=dict(l=0, r=0, t=0, b=0, pad=0),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Helvetica, 'TeX Gyre Heros', Arial, sans-serif", color="black", size=ROOT_EM * 0.035 * H),
            showlegend=False,
            template=None,
            hovermode="closest",
            bargap=0,
        )
    )
    _convert_pad(fig, pad, ROOT, rect=(0.0, 0.0, 1.0, 1.0), canvas_px=(float(W), float(H)), index=1)
    return fig


# --------------------------------------------------------------------------- uproot objects
def _from_uproot(obj, opt: str, *, width, height) -> go.Figure:
    W, H = width or 700, height or 500
    fig = go.Figure(
        layout=dict(
            width=W,
            height=H,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="white",
            plot_bgcolor="white",
            showlegend=False,
            template=None,
            font=dict(family="Helvetica, 'TeX Gyre Heros', Arial, sans-serif", color="black", size=ROOT_EM * 0.035 * H),
        )
    )
    ctx = _Ctx(None, H)
    cname = obj.classname
    m = obj.member

    class _A:  # a tiny stand-in with the TAxis getters the drawers use
        def __init__(self, ax):
            self.ax = ax

        def GetTitle(self):
            return self.ax.member("fTitle")

        def GetLabelSize(self):
            return self.ax.member("fLabelSize")

        def GetLabelFont(self):
            return self.ax.member("fLabelFont")

        def GetTitleSize(self):
            return self.ax.member("fTitleSize")

        def GetTitleFont(self):
            return self.ax.member("fTitleFont")

        def GetTitleOffset(self):
            return self.ax.member("fTitleOffset")

        def GetTickLength(self):
            return self.ax.member("fTickLength")

        def GetNdivisions(self):
            return self.ax.member("fNdivisions")

        def GetCenterTitle(self):
            return False

        def GetLabelColor(self):
            return 1

        def GetTitleColor(self):
            return 1

    class _Pad:
        def GetLeftMargin(self):
            return 0.1

        def GetRightMargin(self):
            return 0.1

        def GetTopMargin(self):
            return 0.1

        def GetBottomMargin(self):
            return 0.1

    pad = _Pad()
    if cname.startswith("TH2"):
        vals, xe, ye = obj.to_numpy(flow=False)
        z = np.where(vals.T == 0, np.nan, vals.T)
        ctx.add(
            go.Heatmap(
                x=0.5 * (xe[1:] + xe[:-1]),
                y=0.5 * (ye[1:] + ye[:-1]),
                z=z,
                colorscale=[[k / 8, c] for k, c in enumerate(_KBIRD)],
                showscale="Z" in opt.upper(),
                xgap=0,
                ygap=0,
            )
        )
        lo_x, hi_x, lo_y, hi_y = xe[0], xe[-1], ye[0], ye[-1]
        xa, ya = _A(obj.axis("x")), _A(obj.axis("y"))
    elif cname.startswith("TH1") or cname.startswith("TProfile"):
        vals, xe = obj.to_numpy(flow=False)
        vals = np.asarray(vals, float)
        errs = np.asarray(obj.errors(flow=False), float)
        lc = ctx.color(m("fLineColor"))
        lw, dash = float(m("fLineWidth")), _DASH.get(int(m("fLineStyle")), "solid")
        o = opt.upper()
        if "E" in o or "P" in o:
            t = go.Scatter(
                x=0.5 * (xe[1:] + xe[:-1]),
                y=vals,
                mode="markers",
                marker=_mark(int(m("fMarkerStyle")), float(m("fMarkerSize")), ctx.color(m("fMarkerColor"))),
            )
            if "E" in o:
                t.update(error_y=dict(type="data", array=errs, color=lc, thickness=lw, width=0.5 * MARKER_PX if "E1" in o else 0))
                if "X0" not in o:
                    t.update(error_x=dict(type="data", array=0.5 * np.diff(xe), color=lc, thickness=lw, width=0))
            ctx.add(t)
        else:
            x, y = _step_xy(xe, vals)
            t = go.Scatter(x=x, y=y, mode="lines", line=dict(shape="hv", color=lc, width=lw, dash=dash))
            if int(m("fFillColor")) > 0 and int(m("fFillStyle")) not in (0,):
                t.update(fill="tozeroy", fillcolor=ctx.color(m("fFillColor")))
            ctx.add(t)
        lo_x, hi_x = xe[0], xe[-1]
        lo_y, hi_y = min(0.0, float(np.nanmin(vals))), 1.05 * float(np.nanmax(vals + (errs if "E" in o else 0)))
        xa, ya = _A(obj.axis("x")), _A(obj.member("fYaxis"))
    elif cname.startswith("TGraph"):
        x, y = np.asarray(obj.values(axis="x"), float), np.asarray(obj.values(axis="y"), float)
        o = opt.upper()
        mode = "+".join(k for k, on in (("markers", "P" in o), ("lines", "L" in o or "C" in o or ("P" not in o))) if on)
        t = go.Scatter(
            x=x,
            y=y,
            mode=mode,
            line=dict(color=ctx.color(m("fLineColor")), width=float(m("fLineWidth"))),
            marker=_mark(int(m("fMarkerStyle")), float(m("fMarkerSize")), ctx.color(m("fMarkerColor"))),
        )
        if cname == "TGraphErrors":
            t.update(
                error_y=dict(
                    type="data", array=np.asarray(obj.errors(axis="y"), float), color=ctx.color(m("fLineColor")), width=0.5 * MARKER_PX
                ),
                error_x=dict(
                    type="data", array=np.asarray(obj.errors(axis="x"), float), color=ctx.color(m("fLineColor")), width=0.5 * MARKER_PX
                ),
            )
        elif cname == "TGraphAsymmErrors":
            lo, hi = obj.errors(axis="y", which="low"), obj.errors(axis="y", which="high")
            t.update(
                error_y=dict(type="data", array=np.asarray(hi, float), arrayminus=np.asarray(lo, float), color=ctx.color(m("fLineColor")))
            )
        ctx.add(t)
        sx, sy = np.ptp(x) or 1.0, np.ptp(y) or 1.0
        lo_x, hi_x, lo_y, hi_y = x.min() - 0.1 * sx, x.max() + 0.1 * sx, y.min() - 0.1 * sy, y.max() + 0.1 * sy
        hist = obj.member("fHistogram")
        xa, ya = (_A(hist.member("fXaxis")), _A(hist.member("fYaxis"))) if hist is not None else (None, None)  # type: ignore[assignment]
    else:
        raise TypeError(f"from_root: cannot convert uproot object of class {cname}")
    fw, fh = 0.8 * W, 0.8 * H
    xl = _axis_layout(ctx, pad, xa, which="x", lo=lo_x, hi=hi_x, log=False, frame_px=(fw, fh), grid=False, tick_both=False, pad_h=H)
    yl = _axis_layout(ctx, pad, ya, which="y", lo=lo_y, hi=hi_y, log=False, frame_px=(fw, fh), grid=False, tick_both=False, pad_h=H)
    fig.update_layout(xaxis=xl, yaxis=yl)
    _axis_title(ctx, xa, which="x", dom_x=xl["domain"], dom_y=yl["domain"], pad_h=H)
    _axis_title(ctx, ya, which="y", dom_x=xl["domain"], dom_y=yl["domain"], pad_h=H, hi=hi_y)
    title = m("fTitle")
    if title:
        ctx.annotations.append(
            dict(
                text=rootlatex_to_html(title),
                x=0.5,
                y=0.965,
                xref="paper",
                yref="paper",
                xanchor="center",
                yanchor="middle",
                showarrow=False,
                font=dict(size=ROOT_EM * 0.05 * H),
            )
        )
    for t in ctx.traces:
        fig.add_trace(t)
    fig.update_layout(annotations=ctx.annotations)
    return fig


# --------------------------------------------------------------------------- public API
def from_root(obj, opt: str = "", *, width: int | None = None, height: int | None = None) -> go.Figure:
    """ROOT -> Plotly. obj: a TCanvas / TPad (everything drawn on it, sub-pads included), or a single
    TH1 / TH2 / TGraph* / TMultiGraph / THStack / TF1 with a ROOT draw option in `opt` (it is drawn on a
    temporary batch canvas so ROOT's own axis ranges, title and stats apply), or an object read with
    uproot (no ROOT needed). width/height override the canvas size in pixels."""
    if _is_uproot(obj):
        return _from_uproot(obj, opt, width=width, height=height)
    if not _is_root(obj):
        raise TypeError(f"from_root: not a ROOT (or uproot) object: {type(obj)!r}")
    ROOT = _root()
    if obj.InheritsFrom("TPad"):
        return _pad_to_figure(obj, ROOT, width=width, height=height)
    W, H = width or 700, height or 500
    c = ROOT.TCanvas(f"_plotlyhep_{_addr(obj)}", "", int(W), int(H))
    obj.Draw(opt)
    c.Update()
    try:
        return _pad_to_figure(c, ROOT, width=int(W), height=int(H))
    finally:
        c.Close()


# --------------------------------------------------------------------------- Plotly -> ROOT
def _steps_to_hist(x, y):
    """hv step polyline (as histplot / from_mpl draw it) -> (edges, values)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    edges, vals = [x[0]], []
    for i in range(len(x) - 1):
        if x[i + 1] != x[i]:
            edges.append(x[i + 1])
            vals.append(y[i])
    if len(vals) and len(edges) == len(vals) + 1:
        # drop the closing segment histplot adds (last value repeated to the last edge, then zero)
        if len(vals) >= 2 and vals[-1] == vals[-2] and y[-1] == 0.0 and len(edges) > 2 and edges[-1] == edges[-2]:
            edges, vals = edges[:-1], vals[:-1]
        return np.array(edges), np.array(vals)
    return np.array(edges), np.array(vals[: len(edges) - 1])


_NAMED = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "magenta": (255, 0, 255),
    "cyan": (0, 255, 255),
    "purple": (128, 0, 128),
}


def _css_rgba(c) -> tuple[float, float, float, float]:
    """CSS colour (hex, rgb()/rgba(), a few names) -> (r, g, b, a) in 0-1; matplotlib parses the rest when present."""
    if isinstance(c, str):
        c = c.strip()
        m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+))?\s*\)", c)
        if m:
            return float(m.group(1)) / 255, float(m.group(2)) / 255, float(m.group(3)) / 255, float(m.group(4)) if m.group(4) else 1.0
        if c.startswith("#") and len(c) in (7, 9):
            r, g, b = (int(c[i : i + 2], 16) / 255 for i in (1, 3, 5))
            return r, g, b, int(c[7:9], 16) / 255 if len(c) == 9 else 1.0
        if c.startswith("#") and len(c) == 4:
            return tuple(int(ch * 2, 16) / 255 for ch in c[1:]) + (1.0,)  # type: ignore[return-value]
        if c.lower() in _NAMED:
            r, g, b = _NAMED[c.lower()]
            return r / 255, g / 255, b / 255, 1.0
    try:
        from matplotlib.colors import to_rgba

        return tuple(float(v) for v in to_rgba(c))  # type: ignore[return-value]
    except Exception:
        return 0.0, 0.0, 0.0, 1.0


def _color_index(ROOT, c) -> int:
    if c is None:
        return 1
    r, g, b, a = _css_rgba(c)
    idx = ROOT.TColor.GetColor(float(r), float(g), float(b))
    return ROOT.TColor.GetColorTransparent(idx, float(a)) if a < 0.999 else idx


def to_root(pfig: go.Figure, *, name: str = "c"):
    """Plotly -> ROOT TCanvas (the objects stay alive as canvas._plotlyhep_keep)."""
    ROOT = _root()
    L = pfig.layout
    W, H = int(L.width or 700), int(L.height or 500)
    c = ROOT.TCanvas(name, "", W, H)
    keep: list = []
    xdom = list(L.xaxis.domain) if L.xaxis.domain else [0, 1]
    ydom = list(L.yaxis.domain) if L.yaxis.domain else [0, 1]
    m = L.margin
    l, r, t, b = (m.l or 0) / W, (m.r or 0) / W, (m.t or 0) / H, (m.b or 0) / H
    left = l + (1 - l - r) * xdom[0]
    right = r + (1 - l - r) * (1 - xdom[1])
    bottom = b + (1 - t - b) * ydom[0]
    top = t + (1 - t - b) * (1 - ydom[1])
    c.SetMargin(left, right, bottom, top)
    logx, logy = L.xaxis.type == "log", L.yaxis.type == "log"
    c.SetLogx(int(logx))
    c.SetLogy(int(logy))
    xt = html_to_rootlatex(L.xaxis.title.text or "")
    yt = html_to_rootlatex(L.yaxis.title.text or "")
    for a in L.annotations:  # plotlyhep's end-aligned axis labels are annotations
        if a.textangle == -90 and a.x == 0 and a.y == 1 and not yt:
            yt = html_to_rootlatex(a.text)
        elif a.xanchor == "right" and a.y == 0 and a.x == 1 and a.textangle in (None, 0) and not xt:
            xt = html_to_rootlatex(a.text)
    xr = list(L.xaxis.range) if L.xaxis.range else None
    yr = list(L.yaxis.range) if L.yaxis.range else None
    if logx and xr:
        xr = [10**v for v in xr]
    if logy and yr:
        yr = [10**v for v in yr]
    for tr in pfig.data:
        if xr is None and hasattr(tr, "x") and tr.x is not None and len(tr.x):
            xs = np.asarray(tr.x, float)
            xr = [float(np.nanmin(xs)), float(np.nanmax(xs))]
        if yr is None and hasattr(tr, "y") and tr.y is not None and len(tr.y):
            ys = np.asarray(tr.y, float)
            yr = [min(0.0, float(np.nanmin(ys))), 1.05 * float(np.nanmax(ys))]
    xr, yr = xr or [0, 1], yr or [0, 1]
    frame = c.DrawFrame(xr[0], yr[0], xr[1], yr[1], f";{xt};{yt}")
    keep.append(frame)
    leg_entries = []
    for i, tr in enumerate(pfig.data):
        kind = tr.type
        label = html_to_rootlatex(tr.name or "")
        if kind == "heatmap":
            x, y = np.asarray(tr.x, float), np.asarray(tr.y, float)
            z = np.asarray(tr.z, float)
            dx = np.diff(x).mean() if len(x) > 1 else 1.0
            dy = np.diff(y).mean() if len(y) > 1 else 1.0
            h2 = ROOT.TH2D(f"h2_{i}", label, len(x), x[0] - dx / 2, x[-1] + dx / 2, len(y), y[0] - dy / 2, y[-1] + dy / 2)
            for jy in range(len(y)):
                for ix in range(len(x)):
                    v = z[jy][ix]
                    if v == v:
                        h2.SetBinContent(ix + 1, jy + 1, float(v))
            h2.Draw("COLZ SAME" if tr.showscale else "COL SAME")
            keep.append(h2)
            continue
        if kind == "bar":
            x, y = np.asarray(tr.x, float), np.asarray(tr.y, float)
            w = np.asarray(tr.width, float) if tr.width is not None else np.full_like(x, np.diff(x).mean() if len(x) > 1 else 1.0)
            edges = np.concatenate([x - w / 2, [x[-1] + w[-1] / 2]])
            h = ROOT.TH1D(f"h_{i}", label, len(x), edges)
            for k, v in enumerate(y):
                h.SetBinContent(k + 1, float(v))
            h.SetFillColor(_color_index(ROOT, tr.marker.color))
            h.SetLineColor(_color_index(ROOT, tr.marker.line.color or tr.marker.color))
            h.Draw("HIST SAME")
            keep.append(h)
            if tr.showlegend:
                leg_entries.append((h, label, "f"))
            continue
        if kind != "scatter":
            continue
        x, y = np.asarray(tr.x, float), np.asarray(tr.y, float)
        mode = tr.mode or "lines"
        if "lines" in mode and tr.line.shape == "hv" and "markers" not in mode:
            edges, vals = _steps_to_hist(x, y)
            h = ROOT.TH1D(f"h_{i}", label, len(vals), np.asarray(edges, float))
            for k, v in enumerate(vals):
                h.SetBinContent(k + 1, float(v))
            h.SetLineColor(_color_index(ROOT, tr.line.color))
            h.SetLineWidth(int(round(tr.line.width or 1)))
            h.SetLineStyle(_DASH_INV.get(tr.line.dash or "solid", 1))
            if tr.fill in ("tozeroy", "tonexty") and tr.fillcolor:
                h.SetFillColor(_color_index(ROOT, tr.fillcolor))
            h.Draw("HIST SAME")
            keep.append(h)
            if tr.showlegend:
                leg_entries.append((h, label, "f" if tr.fill else "l"))
            continue
        ey = tr.error_y
        ex = tr.error_x
        if ey.array is not None or ex.array is not None:
            n = len(x)
            if ey.arrayminus is not None or ex.arrayminus is not None:
                g = ROOT.TGraphAsymmErrors(n)
                for k in range(n):
                    g.SetPoint(k, float(x[k]), float(y[k]))
                    g.SetPointError(
                        k,
                        float(ex.arrayminus[k]) if ex.arrayminus is not None else (float(ex.array[k]) if ex.array is not None else 0.0),
                        float(ex.array[k]) if ex.array is not None else 0.0,
                        float(ey.arrayminus[k]) if ey.arrayminus is not None else (float(ey.array[k]) if ey.array is not None else 0.0),
                        float(ey.array[k]) if ey.array is not None else 0.0,
                    )
            else:
                g = ROOT.TGraphErrors(n)
                for k in range(n):
                    g.SetPoint(k, float(x[k]), float(y[k]))
                    g.SetPointError(
                        k, float(ex.array[k]) if ex.array is not None else 0.0, float(ey.array[k]) if ey.array is not None else 0.0
                    )
        else:
            g = ROOT.TGraph(len(x), np.asarray(x, float), np.asarray(y, float))
        g.SetTitle(label)
        col = tr.marker.color if "markers" in mode and tr.marker.color else tr.line.color
        ci = _color_index(ROOT, col if isinstance(col, str) else None)
        g.SetLineColor(_color_index(ROOT, tr.line.color) if tr.line.color else ci)
        g.SetMarkerColor(ci)
        g.SetLineWidth(int(round(tr.line.width or 1)))
        g.SetLineStyle(_DASH_INV.get(tr.line.dash or "solid", 1))
        g.SetMarkerStyle(_MARKER_INV.get(tr.marker.symbol or "circle", 20))
        g.SetMarkerSize(float(tr.marker.size or MARKER_PX) / MARKER_PX)
        dopt = ("P" if "markers" in mode else "") + ("L" if "lines" in mode else "")
        if tr.error_y.width == 0:
            dopt += "Z"
        g.Draw(dopt + " SAME")
        keep.append(g)
        if tr.showlegend:
            leg_entries.append(
                (g, label, ("p" if "markers" in mode else "") + ("l" if "lines" in mode else "") + ("e" if ey.array is not None else ""))
            )
    for a in L.annotations:
        if not a.text or a.showarrow:
            continue
        if a.textangle == -90 or (a.xanchor == "right" and a.y == 0 and a.x == 1 and a.yref == "paper"):
            continue  # axis labels, already on the frame
        t = ROOT.TLatex()
        t.SetNDC(a.xref == "paper")
        t.SetTextSize((a.font.size or 14) / (ROOT_EM * H))
        t.SetTextAlign(
            {"left": 1, "center": 2, "right": 3}.get(a.xanchor or "center", 2) * 10
            + {"bottom": 1, "middle": 2, "top": 3}.get(a.yanchor or "middle", 2)
        )
        if a.font.color:
            t.SetTextColor(_color_index(ROOT, a.font.color))
        txt = html_to_rootlatex(a.text)
        ax_, ay_ = float(a.x), float(a.y)
        if a.xref != "paper" and logx:
            ax_ = 10**ax_
        if a.yref != "paper" and logy:
            ay_ = 10**ay_
        keep.append(t.DrawLatex(ax_, ay_, txt))
        keep.append(t)
    for s in L.shapes:
        if s.type == "line":
            ln = ROOT.TLine(float(s.x0), float(s.y0), float(s.x1), float(s.y1))
            if s.xref == "paper":
                ln.SetNDC(True)
            ln.SetLineColor(_color_index(ROOT, s.line.color))
            ln.SetLineWidth(int(round(s.line.width or 1)))
            ln.SetLineStyle(_DASH_INV.get(s.line.dash or "solid", 1))
            ln.Draw()
            keep.append(ln)
    if leg_entries and L.showlegend is not False:
        lg = L.legend
        lx = float(lg.x if lg.x is not None else 0.98)
        ly = float(lg.y if lg.y is not None else 0.98)
        xa, ya = lg.xanchor or "auto", lg.yanchor or "auto"
        xa = "right" if xa == "auto" else xa
        ya = "top" if ya == "auto" else ya
        lw_, lh_ = 0.28, 0.05 * len(leg_entries) + 0.02
        x1 = lx if xa == "left" else (lx - lw_ if xa == "right" else lx - lw_ / 2)
        y2 = ly if ya == "top" else (ly + lh_ if ya == "bottom" else ly + lh_ / 2)
        leg = ROOT.TLegend(
            left + (1 - left - right) * x1,
            bottom + (1 - top - bottom) * (y2 - lh_),
            left + (1 - left - right) * (x1 + lw_),
            bottom + (1 - top - bottom) * y2,
        )
        leg.SetBorderSize(int(lg.borderwidth or 0))
        leg.SetFillStyle(0 if (lg.bgcolor in (None, "rgba(0,0,0,0)")) else 1001)
        if lg.font.size:
            leg.SetTextSize(lg.font.size / (ROOT_EM * H))
        for obj, label, o in leg_entries:
            leg.AddEntry(obj, label, o)
        leg.Draw()
        keep.append(leg)
    c.Update()
    for o in keep:
        try:
            ROOT.SetOwnership(o, False)
        except Exception:
            pass
    c._plotlyhep_keep = keep
    return c
