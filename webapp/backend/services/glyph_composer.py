# -*- coding: utf-8 -*-
"""Compose a pinyin letter from a base glyph plus a tone mark.

Pure geometry on otfcc-format glyphs (``{"advanceWidth", "contours":
[[{"x", "y", "on"}]]}``, TrueType quadratic semantics), the same format
as the entries of json/alphabet_for_pinyin.json. The mark is cut out of
an existing accented glyph (e.g. the macron of ``ē``), transformed, and
merged with the base glyph's contours (e.g. ``ê`` -> ``ê̄``).

Mark placement = automatic alignment + user adjustment:
  1. scale (and optional vertical flip, e.g. caron -> circumflex) about
     the mark's bbox center;
  2. auto offset: keep the mark where it sat relative to the source
     glyph's body, re-centered on the base horizontally and lifted by
     the difference in height between the base and the source body;
  3. user offset (dx, dy).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

Point = Dict[str, Any]
Contour = List[Point]
Glyph = Dict[str, Any]
BBox = Tuple[float, float, float, float]

# Point-wise tolerance (font units) when matching source contours to the
# plain letter's contours
_MATCH_TOLERANCE = 1.0
# Slack (font units) when testing "mark sits above the letter body"
_ABOVE_TOLERANCE = 10.0


class CompositionError(ValueError):
    """The requested composition cannot be produced."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Recipe:
    """User-adjustable part of a composition."""

    dx: float = 0.0
    dy: float = 0.0
    scale: float = 1.0
    flip_y: bool = False
    # Indices of the source glyph's contours forming the mark; None means
    # detect automatically
    mark_contours: Optional[Sequence[int]] = None


@dataclass
class Composition:
    glyph: Glyph
    mark_contours: List[int]
    auto_dx: float
    auto_dy: float
    base_contour_count: int = field(default=0)


def bbox(contours: Sequence[Contour]) -> Optional[BBox]:
    xs = [float(p["x"]) for contour in contours for p in contour]
    ys = [float(p["y"]) for contour in contours for p in contour]
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def signed_area(contour: Contour) -> float:
    """Shoelace area of the control polygon (sign = winding direction)."""
    total = 0.0
    for i, p in enumerate(contour):
        q = contour[(i + 1) % len(contour)]
        total += float(p["x"]) * float(q["y"]) - float(q["x"]) * float(p["y"])
    return total / 2.0


def _same_contour(a: Contour, b: Contour) -> bool:
    if len(a) != len(b):
        return False
    return all(
        abs(float(p["x"]) - float(q["x"])) <= _MATCH_TOLERANCE
        and abs(float(p["y"]) - float(q["y"])) <= _MATCH_TOLERANCE
        and bool(p["on"]) == bool(q["on"])
        for p, q in zip(a, b)
    )


def detect_mark_contours(source: Glyph, plain: Optional[Glyph]) -> List[int]:
    """Indices of the source glyph's contours that form its diacritic(s).

    Primary rule: contours not found (point-for-point) in the plain
    letter. Fallback when the body was redrawn: contours lying entirely
    above the plain letter's top (or, without a plain letter, above the
    lowest contour).
    """
    contours: List[Contour] = list(source.get("contours", []))
    if not contours:
        return []

    if plain is not None and plain.get("contours"):
        plain_contours = plain["contours"]
        unmatched = [
            i
            for i, contour in enumerate(contours)
            if not any(_same_contour(contour, other) for other in plain_contours)
        ]
        if 0 < len(unmatched) < len(contours):
            return unmatched
        top = max(float(p["y"]) for contour in plain_contours for p in contour)
    else:
        lowest = min(contours, key=lambda c: min(float(p["y"]) for p in c))
        top = max(float(p["y"]) for p in lowest)

    above = [
        i
        for i, contour in enumerate(contours)
        if contour and min(float(p["y"]) for p in contour) >= top - _ABOVE_TOLERANCE
    ]
    return above if len(above) < len(contours) else []


def _start_on_curve(contour: Contour) -> Contour:
    for i, point in enumerate(contour):
        if point["on"]:
            return contour[i:] + contour[:i]
    return contour


def _transform_mark(
    mark: Sequence[Contour], recipe: Recipe, offset_x: float, offset_y: float
) -> List[Contour]:
    box = bbox(mark) or (0.0, 0.0, 0.0, 0.0)
    cx = (box[0] + box[2]) / 2.0
    cy = (box[1] + box[3]) / 2.0
    sx = recipe.scale
    sy = -recipe.scale if recipe.flip_y else recipe.scale

    result: List[Contour] = []
    for contour in mark:
        points = [
            {
                "x": int(round(cx + (float(p["x"]) - cx) * sx + offset_x)),
                "y": int(round(cy + (float(p["y"]) - cy) * sy + offset_y)),
                "on": bool(p["on"]),
            }
            for p in contour
        ]
        if recipe.flip_y:
            # Mirroring flips the winding; reverse to keep the direction
            points = _start_on_curve(list(reversed(points)))
        result.append(points)
    return result


