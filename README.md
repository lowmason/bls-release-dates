# bls-release-dates

Scrapes BLS news release archive pages for CES, SAE, and QCEW; downloads release HTMLs and extracts release dates into a parquet dataset.

## Usage

```bash
uv run python -m bls_revision_dates
```

Output: `data/releases/{ces,sae,qcew}/*.htm` and `data/release_dates.parquet`.

### Vintage dates (revisions)

From `release_dates.parquet`, build a vintage_dates dataset that adds a `revision` column:

```bash
uv run python -m bls_revision_dates.vintage_dates
```

Output: `data/vintage_dates.parquet`.

- **CES**: revisions 0, 1, 2, and 9 (benchmark for March ref_dates only).
- **SAE**: revisions 0, 1, and 9 (benchmark twice for April–September: first at March Y+1, second at March Y+2).
- **QCEW**: by quarter of ref_date — Q1: 0,1,2,3,4; Q2: 0,1,2,3; Q3: 0,1,2; Q4: 0,1.

**benchmark_revision**: 0 = not a benchmark row; 1 = first benchmark; 2 = second benchmark (SAE re-replacement only).

(For recent ref_dates, not all revisions may exist yet.) See `docs/ces.md`, `docs/sae.md`, `docs/qcew.md`.

## Using in other projects

Install without publishing to PyPI:

- **Path (sibling repo or same machine):** From the other project root, run `uv add ../bls-release-dates`. Or in that project’s `pyproject.toml`: `"bls_revision_dates @ file:///path/to/bls-release-dates"`.
- **Git:** `"bls_revision_dates @ git+https://github.com/lowmason/bls-release-dates.git@v0.1.0"` (pin to a tag for reproducible installs).
- **Wheel:** In this repo run `uv build`, then in the other project: `uv add /path/to/bls-release-dates/dist/bls_revision_dates-0.1.0-py3-none-any.whl`.
