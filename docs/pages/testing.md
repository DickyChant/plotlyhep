# Testing

The suite is laid out like mplhep's. Where mplhep uses pytest-mpl, `tests/conftest.py`
provides the same idea for Plotly:

```python
@pytest.mark.image_compare(tolerance=4, remove_text=True)
def test_histplot_step():
    fig = php.figure()
    php.histplot(fig, [h1, h2], bins, label=["a", "b"])
    return fig      # rendered with kaleido, RMS-compared with tests/baseline/test_histplot_step.png
```

`remove_text=True` strips annotations, titles, tick labels, colorbar labels and the legend
before rendering, so a baseline tests geometry rather than fonts. `pytest --regen-baselines`
rewrites the baselines after an intentional visual change; a failure saves actual, expected
and diff images under `tests/output/failed/`.

Tests that keep their text rely on the conftest pinning fontconfig to the font files that
`mplhep-data` ships, and nothing else. matplotlib lays text out from those files itself, so
it renders the same everywhere; kaleido's Chromium takes whatever fontconfig offers, and two
builds of the same TeX Gyre Heros moved a top-anchored label by ten pixels between a laptop
and the CI runner. With both stacks reading the same bytes the baselines are portable.
`PLOTLYHEP_SYSTEM_FONTS=1` turns the pin off.

| file | covers |
|---|---|
| `test_basic.py` | `histplot` step / fill / errorbar / stack / density, `hist2dplot` |
| `test_styles.py` | template values from mplhep's rcParams, `use`, `root_template`, transparent JSON |
| `test_labels.py` | `exp_text` / `exp_label` geometry for `loc` 0–4, the lumi line, axis-label helpers |
| `test_layouts.py` | ratio-panel domains against matplotlib's own GridSpec, `ratioplot` values |
| `test_convert.py`, `test_html.py`, `test_inputs.py` | conversion, embeds, input shapes |
| `test_hover.py` | hover content, probed headlessly |
| `test_pixel.py` + `compare.py` | the same figure through mplhep and plotlyhep at 1000×1000, ratchet thresholds |
| `test_root.py` + `compare_root.py` | the gallery rebuilds against ROOT's tutorial images |

```bash
pip install -e ".[dev]"
pytest                    # 79 tests, about 6 s
nox                       # lint (ruff, ruff format, mypy, codespell) and the test matrix
mkdocs serve              # this site, live
```
