# flakyscan

Detect flaky tests from a folder of JUnit XML reports.

A test is **flaky** if it passed in some CI runs and failed in others.
`flakyscan` reads all `*.xml` files in a folder, aggregates pass/fail counts per test, and prints the ones that flipped.

## Install

No third-party dependencies — standard library only.

```bash
# Run directly from the repo
python -m flakyscan <folder> [options]

# Or install as a CLI tool
pip install .
flakyscan <folder> [options]
```

Requires Python 3.11+.

## Usage

```
usage: flakyscan [-h] [--min-runs N] [--format {table,json}] folder

positional arguments:
  folder                Folder containing JUnit XML files from multiple CI runs.

options:
  --min-runs N          Skip tests seen fewer than N times total (default: 1).
  --format {table,json} Output format: table (default) or json.
```

### Example

Given two XML reports in `reports/`:

```bash
python -m flakyscan reports/
```

Sample output:

```
Test                          Passes  Failures  Total  Flake Rate
-----------------------------  ------  --------  -----  ----------
tests.module_a.test_beta       1       1         2      50.0%
tests.module_b.test_gamma      1       1         2      50.0%
```

With JSON output:

```bash
python -m flakyscan reports/ --format json
```

```json
[
  {
    "test": "tests.module_a.test_beta",
    "passes": 1,
    "failures": 1,
    "total": 2,
    "flake_rate": 0.5
  }
]
```

Filtering by minimum run count:

```bash
python -m flakyscan reports/ --min-runs 5
```

Only tests seen at least 5 times are considered.

## How it works

1. **Parse** — reads each `*.xml` with `xml.etree.ElementTree`; supports `<testsuites>` and bare `<testsuite>` roots.
2. **Aggregate** — counts passes and failures per test name across all files.
3. **Detect** — a test is flaky when it has at least one pass and one failure.
4. **Sort** — results are sorted by flake rate (minority runs / total runs) descending.

Malformed XML files produce a warning on stderr and are skipped; the rest of the folder is still processed.

## Running tests

```bash
pip install pytest
pytest
```

### Coverage

```bash
pip install pytest-cov
pytest --cov --cov-report=term-missing
```

CI fails if line coverage drops below 80% (`fail_under` in `pyproject.toml`).
