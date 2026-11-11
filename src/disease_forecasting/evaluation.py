"""Expanding-window backtesting with separated target periods."""

import numpy as np
import pandas as pd

from disease_forecasting.features import make_features
from disease_forecasting.models import fit_forest, forecast


def split_periods(n: int, config: dict) -> dict[str, tuple[int, int]]:
    test = n - config["test_weeks"]
    calibration = test - config["calibration_weeks"]
    validation = calibration - config["validation_weeks"]
    if validation < 78:
        raise ValueError("Need at least 78 initial training weeks before validation")
    return {
        "validation": (validation, calibration),
        "calibration": (calibration, test),
        "test": (test, n),
    }


def origins(start: int, stop: int, horizons: list[int]) -> range:
    """Every requested target must lie within [start, stop); skip boundary crossovers."""
    return range(start - 1, stop - max(horizons))


def tune_forest(cases: pd.Series, config: dict, period: tuple[int, int]):
    records = []
    for candidate_id, params in enumerate(config["rf_candidates"]):
        errors = []
        for origin in origins(*period, config["horizons"]):
            history = cases.iloc[: origin + 1]
            for h in config["horizons"]:
                model = fit_forest(history, h, params, config["seed"])
                pred = model.predict(make_features(history, h).iloc[[-1]])[0]
                errors.append(abs(float(cases.iloc[origin + h]) - pred))
        records.append({"candidate": candidate_id, "mae": float(np.mean(errors)), **params})
    scores = pd.DataFrame(records)
    winner = int(scores.sort_values(["mae", "candidate"]).iloc[0]["candidate"])
    return config["rf_candidates"][winner], scores


def backtest(cases, config, period, params, phase):
    records = []
    for origin in origins(*period, config["horizons"]):
        history = cases.iloc[: origin + 1]
        # Seasonal MASE scale uses only observations available at this origin.
        scale = float(np.mean(np.abs(history.to_numpy()[52:] - history.to_numpy()[:-52])))
        predictions = forecast(history, config["horizons"], params, config["seed"])
        for h, models in predictions.items():
            for model, prediction in models.items():
                records.append(
                    {
                        "phase": phase,
                        "origin": cases.index[origin],
                        "target_date": cases.index[origin + h],
                        "horizon": h,
                        "model": model,
                        "actual": float(cases.iloc[origin + h]),
                        "prediction": prediction,
                        "mase_scale": scale,
                    }
                )
    return pd.DataFrame(records)


def metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, horizon), group in predictions.groupby(["model", "horizon"]):
        error = group["actual"] - group["prediction"]
        row = {
            "model": model,
            "horizon": int(horizon),
            "n": len(group),
            "mae": float(error.abs().mean()),
            "rmse": float(np.sqrt((error**2).mean())),
            "mase": float((error.abs() / group["mase_scale"].replace(0, np.nan)).mean()),
        }
        for level in (80, 95):
            if f"lower_{level}" in group:
                row[f"coverage_{level}"] = float(
                    (
                        (group.actual >= group[f"lower_{level}"])
                        & (group.actual <= group[f"upper_{level}"])
                    ).mean()
                )
                row[f"width_{level}"] = float(
                    (group[f"upper_{level}"] - group[f"lower_{level}"]).mean()
                )
        rows.append(row)
    return pd.DataFrame(rows)
