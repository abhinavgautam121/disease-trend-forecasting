import json
import shutil
from pathlib import Path

import pandas as pd

from disease_forecasting.pipeline import run

ROOT = Path(__file__).resolve().parents[1]


def test_small_real_data_pipeline(tmp_path):
    shutil.copytree(ROOT / "data/raw", tmp_path / "data/raw")
    config = json.loads((ROOT / "configs/default.json").read_text())
    config.update(validation_weeks=10, calibration_weeks=24, test_weeks=8)
    config["rf_candidates"] = [{"n_estimators": 3, "max_depth": 3, "min_samples_leaf": 2}]
    metadata = run(tmp_path, config)
    scores = pd.read_csv(tmp_path / "reports/test_metrics.csv")
    assert len(scores) == 12
    assert scores.n.eq(5).all()
    assert scores.mae.ge(0).all()
    assert scores.coverage_95.between(0, 1).all()
    assert metadata["clinical_use"] is False
    assert (tmp_path / "reports/figures/forecast.html").exists()
    assert (tmp_path / "artifacts/forest_h4.joblib").exists()


def test_saved_results_match_predictions():
    predictions = pd.read_csv(ROOT / "reports/test_predictions.csv")
    scores = pd.read_csv(ROOT / "reports/test_metrics.csv")
    for row in scores.itertuples():
        group = predictions[(predictions.model == row.model) & (predictions.horizon == row.horizon)]
        assert abs((group.actual - group.prediction).abs().mean() - row.mae) < 1e-6
    assert predictions.origin.max() < predictions.target_date.max()
