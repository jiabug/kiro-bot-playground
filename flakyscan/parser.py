"""Parse JUnit XML report files into (test_name, passed) records."""

# xml.etree.ElementTree does not fetch external entities (safe by default).
# shortcut: does not guard against internal entity expansion (billion laughs);
# replace with defusedxml if parsing untrusted CI artifacts.

import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


class ParseError(Exception):
    """Raised when a JUnit XML file cannot be parsed."""


def _parse_timestamp(value: str) -> date | None:
    """Parse an ISO-8601 timestamp string to a date, or None on failure."""
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, IndexError):
        return None


def parse_file(path: Path) -> tuple[list[tuple[str, bool]], date | None]:
    """
    Parse one JUnit XML file.

    Returns a tuple of:
      - list of (classname.testname, passed) tuples
      - the date from the first <testsuite> timestamp attribute, or None
    Raises ParseError on malformed XML.
    """
    try:
        # xml.etree.ElementTree does not fetch external entities (safe by default).
        # shortcut: does not guard against internal entity expansion (billion laughs);
        # replace with defusedxml if parsing untrusted CI artifacts.
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ParseError(f"Malformed XML in {path}: {exc}") from exc

    root = tree.getroot()
    # Support both <testsuites><testsuite>... and bare <testsuite>...
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    elif root.tag == "testsuite":
        suites = [root]
    else:
        raise ParseError(f"Unexpected root element <{root.tag}> in {path}")

    # Read timestamp from the first suite that has one.
    run_date: date | None = None
    for suite in suites:
        ts_attr = suite.get("timestamp")
        if ts_attr is not None:
            run_date = _parse_timestamp(ts_attr)
            break

    results: list[tuple[str, bool]] = []
    for suite in suites:
        for case in suite.findall("testcase"):
            classname = case.get("classname", "")
            name = case.get("name", "")
            # Use (no-class) prefix when classname is absent to prevent collisions
            # across different suites that share bare test names.
            full_name = f"{classname}.{name}" if classname else f"(no-class).{name}"
            # A testcase is failed/errored when it contains <failure> or <error>.
            # A <skipped/> child means the test did not run; exclude it entirely.
            if case.find("skipped") is not None:
                continue
            failed = case.find("failure") is not None or case.find("error") is not None
            results.append((full_name, not failed))

    return results, run_date


def parse_folder(folder: Path) -> dict[str, tuple[list[tuple[str, bool]], date | None]]:
    """
    Walk *folder* for *.xml files and parse each one.

    Returns {filename: ([(test_name, passed), ...], run_date)}.
    Files that fail to parse are skipped with a printed warning.
    """
    xml_files = sorted(folder.rglob("*.xml"))
    runs: dict[str, tuple[list[tuple[str, bool]], date | None]] = {}
    for xml_path in xml_files:
        try:
            runs[str(xml_path.relative_to(folder))] = parse_file(xml_path)
        except ParseError as exc:
            # Warn but continue; don't crash the whole run.
            print(f"Warning: {exc}", file=sys.stderr)
    return runs
