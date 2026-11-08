"""Tests for flakyscan.parser."""

from datetime import date
from pathlib import Path

import pytest

from flakyscan.parser import ParseError, parse_file, parse_folder

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_valid_run1():
    results, _run_date = parse_file(FIXTURES / "run1.xml")
    names = [name for name, _ in results]
    assert "tests.module_a.test_alpha" in names
    assert "tests.module_a.test_beta" in names


def test_run1_pass_fail_counts():
    results, _run_date = parse_file(FIXTURES / "run1.xml")
    by_name = dict(results)
    assert by_name["tests.module_a.test_alpha"] is True   # passed
    assert by_name["tests.module_a.test_beta"] is False   # failed


def test_run2_different_failures():
    results, _run_date = parse_file(FIXTURES / "run2.xml")
    by_name = dict(results)
    assert by_name["tests.module_a.test_beta"] is True    # passed this run
    assert by_name["tests.module_b.test_gamma"] is False  # failed this run


def test_parse_broken_raises():
    with pytest.raises(ParseError):
        parse_file(FIXTURES / "broken.xml")


def test_parse_folder_skips_broken(capsys):
    """parse_folder should warn but not crash on broken XML."""
    runs = parse_folder(FIXTURES)
    captured = capsys.readouterr()
    # broken.xml should be skipped (not in results) with a warning
    assert "broken.xml" not in runs
    assert "Warning" in captured.err


def test_parse_folder_returns_expected_runs():
    runs = parse_folder(FIXTURES)
    # All valid XML files in the fixtures folder should parse successfully.
    expected = {
        "run1.xml",
        "run2.xml",
        "run_with_skipped.xml",
        "run_since_old.xml",
        "run_since_new.xml",
    }
    assert set(runs.keys()) == expected


def test_parse_folder_timestamp():
    """run_since_old.xml has timestamp 2020-01-01; run_since_new.xml has 2099-01-01."""
    runs = parse_folder(FIXTURES)
    _, old_date = runs["run_since_old.xml"]
    _, new_date = runs["run_since_new.xml"]
    assert old_date == date(2020, 1, 1)
    assert new_date == date(2099, 1, 1)


def test_skipped_not_counted_as_pass():
    """<skipped/> runs must be excluded, not recorded as passes."""
    results, _run_date = parse_file(FIXTURES / "run_with_skipped.xml")
    by_name = dict(results)
    # test_alpha and test_gamma are present and passed
    assert by_name["tests.module_a.test_alpha"] is True
    assert by_name["tests.module_a.test_gamma"] is True
    # test_beta was skipped -- must not appear at all
    assert "tests.module_a.test_beta" not in by_name


def test_parse_empty_folder():
    runs = parse_folder(FIXTURES / "empty")
    assert runs == {}
