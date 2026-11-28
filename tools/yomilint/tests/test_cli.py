import json

from fontmaker import FontPlan
from yomilint.cli import main


def test_a_good_font_exits_zero(project, capsys):
    built = project()
    assert main(["check", str(built.font), "--spec", str(built.spec)]) == 0
    assert "0 errors" in capsys.readouterr().out


def test_an_error_exits_one_and_is_named(project, capsys):
    built = project(plan=FontPlan(with_rclt=False))
    assert main(["check", str(built.font), "--spec", str(built.spec)]) == 1
    out = capsys.readouterr().out
    assert "context/phrase" in out and "着手" in out


def test_json_output_lists_the_findings(project, capsys):
    built = project(plan=FontPlan(with_rclt=False))
    main(["check", str(built.font), "--spec", str(built.spec), "--format", "json"])
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["errors"] == 1
    finding = report["findings"][0]
    assert finding["check"] == "context/phrase"
    assert finding["severity"] == "ERROR"
    assert finding["subject"] == "着手"


def test_select_runs_only_the_named_checks(project, capsys):
    built = project(plan=FontPlan(with_rclt=False, with_aalt=False))
    code = main(
        ["check", str(built.font), "--spec", str(built.spec), "--select", "select/"]
    )
    out = capsys.readouterr().out
    assert code == 1 and "context/phrase" not in out


def test_a_spec_that_cannot_be_used_exits_two(project, capsys):
    built = project()
    text = built.spec.read_text(encoding="utf-8")
    built.spec.write_text(text.replace('"pinyin"', '"klingon"'), encoding="utf-8")
    assert main(["check", str(built.font), "--spec", str(built.spec)]) == 2
    assert "klingon" in capsys.readouterr().err


# ---- known findings ------------------------------------------------------


def _check(built, *extra):
    return main(["check", str(built.font), "--spec", str(built.spec), *extra])


def test_known_findings_do_not_fail_the_run(project, tmp_path, capsys):
    built = project(plan=FontPlan(with_rclt=False))
    known = tmp_path / "known.json"
    assert main(
        ["baseline", str(built.font), "--spec", str(built.spec), "-o", str(known)]
    ) == 0
    capsys.readouterr()
    assert _check(built, "--baseline", str(known)) == 0
    out = capsys.readouterr().out
    assert "1 known" in out and "0 errors" in out


def test_a_new_finding_fails_beside_the_known_ones(project, tmp_path, capsys):
    built = project(plan=FontPlan(with_rclt=False))
    known = tmp_path / "known.json"
    main(["baseline", str(built.font), "--spec", str(built.spec), "-o", str(known)])
    # The same font, now without alternates as well.
    project(plan=FontPlan(with_rclt=False, with_aalt=False))
    capsys.readouterr()
    assert _check(built, "--baseline", str(known)) == 1
    out = capsys.readouterr().out
    assert "select/aalt-covers-readings" in out and "1 known" in out


def test_a_known_finding_that_is_gone_is_pointed_out(project, tmp_path, capsys):
    built = project(plan=FontPlan(with_rclt=False))
    known = tmp_path / "known.json"
    main(["baseline", str(built.font), "--spec", str(built.spec), "-o", str(known)])
    project()  # the font is fixed
    capsys.readouterr()
    assert _check(built, "--baseline", str(known)) == 0
    assert "no longer found" in capsys.readouterr().out
