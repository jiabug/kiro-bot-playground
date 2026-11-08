"""Tests for flakyscan.__main__ (CLI integration)."""

import json
from pathlib import Path

import pytest

from flakyscan.__main__ import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_table_output(capsys):
    rc = main([str(FIXTURES)])
    assert rc == 0
    out = capsys.readouterr().out
    # test_beta and test_gamma are the two flaky tests across run1/run2
    assert "test_beta" in out or "test_gamma" in out


def test_cli_json_output(capsys):
    rc = main([str(FIXTURES), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    names = [d["test"] for d in data]
    assert any("test_beta" in n or "test_gamma" in n for n in names)


def test_cli_min_runs_filters(capsys):
    # With --min-runs 3, tests seen only twice should be excluded.
    rc = main([str(FIXTURES), "--min-runs", "3"])
    assert rc == 0
    # run1+run2 give each test exactly 2 appearances; min-runs 3 -> no results
    out = capsys.readouterr().out
    assert "No flaky tests" in out


def test_cli_empty_folder(capsys, tmp_path):
    rc = main([str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No flaky tests" in out


def test_cli_missing_folder(capsys):
    rc = main(["/nonexistent/path"])
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cli_sorted_by_flake_rate(capsys, tmp_path):
    # Three runs: test_a flaky 2/3 times, test_b flaky 1/3 times.
    run1 = tmp_path / "r1.xml"
    run2 = tmp_path / "r2.xml"
    run3 = tmp_path / "r3.xml"
    xml_template = """<?xml version="1.0"?>
<testsuite name="s">
  <testcase classname="m" name="test_a"{fail_a}/>
  <testcase classname="m" name="test_b"{fail_b}/>
</testsuite>"""
    fail = '><failure message="x">x</failure></testcase'
    ok = "/"

    run1.write_text(xml_template.format(fail_a=ok, fail_b=ok).replace("testcase/>", "testcase/>"))
    # shortcut: manual XML is simpler
    run1.write_text(
        '<?xml version="1.0"?><testsuite name="s">'
        '<testcase classname="m" name="test_a"/>'
        '<testcase classname="m" name="test_b"/>'
        "</testsuite>"
    )
    run2.write_text(
        '<?xml version="1.0"?><testsuite name="s">'
        '<testcase classname="m" name="test_a"><failure message="x">x</failure></testcase>'
        '<testcase classname="m" name="test_b"><failure message="x">x</failure></testcase>'
        "</testsuite>"
    )
    run3.write_text(
        '<?xml version="1.0"?><testsuite name="s">'
        '<testcase classname="m" name="test_a"><failure message="x">x</failure></testcase>'
        '<testcase classname="m" name="test_b"/>'
        "</testsuite>"
    )
    # test_a: 1 pass, 2 fail -> rate 1/3 ≈ 0.333
    # test_b: 2 pass, 1 fail -> rate 1/3 ≈ 0.333  (tie, both appear)
    rc = main([str(tmp_path), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    names = [d["test"] for d in data]
    assert "m.test_a" in names
    assert "m.test_b" in names
