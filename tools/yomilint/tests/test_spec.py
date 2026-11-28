"""The thresholds of the geometry checks come from the spec, with defaults."""

import pytest
from yomilint.spec import SpecError, load_spec


def test_geometry_thresholds_have_defaults(tmp_path):
    path = tmp_path / "yomilint.toml"
    path.write_text('[font]\nprofile = "pinyin"\n', encoding="utf-8")
    spec = load_spec(path)
    assert (spec.min_gap, spec.center_tolerance) == (0, 0.01)
    assert (spec.baseline_tolerance, spec.min_scale) == (0.001, 0.6)


def test_geometry_thresholds_are_read(tmp_path):
    path = tmp_path / "yomilint.toml"
    path.write_text(
        "[geometry]\ncenter_tolerance = 0.02\nbaseline_tolerance = 0\n"
        "min_scale = 0.8\n",
        encoding="utf-8",
    )
    spec = load_spec(path)
    assert (spec.center_tolerance, spec.baseline_tolerance) == (0.02, 0)
    assert spec.min_scale == 0.8


def _load(tmp_path, geometry):
    path = tmp_path / "yomilint.toml"
    path.write_text(f"[geometry]\n{geometry}\n", encoding="utf-8")
    return load_spec(path)


@pytest.mark.parametrize(
    "geometry",
    [
        "center_tolerance = 20",  # the old unit: font units
        "center_tolerance = 1",
        "center_tolerance = -0.1",
        'center_tolerance = "0.01"',
        "baseline_tolerance = 1",
        "baseline_tolerance = -0.001",
        "baseline_tolerance = true",
        "min_scale = 0",
        "min_scale = 1.5",
        "min_scale = -0.6",
    ],
)
def test_a_threshold_out_of_range_is_refused(tmp_path, geometry):
    with pytest.raises(SpecError):
        _load(tmp_path, geometry)


def test_thresholds_at_the_edges_are_accepted(tmp_path):
    spec = _load(
        tmp_path, "center_tolerance = 0\nbaseline_tolerance = 0\nmin_scale = 1"
    )
    assert (spec.center_tolerance, spec.baseline_tolerance, spec.min_scale) == (0, 0, 1)


def test_the_default_features_have_a_default(tmp_path):
    path = tmp_path / "yomilint.toml"
    path.write_text('[font]\nprofile = "pinyin"\n', encoding="utf-8")
    spec = load_spec(path)
    assert {"rclt", "calt", "ccmp", "liga"} <= set(spec.default_features)
    assert "aalt" not in spec.default_features and "ss01" not in spec.default_features


def test_the_default_features_are_read(tmp_path):
    path = tmp_path / "yomilint.toml"
    path.write_text('[context]\ndefault_features = ["rclt", "ss01"]\n', "utf-8")
    assert load_spec(path).default_features == ("rclt", "ss01")


@pytest.mark.parametrize(
    "value", ['"rclt"', "[1]", '["rcl"]', '["rclt", ""]', '["rclt "]']
)
def test_default_features_that_are_not_tags_are_refused(tmp_path, value):
    path = tmp_path / "yomilint.toml"
    path.write_text(f"[context]\ndefault_features = {value}\n", encoding="utf-8")
    with pytest.raises(SpecError):
        load_spec(path)
