"""Build vintage_dates dataset from release_dates.parquet with revision codes.

Revision semantics (publication-specific; may not hold for most recent ref_dates):
- 0: initial release (vintage_date from release_dates.parquet)
- 1, 2, ...: subsequent revisions (vintage_date shifted by 1, 2, ... months)
- 9: benchmark revision (CES and SAE only)

benchmark_revision: 0 = not a benchmark row; 1 = first benchmark; 2 = second benchmark (SAE re-replacement only).

CES: revisions 0, 1, 2, and 9. Benchmark 9 only for March ref_date (vintage = Jan release next year); benchmark_revision=1.
SAE: revisions 0, 1, and 9. Benchmark 9 twice for April–September ref_dates (double-revision):
     first at March Y+1 (benchmark_revision=1), second at March Y+2 (benchmark_revision=2).
QCEW: by quarter of ref_date — Q1: 0,1,2,3,4; Q2: 0,1,2,3; Q3: 0,1,2; Q4: 0,1. No benchmarks (benchmark_revision=0).
"""

from datetime import date
from pathlib import Path

import polars as pl

from .config import DATA_DIR, PARQUET_PATH

VINTAGE_DATES_PATH = DATA_DIR.parent / "vintage_dates.parquet"

# Publication-specific revision sets (monthly-style; 9 added separately for CES/SAE).
CES_MONTHLY_REVISIONS = [0, 1, 2]
SAE_MONTHLY_REVISIONS = [0, 1]
# QCEW max revision by quarter (ref_date month): Q1=4, Q2=3, Q3=2, Q4=1


def _add_ces_revisions(df: pl.DataFrame) -> pl.DataFrame:
    """CES: revisions 0, 1, 2 (and 9 added separately for March). benchmark_revision=0."""
    parts = []
    for n in CES_MONTHLY_REVISIONS:
        if n == 0:
            parts.append(
                df.filter(pl.col("publication") == "ces").with_columns(
                    pl.lit(0).alias("revision"),
                    pl.lit(0).alias("benchmark_revision"),
                )
            )
        else:
            parts.append(
                df.filter(pl.col("publication") == "ces").with_columns(
                    pl.col("vintage_date").dt.offset_by(f"{n}mo").alias("vintage_date"),
                    pl.lit(n).alias("revision"),
                    pl.lit(0).alias("benchmark_revision"),
                )
            )
    return pl.concat(parts)


def _add_sae_revisions(df: pl.DataFrame) -> pl.DataFrame:
    """SAE: revisions 0, 1 (and 9 added separately for Apr–Sep). benchmark_revision=0."""
    parts = []
    for n in SAE_MONTHLY_REVISIONS:
        if n == 0:
            parts.append(
                df.filter(pl.col("publication") == "sae").with_columns(
                    pl.lit(0).alias("revision"),
                    pl.lit(0).alias("benchmark_revision"),
                )
            )
        else:
            parts.append(
                df.filter(pl.col("publication") == "sae").with_columns(
                    pl.col("vintage_date").dt.offset_by(f"{n}mo").alias("vintage_date"),
                    pl.lit(n).alias("revision"),
                    pl.lit(0).alias("benchmark_revision"),
                )
            )
    return pl.concat(parts)


def _add_qcew_revisions(df: pl.DataFrame) -> pl.DataFrame:
    """QCEW: revisions 0..max by quarter (Q1=4, Q2=3, Q3=2, Q4=1)."""
    qcew = df.filter(pl.col("publication") == "qcew").with_columns(
        pl.col("ref_date").dt.month().alias("month"),
    )
    max_rev = (
        pl.when(pl.col("month").is_between(1, 3))
        .then(4)
        .when(pl.col("month").is_between(4, 6))
        .then(3)
        .when(pl.col("month").is_between(7, 9))
        .then(2)
        .otherwise(1)
        .alias("max_rev")
    )
    qcew = qcew.with_columns(max_rev)
    parts = []
    for n in range(5):  # 0..4
        if n == 0:
            parts.append(
                qcew.with_columns(
                    pl.lit(0).alias("revision"),
                    pl.lit(0).alias("benchmark_revision"),
                ).select("publication", "ref_date", "vintage_date", "revision", "benchmark_revision")
            )
        else:
            subset = qcew.filter(pl.col("max_rev") >= n)
            parts.append(
                subset.with_columns(
                    pl.col("vintage_date").dt.offset_by(f"{n}mo").alias("vintage_date"),
                    pl.lit(n).alias("revision"),
                    pl.lit(0).alias("benchmark_revision"),
                ).select("publication", "ref_date", "vintage_date", "revision", "benchmark_revision")
            )
    return pl.concat(parts)


