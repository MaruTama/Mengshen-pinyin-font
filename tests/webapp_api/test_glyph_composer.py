# -*- coding: utf-8 -*-
"""Geometry of composing pinyin letters from a base glyph + a tone mark."""

from __future__ import annotations

import pytest

from webapp.backend.services import glyph_composer as gc


def _rect(x0, y0, x1, y1):
    """Clockwise (TrueType outer) rectangle of on-curve points."""
    return [
        {"x": x0, "y": y0, "on": True},
        {"x": x0, "y": y1, "on": True},
        {"x": x1, "y": y1, "on": True},
        {"x": x1, "y": y0, "on": True},
    ]


# plain "e": body box 50..450 x 0..500
PLAIN_E = {"advanceWidth": 500, "contours": [_rect(50, 0, 450, 500)]}
# "ē": same body + macron bar 100..400 x 600..650
E_MACRON = {
    "advanceWidth": 500,
    "contours": [_rect(50, 0, 450, 500), _rect(100, 600, 400, 650)],
}
# "ê": taller base (circumflex already merged), top at 700
E_CIRCUMFLEX = {
    "advanceWidth": 500,
    "contours": [_rect(50, 0, 450, 500), _rect(150, 550, 350, 700)],
}
# "m": wider body 0..600, same height as e
PLAIN_M = {"advanceWidth": 600, "contours": [_rect(0, 0, 600, 500)]}


class TestBBox:
    def test_bbox(self):
        assert gc.bbox(E_MACRON["contours"]) == (50, 0, 450, 650)

    def test_bbox_empty(self):
        assert gc.bbox([]) is None


class TestDetectMark:
    def test_unmatched_contours_are_mark(self):
        assert gc.detect_mark_contours(E_MACRON, PLAIN_E) == [1]

    def test_fallback_contours_above_plain_top(self):
        # Body redrawn slightly differently: no exact match, use position
        source = {
            "advanceWidth": 500,
            "contours": [_rect(52, 0, 448, 502), _rect(100, 600, 400, 650)],
        }
        assert gc.detect_mark_contours(source, PLAIN_E) == [1]

    def test_without_plain_uses_highest_separate_contours(self):
        assert gc.detect_mark_contours(E_MACRON, None) == [1]

    def test_no_mark(self):
        assert gc.detect_mark_contours(PLAIN_E, PLAIN_E) == []


class TestCompose:
    def test_mark_lifted_onto_taller_base(self):
        result = gc.compose(E_CIRCUMFLEX, E_MACRON, PLAIN_E)
        glyph = result.glyph
        assert glyph["advanceWidth"] == 500
        assert glyph["contours"][:2] == E_CIRCUMFLEX["contours"]
        # base top 700 vs source body top 500 -> lift by 200
        assert result.auto_dy == 200
        assert result.auto_dx == 0
        assert gc.bbox([glyph["contours"][2]]) == (100, 800, 400, 850)
        assert result.mark_contours == [1]

    def test_mark_centered_on_wider_base(self):
        result = gc.compose(PLAIN_M, E_MACRON, PLAIN_E)
        # m body center 300 vs e body center 250
        assert result.auto_dx == 50
        assert gc.bbox([result.glyph["contours"][1]]) == (150, 600, 450, 650)
        assert result.glyph["advanceWidth"] == 600

    def test_user_offset_and_scale(self):
        recipe = gc.Recipe(dx=10, dy=-20, scale=0.5)
        result = gc.compose(PLAIN_E, E_MACRON, PLAIN_E, recipe)
        # scaled about mark center (250, 625): 175..325 x 612.5..637.5
        assert gc.bbox([result.glyph["contours"][1]]) == (185, 592, 335, 618)

    def test_flip_y_mirrors_and_keeps_winding(self):
        caron = [
            {"x": 100, "y": 600, "on": True},
            {"x": 250, "y": 700, "on": True},
            {"x": 400, "y": 600, "on": True},
        ]
        source = {"advanceWidth": 500, "contours": [_rect(50, 0, 450, 500), caron]}
        result = gc.compose(PLAIN_E, source, PLAIN_E, gc.Recipe(flip_y=True))
        flipped = result.glyph["contours"][1]
        assert gc.bbox([flipped]) == (100, 600, 400, 700)
        assert gc.signed_area(flipped) * gc.signed_area(caron) > 0
        assert all(p["on"] for p in flipped)
        assert flipped[0]["on"]

    def test_explicit_mark_contours_override(self):
        result = gc.compose(PLAIN_E, E_MACRON, PLAIN_E, gc.Recipe(mark_contours=[0, 1]))
        assert result.mark_contours == [0, 1]
        assert len(result.glyph["contours"]) == 3

    def test_invalid_mark_index(self):
        with pytest.raises(gc.CompositionError):
            gc.compose(PLAIN_E, E_MACRON, PLAIN_E, gc.Recipe(mark_contours=[5]))

    def test_no_mark_found(self):
        with pytest.raises(gc.CompositionError):
            gc.compose(PLAIN_E, PLAIN_E, PLAIN_E)

    def test_coordinates_are_integers(self):
        result = gc.compose(PLAIN_E, E_MACRON, PLAIN_E, gc.Recipe(scale=0.33))
        for contour in result.glyph["contours"]:
            for point in contour:
                assert isinstance(point["x"], int)
                assert isinstance(point["y"], int)


class TestSvgPath:
    def test_lines(self):
        assert gc.contours_to_svg_path([_rect(0, 0, 10, 10)]) == (
            "M0 0L0 10L10 10L10 0Z"
        )

    def test_quadratic(self):
        contour = [
            {"x": 0, "y": 0, "on": True},
            {"x": 5, "y": 10, "on": False},
            {"x": 10, "y": 0, "on": True},
        ]
        assert gc.contours_to_svg_path([contour]) == "M0 0Q5 10 10 0Z"

    def test_implied_on_point_between_offs(self):
        contour = [
            {"x": 0, "y": 0, "on": True},
            {"x": 0, "y": 10, "on": False},
            {"x": 10, "y": 10, "on": False},
            {"x": 10, "y": 0, "on": True},
        ]
        assert gc.contours_to_svg_path([contour]) == ("M0 0Q0 10 5 10Q10 10 10 0Z")

    def test_off_curve_start(self):
        contour = [
            {"x": 0, "y": 10, "on": False},
            {"x": 10, "y": 0, "on": True},
            {"x": 0, "y": 0, "on": True},
        ]
        assert gc.contours_to_svg_path([contour]) == "M10 0L0 0Q0 10 10 0Z"

    def test_all_off_curve(self):
        contour = [
            {"x": 0, "y": 0, "on": False},
            {"x": 10, "y": 0, "on": False},
            {"x": 10, "y": 10, "on": False},
            {"x": 0, "y": 10, "on": False},
        ]
        path = gc.contours_to_svg_path([contour])
        assert path.startswith("M0 5Q0 0 5 0")
        assert path.endswith("Z")
