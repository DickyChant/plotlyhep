#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["nox>=2025.2.9"]
# ///
"""nox sessions, as in scikit-hep projects: `nox` runs lint and tests."""

import nox

nox.needs_version = ">=2025.2.9"
nox.options.default_venv_backend = "uv|virtualenv"


@nox.session
def lint(session: nox.Session) -> None:
    session.install("ruff", "mypy", "codespell", "numpy", "plotly")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")
    session.run("mypy")
    session.run("codespell")


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    session.install("-e", ".[test]")
    session.run("pytest", *session.posargs)


@nox.session(default=False)
def baselines(session: nox.Session) -> None:
    """Regenerate the image baselines (commit the result deliberately)."""
    session.install("-e", ".[test]")
    session.run("pytest", "--regen-baselines", "-q", "tests")


if __name__ == "__main__":
    nox.main()
