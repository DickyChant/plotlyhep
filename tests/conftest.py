"""Test infrastructure, modelled on mplhep's suite.

mplhep uses pytest-mpl: a test returns a matplotlib figure and
``@pytest.mark.mpl_image_compare(style=..., remove_text=...)`` compares its render against a
baseline PNG in ``tests/baseline`` with an RMS tolerance. plotlyhep tests do the same for Plotly
figures with ``@pytest.mark.image_compare(tolerance=..., remove_text=...)``:

* the test returns a ``plotly.graph_objects.Figure``;
* it is rendered with kaleido at the figure's own width/height (scale 1);
* ``remove_text=True`` strips annotations, titles, tick labels and the legend before rendering,
  so geometry is compared independently of fonts (mplhep's ``remove_text`` does the same);
* the render is compared with ``tests/baseline/<test name>.png`` by the RMS of the grey-level
  difference; ``tolerance`` is in grey levels (0-255), like pytest-mpl's;
* ``pytest --regen-baselines`` writes the baselines; failures save actual / expected / diff
  images under ``tests/output/failed/``.
"""
from __future__ import annotations

import io
import os
import sys

import numpy as np
import pytest
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))
BASELINE = os.path.join(HERE, "baseline")
FAILED = os.path.join(HERE, "output", "failed")


def pytest_addoption(parser):
    parser.addoption("--regen-baselines", action="store_true", default=False, help="write baseline images instead of comparing")


def pytest_configure(config):
    config.addinivalue_line("markers", "image_compare(tolerance=4, remove_text=True): compare the returned Plotly figure with tests/baseline/<name>.png")
    config.addinivalue_line("markers", "render: needs kaleido (image rendering)")
    config.addinivalue_line("markers", "slow: takes more than a few seconds")


def _strip_text(fig):
    """Font-independent geometry: like pytest-mpl's remove_text."""
    import plotly.graph_objects as go

    f = go.Figure(fig)
    f.update_layout(annotations=[], showlegend=False, title=None)
    for name in f.layout:
        if name.startswith(("xaxis", "yaxis")):
            f.layout[name].update(showticklabels=False, title=dict(text=""))
    f.update_traces(selector=dict(type="scatter"), hoverinfo="skip")
    return f


def render(fig, *, remove_text=False, scale=1):
    f = _strip_text(fig) if remove_text else fig
    w, h = f.layout.width or 700, f.layout.height or 500
    png = f.to_image(format="png", width=w, height=h, scale=scale)
    return Image.open(io.BytesIO(png)).convert("RGB")


def rms(a: Image.Image, b: Image.Image) -> float:
    if a.size != b.size:
        return float("inf")
    x = np.asarray(a.convert("L"), dtype=float)
    y = np.asarray(b.convert("L"), dtype=float)
    return float(np.sqrt(np.mean((x - y) ** 2)))


@pytest.hookimpl(hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    marker = pyfuncitem.get_closest_marker("image_compare")
    if marker is None:
        yield
        return
    tol = marker.kwargs.get("tolerance", 4.0)
    remove_text = marker.kwargs.get("remove_text", True)
    funcargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
    fig = pyfuncitem.obj(**funcargs)
    if fig is None:
        pytest.fail(f"{pyfuncitem.name}: an image_compare test must return a Plotly figure")
    name = pyfuncitem.originalname or pyfuncitem.name
    actual = render(fig, remove_text=remove_text)
    path = os.path.join(BASELINE, name + ".png")
    if pyfuncitem.config.getoption("--regen-baselines"):
        os.makedirs(BASELINE, exist_ok=True)
        actual.save(path)
    else:
        if not os.path.exists(path):
            pytest.fail(f"baseline missing: {path} (run pytest --regen-baselines)")
        expected = Image.open(path).convert("RGB")
        err = rms(actual, expected)
        if err > tol:
            os.makedirs(FAILED, exist_ok=True)
            actual.save(os.path.join(FAILED, name + "-actual.png"))
            expected.save(os.path.join(FAILED, name + "-expected.png"))
            if actual.size == expected.size:
                d = np.abs(np.asarray(actual, float) - np.asarray(expected, float)).astype(np.uint8)
                Image.fromarray(255 - d).save(os.path.join(FAILED, name + "-diff.png"))
            pytest.fail(f"{name}: image RMS {err:.2f} > tolerance {tol} (see {FAILED})")
    # the hook must not run the function again
    outcome = yield  # noqa: F841
