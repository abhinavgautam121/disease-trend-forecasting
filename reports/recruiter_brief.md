# Casecast · recruiter brief

**Author:** Abhinav Gautam  
**Repository:** https://github.com/abhinavgautam121/disease-trend-forecasting  
**Stack:** Python, pandas, scikit-learn, statsmodels, Plotly, Streamlit, pytest, GitHub Actions

## The project in 30 seconds

Casecast turns real CDC weekly California COVID-19 reports into a reproducible forecasting experiment and interactive dashboard. It compares naive, seasonal naive, damped exponential smoothing, and direct Random Forest forecasts at 1, 2, and 4 weeks. It uses chronological model selection, separate uncertainty calibration, and a final held-out rolling test, with source provenance and leakage checks.

The headline finding is that the simple last-observation baseline won on test MAE at every horizon. Keeping that result makes the project useful evidence of analytical judgment: model complexity must earn its place. The dashboard shows interval coverage and width together, so apparently good coverage cannot hide uninformative intervals.

## A 60-second interview explanation

“I built Casecast to forecast population-level reported disease trends and test whether Random Forest actually improves on basic time-series forecasts. I downloaded an official CDC archive containing 173 California weekly COVID reports and validated the dates, case definitions, missingness, and reporting periods.

I used expanding-window evaluation with separate validation, calibration, and final test target blocks. For Random Forest, I trained a direct model at each horizon using only lagged observations and known calendar features. Each training label had to be available at the forecast origin.

The naive model was selected on validation and achieved test MAEs of about 7,670, 10,292, and 17,077 weekly cases at 1, 2, and 4 weeks. Random Forest performed worse, especially at longer horizons. I calibrated prediction intervals using a separate period and reported both coverage and interval width. Some intervals were very wide, which is a limitation rather than proof of a strong model.

I packaged it as a tested Streamlit application with downloadable results, data and model cards, and GitHub CI. The data end in 2023, and I clearly distinguish this historical population forecast from current surveillance or an individual diagnosis.”

## Honest resume bullets

- Built an end-to-end disease surveillance forecasting pipeline using 173 real CDC weekly California COVID-19 observations, with validated source ingestion, provenance hashing, and a Streamlit/Plotly dashboard.
- Benchmarked four forecasting approaches across 1-, 2-, and 4-week horizons using chronological selection and 23 held-out rolling origins; the validation-selected naive model achieved test MAEs of 7,670, 10,292, and 17,077 weekly reported cases.
- Implemented separate residual calibration for 80%/95% prediction intervals, coverage-and-width reporting, temporal leakage checks, automated tests, and GitHub Actions quality checks.

## Recruiter message template

Hi [Recruiter Name],

I’d like to share Casecast, my end-to-end disease trend forecasting project: https://github.com/abhinavgautam121/disease-trend-forecasting

It uses real CDC surveillance data, compares time-series baselines with Random Forest, and includes a Streamlit dashboard, chronological backtesting, prediction intervals, tests, and reproducible documentation. A key finding was that the simple baseline generalized better than the more complex models, which I explain with the evaluation evidence and limitations.

The README includes the dashboard preview and results. I’d be happy to discuss the modeling and engineering decisions.

Best,  
Abhinav Gautam

## Demo route

1. Open the README screenshot and explain the historical source cutoff.
2. In Forecast studio, change the model and horizon; explain the two interval levels.
3. Open Backtest explorer and show what the model could see at a historical origin.
4. In Model comparison, discuss why Random Forest lost and why coverage needs interval width.
5. Show a leakage-prevention test and the source metadata hash.

Do not describe this as a clinical predictor, claim deployment that has not occurred, or claim an improvement over baselines that the measured results do not support.

