import copy
import json
from pathlib import Path

import pytest

from disease_forecasting.data import load_data, prepare

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def rows():
    return json.loads((ROOT / "data/raw/cdc_ca_weekly.json").read_text())


def test_real_snapshot_is_regular_and_verified():
    data = load_data(ROOT)
    assert len(data) == 173
    assert data.index.min().strftime("%Y-%m-%d") == "2020-01-22"
    assert data.index.max().strftime("%Y-%m-%d") == "2023-05-10"
    assert data.index.is_unique
    assert data.cases.ge(0).all()
    assert data.cases.isna().sum() == 0


@pytest.mark.parametrize(
    "problem", ["missing", "duplicate", "negative", "null", "state", "partial"]
)
def test_bad_data_is_rejected(rows, problem):
    changed = copy.deepcopy(rows)
    if problem == "missing":
        changed.pop(20)
    elif problem == "duplicate":
        changed.append(changed[20])
    elif problem == "negative":
        changed[20]["new_cases"] = "-1"
    elif problem == "null":
        changed[20]["new_cases"] = None
    elif problem == "state":
        changed[20]["state"] = "NY"
    else:
        changed[20]["start_date"] = changed[20]["end_date"]
    with pytest.raises(ValueError):
        prepare(changed)
