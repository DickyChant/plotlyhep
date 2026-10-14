"""Check that the built sdist and wheel ship every file of src/plotlyhep, data files included.

The test suite imports plotlyhep from src/ (tests/conftest.py), so a file that the build leaves
out passes every test and still breaks every install: v0.2.0 shipped without _root_colors.json,
and `import plotlyhep` failed with FileNotFoundError in plotlyhep/root.py.

Usage: python -m build && python tests/check_dist.py dist
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tarfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def package_files() -> set[str]:
    """The tracked files under src/plotlyhep, as paths relative to src/ (plotlyhep/...)."""
    out = subprocess.run(["git", "ls-files", "src/plotlyhep"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return {f.removeprefix("src/") for f in out.split()}


def main(dist: str) -> int:
    want = package_files()
    if not want:
        print("no tracked files under src/plotlyhep")
        return 1
    wheels, sdists = sorted(pathlib.Path(dist).glob("*.whl")), sorted(pathlib.Path(dist).glob("*.tar.gz"))
    if not wheels or not sdists:
        print(f"need a wheel and an sdist in {dist}, found {[p.name for p in wheels + sdists]}")
        return 1
    bad = 0
    for w in wheels:
        with zipfile.ZipFile(w) as z:
            missing = sorted(want - set(z.namelist()))
        print(f"{w.name}: {len(want) - len(missing)}/{len(want)} package files" + (f", MISSING {missing}" if missing else ""))
        bad += bool(missing)
    for s in sdists:
        with tarfile.open(s) as t:
            have = {n.split("/", 1)[1].removeprefix("src/") for n in t.getnames() if "/" in n}
        missing = sorted(want - have)
        print(f"{s.name}: {len(want) - len(missing)}/{len(want)} package files" + (f", MISSING {missing}" if missing else ""))
        bad += bool(missing)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "dist"))
