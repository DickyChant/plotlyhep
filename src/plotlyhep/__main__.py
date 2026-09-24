"""python -m plotlyhep export-templates <dir>   -> hep_cms.json, hep_atlas.json (opaque and transparent)"""
import json
import os
import sys

from .html import _NumpyEncoder
from .styles import template_json


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "export-templates":
        print(__doc__); return 2
    out = argv[1]; os.makedirs(out, exist_ok=True)
    for exp in ("CMS", "ATLAS"):
        for flavour, tr in (("", False), ("_transparent", True)):
            path = os.path.join(out, f"hep_{exp.lower()}{flavour}.json")
            json.dump(template_json(exp, transparent=tr), open(path, "w"), cls=_NumpyEncoder, indent=1)
            print("wrote", path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
