# BLS Release Dates

Homepage: https://lowmason.github.io/bls-release-dates/

This repository contains the release dates for BLS data.

## Usage

### 1. Download releases and build release_dates

```bash
uv run python -m bls_release_dates
# or, if installed: bls-release-dates
```

Writes `data/releases/{ces,sae,qcew}/*.htm` and `data/release_dates.parquet` (columns: `publication`, `ref_date`, `vintage_date`).

### 2. Build vintage_dates (revisions)

From `release_dates.parquet`, build a dataset with revision codes:

```bash
uv run python -m bls_release_dates.vintage_dates
```

Writes `data/vintage_dates.parquet` with columns: `publication`, `ref_date`, `vintage_date`, `revision`, `benchmark_revision`.

- **CES**: revisions 0, 1, 2, and 9 (benchmark for March ref_dates only).
- **SAE**: revisions 0, 1, and 9 (benchmark twice for April–September: first at March Y+1, second at March Y+2).
- **QCEW**: by quarter of ref_date — Q1: 0,1,2,3,4; Q2: 0,1,2,3; Q3: 0,1,2; Q4: 0,1.

**benchmark_revision**: 0 = not a benchmark row; 1 = first benchmark; 2 = second benchmark (SAE re-replacement only).

(For recent ref_dates, not all revisions may exist yet.)

### 3. Read the parquet data

If the parquet files have been created, read them as polars DataFrames:

```python
from bls_release_dates import read_release_dates, read_vintage_dates

# Default paths: data/release_dates.parquet, data/vintage_dates.parquet
releases = read_release_dates()   # DataFrame or None if not created yet
vintages = read_vintage_dates()   # DataFrame or None if not created yet

if releases is not None:
    print(releases.head())
if vintages is not None:
    print(vintages.head())

# Custom path
releases = read_release_dates("path/to/release_dates.parquet")
```

## Using in other projects

Install without publishing to PyPI:

- **Path (sibling repo or same machine):** From the other project root, run `uv add ../bls-release-dates`. Or in that project's `pyproject.toml`: `"bls-release-dates @ file:///path/to/bls-release-dates"`.
- **Git:** `"bls-release-dates @ git+https://github.com/lowmason/bls-release-dates.git@v0.1.0"` (pin to a tag for reproducible installs).
- **Wheel:** In this repo run `uv build`, then in the other project: `uv add /path/to/bls-release-dates/dist/bls_release_dates-0.1.0-py3-none-any.whl`.

## Documentation

API docs are published at **https://lowmason.github.io/bls-release-dates/** and are built with [MkDocs](https://www.mkdocs.org/), the [Material](https://squidfunk.github.io/mkdocs-material/) theme, and [mkdocstrings](https://mkdocstrings.github.io/) (Google-style docstrings). To build and serve locally:

```bash
uv sync --extra docs
uv run mkdocs serve
```

Then open http://127.0.0.1:8000. To build static files only: `uv run mkdocs build` (output in `site/`).
