"""Format flaky test results as a table or JSON."""

import json
from typing import Literal

from .aggregator import TestStats


def format_table(stats: list[TestStats]) -> str:
    """Aligned text table, sorted by flake_rate descending (caller's order)."""
    if not stats:
        return "No flaky tests found."

    headers = ("Test", "Passes", "Failures", "Total", "Flake Rate")
    rows = [
        (s.name, str(s.passes), str(s.failures), str(s.total), f"{s.flake_rate:.1%}")
        for s in stats
    ]

    # Column widths
    col_data = [headers] + rows
    widths = [max(len(row[i]) for row in col_data) for i in range(len(headers))]

    def fmt_row(row: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    sep = "  ".join("-" * w for w in widths)
    lines = [fmt_row(headers), sep] + [fmt_row(r) for r in rows]
    return "\n".join(lines)


def format_json(stats: list[TestStats]) -> str:
    """JSON array, one object per flaky test."""
    data = [
        {
            "test": s.name,
            "passes": s.passes,
            "failures": s.failures,
            "total": s.total,
            "flake_rate": round(s.flake_rate, 4),
        }
        for s in stats
    ]
    return json.dumps(data, indent=2)


def render(stats: list[TestStats], fmt: Literal["table", "json"] = "table") -> str:
    if fmt == "json":
        return format_json(stats)
    return format_table(stats)
