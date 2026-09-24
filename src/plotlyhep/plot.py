"""Histogram helpers mirroring mplhep.histplot / hist2dplot semantics."""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from ._units import pt2px

def _edges(bins, n):
    bins = np.asarray(bins, dtype=float) if bins is not None else np.arange(n + 1, dtype=float)
    assert len(bins) == n + 1, "bins must be edges (len(H)+1)"
    return bins

def histplot(fig: go.Figure, H, bins=None, *, yerr=None, histtype: str = "step", label=None,
             color=None, linewidth=None, edges: bool = True, stack: bool = False, density: bool = False,
             showlegend=None, **kw) -> list:
    """Add one or several histograms. H: 1D array or list of arrays (same bins).
    histtype: 'step' (mplhep default, stairs with edges to zero), 'fill', 'errorbar'.
    yerr: True -> sqrt(H), or an array / list of arrays."""
    Hs = [np.asarray(h, dtype=float) for h in (H if isinstance(H, (list, tuple)) else [H])]
    n = len(Hs[0]); e = _edges(bins, n); centers = 0.5 * (e[1:] + e[:-1]); widths = np.diff(e)
    labels = label if isinstance(label, (list, tuple)) else [label] * len(Hs)
    colors = color if isinstance(color, (list, tuple)) else [color] * len(Hs)
    if density:
        Hs = [h / (h.sum() * widths) for h in Hs]
    if stack:
        acc = np.zeros(n); stacked = []
        for h in Hs: acc = acc + h; stacked.append(acc.copy())
        Hs = stacked
    if yerr is True: errs = [np.sqrt(np.abs(h)) for h in Hs]
    elif yerr is None or yerr is False: errs = [None] * len(Hs)
    else: errs = [np.asarray(y) for y in (yerr if isinstance(yerr, (list, tuple)) else [yerr])]
    traces = []
    lw = pt2px(1.5 if linewidth is None else linewidth)      # mplhep step default 1.5 pt
    for h, lab, col, err in zip(Hs, labels, colors, errs):
        show = (lab is not None) if showlegend is None else showlegend
        if histtype in ("step", "fill"):
            x = np.concatenate([[e[0]], e, [e[-1]]]) if edges else e
            y = np.concatenate([[0.0], h, [h[-1], 0.0]]) if edges else np.concatenate([h, [h[-1]]])
            t = go.Scatter(x=x, y=y, mode="lines", line=dict(shape="hv", width=lw, color=col),
                           name=lab or "", showlegend=show, **kw)
            if histtype == "fill":
                t.update(fill="tozeroy", line=dict(width=0, color=col), fillcolor=col)
            traces.append(t)
            if err is not None:
                traces.append(go.Scatter(x=centers, y=h, mode="markers",
                                         marker=dict(size=0.1, color=col), showlegend=False,
                                         error_y=dict(type="data", array=err, thickness=lw, width=0, color=col)))
        elif histtype == "errorbar":
            traces.append(go.Scatter(x=centers, y=h, mode="markers", name=lab or "", showlegend=show,
                                     marker=dict(symbol="circle", size=pt2px(3.5), color=col),   # mplhep marker "." ~ half of markersize 6 pt
                                     error_y=dict(type="data", array=err, thickness=pt2px(1), width=0, color=col)
                                     if err is not None else None, **kw))
        else:
            raise ValueError(f"histtype {histtype!r} not supported")
    for t in traces:
        fig.add_trace(t)
    if any(l is not None for l in labels):
        fig.update_layout(showlegend=True)
    return traces

def hist2dplot(fig: go.Figure, H, xbins, ybins, *, colorscale="Viridis", cbar: bool = True, **kw):
    H = np.asarray(H, dtype=float)
    xe, ye = np.asarray(xbins, float), np.asarray(ybins, float)
    xc, yc = 0.5 * (xe[1:] + xe[:-1]), 0.5 * (ye[1:] + ye[:-1])
    t = go.Heatmap(x=xc, y=yc, z=H.T, colorscale=colorscale, showscale=cbar,
                   xgap=0, ygap=0, colorbar=dict(thickness=pt2px(12), outlinewidth=0), **kw)
    fig.add_trace(t)
    return t
