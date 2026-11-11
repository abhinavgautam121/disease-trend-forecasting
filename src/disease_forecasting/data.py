"""Download and validate official CDC weekly reported cases."""

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE = (
    "https://data.cdc.gov/Case-Surveillance/"
    "Weekly-United-States-COVID-19-Cases-and-Deaths-by-/pwn4-m3yp"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(root: Path, config: dict) -> None:
    """Fetch a single jurisdiction; preserve the source's exact response bytes."""
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode(
        {
            "$where": f"state='{config['state']}'",
            "$order": "end_date",
            "$limit": 10000,
        }
    )
    url = f"https://data.cdc.gov/resource/{config['dataset_id']}.json?{query}"
    with urllib.request.urlopen(url, timeout=60) as response:
        content = response.read()
    rows = json.loads(content)
    if len(rows) >= 10000:
        raise ValueError("Pagination required: refusing a potentially truncated download")
    # Validate before replacing the cached snapshot.
    prepare(rows, config["state"])
    path = raw / "cdc_ca_weekly.json"
    path.write_bytes(content)
    with urllib.request.urlopen(
        f"https://data.cdc.gov/api/views/{config['dataset_id']}.json", timeout=60
    ) as response:
        source_meta = json.load(response)
    metadata = {
        "publisher": "Centers for Disease Control and Prevention (CDC)",
        "source_url": SOURCE,
        "download_url": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256(path),
        "records": len(rows),
        "license": source_meta.get("license"),
        "source_description": source_meta.get("description"),
        "source_rows_updated_at": source_meta.get("rowsUpdatedAt"),
        "variable": "new_cases",
        "state": config["state"],
    }
    (raw / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


def prepare(rows: list[dict], state: str = "CA") -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    required = {"state", "end_date", "start_date", "new_cases"}
    if not required.issubset(frame):
        raise ValueError(f"Missing columns: {required - set(frame)}")
    if not frame["state"].eq(state).all():
        raise ValueError("Unexpected geography in the source snapshot")
    dates = pd.to_datetime(frame["end_date"], errors="raise")
    starts = pd.to_datetime(frame["start_date"], errors="raise")
    if dates.duplicated().any():
        raise ValueError("Duplicate reporting weeks")
    if not (dates - starts).eq(pd.Timedelta(days=6)).all():
        raise ValueError("Incomplete reporting period")
    values = pd.to_numeric(frame["new_cases"], errors="raise")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Missing, non-finite, or negative reported cases; review source")
    if not np.equal(values, np.floor(values)).all():
        raise ValueError("Case counts must be integers")
    result = pd.DataFrame({"date": dates, "cases": values.astype(int)}).sort_values("date")
    result = result.set_index("date")
    if not result.index.dayofweek.to_series().eq(2).all():
        raise ValueError("Expected Wednesday week-ending dates")
    regular = result.asfreq("W-WED")
    if regular["cases"].isna().any():
        raise ValueError("Missing reporting weeks; a missing report is not zero")
    return regular


def load_data(root: Path, state: str = "CA") -> pd.DataFrame:
    path = root / "data/raw/cdc_ca_weekly.json"
    metadata = json.loads((root / "data/raw/metadata.json").read_text())
    if sha256(path) != metadata["sha256"]:
        raise ValueError("Snapshot hash mismatch: rerun download or review the data change")
    return prepare(json.loads(path.read_text()), state)
