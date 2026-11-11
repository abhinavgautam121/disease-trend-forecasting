"""Four forecasting approaches sharing the same observed history."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from disease_forecasting.features import make_features, supervised

MODELS = ("Naive", "Seasonal naive", "Damped ETS", "Random Forest")


def fit_forest(cases: pd.Series, horizon: int, params: dict, seed: int = 42):
    x_train, y_train = supervised(cases, horizon)
    if len(x_train) < 10:
        raise ValueError("Insufficient complete training examples")
    model = RandomForestRegressor(**params, random_state=seed, n_jobs=1)
    model.fit(x_train, y_train)
    return model


def forecast(cases: pd.Series, horizons: list[int], params: dict, seed: int = 42) -> dict:
    if len(cases) < 60 or max(horizons) > 52:
        raise ValueError("At least 60 weeks of history and horizons <= 52 are required")
    ets = ExponentialSmoothing(
        np.log1p(cases.to_numpy(dtype=float)),
        trend="add",
        damped_trend=True,
        initialization_method="estimated",
    ).fit(optimized=True)
    ets_forecast = np.maximum(0, np.expm1(ets.forecast(max(horizons))))
    predictions = {}
    for h in horizons:
        forest = fit_forest(cases, h, params, seed)
        x_next = make_features(cases, h).iloc[[-1]]
        predictions[h] = {
            "Naive": float(cases.iloc[-1]),
            "Seasonal naive": float(cases.iloc[-1 + h - 52]),
            "Damped ETS": float(ets_forecast[h - 1]),
            "Random Forest": max(0.0, float(forest.predict(x_next)[0])),
        }
    return predictions
