"""Render measured results without inventing achievements or metrics."""

from pathlib import Path

import pandas as pd


def markdown_table(frame: pd.DataFrame) -> str:
    header = "| " + " | ".join(str(name) for name in frame.columns) + " |"
    separator = "| " + " | ".join("---" for _ in frame.columns) + " |"
    rows = [
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    ]
    return "\n".join([header, separator, *rows])


def write_results(root: Path, scores: pd.DataFrame, metadata: dict) -> None:
    metrics = scores[["model", "horizon", "n", "mae", "rmse", "mase"]].copy()
    for name in ["mae", "rmse"]:
        metrics[name] = metrics[name].map(lambda value: f"{value:,.0f}")
    metrics["mase"] = metrics.mase.map(lambda value: f"{value:.3f}")
    intervals = scores[
        ["model", "horizon", "coverage_80", "width_80", "coverage_95", "width_95"]
    ].copy()
    for name in ["coverage_80", "coverage_95"]:
        intervals[name] = intervals[name].map(lambda value: f"{value:.1%}")
    for name in ["width_80", "width_95"]:
        intervals[name] = intervals[name].map(lambda value: f"{value:,.0f}")
    best = scores.loc[scores.groupby("horizon").mae.idxmin(), ["horizon", "model"]]
    winners = "; ".join(f"{row.horizon} weeks: {row.model}" for row in best.itertuples())
    text = f"""# Measured forecasting results

Data: {metadata["observations"]} weekly CDC observations for California, {metadata["data_start"]}–{metadata["data_through"]}.
Run generated: {metadata["generated_at_utc"]}. Full settings, package versions, and source hash are in `run_metadata.json`.

**Validation-selected model: {metadata["selected_model"]}.** Selection uses the lowest validation MAE averaged over horizons. Hyperparameters, model choice, and interval radii are not chosen using final test errors.

## Final test point forecasts

{markdown_table(metrics)}

MAE and RMSE are weekly case counts; lower is better. Seasonal MASE divides absolute error by the mean absolute 52-week difference calculated only from each origin's training history. A value below 1 beats that training-scale reference; it is not a direct comparison to the seasonal model's held-out score. Each horizon has the same forecast origins across models.

Lowest observed test MAE by horizon: **{winners}**. These test winners are reported descriptively; they do not replace the frozen validation selection.

## Prediction interval performance

{markdown_table(intervals)}

Coverage is the proportion of held-out targets within each interval. Width is the average upper minus lower bound, in case counts. Nominal levels are 80% and 95%. Always read coverage alongside width: extremely broad intervals can cover outcomes while offering little practical precision. Lower bounds are clipped at zero.

## Interpretation of the included default experiment

The naive baseline beats Random Forest on test MAE at every horizon in the included default run. Random Forest's long-horizon errors are large; more complex lag relationships did not generalize well into the later reporting regime. This does not prove forests are unsuitable for every disease or geography. The annual seasonal benchmark also performs poorly: only about three years of data and changing pandemic waves do not provide stable annual seasonality.

For the naive model, 95% intervals cover every evaluated test target in the default run, but they are very wide. Calibration occurred during a period with larger errors; this can produce conservative bands during later quieter periods. The Random Forest 4-week 95% interval covers only about 70% of test targets, illustrating that the same calibration recipe need not work equally well for all models or regimes.

These are observations of performance, not causal explanations. Testing/reporting changes, limited training samples, correlated lag inputs, changing epidemic patterns, and the inability of forests to extrapolate are plausible contributors. The study does not isolate their individual effects.

## Evaluation limits

- Rolling target periods are separate for validation, calibration, and test. Origins crossing a period boundary at any requested horizon are omitted; each horizon therefore covers a slightly different range of target dates within a block.
- Later test fits may consume earlier observed test weeks, as in sequential forecasting. No future values are supplied at an origin, and no test outcomes update hyperparameters or interval radii.
- Forecast errors from neighboring origins and overlapping horizons are dependent. Sample coverage is descriptive; no confidence interval for coverage or statistical significance of model differences is claimed.
- This is a retrospective backtest using one revised extract. Historical real-time data vintages are not available, so revision-related optimism remains possible.
- Reported cases are not all infections; the source ended in 2023. Latest projections are historical and not validated beyond the observed archive.
- Population forecasts cannot diagnose an individual or provide personal medical advice.

Machine-readable evidence: `test_predictions.csv`, `test_metrics.csv`, `validation_metrics.csv`, `tuning.csv`, `interval_calibration.csv`, and `run_metadata.json`.
"""
    (root / "reports/results.md").write_text(text)
