"""The thresholds of the geometry checks come from the spec, with defaults."""

from yomilint.spec import load_spec


def test_geometry_thresholds_have_defaults(tmp_path):
    path = tmp_path / "yomilint.toml"
    path.write_text('[font]\nprofile = "pinyin"\n', encoding="utf-8")
    spec = load_spec(path)
    assert (spec.min_gap, spec.center_tolerance) == (0, 20)
    assert (spec.baseline_tolerance, spec.min_scale) == (1, 0.6)


def test_geometry_thresholds_are_read(tmp_path):
    path = tmp_path / "yomilint.toml"
    path.write_text(
        "[geometry]\ncenter_tolerance = 5\nbaseline_tolerance = 0\n"
        "min_scale = 0.8\n",
        encoding="utf-8",
    )
    spec = load_spec(path)
    assert (spec.center_tolerance, spec.baseline_tolerance) == (5, 0)
    assert spec.min_scale == 0.8
