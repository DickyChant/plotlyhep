"""ROOT <-> Plotly conversion. Needs PyROOT; the whole module is skipped without it.
The pixel test renders the same canvas with ROOT (c.SaveAs) and with plotlyhep (kaleido) and ratchets
mean|Δ| and SSIM like the ROOT-tutorial rebuilds do."""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

ROOT = pytest.importorskip("ROOT")
ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

from plotlyhep.root import from_root, to_root

HERE = os.path.dirname(os.path.abspath(__file__))


def _hist(name="h", n=20, lo=0.0, hi=100.0):
    h = ROOT.TH1F(name, "a title;m_{jj} [GeV];Events", n, lo, hi)
    for i in range(1, n + 1):
        h.SetBinContent(i, 10.0 + i)
        h.SetBinError(i, 2.0)
    return h


@pytest.fixture(autouse=True)
def _no_stats():
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetOptTitle(1)
    yield


def test_th1_hist_option():
    h = _hist()
    h.SetLineColor(ROOT.kBlue + 1)
    h.SetLineStyle(2)
    h.SetLineWidth(3)
    fig = from_root(h, "HIST")
    steps = [t for t in fig.data if t.type == "scatter" and t.line.shape == "hv"]
    assert len(steps) == 1
    t = steps[0]
    assert t.line.color == "#0000cc" and t.line.dash == "dash" and t.line.width == 3
    np.testing.assert_allclose(np.asarray(t.y[1:-2]), 10.0 + np.arange(1, 21))
    assert list(fig.layout.xaxis.range) == [0.0, 100.0]
    assert fig.layout.yaxis.range[1] > 30  # ROOT's own autoscale, not ours
    texts = [a.text for a in fig.layout.annotations]
    assert "m<sub>jj</sub> [GeV]" in texts and "Events" in texts and "a title" in texts


def test_th1_errors_option():
    h = _hist()
    h.SetMarkerStyle(21)
    fig = from_root(h, "E1")
    (t,) = [t for t in fig.data if t.mode == "markers"]
    assert t.marker.symbol == "square"
    np.testing.assert_allclose(np.asarray(t.error_y.array), 2.0)
    assert t.error_y.width > 0  # E1 draws caps
    fig0 = from_root(h, "E X0")
    (t0,) = [t for t in fig0.data if t.mode == "markers"]
    assert t0.error_y.width == 0 and t0.error_x.array is None


def test_tgraph_errors_and_styles():
    g = ROOT.TGraphErrors(3)
    for i in range(3):
        g.SetPoint(i, 10.0 * i, 1.0 + i)
        g.SetPointError(i, 1.5, 0.5)
    g.SetMarkerStyle(24)
    g.SetMarkerColor(ROOT.kRed)
    g.SetLineColor(ROOT.kGreen + 2)
    fig = from_root(g, "APL")
    (t,) = [t for t in fig.data if t.type == "scatter"]
    assert t.mode == "markers+lines" and t.marker.symbol == "circle-open" and t.marker.color == "#ff0000"
    assert t.line.color == ROOT.gROOT.GetColor(ROOT.kGreen + 2).AsHexString()
    np.testing.assert_allclose(np.asarray(t.error_y.array), 0.5)
    np.testing.assert_allclose(np.asarray(t.error_x.array), 1.5)


def test_tgraph_asymm_band():
    g = ROOT.TGraphAsymmErrors(3)
    for i in range(3):
        g.SetPoint(i, i, 2.0)
        g.SetPointError(i, 0, 0, 0.5, 1.0)
    fig = from_root(g, "A3")
    band = [t for t in fig.data if t.fill == "tonexty"]
    assert len(band) == 1
    hi = [t for t in fig.data if t.fill is None][0]
    np.testing.assert_allclose(np.asarray(hi.y), 3.0)
    np.testing.assert_allclose(np.asarray(band[0].y), 1.5)


def test_th2_colz_uses_palette():
    h2 = ROOT.TH2F("h2", "h2;x;y", 4, 0, 4, 3, 0, 3)
    h2.Fill(1.5, 1.5)
    h2.Fill(1.5, 1.5)
    fig = from_root(h2, "COLZ")
    (t,) = [t for t in fig.data if t.type == "heatmap"]
    z = np.asarray(t.z, float)
    assert z.shape == (3, 4) and z[1][1] == 2.0 and np.isnan(z[0][0])  # empty bins are not painted
    assert t.showscale and len(t.colorscale) == 9
    pal = ROOT.TColor.GetPalette()
    assert t.colorscale[0][1] == ROOT.gROOT.GetColor(pal[0]).AsHexString()


