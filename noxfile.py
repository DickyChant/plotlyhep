"""nox sessions, as in scikit-hep projects: `nox -s lint tests`."""
import nox

nox.options.sessions = ["lint", "tests"]


@nox.session
def lint(session):
    session.install("ruff")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session):
    session.install("-e", ".[test]")
    session.run("pytest", *session.posargs)


@nox.session
def baselines(session):
    """Regenerate the image baselines (commit the result deliberately)."""
    session.install("-e", ".[test]")
    session.run("pytest", "--regen-baselines", "-q", "tests")
