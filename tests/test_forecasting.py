import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from disease_forecasting.data import load_data
from disease_forecasting.evaluation import backtest, origins, split_periods
from disease_forecasting.features import make_features, supervised
from disease_forecasting.models import MODELS, forecast
from disease_forecasting.uncertainty import add_intervals, calibrate, residual_quantile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/default.json").read_text())
FAST = {"n_estimators": 3, "max_depth": 3, "min_samples_leaf": 2}


@pytest.fixture
def cases():
    return load_data(ROOT).cases


def test_features_do_not_change_when_future_changes(cases):
    changed = cases.copy()
    changed.iloc[100:] = 9999999
    before = make_features(cases, 4).iloc[:100]
    after = make_features(changed, 4).iloc[:100]
    pd.testing.assert_frame_equal(before, after)
    assert before.iloc[-1].cases_lag_0 == cases.iloc[99]
    assert before.iloc[-1].cases_lag_51 == cases.iloc[48]
    assert before.iloc[-1].mean_4 == cases.iloc[96:100].mean()


@pytest.mark.parametrize("horizon", [1, 2, 4])
def test_training_labels_are_available_at_origin(cases, horizon):
    history = cases.iloc[:100]
    features, targets = supervised(history, horizon)
    assert (features.index + pd.Timedelta(weeks=horizon) <= history.index[-1]).all()
    expected = history.reindex(features.index + pd.Timedelta(weeks=horizon)).to_numpy()
    np.testing.assert_array_equal(targets.to_numpy(), expected)


def test_split_targets_never_cross_boundaries(cases):
    periods = split_periods(len(cases), CONFIG)
    target_sets = []
    for start, stop in periods.values():
        targets = {
            origin + h
            for origin in origins(start, stop, CONFIG["horizons"])
            for h in CONFIG["horizons"]
        }
        assert min(targets) >= start
        assert max(targets) < stop
        target_sets.append(targets)
    assert target_sets[0].isdisjoint(target_sets[1])
    assert target_sets[1].isdisjoint(target_sets[2])


def test_forecasts_have_correct_shape_and_baseline_alignment(cases):
    history = cases.iloc[:100]
    result = forecast(history, [1, 2, 4], FAST)
    assert set(result) == {1, 2, 4}
    for h, predictions in result.items():
        assert set(predictions) == set(MODELS)
        assert all(np.isfinite(value) and value >= 0 for value in predictions.values())
        assert predictions["Naive"] == history.iloc[-1]
        assert predictions["Seasonal naive"] == cases.iloc[99 + h - 52]


def test_backtest_uses_prefix_history_only(cases, monkeypatch):
    observed = []

    def spy(history, horizons, params, seed):
        observed.append(history.index[-1])
        return {h: {model: float(history.iloc[-1]) for model in MODELS} for h in horizons}

    monkeypatch.setattr("disease_forecasting.evaluation.forecast", spy)
    result = backtest(cases, CONFIG, (110, 120), FAST, "test")
    assert (result.target_date > result.origin).all()
    assert len(observed) == 7
    assert observed[0] == cases.index[109]
    assert observed[-1] == cases.index[115]
    assert result.groupby(["origin", "horizon"]).size().eq(4).all()


def test_quantile_rank_and_small_sample_guard():
    assert residual_quantile(np.arange(1, 37), 0.95) == 36
    assert residual_quantile(np.arange(1, 37), 0.80) == 30
    with pytest.raises(ValueError, match="Not enough"):
        residual_quantile([1, 2, 3], 0.95)


def test_intervals_are_nested_nonnegative_and_frozen():
    calibration = pd.DataFrame(
        {
            "model": ["Naive"] * 36,
            "horizon": [1] * 36,
            "prediction": np.arange(36),
            "actual": np.arange(36) * 2,
        }
    )
    radii = calibrate(calibration)
    held_out = pd.DataFrame(
        {"model": ["Naive"], "horizon": [1], "prediction": [5], "actual": [1000]}
    )
    result = add_intervals(held_out, radii).iloc[0]
    assert 0 <= result.lower_95 <= result.lower_80 <= result.prediction
    assert result.prediction <= result.upper_80 <= result.upper_95
    held_out["actual"] = -1000
    updated = add_intervals(held_out, radii).iloc[0]
    assert result.upper_95 == updated.upper_95
    assert result.lower_80 == updated.lower_80
