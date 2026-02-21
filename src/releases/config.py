"""Publication definitions and paths."""

from dataclasses import dataclass
from pathlib import Path

BASE_URL = "https://www.bls.gov"
DATA_DIR = Path("data/releases")
PARQUET_PATH = Path("data/release_dates.parquet")
START_YEAR = 2010


@dataclass(frozen=True)
class Publication:
    """BLS publication: name, series code, index URL, frequency."""

    name: str
    series: str
    index_url: str
    frequency: str  # "monthly" | "quarterly"


PUBLICATIONS = [
    Publication(
        name="ces",
        series="empsit",
        index_url=f"{BASE_URL}/bls/news-release/empsit.htm",
        frequency="monthly",
    ),
    Publication(
        name="sae",
        series="laus",
        index_url=f"{BASE_URL}/bls/news-release/laus.htm",
        frequency="monthly",
    ),
    Publication(
        name="qcew",
        series="cewqtr",
        index_url=f"{BASE_URL}/bls/news-release/cewqtr.htm",
        frequency="quarterly",
    ),
]
