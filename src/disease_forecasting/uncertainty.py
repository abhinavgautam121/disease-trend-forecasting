"""Frozen, horizon-specific absolute-error intervals from a separate calibration period."""

import math

import numpy as np
import pandas as pd


def residual_quantile(errors, coverage: float) -> float:
    errors = np.asarray(errors, dtype=float)
    if len(errors) == 0 or not np.isfinite(errors).all():
        raise ValueError("Calibration residuals must be finite and nonempty")
    rank = math.ceil((len(errors) + 1) * coverage)
    if rank > len(errors):
        raise ValueError("Not enough calibration residuals for the requested coverage")
    return float(np.sort(errors)[rank - 1])


def calibrate(calibration: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, horizon), group in calibration.groupby(["model", "horizon"]):
        errors = np.abs(group.actual - group.prediction)
        rows.append(
            {
                "model": model,
                "horizon": int(horizon),
                "n_calibration": len(errors),
                "radius_80": residual_quantile(errors, 0.80),
                "radius_95": residual_quantile(errors, 0.95),
            }
        )
    return pd.DataFrame(rows)


def add_intervals(predictions: pd.DataFrame, radii: pd.DataFrame) -> pd.DataFrame:
    result = predictions.merge(radii, on=["model", "horizon"], how="left", validate="many_to_one")
    if result.radius_95.isna().any():
        raise ValueError("Missing calibration for one or more forecasts")
    for level in (80, 95):
        result[f"lower_{level}"] = np.maximum(0, result.prediction - result[f"radius_{level}"])
        result[f"upper_{level}"] = result.prediction + result[f"radius_{level}"]
    return result
