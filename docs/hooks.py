"""mkdocs hooks: build the live figure on the home page from the installed plotlyhep at every build,
so the docs never show a stale embed (the snippet is generated, not committed)."""

from __future__ import annotations

import os

import numpy as np


def on_pre_build(config, **kwargs):
    import plotlyhep as php
    from plotlyhep import html

    php.style.use("CMS")
    bins = np.linspace(0, 200, 41)
    mc = np.histogram(np.random.default_rng(1).normal(90, 25, 3000), bins)[0] * 1.3
    data = np.histogram(np.random.default_rng(2).normal(90, 25, 4000), bins)[0]
    fig = php.figure(width=640, height=640)  # scaled: fonts, ticks and margins at 0.64
    php.histplot(fig, mc, bins, label="MC")
    php.histplot(fig, data, bins, yerr=True, histtype="errorbar", color="black", label="Data")
    php.cms.label(fig, "Preliminary", data=True, lumi=138, com=13.6)
    php.set_xlabel(fig, "m<sub>jj</sub> [GeV]")
    php.set_ylabel(fig, "Events")
    out = os.path.join(config["docs_dir"], "_snippets")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "hello.html"), "w") as fh:
        fh.write(
            html.script_tag(None)
            + html.SLIDE_CSS
            + '<div style="max-width:640px">'
            + html.embed(fig, "hello-fig", width="100%", height="640px", inherit_template=False)
            + "</div>\n"
        )
