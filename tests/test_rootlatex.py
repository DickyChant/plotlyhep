"""TLatex markup <-> HTML (pure functions, no ROOT needed)."""

from plotlyhep.root import html_to_rootlatex, root_color, rootlatex_to_html


def test_rootlatex_to_html():
    assert rootlatex_to_html("m_{jj} [GeV]") == "m<sub>jj</sub> [GeV]"
    assert rootlatex_to_html("#sqrt{s} = 13 TeV") == "√s = 13 TeV"
    assert rootlatex_to_html("#it{CMS} #bf{Preliminary}") == "<i>CMS</i> <b>Preliminary</b>"
    assert rootlatex_to_html("p_{T}^{#mu} #pm 1") == "p<sub>T</sub><sup>μ</sup> ± 1"
    assert rootlatex_to_html("#bar{q}q #rightarrow #gamma#gamma") == "q̄q → γγ"
    assert rootlatex_to_html("#scale[0.8]{x^2}") == "x<sup>2</sup>"
    assert rootlatex_to_html("#it{#alpha_{s}}") == "<i>α<sub>s</sub></i>"  # nested


def test_html_to_rootlatex():
    assert html_to_rootlatex("m<sub>jj</sub> [GeV]") == "m_{jj} [GeV]"
    assert html_to_rootlatex("<b>CMS</b> <i>Preliminary</i>") == "#bf{CMS} #it{Preliminary}"
    assert html_to_rootlatex("138 fb⁻¹ (13.6 TeV)") == "138 fb^{-1} (13.6 TeV)"
    assert html_to_rootlatex("α ± β") == "#alpha #pm #beta"


def test_root_color_table_without_root():
    assert root_color(1) == "#000000" and root_color(2) == "#ff0000" and root_color(601) == "#0000cc"
    assert root_color(2, 0.5) == "rgba(255,0,0,0.500)"
    assert root_color(None) == "black"
