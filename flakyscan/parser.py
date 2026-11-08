"""Parse JUnit XML report files into (test_name, passed) records."""

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
            full_name = f"{classname}.{name}" if classname else name
            # A testcase is failed/errored when it contains <failure> or <error>
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
            runs[xml_path.name] = parse_file(xml_path)
        except ParseError as exc:
            # Warn but continue; don't crash the whole run.
            import sys
            print(f"Warning: {exc}", file=sys.stderr)
    return runs
