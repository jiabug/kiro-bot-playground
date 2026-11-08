"""Tests for flakyscan.parser."""

import pytest
from pathlib import Path

from flakyscan.parser import parse_file, parse_folder, ParseError

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_valid_run1():
    results = parse_file(FIXTURES / "run1.xml")
    names = [name for name, _ in results]
    assert "tests.module_a.test_alpha" in names
    assert "tests.module_a.test_beta" in names


def test_run1_pass_fail_counts():
    results = parse_file(FIXTURES / "run1.xml")
    by_name = dict(results)
    assert by_name["tests.module_a.test_alpha"] is True   # passed
    assert by_name["tests.module_a.test_beta"] is False   # failed


def test_run2_different_failures():
    results = parse_file(FIXTURES / "run2.xml")
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


def test_parse_folder_returns_two_runs():
    runs = parse_folder(FIXTURES)
    # Only run1.xml and run2.xml should parse successfully
    assert set(runs.keys()) == {"run1.xml", "run2.xml"}


def test_parse_empty_folder():
    runs = parse_folder(FIXTURES / "empty")
    assert runs == {}
