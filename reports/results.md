# Measured forecasting results

Data: 173 weekly CDC observations for California, 2020-01-22–2023-05-10.
Run generated: 2026-11-11T11:47:40.900431+00:00. Full settings, package versions, and source hash are in `run_metadata.json`.

**Validation-selected model: Naive.** Selection uses the lowest validation MAE averaged over horizons. Hyperparameters, model choice, and interval radii are not chosen using final test errors.

## Final test point forecasts

| model | horizon | n | mae | rmse | mase |
| --- | --- | --- | --- | --- | --- |
| Damped ETS | 1 | 23 | 7,680 | 13,216 | 0.115 |
| Damped ETS | 2 | 23 | 10,505 | 16,275 | 0.155 |
| Damped ETS | 4 | 23 | 19,465 | 35,968 | 0.291 |
| Naive | 1 | 23 | 7,670 | 12,282 | 0.114 |
| Naive | 2 | 23 | 10,292 | 14,621 | 0.152 |
| Naive | 4 | 23 | 17,077 | 24,127 | 0.253 |
| Random Forest | 1 | 23 | 13,961 | 26,593 | 0.212 |
| Random Forest | 2 | 23 | 47,043 | 86,070 | 0.701 |
| Random Forest | 4 | 23 | 130,140 | 216,231 | 1.833 |
| Seasonal naive | 1 | 23 | 155,203 | 289,821 | 2.120 |
| Seasonal naive | 2 | 23 | 156,448 | 289,892 | 2.254 |
| Seasonal naive | 4 | 23 | 159,464 | 290,175 | 2.434 |

MAE and RMSE are weekly case counts; lower is better. Seasonal MASE divides absolute error by the mean absolute 52-week difference calculated only from each origin's training history. A value below 1 beats that training-scale reference; it is not a direct comparison to the seasonal model's held-out score. Each horizon has the same forecast origins across models.

Lowest observed test MAE by horizon: **1 weeks: Naive; 2 weeks: Naive; 4 weeks: Naive**. These test winners are reported descriptively; they do not replace the frozen validation selection.

## Prediction interval performance

| model | horizon | coverage_80 | width_80 | coverage_95 | width_95 |
| --- | --- | --- | --- | --- | --- |
| Damped ETS | 1 | 87.0% | 36,534 | 95.7% | 59,006 |
| Damped ETS | 2 | 91.3% | 57,932 | 95.7% | 75,373 |
| Damped ETS | 4 | 87.0% | 78,058 | 95.7% | 137,203 |
| Naive | 1 | 91.3% | 41,205 | 100.0% | 132,775 |
| Naive | 2 | 95.7% | 59,497 | 100.0% | 171,650 |
| Naive | 4 | 91.3% | 86,883 | 100.0% | 199,186 |
| Random Forest | 1 | 87.0% | 55,118 | 100.0% | 288,612 |
| Random Forest | 2 | 69.6% | 79,322 | 87.0% | 209,617 |
| Random Forest | 4 | 60.9% | 112,758 | 69.6% | 178,622 |
| Seasonal naive | 1 | 69.6% | 160,542 | 69.6% | 192,991 |
| Seasonal naive | 2 | 69.6% | 160,841 | 69.6% | 193,290 |
| Seasonal naive | 4 | 69.6% | 162,651 | 69.6% | 195,101 |

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