def test_tf1_and_fit_function():
    f = ROOT.TF1("f", "x*x", 0, 3)
    f.SetNpx(6)
    fig = from_root(f)
    (t,) = fig.data
    np.testing.assert_allclose(np.asarray(t.x), np.linspace(0, 3, 7))
    np.testing.assert_allclose(np.asarray(t.y), np.linspace(0, 3, 7) ** 2)
    h = _hist("hfit")
    h.Fit("pol1", "Q")
    fig = from_root(h, "HIST")
    assert any(t.name == "pol1" for t in fig.data)  # the fit lives in the list of functions


def test_canvas_legend_text_line_and_log():
    c = ROOT.TCanvas("cl", "", 800, 600)
    c.SetLogy(True)
    h = _hist("hl")
    h.Draw("E1")
    g = ROOT.TGraph(2, np.array([0.0, 100.0]), np.array([15.0, 25.0]))
    g.Draw("L SAME")
    leg = ROOT.TLegend(0.6, 0.7, 0.88, 0.88)
    leg.AddEntry(h, "the #it{data}", "lep")
    leg.AddEntry(g, "a line", "l")
    leg.Draw()
    t = ROOT.TLatex()
    t.SetNDC(True)
    t.SetTextAlign(13)
    t.SetTextSize(0.05)
    t.DrawLatex(0.15, 0.85, "#sqrt{s} = 13 TeV, #alpha_{s}")
    ln = ROOT.TLine(0, 20, 100, 20)
    ln.SetLineColor(ROOT.kRed)
    ln.Draw()
    c.Update()
    fig = from_root(c)
    assert (fig.layout.width, fig.layout.height) == (c.GetWw(), c.GetWh())
    assert fig.layout.yaxis.type == "log" and fig.layout.xaxis.domain[0] == pytest.approx(c.GetLeftMargin())
    named = {t.name for t in fig.data if t.showlegend}
    assert named == {"the <i>data</i>", "a line"}
    L = fig.layout.legend
    assert (L.x, L.y, L.xanchor, L.yanchor) == (0.6, 0.88, "left", "top") and L.borderwidth == 1
    a = next(a for a in fig.layout.annotations if "13 TeV" in a.text)
    assert a.text == "<b>√s = 13 TeV, α<sub>s</sub></b>" and (a.x, a.y, a.xanchor, a.yanchor) == (0.15, 0.85, "left", "top")
    assert a.font.size == pytest.approx(0.90 * 0.05 * c.GetWh())
    (s,) = fig.layout.shapes
    assert s.type == "line" and s.line.color == "#ff0000" and s.y0 == pytest.approx(np.log10(20))  # data coords on a log axis
    c.Close()


def test_divided_canvas_gives_two_panels():
    c = ROOT.TCanvas("cd", "", 800, 400)
    c.Divide(2, 1)
    c.cd(1)
    h = _hist("hd")
    h.Draw("HIST")
    c.cd(2)
    g = ROOT.TGraph(3, np.array([0.0, 1.0, 2.0]), np.array([1.0, 3.0, 2.0]))
    g.Draw("APL")
    c.Update()
    fig = from_root(c)
    assert fig.layout.xaxis.domain[1] <= 0.5 and fig.layout.xaxis2.domain[0] >= 0.5
    assert [t.xaxis for t in fig.data] == ["x", "x2"]
    c.Close()


def test_stack_paints_top_down():
    hs = ROOT.THStack("hs", "")
    a, b = _hist("sa"), _hist("sb")
    a.SetFillColor(ROOT.kBlue)
    b.SetFillColor(ROOT.kRed)
    hs.Add(a)
    hs.Add(b)
    fig = from_root(hs, "HIST")
    fills = [t for t in fig.data if t.fill == "tozeroy"]
    assert len(fills) == 2
    top, bottom = fills
    assert np.nanmax(np.asarray(top.y, float)) > np.nanmax(np.asarray(bottom.y, float))
    np.testing.assert_allclose(np.asarray(top.y[1:-2]), 2 * (10.0 + np.arange(1, 21)))


def test_stats_box_when_enabled():
    ROOT.gStyle.SetOptStat(1111)
    h = _hist("hs1")
    fig = from_root(h)
    box = [a for a in fig.layout.annotations if "Entries" in a.text]
    assert box and box[0].xanchor == "right" and box[0].borderwidth == 1


