# Model card

## Scope

**Casecast 1.0**, by Abhinav Gautam. Forecast weekly reported COVID-19 cases in California, 1, 2, or 4 weeks after a Wednesday reporting cutoff. Portfolio/research use only. No individual risk, diagnosis, treatment recommendation, or operational validation.

## Candidate models

1. Naive: repeat the most recent weekly reported count for every horizon.
2. Seasonal naive: reuse the count 52 weeks before each target week. This is a deliberately simple annual-pattern benchmark, not an epidemiological assumption that COVID recurs identically each year.
3. Damped ETS: statsmodels exponential smoothing with additive damped trend on `log1p(cases)`, no annual seasonal component. Convert to case scale with `expm1`, then clip at zero. The transformed point forecast is not bias-adjusted to estimate a case-scale conditional mean; evaluate it directly as implemented.
4. Random Forest: separate direct regressors at each horizon; raw target counts; 150 trees. Compare two depth/leaf-size configurations during validation. The saved run records the selected settings and random seed.

## Features and timing

At origin t, counts at t, t−1, t−2, t−3, t−7, t−11, t−51; trailing 4/8/12-week mean and sample standard deviation including t; first difference at t; cyclic calendar encodings of the known target date. Lag 0 denotes the latest observed week, not the future label. At horizon h, a historical training row at s is usable only when s+h≤t.

There are no clinical variables or future external predictors. No scaling is fitted, and missing observations are rejected. Full-data forest models are saved locally for reproducibility but excluded from Git.

## Selection and evaluation

Select hyperparameters and the model with lowest average horizon MAE using the 26-week validation target block. The two forest candidates share this validation block, so validation scores are model-selection scores, not unbiased performance estimates. Selection is frozen before interval calibration and final testing. **Naive** is the selected model in the included run.

Use expanding-window refits and identical origins/horizons for every candidate. A separate 39-week calibration target block supplies residuals; a 26-week test target block supplies the final metrics. The requirement that all horizon targets fit within each block leaves 23 validation, 36 calibration, and 23 test origins. Earlier observed test weeks can enter later test training windows; future observations cannot.

MAE and RMSE are in weekly cases. Seasonal MASE is scaled by the mean absolute 52-week training differences at each origin. See `test_metrics.csv` and `results.md`; model choice does not change after seeing the test winner.

## Uncertainty

Absolute chronological out-of-sample calibration errors are grouped by model and horizon. Use rank `ceil((n+1)c)` for c=.80 and .95; reject samples too small to supply a finite requested quantile. The included run has n=36 per group. Intervals are point forecast ± radius, truncated at zero. Quantiles are frozen before test scoring and reused for the latest historical refit.

These are residual-based prediction intervals, not parameter confidence intervals and not spread between forest trees. Temporal dependence, model refitting, and distribution shift violate assumptions needed for simple distribution-free coverage guarantees. Nominal coverage is therefore a target, not a promise; observed test coverage and width are reported together.

## Failure modes

Unprecedented outbreaks, changes in testing access, unreported home tests, revised counts, holiday backlogs, and geography changes can break the learned relationships. Random Forest averages observed training targets and cannot reliably extrapolate to new ranges. There is little stable annual history. The 23-origin test sample is small and overlapping horizon errors are dependent.

Final full-data feature importance is impurity based and descriptive: correlated lags share credit and importance does not establish causation or clinical relevance. The final refit is not itself independently evaluated after May 2023. No subgroup fairness claims or individual health claims are made from aggregate state data.

## Maintenance

The archive is fixed in time. Data updates must pass validation, produce a new hash, and rerun the pipeline. A new disease series requires renewed source verification, split design, model evaluation, and uncertainty assessment; changing the label alone is not sufficient.

