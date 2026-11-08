"""Tests for flakyscan.aggregator."""

from flakyscan.aggregator import aggregate, TestStats


def _make_runs(data: dict[str, list[tuple[str, bool]]]) -> dict:
    return data


def test_flaky_test_detected():
    runs = {
        "run1": [("tests.a.test_x", True), ("tests.a.test_y", True)],
        "run2": [("tests.a.test_x", False), ("tests.a.test_y", True)],
    }
    stats = aggregate(runs)
    names = [s.name for s in stats]
    assert "tests.a.test_x" in names
    # test_y always passes — not flaky
    assert "tests.a.test_y" not in names


def test_pass_fail_counts():
    runs = {
        "r1": [("t", True)],
        "r2": [("t", False)],
        "r3": [("t", True)],
    }
    stats = aggregate(runs)
    assert len(stats) == 1
    assert stats[0].passes == 2
    assert stats[0].failures == 1
    assert stats[0].total == 3


def test_flake_rate_value():
    runs = {
        "r1": [("t", True)],
        "r2": [("t", False)],
    }
    stats = aggregate(runs)
    # minority = 1, total = 2 -> 0.5
    assert stats[0].flake_rate == 0.5


def test_sorted_by_flake_rate_descending():
    runs = {
        "r1": [("a", True), ("b", True)],
        "r2": [("a", False), ("b", True)],
        "r3": [("a", True), ("b", False)],
        "r4": [("a", False), ("b", True)],
    }
    # a: 2 passes, 2 failures -> rate 0.5
    # b: 3 passes, 1 failure  -> rate 0.25
    stats = aggregate(runs)
    assert stats[0].name == "a"
    assert stats[1].name == "b"


def test_min_runs_filters():
    runs = {
        "r1": [("rare", True)],
        "r2": [("rare", False)],
        "r3": [("common", True)],
        "r4": [("common", False)],
        "r5": [("common", True)],
    }
    # rare seen 2 times, common 3 times
    stats = aggregate(runs, min_runs=3)
    names = [s.name for s in stats]
    assert "rare" not in names
    assert "common" in names


def test_empty_runs():
    stats = aggregate({})
    assert stats == []


def test_all_passing_not_flaky():
    runs = {"r1": [("t", True)], "r2": [("t", True)]}
    stats = aggregate(runs)
    assert stats == []
