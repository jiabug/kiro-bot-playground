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
        "run_multisuite.xml",
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


# --- multi-suite timestamp tests ---

def test_multisuite_max_timestamp():
    """run_multisuite.xml has s1=2020-01-01 and s2=2099-06-01; max wins."""
    _, run_date = parse_file(FIXTURES / "run_multisuite.xml")
    assert run_date == date(2099, 6, 1)


def test_multisuite_included_when_max_in_window():
    """File with max-timestamp 2099-06-01 must be included for since=2050-01-01."""
    _, run_date = parse_file(FIXTURES / "run_multisuite.xml")
    assert run_date is not None
    assert run_date >= date(2050, 1, 1)


def test_multisuite_excluded_when_max_before_since():
    """File with max-timestamp 2099-06-01 must be excluded for since=2200-01-01."""
    _, run_date = parse_file(FIXTURES / "run_multisuite.xml")
    assert run_date is not None
    assert run_date < date(2200, 1, 1)


# --- malformed / empty timestamp tests ---

from flakyscan.parser import _parse_timestamp


def test_parse_timestamp_malformed_returns_none(capsys: pytest.CaptureFixture[str]) -> None:
    assert _parse_timestamp("not-a-date") is None
    assert _parse_timestamp("2024-99-01T00:00:00") is None


def test_parse_timestamp_malformed_warns(capsys: pytest.CaptureFixture[str]) -> None:
    _parse_timestamp("not-a-date")
    captured = capsys.readouterr()
    assert "Warning" in captured.err
    assert "not-a-date" in captured.err


def test_parse_timestamp_empty_string() -> None:
    assert _parse_timestamp("") is None


def test_parse_timestamp_valid() -> None:
    assert _parse_timestamp("2024-06-01T12:00:00") == date(2024, 6, 1)