def _mark_indices(
    source: Glyph, plain: Optional[Glyph], mark_contours: Optional[Sequence[int]]
) -> List[int]:
    """Validated explicit mark contour indices, else the detected ones."""
    count = len(source.get("contours", []))
    if mark_contours is not None:
        indices = sorted(set(int(i) for i in mark_contours))
        if not indices or any(i < 0 or i >= count for i in indices):
            raise CompositionError(
                "invalid_mark_contours",
                f"Mark contour indices out of range (0..{count - 1})",
            )
    else:
        indices = detect_mark_contours(source, plain)
    if not indices:
        raise CompositionError(
            "mark_not_found", "Could not find a tone mark in the source glyph"
        )
    return indices


def compose(
    base: Glyph,
    mark_source: Glyph,
    plain_of_source: Optional[Glyph],
    recipe: Optional[Recipe] = None,
) -> Composition:
    """Merge the base glyph with the (transformed) mark of mark_source."""
    recipe = recipe or Recipe()
    if recipe.scale <= 0:
        raise CompositionError("invalid_scale", "Scale must be positive")

    source_contours: List[Contour] = list(mark_source.get("contours", []))
    indices = _mark_indices(mark_source, plain_of_source, recipe.mark_contours)

    mark = [source_contours[i] for i in indices]
    body = [c for i, c in enumerate(source_contours) if i not in indices]
    base_contours: List[Contour] = [
        [dict(p) for p in contour] for contour in base.get("contours", [])
    ]

    base_box = bbox(base_contours)
    body_box = bbox(body)
    auto_dx = 0.0
    auto_dy = 0.0
    if base_box is not None and body_box is not None:
        auto_dx = (base_box[0] + base_box[2]) / 2.0 - (body_box[0] + body_box[2]) / 2.0
        auto_dy = base_box[3] - body_box[3]

    transformed = _transform_mark(
        mark, recipe, auto_dx + recipe.dx, auto_dy + recipe.dy
    )
    glyph: Glyph = {
        "advanceWidth": base.get("advanceWidth", mark_source.get("advanceWidth", 0)),
        "contours": base_contours + transformed,
    }
    return Composition(
        glyph=glyph,
        mark_contours=indices,
        auto_dx=auto_dx,
        auto_dy=auto_dy,
        base_contour_count=len(base_contours),
    )


def strip_mark(
    source: Glyph,
    plain: Optional[Glyph],
    mark_contours: Optional[Sequence[int]] = None,
) -> Glyph:
    """The source glyph without its tone mark (e.g. ``à`` -> its ``a`` body).

    Useful when the accented glyphs are drawn differently from the plain
    letter (e.g. single-story à vs double-story a) and the plain letter
    should match them. The mark is detected like in compose() unless
    ``mark_contours`` gives its contour indices.
    """
    contours: List[Contour] = list(source.get("contours", []))
    indices = _mark_indices(source, plain, mark_contours)
    return {
        "advanceWidth": source.get("advanceWidth", 0),
        "contours": [
            [dict(p) for p in contour]
            for i, contour in enumerate(contours)
            if i not in indices
        ],
    }


def _fmt(value: float) -> str:
    return f"{value:g}"


def _contour_path(contour: Contour) -> str:
    if not contour:
        return ""
    points = [(float(p["x"]), float(p["y"]), bool(p["on"])) for p in contour]
    if not any(on for _, _, on in points):
        # All off-curve: start from the implied point between last and first
        (x0, y0, _), (x1, y1, _) = points[-1], points[0]
        points = [((x0 + x1) / 2.0, (y0 + y1) / 2.0, True)] + points
    else:
        first_on = next(i for i, (_, _, on) in enumerate(points) if on)
        points = points[first_on:] + points[:first_on]

    count = len(points)
    parts = [f"M{_fmt(points[0][0])} {_fmt(points[0][1])}"]
    i = 1
    while i < count:
        x, y, on = points[i]
        if on:
            parts.append(f"L{_fmt(x)} {_fmt(y)}")
            i += 1
            continue
        nx, ny, next_on = points[(i + 1) % count]
        if next_on:
            parts.append(f"Q{_fmt(x)} {_fmt(y)} {_fmt(nx)} {_fmt(ny)}")
            i += 2
        else:
            mx, my = (x + nx) / 2.0, (y + ny) / 2.0
            parts.append(f"Q{_fmt(x)} {_fmt(y)} {_fmt(mx)} {_fmt(my)}")
            i += 1
    parts.append("Z")
    return "".join(parts)


def contours_to_svg_path(contours: Sequence[Contour]) -> str:
    """SVG path data (font coordinates, Y-up) for quadratic contours."""
    return "".join(_contour_path(contour) for contour in contours)
