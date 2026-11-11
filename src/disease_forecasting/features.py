"""Features at forecast origin t; training labels are available only through t."""

import numpy as np
import pandas as pd

LAGS = (0, 1, 2, 3, 7, 11, 51)


def make_features(cases: pd.Series, horizon: int) -> pd.DataFrame:
    """Lag 0 means the most recent observed week at origin, never a future target."""
    features = pd.DataFrame(index=cases.index)
    for lag in LAGS:
        features[f"cases_lag_{lag}"] = cases.shift(lag)
    for window in (4, 8, 12):
        features[f"mean_{window}"] = cases.rolling(window).mean()
        features[f"std_{window}"] = cases.rolling(window).std()
    features["change_1"] = cases.diff()
    target_dates = cases.index + pd.Timedelta(weeks=horizon)
    phase = 2 * np.pi * target_dates.dayofyear / 365.25
    features["target_season_sin"] = np.sin(phase)
    features["target_season_cos"] = np.cos(phase)
    return features


def supervised(cases: pd.Series, horizon: int) -> tuple[pd.DataFrame, pd.Series]:
    features = make_features(cases, horizon)
    target = cases.shift(-horizon)
    valid = features.notna().all(axis=1) & target.notna()
    return features.loc[valid], target.loc[valid]
