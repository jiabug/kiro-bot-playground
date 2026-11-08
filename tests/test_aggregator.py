"""Tests for flakyscan.aggregator."""

from flakyscan.aggregator import aggregate


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

# --- since filter tests ---

from datetime import date
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_since_excludes_old_run():
    """Only run_since_new.xml (2099) is included; run_since_old.xml (2020) is skipped."""
    from flakyscan.parser import parse_folder

    runs = parse_folder(FIXTURES / "..")  # parse only the two since-fixtures via direct call
    # Build a minimal runs dict with just the two since-fixtures.
    from flakyscan.parser import parse_file

    old_results, old_date = parse_file(FIXTURES / "run_since_old.xml")
    new_results, new_date = parse_file(FIXTURES / "run_since_new.xml")

    runs = {
        "run_since_old.xml": (old_results, old_date),
        "run_since_new.xml": (new_results, new_date),
    }
    stats = aggregate(runs, since=date(2050, 1, 1))
    # Only new file included: tests.since.test_alpha failed, tests.since.test_beta passed.
    # Both appear only once -> not flaky (need both pass and fail across runs).
    # So no flaky tests from one run -> stats empty.
    assert stats == []

    # Without since, both runs are included -> test_alpha: pass+fail, test_beta: fail+pass -> flaky.
    stats_all = aggregate(runs, since=None)
    names = {s.name for s in stats_all}
    assert "tests.since.test_alpha" in names
    assert "tests.since.test_beta" in names


def test_since_none_includes_both():
    """With since=None both old and new runs are included."""
    from flakyscan.parser import parse_file

    old_results, old_date = parse_file(FIXTURES / "run_since_old.xml")
    new_results, new_date = parse_file(FIXTURES / "run_since_new.xml")

    runs = {
        "run_since_old.xml": (old_results, old_date),
        "run_since_new.xml": (new_results, new_date),
    }
    stats = aggregate(runs, since=None)
    names = {s.name for s in stats}
    assert "tests.since.test_alpha" in names
    assert "tests.since.test_beta" in names


def test_since_no_timestamp_always_included():
    """A run with no timestamp is never filtered out."""
    runs: dict = {
        "no_ts": ([("t.x", True), ("t.x", False)], None),
    }
    # Even with a far-future cutoff, no-timestamp run is included.
    stats = aggregate(runs, since=date(9999, 1, 1))
    assert len(stats) == 1
    assert stats[0].name == "t.x"
