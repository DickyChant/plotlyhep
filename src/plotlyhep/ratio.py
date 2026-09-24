"""Main panel + ratio panel, the standard HEP layout, with matplotlib's gridspec geometry so the
pixel harness can check it against mplhep:

    fig = php.ratio_figure("CMS", height_ratios=(3, 1), hspace=0.05)
    php.histplot(fig, mc, bins, label="MC")                       # top panel (row 1)
    php.histplot(fig, data, bins, yerr=True, histtype="errorbar", label="Data", color="black")
    php.ratioplot(fig, data, mc, bins, den_w2=mc_w2, label="Data / MC")   # bottom panel
"""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from .styles import template, figsize_px
from ._units import SUBPLOT, pt2px

def gridspec_domains(height_ratios=(3, 1), hspace=0.05, *, top=SUBPLOT["top"], bottom=SUBPLOT["bottom"]):
    """matplotlib GridSpec vertical layout as Plotly domains (fractions of the plot area).
    total = Σ h_i + (n-1)·hspace·mean(h)  →  paper y domains, top row first."""
    r = np.asarray(height_ratios, float); n = len(r); total = top - bottom
    axes_h = total / (1 + hspace * (n - 1) / n); sep = hspace * axes_h / n
    h = r / r.sum() * axes_h
    doms = []; y = top
    for hi in h:
        doms.append((round(min(1.0, max(0.0, (y - hi - bottom) / total)), 6), round(min(1.0, max(0.0, (y - bottom) / total)), 6))); y -= hi + sep
    return doms

def ratio_figure(exp: str = "CMS", *, height_ratios=(3, 1), hspace: float = 0.05,
                 ratio_range=(0.5, 1.5), ratio_title: str = "Data / MC", width=None, height=None) -> go.Figure:
    """Two stacked panels sharing x: (xaxis, yaxis) on top, (xaxis2, yaxis2) below."""
    t = template(exp); W, H = figsize_px(exp)
    top_dom, bot_dom = gridspec_domains(height_ratios, hspace)
    fig = go.Figure(layout=dict(template=t, width=width or W, height=height or H))
    ax = t.layout.xaxis.to_plotly_json(); ay = t.layout.yaxis.to_plotly_json()
    fig.update_layout(
        xaxis=dict(ax, domain=[0, 1], anchor="y", showticklabels=False, matches="x2"),
        yaxis=dict(ay, domain=list(top_dom), anchor="x"),
        xaxis2=dict(ax, domain=[0, 1], anchor="y2"),
        yaxis2=dict(ay, domain=list(bot_dom), anchor="x2", range=list(ratio_range),
                    title=dict(text=ratio_title, standoff=ay.get("title", {}).get("standoff", 8))),
    )
    # dashed reference line at ratio = 1 (drawn in data space of the ratio panel)
    fig.add_shape(type="line", xref="x2 domain", yref="y2", x0=0, x1=1, y0=1, y1=1, line=dict(color="rgba(25,28,32,0.55)", width=pt2px(1), dash="dash"))
    return fig

def ratioplot(fig: go.Figure, num, den, bins=None, *, num_w2=None, den_w2=None, band: bool = True,
              color="black", label=None, **kw):
    """num/den per bin with the numerator's Poisson (or num_w2) error as points in the ratio panel,
    plus the denominator's relative uncertainty as a band around 1 (band=True)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    n = len(num); e = np.asarray(bins, float) if bins is not None else np.arange(n + 1, dtype=float)
    ctr = 0.5 * (e[1:] + e[:-1])
    ok = den > 0
    r = np.where(ok, num / np.where(ok, den, 1), np.nan)
    nv = np.asarray(num_w2, float) if num_w2 is not None else num
    rerr = np.where(ok, np.sqrt(np.abs(nv)) / np.where(ok, den, 1), np.nan)
    traces = []
    if band and den_w2 is not None:
        rel = np.where(ok, np.sqrt(np.asarray(den_w2, float)) / np.where(ok, den, 1), 0.0)
        x = np.concatenate([[e[0]], e, [e[-1]]])
        lo = np.concatenate([[1.0], 1 - rel, [1 - rel[-1], 1.0]]); hi = np.concatenate([[1.0], 1 + rel, [1 + rel[-1], 1.0]])
        traces.append(go.Scatter(x=x, y=lo, mode="lines", line=dict(shape="hv", width=0), hoverinfo="skip", showlegend=False, xaxis="x2", yaxis="y2"))
        traces.append(go.Scatter(x=x, y=hi, mode="lines", line=dict(shape="hv", width=0), fill="tonexty", fillcolor="rgba(25,28,32,0.18)",
                                 hoverinfo="skip", showlegend=False, xaxis="x2", yaxis="y2", name="MC stat. unc."))
    hover = [f"[{e[i]:g}, {e[i+1]:g})<br>ratio <b>{r[i]:.3f}</b> ± {rerr[i]:.3f}<br>num {num[i]:.4g} · den {den[i]:.4g}" if ok[i] else f"[{e[i]:g}, {e[i+1]:g})<br>empty denominator" for i in range(n)]
    traces.append(go.Scatter(x=ctr, y=r, mode="markers", marker=dict(symbol="circle", size=pt2px(3.5), color=color), name=label or "ratio",
                             showlegend=False, xaxis="x2", yaxis="y2", customdata=hover, hovertemplate="%{customdata}<extra></extra>",
                             error_y=dict(type="data", array=rerr, thickness=pt2px(1), width=0, color=color), **kw))
    for t in traces: fig.add_trace(t)
    return traces
