# Install

plotlyhep is not on PyPI. Install it from git, which is what the tags and releases are for:

```bash
# the current main branch
pip install "plotlyhep @ git+https://github.com/DickyChant/plotlyhep"

# a tagged version
pip install "plotlyhep @ git+https://github.com/DickyChant/plotlyhep@v0.1.0"

# the release tarball or wheel (built by CI on every tag)
pip install https://github.com/DickyChant/plotlyhep/releases/download/v0.1.0/plotlyhep-0.1.0-py3-none-any.whl
pip install https://github.com/DickyChant/plotlyhep/releases/download/v0.1.0/plotlyhep-0.1.0.tar.gz
```

In a `requirements.txt` or `pyproject.toml` the same `plotlyhep @ git+https://...@v0.1.0` spec works.

The runtime dependencies are only `plotly>=5.20` and `numpy>=1.22`; plotly 5 and 6 both work.

## Extras

| extra | adds | for |
|---|---|---|
| `test` | plotly 5, `kaleido==0.2.1`, matplotlib, mplhep, pillow, scikit-image, pytest | rendering to PNG (`fig.to_image`), the converter, the test suite |
| `docs` | mkdocs-material, mkdocstrings | building this site |
| `dev` | test + ruff, mypy, nox, pre-commit, codespell | contributing |

```bash
pip install "plotlyhep[test] @ git+https://github.com/DickyChant/plotlyhep"
```

!!! note "kaleido"
    Static export (`fig.to_image`, `fig.write_image`) needs kaleido. The `test` extra pins
    `kaleido==0.2.1`, the last version that bundles its own Chromium, because Plotly 6 with
    kaleido 1.x expects a system Chrome. The library itself never imports kaleido.

## Development checkout

```bash
git clone https://github.com/DickyChant/plotlyhep
cd plotlyhep
pip install -e ".[dev]"
pytest
```
