"""Tests for flakyscan.formatter."""

import json

from flakyscan.aggregator import TestStats
from flakyscan.formatter import format_json, format_table, render


def _stat(name: str, passes: int, failures: int) -> TestStats:
    return TestStats(name=name, passes=passes, failures=failures)


def test_table_has_headers():
    stats = [_stat("a.b.test_x", 2, 1)]
    out = format_table(stats)
    assert "Test" in out
    assert "Passes" in out
    assert "Failures" in out
    assert "Flake Rate" in out


def test_table_contains_test_name():
    stats = [_stat("a.b.test_x", 2, 1)]
    out = format_table(stats)
    assert "a.b.test_x" in out


def test_table_sorted_descending():
    # Caller must already sort; formatter preserves order.
    stats = [_stat("high", 1, 1), _stat("low", 3, 1)]
    out = format_table(stats)
    assert out.index("high") < out.index("low")


def test_table_empty():
    out = format_table([])
    assert "No flaky tests" in out


def test_json_valid():
    stats = [_stat("x.y.test_z", 3, 2)]
    out = format_json(stats)
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["test"] == "x.y.test_z"
    assert data[0]["passes"] == 3
    assert data[0]["failures"] == 2
    assert data[0]["total"] == 5
    assert isinstance(data[0]["flake_rate"], float)


def test_json_empty():
    out = format_json([])
    assert json.loads(out) == []


def test_render_dispatches_table():
    stats = [_stat("t", 1, 1)]
    assert "Test" in render(stats, fmt="table")


def test_render_dispatches_json():
    stats = [_stat("t", 1, 1)]
    parsed = json.loads(render(stats, fmt="json"))
    assert parsed[0]["test"] == "t"
