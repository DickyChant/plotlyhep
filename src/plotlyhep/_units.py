"""matplotlib works in points and inches; Plotly works in CSS pixels.
Everything is compared at DPI = 100, so 1 pt = 100/72 px."""
DPI = 100.0
PT = DPI / 72.0                       # pixels per point at the comparison DPI

# matplotlib relative font sizes (rcParams 'small', 'medium', ...)
_REL = {"xx-small": 0.579, "x-small": 0.694, "small": 0.833, "medium": 1.0,
        "large": 1.2, "x-large": 1.44, "xx-large": 1.728}

def pt2px(pt: float) -> float:
    return float(pt) * PT

def fontsize_pt(value, base_pt: float) -> float:
    """Resolve an rcParams font size ('small', 12, '12') to points."""
    if value is None:
        return base_pt
    if isinstance(value, str):
        if value in _REL:
            return base_pt * _REL[value]
        return float(value)
    return float(value)

# default matplotlib subplot box, as fractions of the figure
SUBPLOT = dict(left=0.125, right=0.9, bottom=0.11, top=0.88)
