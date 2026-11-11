"""Generate and execute a compact, dependency-light exploration notebook."""

import contextlib
import io
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def main():
    notebook = nbformat.v4.new_notebook()
    notebook.metadata.update(
        {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        }
    )
    notebook.cells = [
        nbformat.v4.new_markdown_cell(
            "# Casecast · exploratory analysis\n\n"
            "Real CDC weekly reported COVID-19 cases in California. "
            "This executed notebook inspects the cached snapshot and completed experiment. "
            "Modeling logic lives in `src/`; use `disease-forecast run` to reproduce forecasts. "
            "No synthetic data or clinical predictions are used."
        ),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport json\nimport pandas as pd\n"
            "from disease_forecasting.data import load_data\n"
            "root = Path.cwd()\n"
            "if not (root / 'configs').exists():\n    root = root.parent\n"
            "data = load_data(root)\n"
            "print(f'Weeks: {len(data)}; start: {data.index.min().date()}; end: {data.index.max().date()}')\n"
            "print(data.head().to_string())"
        ),
        nbformat.v4.new_markdown_cell(
            "## Integrity and reporting distribution\n\n"
            "Missing reports must not become zeros. The validator rejects missing or duplicate "
            "weeks, negative counts, non-integer counts, unexpected geography, and incomplete periods. "
            "The large peaks below are retained. Changes in reported cases can reflect both "
            "transmission and changes in testing/reporting."
        ),
        nbformat.v4.new_code_cell(
            "print('Missing values:', int(data.cases.isna().sum()))\n"
            "print('Source-reported zero weeks:', int(data.cases.eq(0).sum()))\n"
            "print('Peak week:', data.cases.idxmax().date(), 'cases:', int(data.cases.max()))\n"
            "print(data.groupby(data.index.year).cases.agg(['count', 'mean', 'median', 'max']).round(1).to_string())"
        ),
        nbformat.v4.new_markdown_cell(
            "## Seasonality is a hypothesis, not a guarantee\n\n"
            "Lag correlations below summarize the entire descriptive series, not a model-selection "
            "procedure. Only about three annual cycles are available; COVID waves and reporting "
            "changes do not imply a stable annual seasonal pattern."
        ),
        nbformat.v4.new_code_cell(
            "for lag in [1, 2, 4, 12, 52]:\n"
            "    print(f'Lag {lag:2d} weeks: correlation {data.cases.autocorr(lag):.3f}')"
        ),
        nbformat.v4.new_markdown_cell(
            "## Honest held-out comparison\n\n"
            "Model choice uses validation only. Calibration errors supply interval radii; "
            "final test errors are never used to tune parameters or intervals. "
            "All candidates share origins and horizons. This is a retrospective revised-data "
            "evaluation, not a reconstruction of real-time data vintages."
        ),
        nbformat.v4.new_code_cell(
            "metadata = json.loads((root / 'reports/run_metadata.json').read_text())\n"
            "scores = pd.read_csv(root / 'reports/test_metrics.csv')\n"
            "print('Validation-selected model:', metadata['selected_model'])\n"
            "print(scores[['model', 'horizon', 'n', 'mae', 'rmse', 'coverage_95', 'width_95']].round(2).to_string(index=False))"
        ),
        nbformat.v4.new_markdown_cell(
            "## Interpretation\n\n"
            "The naive baseline has the lowest test MAE at every horizon. More complex models "
            "did not improve generalization here. High interval coverage must be read alongside "
            "wide intervals and small, dependent test samples. Random Forest's longer-horizon "
            "errors show how unstable lag relationships can be across epidemic regimes. "
            "See [interactive historical chart](../reports/figures/historical_cases.html) and "
            "[dashboard screenshot](../reports/figures/dashboard.png).\n\n"
            "**Not a diagnosis:** aggregate state case counts contain no individual symptoms, "
            "examinations, or test results. They cannot establish whether any person has a disease."
        ),
    ]
    namespace = {"__name__": "__main__"}
    execution = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        execution += 1
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(cell.source, "notebook-cell", "exec"), namespace)
        cell.execution_count = execution
        cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text=output.getvalue())]
    nbformat.write(notebook, ROOT / "notebooks/01_exploration.ipynb")
    print("Exploration notebook executed and saved.")


if __name__ == "__main__":
    main()
