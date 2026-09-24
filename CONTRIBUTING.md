# Contributing

plotlyhep follows the [scikit-hep developer guidelines](https://scikit-hep.org/developer).

```bash
pip install -e ".[dev]"
pre-commit install            # ruff on every commit
pytest                        # 79 tests (needs kaleido 0.2.1, which bundles Chromium)
pytest --regen-baselines      # after an intentional visual change: regenerate tests/baseline and commit it
nox                           # lint (ruff, ruff format, mypy, codespell) + tests, what CI runs
pipx run 'repo-review[cli]' --package sp-repo-review .   # scikit-hep conformance report
```

The scikit-hep checks are all green except the optional ones we chose not to adopt
(mypy strict mode, a Markdown formatter, a type checker inside pre-commit); `convert.py`
is excluded from mypy until matplotlib's dynamic getters are typed. GitHub Actions
are hash-pinned (dependabot keeps them fresh) and pass zizmor.

## How the tests are organised

The suite mirrors [mplhep's](https://github.com/scikit-hep/mplhep/tree/master/tests):

| file | what it covers |
|---|---|
| `conftest.py` | the `@pytest.mark.image_compare(tolerance, remove_text)` marker: a Plotly analogue of pytest-mpl (render with kaleido, RMS against `tests/baseline/`) |
| `helpers.py` | deterministic inputs |
| `test_basic.py` | `histplot` (step / fill / errorbar / stack / density), `hist2dplot` |
| `test_styles.py` | templates: values derived from mplhep's rcParams, `use`, `root_template`, `template_json` |
| `test_labels.py` | `exp_text` / `exp_label` geometry (`loc` 0-4, size ratios, lumi line), axis-label helpers |
| `test_layouts.py` | `ratio_figure` (GridSpec geometry checked against matplotlib itself), `ratioplot` |
| `test_convert.py` | `from_mpl` / `to_mpl`, mathtext <-> HTML |
| `test_html.py` | `embed` (frozen by default, edit chip, page-level template), `script_tag` |
| `test_inputs.py` | input shapes and error messages |
| `test_hover.py` | hover content |
| `test_pixel.py`, `compare.py` | fidelity to mplhep: same figure through both stacks at 1000×1000, ratchet thresholds |
| `test_root.py`, `compare_root.py` | fidelity to ROOT's tutorial output images for the gallery rebuilds |

`remove_text=True` (the default) strips text before rendering so baselines depend on geometry,
not on the fonts of the machine — the same idea as pytest-mpl's `remove_text`.

Tests that keep their text (the label tests) rely on `conftest.py` pinning fontconfig to the
font files that `mplhep-data` ships, and nothing else. matplotlib already lays text out from
those files, so it renders the same everywhere; kaleido's Chromium takes whatever fontconfig
offers, and two versions of the same TeX Gyre Heros moved a top-anchored label by ~10 px
between a laptop and the CI runner. With both stacks reading the same bytes the baselines
are portable and the pixel harness compares like with like. `PLOTLYHEP_SYSTEM_FONTS=1`
turns the pin off when you want to see what your own machine renders.
