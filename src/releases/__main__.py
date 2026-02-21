"""Run the BLS release scraper: download releases, extract dates, save parquet."""

import asyncio
import logging
from pathlib import Path

import httpx
import polars as pl

from .config import DATA_DIR, PARQUET_PATH, PUBLICATIONS
from .parser import collect_release_dates
from .scraper import download_all, fetch_index, parse_index_page

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def download_all_publications() -> None:
    """Fetch each publication's index, parse entries, and download HTMLs."""
    async with httpx.AsyncClient(
        http2=True,
        follow_redirects=True,
        timeout=30.0,
    ) as client:
        for pub in PUBLICATIONS:
            log.info("Fetching index for %s", pub.name)
            html = await fetch_index(client, pub.index_url)
            entries = parse_index_page(html, pub.name, pub.series, pub.frequency)
            log.info("Found %d releases for %s", len(entries), pub.name)
            await download_all(entries, pub.name)


def build_dataframe() -> pl.DataFrame:
    """Collect release dates from downloaded files and return a polars DataFrame."""
    rows: list[tuple[str, str, str]] = []
    for pub in PUBLICATIONS:
        releases_dir = DATA_DIR / pub.name
        if not releases_dir.is_dir():
            continue
        for publication, ref_date, vintage_date in collect_release_dates(pub.name, releases_dir):
            rows.append((publication, ref_date.isoformat(), vintage_date.isoformat()))

    if not rows:
        return pl.DataFrame(
            schema={
                "publication": pl.Utf8,
                "ref_date": pl.Date,
                "vintage_date": pl.Date,
            }
        )

    return pl.DataFrame(
        {
            "publication": [r[0] for r in rows],
            "ref_date": [r[1] for r in rows],
            "vintage_date": [r[2] for r in rows],
        }
    ).with_columns(
        pl.col("ref_date").str.to_date(),
        pl.col("vintage_date").str.to_date(),
    )


def main() -> None:
    """Download BLS releases, parse dates, and write parquet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log.info("Downloading release HTMLs...")
    asyncio.run(download_all_publications())

    log.info("Parsing release dates...")
    df = build_dataframe()
    log.info("Collected %d rows", len(df))

    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(PARQUET_PATH)
    log.info("Wrote %s", PARQUET_PATH)


if __name__ == "__main__":
    main()
