# Run or deploy Casecast

## Local

Use the README setup commands, then `streamlit run app/streamlit_app.py` from the repository root. Committed processed CSV files and reports support immediate exploration. Training is a separate CLI operation.

## Streamlit Community Cloud

1. Sign in at https://share.streamlit.io with the GitHub account that owns the repository.
2. Create an app from `abhinavgautam121/disease-trend-forecasting`, branch `main`.
3. Set the entry point to `app/streamlit_app.py` and choose Python 3.12 in advanced settings.
4. Deploy. The root `requirements.txt` installs the package and runtime dependencies.
5. Verify each tab, the backtest controls, charts, and CSV downloads. Keep the historical-data notice visible.

No API keys, secrets, database, or training job are needed for this demo. The application reads precomputed public-data artifacts. Do not add secrets to the repository. A live deployment URL is not provided or claimed until the deployment is actually completed and verified.

## Rebuild reports

`disease-forecast all` downloads the public CDC snapshot, validates and hashes it, runs the complete experiment, saves local forest artifacts, and refreshes CSV reports and HTML charts. Screenshots are separate browser-generated assets: run `python scripts/browser_smoke.py` against the running app to refresh them. The notebook can be re-executed in Jupyter or rebuilt with `python scripts/build_notebook.py`.

