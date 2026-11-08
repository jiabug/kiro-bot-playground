"""Parse JUnit XML report files into (test_name, passed) records."""

# xml.etree.ElementTree does not fetch external entities (safe by default).
# shortcut: does not guard against internal entity expansion (billion laughs);
# replace with defusedxml if parsing untrusted CI artifacts.

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


class ParseError(Exception):
    """Raised when a JUnit XML file cannot be parsed."""


def parse_file(path: Path) -> list[tuple[str, bool]]:
    """
    Parse one JUnit XML file.

    Returns a list of (classname.testname, passed) tuples.
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

    return results


def parse_folder(folder: Path) -> dict[str, list[tuple[str, bool]]]:
    """
    Walk *folder* for *.xml files and parse each one.

    Returns {filename: [(test_name, passed), ...]}. 
    Files that fail to parse are skipped with a printed warning.
    """
    xml_files = sorted(folder.rglob("*.xml"))
    runs: dict[str, list[tuple[str, bool]]] = {}
    for xml_path in xml_files:
        try:
            runs[str(xml_path.relative_to(folder))] = parse_file(xml_path)
        except ParseError as exc:
            # Warn but continue; don't crash the whole run.
            print(f"Warning: {exc}", file=sys.stderr)
    return runs
