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
