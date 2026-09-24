"""Histogram helpers mirroring mplhep.histplot / hist2dplot semantics."""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from ._units import pt2px

def bin_hover(edges, values, err=None, name=None) -> dict:
    """hovertemplate + customdata for a per-bin trace: '[lo, hi)  value ± err'."""
    e = np.asarray(edges, float); v = np.asarray(values, float)
    lo, hi = e[:-1], e[1:]
    if err is not None:
        cd = np.column_stack([lo, hi, v, np.asarray(err, float)])
        tmpl = "[%{customdata[0]:g}, %{customdata[1]:g})<br>%{customdata[2]:.4g} ± %{customdata[3]:.3g}"
    else:
        cd = np.column_stack([lo, hi, v])
        tmpl = "[%{customdata[0]:g}, %{customdata[1]:g})<br>%{customdata[2]:.4g}"
    if name: tmpl = f"<b>{name}</b><br>" + tmpl
    return dict(customdata=cd, hovertemplate=tmpl + "<extra></extra>", hoverinfo=None)

def _edges(bins, n):
    bins = np.asarray(bins, dtype=float) if bins is not None else np.arange(n + 1, dtype=float)
    assert len(bins) == n + 1, "bins must be edges (len(H)+1)"
    return bins

def histplot(fig: go.Figure, H, bins=None, *, yerr=None, histtype: str = "step", label=None,
             color=None, linewidth=None, edges: bool = True, stack: bool = False, density: bool = False,
             showlegend=None, row: int = 1, **kw) -> list:
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
    axes = dict(xaxis="x" if row == 1 else f"x{row}", yaxis="y" if row == 1 else f"y{row}")   # panel of a ratio_figure
    for h, lab, col, err in zip(Hs, labels, colors, errs):
        show = (lab is not None) if showlegend is None else showlegend
        # hover: one entry per bin — "[lo, hi)  content ± err" — on an invisible marker at the bin centre,
        # so the drawn outline/fill/error segments never answer the cursor themselves
        hover = bin_hover(e, h, err, name=lab)
        if histtype in ("step", "fill"):
            x = np.concatenate([[e[0]], e, [e[-1]]]) if edges else e
            y = np.concatenate([[0.0], h, [h[-1], 0.0]]) if edges else np.concatenate([h, [h[-1]]])
            t = go.Scatter(x=x, y=y, mode="lines", line=dict(shape="hv", width=lw, color=col),
                           name=lab or "", showlegend=show, hoverinfo="skip", **kw)
            if histtype == "fill":
                t.update(fill="tozeroy", line=dict(width=0, color=col), fillcolor=col)
            traces.append(t)
            traces.append(go.Scatter(x=centers, y=h, mode="markers", name=lab or "",
                                     marker=dict(size=0.1, color=col), showlegend=False,
                                     error_y=dict(type="data", array=err, thickness=lw, width=0, color=col) if err is not None else None,
                                     **hover))
        elif histtype == "errorbar":
            traces.append(go.Scatter(x=centers, y=h, mode="markers", name=lab or "", showlegend=show,
                                     marker=dict(symbol="circle", size=pt2px(3.5), color=col),   # mplhep marker "." ~ half of markersize 6 pt
                                     error_y=dict(type="data", array=err, thickness=pt2px(1), width=0, color=col)
                                     if err is not None else None, **hover, **kw))
        else:
            raise ValueError(f"histtype {histtype!r} not supported")
    # stacked fills are cumulative sums drawn with fill='tozeroy': paint the tallest first so
    # each lower layer covers the ones above it; legend keeps the given order via legendrank
    if stack and histtype == "fill":
        for r, t in enumerate(traces): t.update(legendrank=1000 + r)
        traces = traces[::-1]
    for t in traces:
        t.update(**axes); fig.add_trace(t)
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
