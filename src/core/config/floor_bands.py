"""
Floor bands: per-floor-range tables in balance YAML, keyed by their range.

A band table maps keys that name a floor range to a value (spawn weights,
count formulas, ...):

    floor_1:          floor 1 only
    floors_3_5:       floors 3 to 5 inclusive
    floors_16_plus:   floor 16 and every floor below it

The range lives in the key, so adding or splitting a band is a YAML edit, not
a code change. At load, `validate_bands` checks that the bands start at floor 1,
leave no gaps, do not overlap, and end with an open `_plus` band, so every floor
down to the victory floor resolves to exactly one entry.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ..exceptions import ContentValidationError

_SINGLE = re.compile(r"^floor_(\d+)$")
_RANGE = re.compile(r"^floors_(\d+)_(\d+)$")
_OPEN = re.compile(r"^floors_(\d+)_plus$")

Band = Tuple[int, Optional[int]]  # (first, last); last None = open-ended


def parse_band(key: str) -> Band:
    """Floor range named by a band key: 'floor_1', 'floors_3_5' or 'floors_16_plus'."""
    m = _SINGLE.match(key)
    if m:
        n = int(m.group(1))
        return n, n
    m = _RANGE.match(key)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if lo > hi:
            raise ContentValidationError(f"Floor band '{key}' ends before it starts", band=key)
        return lo, hi
    m = _OPEN.match(key)
    if m:
        return int(m.group(1)), None
    raise ContentValidationError(
        f"'{key}' is not a floor band key (expected floor_N, floors_A_B or floors_A_plus)",
        band=key,
    )


def sorted_bands(table: Dict[str, Any], name: str) -> List[Tuple[Band, str]]:
    """Bands of `table` in floor order, validated (see module docstring)."""
    if not table:
        raise ContentValidationError(f"{name}: no floor bands", table=name)
    bands = sorted((parse_band(key), key) for key in table)
    expected = 1
    for (lo, hi), key in bands:
        if expected is None:
            raise ContentValidationError(
                f"{name}: '{key}' comes after an open-ended band", table=name, band=key
            )
        if lo != expected:
            what = "overlaps the band before it" if lo < expected else f"leaves floors {expected}-{lo - 1} uncovered"
            raise ContentValidationError(f"{name}: '{key}' {what}", table=name, band=key)
        expected = None if hi is None else hi + 1
    if expected is not None:
        raise ContentValidationError(
            f"{name}: the last band must be open-ended (floors_N_plus); floors {expected}+ are uncovered",
            table=name,
        )
    return bands


def validate_bands(table: Dict[str, Any], name: str) -> None:
    """Raise ContentValidationError unless `table` covers every floor exactly once."""
    sorted_bands(table, name)


def band_for_floor(table: Dict[str, Any], floor: int) -> Any:
    """The entry of `table` whose band contains `floor` (floors below 1 use the first band)."""
    floor = max(1, floor)
    for key in table:
        lo, hi = parse_band(key)
        if lo <= floor and (hi is None or floor <= hi):
            return table[key]
    raise ContentValidationError(f"No floor band covers floor {floor}", floor=floor)