def _ces_benchmark_vintage_dates(release_df: pl.DataFrame) -> pl.DataFrame:
    """CES: March ref_date → benchmark at vintage_date of (ces, January 12, year+1)."""
    ces = release_df.filter(pl.col("publication") == "ces")
    jan_releases = ces.filter(pl.col("ref_date").dt.month() == 1).select(
        pl.col("ref_date").dt.year().alias("year"),
        pl.col("vintage_date").alias("benchmark_vintage"),
    )
    # ref_date March Y → benchmark_vintage from January Y+1
    march_refs = ces.filter(pl.col("ref_date").dt.month() == 3).select(
        "publication", "ref_date",
        (pl.col("ref_date").dt.year() + 1).alias("benchmark_year"),
    )
    joined = march_refs.join(
        jan_releases,
        left_on="benchmark_year",
        right_on="year",
        how="inner",
    )
    return joined.select(
        pl.col("publication"),
        pl.col("ref_date"),
        pl.col("benchmark_vintage").alias("vintage_date"),
        pl.lit(9).alias("revision"),
        pl.lit(1).alias("benchmark_revision"),
    )


def _sae_benchmark_vintage_dates(release_df: pl.DataFrame) -> pl.DataFrame:
    """SAE: ref_date April–September Y → two benchmarks: March Y+1 (first) and March Y+2 (re-replacement)."""
    sae = release_df.filter(pl.col("publication") == "sae")
    march_releases = sae.filter(pl.col("ref_date").dt.month() == 3).select(
        pl.col("ref_date").dt.year().alias("year"),
        pl.col("vintage_date").alias("benchmark_vintage"),
    )
    apr_sep = sae.filter(
        pl.col("ref_date").dt.month().is_between(4, 9)
    ).select(
        "publication", "ref_date",
        pl.col("ref_date").dt.year().alias("ref_year"),
    )
    # First benchmark: March Y+1 (benchmark_revision=1)
    first = apr_sep.with_columns((pl.col("ref_year") + 1).alias("benchmark_year")).join(
        march_releases,
        left_on="benchmark_year",
        right_on="year",
        how="inner",
    ).select(
        pl.col("publication"),
        pl.col("ref_date"),
        pl.col("benchmark_vintage").alias("vintage_date"),
        pl.lit(9).alias("revision"),
        pl.lit(1).alias("benchmark_revision"),
    )
    # Second benchmark (re-replacement): March Y+2 (benchmark_revision=2)
    second = apr_sep.with_columns((pl.col("ref_year") + 2).alias("benchmark_year")).join(
        march_releases,
        left_on="benchmark_year",
        right_on="year",
        how="inner",
    ).select(
        pl.col("publication"),
        pl.col("ref_date"),
        pl.col("benchmark_vintage").alias("vintage_date"),
        pl.lit(9).alias("revision"),
        pl.lit(2).alias("benchmark_revision"),
    )
    return pl.concat([first, second])


def build_vintage_dates(release_dates_path: Path | None = None) -> pl.DataFrame:
    """Build vintage_dates DataFrame from release_dates parquet."""
    path = release_dates_path or PARQUET_PATH
    df = pl.read_parquet(path)

    # Publication-specific revisions: CES 0,1,2; SAE 0,1; QCEW 0..max by quarter
    with_revisions = pl.concat([
        _add_ces_revisions(df),
        _add_sae_revisions(df),
        _add_qcew_revisions(df),
    ])

    # Benchmark revisions (CES March, SAE Apr–Sep only)
    ces_bench = _ces_benchmark_vintage_dates(df)
    sae_bench = _sae_benchmark_vintage_dates(df)
    benchmark_rows = pl.concat([ces_bench, sae_bench])

    out = (
        pl.concat([with_revisions, benchmark_rows])
        .filter(pl.col("vintage_date") <= pl.lit(date.today()))
        .sort(["publication", "ref_date", "vintage_date", "revision", "benchmark_revision"])
    )
    return out


def main() -> None:
    """Build and write vintage_dates.parquet."""
    df = build_vintage_dates()
    VINTAGE_DATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(VINTAGE_DATES_PATH)
    print(f"Wrote {VINTAGE_DATES_PATH} ({len(df)} rows)")


if __name__ == "__main__":
    main()
