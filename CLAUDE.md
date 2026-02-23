# CLAUDE.md

## Project Overview

BLS Release Dates is a Python package that scrapes U.S. Bureau of Labor Statistics (BLS) news releases to extract publication and reference dates for three economic indicators:

- **CES** (Current Employment Statistics) — monthly
- **SAE** (State and Area Employment) — monthly
- **QCEW** (Quarterly Census of Employment and Wages) — quarterly

The scraped data supports Bayesian Non-Farm Payroll (NFP) nowcasting. Output is stored as Parquet files consumed by downstream projects.

Homepage: https://lowmason.github.io/bls-release-dates/

## Repository Structure

```
src/bls_release_dates/
├── __init__.py          # Package exports
├── config.py            # Paths, URLs, Publication dataclass, PUBLICATIONS list
├── scraper.py           # Async HTTP fetching and BLS archive index parsing
├── parser.py            # HTML parsing to extract vintage/ref dates from releases
├── read.py              # Polars DataFrame readers for parquet output
└── vintage_dates.py     # Revision/benchmark expansion logic per publication

data/
├── releases/{ces,sae,qcew}/  # Downloaded BLS HTML files (*.htm)
├── release_dates.parquet      # Columns: publication, ref_date, vintage_date
└── vintage_dates.parquet      # Columns: + revision, benchmark_revision

docs/                    # MkDocs source (index.md, api.md)
.github/workflows/       # CI: docs.yml builds and deploys MkDocs to GitHub Pages
```

## Tech Stack

- **Python** >=3.10 (uses modern union type syntax `X | None`)
- **Package manager:** [uv](https://docs.astral.sh/uv/) (lockfile: `uv.lock`)
- **Build backend:** Hatchling
- **Key dependencies:**
  - `httpx[http2]` — async HTTP client for scraping
  - `polars` — DataFrame/Parquet I/O (not pandas)
  - `beautifulsoup4` + `lxml` — HTML parsing
- **Docs:** MkDocs + Material theme + mkdocstrings (Google-style docstrings)

## Common Commands

```bash
# Install dependencies
uv sync

# Download releases and build release_dates.parquet
uv run python -m bls_release_dates

# Build vintage_dates.parquet (revisions/benchmarks)
uv run python -m bls_release_dates.vintage_dates

# Install with docs dependencies
uv sync --extra docs

# Serve docs locally at http://127.0.0.1:8000
uv run mkdocs serve

# Build static docs
uv run mkdocs build --strict
```

There is no test suite or linter configured in this project.

## Architecture and Key Concepts

### Pipeline Flow

1. **Scrape** (`scraper.py`): Fetch BLS archive index pages, parse links to individual release HTML files, download them with concurrency control (async + semaphore).
2. **Parse** (`parser.py`): Extract the embargo/publication date (`vintage_date`) and reference period (`ref_date`) from each downloaded HTML file.
3. **Output** (`release_dates.parquet`): One row per release with `publication`, `ref_date`, `vintage_date`.
4. **Expand** (`vintage_dates.py`): Apply publication-specific revision and benchmark logic to produce `vintage_dates.parquet`.

### Revision Logic (vintage_dates.py)

Each publication has distinct revision patterns:

- **CES**: Revisions 0, 1, 2; benchmark revision 9 for March ref_dates only
- **SAE**: Revisions 0, 1; benchmark revision 9 twice (April–September ref_dates get first benchmark at March Y+1, second at March Y+2)
- **QCEW**: Variable by quarter — Q1: 0–4, Q2: 0–3, Q3: 0–2, Q4: 0–1

`revision=9` always indicates a benchmark. `benchmark_revision` distinguishes first (1) vs second (2, SAE only) benchmarks.

### Configuration (config.py)

- `Publication` is a frozen dataclass with `name`, `series`, `index_url`, `frequency`
- `PUBLICATIONS` list defines all three publications
- `START_YEAR = 2010` — scraping begins from this year
- Paths are relative to repo root: `data/releases/`, `data/release_dates.parquet`, etc.

### Data Conventions

- `ref_date` is always the 12th of the reference month (arbitrary day choice for consistency)
- HTML files follow the naming pattern: `{publication}_{yyyy}_{mm}.htm`
- Parquet files use Polars for reading/writing (not pandas)

## Code Conventions

- **Type hints** on all public functions and most internal ones
- **Google-style docstrings** (required for mkdocstrings API generation)
- **Naming:** PascalCase for classes, snake_case for functions, UPPER_CASE for module-level constants
- **Private helpers** prefixed with underscore (`_find_next_ul`, `_add_ces_revisions`)
- **Async/await** for network operations in scraper.py
- **Polars** for all DataFrame operations — do not use pandas
- **Pre-compiled regex** constants at module level for performance
- **Logging** module for warnings (not print statements)

## CI/CD

The only CI workflow is `.github/workflows/docs.yml`:
- Triggers on push to `main` or manual dispatch
- Builds MkDocs with `--strict` flag and deploys to GitHub Pages
- Uses Python 3.12, uv for dependency management

## Known Gaps

- `__init__.py` imports from `.__main__` (`main`, `build_dataframe`, `download_all_publications`) but the `__main__.py` module is referenced in `pyproject.toml` as the CLI entry point and has not yet been implemented
- No test suite exists
- No linter/formatter configuration (no ruff, black, mypy, etc.)
