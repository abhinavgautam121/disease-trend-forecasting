"""CLI for data, training, evaluation, and reproducible reporting."""

import argparse
import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from disease_forecasting.data import download, load_data, sha256
from disease_forecasting.evaluation import backtest, metrics, split_periods, tune_forest
from disease_forecasting.models import fit_forest, forecast
from disease_forecasting.reporting import write_results
from disease_forecasting.uncertainty import add_intervals, calibrate
from disease_forecasting.visualization import export_figures

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


def run(root: Path, config: dict) -> dict:
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    processed = root / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    data = load_data(root, config["state"])
    data.to_csv(processed / "weekly_cases.csv")
    cases = data.cases
    periods = split_periods(len(cases), config)
    print("Tuning Random Forest on rolling validation origins...", flush=True)
    params, tuning = tune_forest(cases, config, periods["validation"])
    tuning.to_csv(reports / "tuning.csv", index=False)
    frames = []
    for phase, period in periods.items():
        print(f"Evaluating {phase} period...", flush=True)
        frames.append(backtest(cases, config, period, params, phase))
    all_predictions = pd.concat(frames, ignore_index=True)
    validation = metrics(all_predictions.query("phase == 'validation'"))
    validation.to_csv(reports / "validation_metrics.csv", index=False)
    # Model choice is frozen before inspecting calibration or test outcomes.
    selected = validation.groupby("model").mae.mean().sort_values().index[0]
    radii = calibrate(all_predictions.query("phase == 'calibration'"))
    radii.to_csv(reports / "interval_calibration.csv", index=False)
    all_predictions.to_csv(reports / "backtest_predictions.csv", index=False)
    test = add_intervals(all_predictions.query("phase == 'test'"), radii)
    test.to_csv(reports / "test_predictions.csv", index=False)
    scores = metrics(test)
    scores.to_csv(reports / "test_metrics.csv", index=False)
    latest_rows = []
    for h, predictions in forecast(cases, config["horizons"], params, config["seed"]).items():
        for model, prediction in predictions.items():
            latest_rows.append(
                {
                    "model": model,
                    "horizon": h,
                    "origin": cases.index[-1],
                    "target_date": cases.index[-1] + pd.Timedelta(weeks=h),
                    "prediction": prediction,
                }
            )
    latest = add_intervals(pd.DataFrame(latest_rows), radii)
    latest.to_csv(reports / "latest_forecasts.csv", index=False)
    artifacts = root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    importances = []
    for h in config["horizons"]:
        model = fit_forest(cases, h, params, config["seed"])
        joblib.dump(model, artifacts / f"forest_h{h}.joblib")
        importances.extend(
            {"horizon": h, "feature": name, "importance": float(value)}
            for name, value in zip(model.feature_names_in_, model.feature_importances_)
        )
    pd.DataFrame(importances).to_csv(reports / "feature_importance.csv", index=False)
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_through": str(cases.index[-1].date()),
        "data_start": str(cases.index[0].date()),
        "observations": len(cases),
        "snapshot_sha256": sha256(root / "data/raw/cdc_ca_weekly.json"),
        "config": config,
        "selected_rf_params": params,
        "selected_model": selected,
        "selection_rule": "Lowest validation MAE averaged over horizons",
        "periods": {
            name: {"start": str(cases.index[a].date()), "end": str(cases.index[b - 1].date())}
            for name, (a, b) in periods.items()
        },
        "python": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("pandas", "numpy", "scikit-learn", "statsmodels", "streamlit", "plotly")
        },
        "evaluation_type": "Retrospective, revised single-vintage expanding-window evaluation",
        "interval_method": "Frozen absolute residual quantiles from pre-test rolling calibration",
        "clinical_use": False,
    }
    (reports / "run_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    write_results(root, scores, metadata)
    export_figures(root, data, test, latest, scores, selected)
    print(scores.round(3).to_string(index=False), flush=True)
    print(f"Selected on validation: {selected}", flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["download", "run", "all"])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    config = json.loads((args.config or root / "configs/default.json").read_text())
    if args.command in ("download", "all"):
        download(root, config)
    if args.command in ("run", "all"):
        run(root, config)


if __name__ == "__main__":
    main()