def test_to_root_roundtrip_hist_graph_and_frame():
    import plotlyhep as php

    bins = np.linspace(0, 10, 6)
    vals = np.array([1.0, 4.0, 2.0, 5.0, 3.0])
    fig = php.figure("CMS")
    php.histplot(fig, vals, bins, label="MC", color="#e42536")
    php.histplot(fig, vals + 1, bins, yerr=np.ones(5), histtype="errorbar", color="black", label="Data")
    php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6)
    php.set_xlabel(fig, "m<sub>jj</sub> [GeV]")
    fig.update_xaxes(range=[0, 10])
    fig.update_yaxes(range=[0, 8])
    c = to_root(fig)
    kinds = [o.ClassName() for o in c._plotlyhep_keep]
    assert "TH1D" in kinds and "TGraphErrors" in kinds and "TLegend" in kinds and "TLatex" in kinds
    h = next(o for o in c._plotlyhep_keep if o.ClassName() == "TH1D")
    assert h.GetNbinsX() == 5 and [h.GetBinContent(i) for i in range(1, 6)] == list(vals)
    assert h.GetXaxis().GetBinLowEdge(1) == 0.0 and h.GetXaxis().GetBinUpEdge(5) == 10.0
    assert ROOT.gROOT.GetColor(h.GetLineColor()).AsHexString() == "#e42536"
    frame = c._plotlyhep_keep[0]
    assert frame.GetXaxis().GetTitle() == "m_{jj} [GeV]"
    assert c.GetUxmax() == 10.0 and c.GetUymax() == 8.0
    g = next(o for o in c._plotlyhep_keep if o.ClassName() == "TGraphErrors")
    assert g.GetN() == 5 and g.GetErrorY(0) == 1.0
    back = from_root(c)
    steps = [t for t in back.data if t.line.shape == "hv"]
    np.testing.assert_allclose(np.asarray(steps[0].y[1:-2]), vals)
    c.Close()


def test_pixel_against_root_rendering():
    """The same canvas through ROOT's painter and through from_root + kaleido: ratchet on the metrics."""
    from PIL import Image
    from skimage.metrics import structural_similarity as ssim

    c = ROOT.TCanvas("cp", "", 800, 600)
    h = _hist("hp")
    h.SetLineColor(ROOT.kBlue + 1)
    h.SetFillColor(ROOT.kAzure - 9)
    h.Draw("HIST")
    g = ROOT.TGraphErrors(5)
    for i in range(5):
        g.SetPoint(i, 10 + 20 * i, 12 + 3 * i)
        g.SetPointError(i, 0, 2)
    g.SetMarkerStyle(20)
    g.Draw("P SAME")
    leg = ROOT.TLegend(0.15, 0.7, 0.45, 0.85)
    leg.AddEntry(h, "histogram", "f")
    leg.AddEntry(g, "points", "pe")
    leg.Draw()
    t = ROOT.TLatex()
    t.SetNDC(True)
    t.SetTextSize(0.045)
    t.DrawLatex(0.55, 0.8, "#it{plotlyhep} #leftrightarrow ROOT")
    c.Update()
    out = os.path.join(HERE, "output", "rootconv")
    os.makedirs(out, exist_ok=True)
    ref_png = os.path.join(out, "canvas_root.png")
    c.SaveAs(ref_png)
    ref = Image.open(ref_png).convert("RGB")
    fig = from_root(c)
    ours = Image.open(__import__("io").BytesIO(fig.to_image(format="png", width=ref.size[0], height=ref.size[1], scale=1))).convert("RGB")
    ours.save(os.path.join(out, "canvas_plotly.png"))
    A, B = np.asarray(ref.convert("L"), float), np.asarray(ours.convert("L"), float)
    d = np.abs(A - B)
    m = {"mean_abs_diff": float(d.mean()), "ssim": float(ssim(A, B, data_range=255.0))}
    Image.fromarray((255 - d).astype(np.uint8)).save(os.path.join(out, "canvas_diff.png"))
    side = Image.new("RGB", (ref.size[0] * 2, ref.size[1]), "white")
    side.paste(ref, (0, 0))
    side.paste(ours, (ref.size[0], 0))
    side.save(os.path.join(out, "canvas_side.png"))
    th = json.load(open(os.path.join(HERE, "thresholds_root.json"))).get("from_root_canvas")
    print("from_root canvas:", m)
    if th:
        assert m["mean_abs_diff"] <= th["mean_abs_diff"], m
        assert m["ssim"] >= th["ssim"], m
    c.Close()
