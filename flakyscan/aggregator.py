"""Aggregate per-run pass/fail data and identify flaky tests."""

from dataclasses import dataclass
from datetime import date


@dataclass
class TestStats:
    name: str
    passes: int
    failures: int

    @property
    def total(self) -> int:
        return self.passes + self.failures

    @property
    def flake_rate(self) -> float:
        """Fraction of runs that went the minority way (0-0.5)."""
        if self.total == 0:
            return 0.0
        minority = min(self.passes, self.failures)
        return minority / self.total

    @property
    def is_flaky(self) -> bool:
        return self.passes > 0 and self.failures > 0


def aggregate(
    runs: dict[str, tuple[list[tuple[str, bool]], date | None] | list[tuple[str, bool]]],
    min_runs: int = 1,
    since: date | None = None,
) -> list[TestStats]:
    """
    Aggregate results across all runs.

    Args:
        runs: output of parser.parse_folder –
              {filename: ([(test_name, passed)], run_date)}
              Also accepts the legacy {filename: [(test_name, passed)]} shape.
        min_runs: skip tests seen fewer than this many times total
        since: if set, skip runs whose timestamp date < since.
               Runs with no timestamp are always included.

    Returns:
        List of TestStats for flaky tests only, sorted by flake_rate descending.
    """
    passes: dict[str, int] = {}
    failures: dict[str, int] = {}

    for run_value in runs.values():
        # Handle both (results, date) tuple and bare list (legacy callers).
        if isinstance(run_value, tuple):
            results, run_date = run_value
        else:
            results = run_value
            run_date = None

        # Filter by --since: skip runs older than the cutoff.
        # No timestamp -> conservative include.
        if since is not None and run_date is not None and run_date < since:
            continue

        for test_name, passed in results:
            if passed:
                passes[test_name] = passes.get(test_name, 0) + 1
            else:
                failures[test_name] = failures.get(test_name, 0) + 1

    all_tests = set(passes) | set(failures)
    stats: list[TestStats] = []
    for name in all_tests:
        p = passes.get(name, 0)
        f = failures.get(name, 0)
        ts = TestStats(name=name, passes=p, failures=f)
        if ts.total < min_runs:
            continue
        if ts.is_flaky:
            stats.append(ts)

    stats.sort(key=lambda s: s.flake_rate, reverse=True)
    return stats
