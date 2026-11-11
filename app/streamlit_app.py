"""Casecast: a retrospective surveillance forecasting workbench."""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from disease_forecasting.visualization import (
    NAVY,
    TEAL,
    comparison_chart,
    forecast_chart,
    style,
)

ROOT = Path(__file__).resolve().parents[1]
NOTICE = (
    "These forecasts estimate population-level reported case trends using historical surveillance "
    "data. They do not diagnose disease, assess an individual’s health, or replace medical advice. "
    "Reporting delays, missing data, policy changes, and unexpected outbreaks can affect accuracy."
)
st.set_page_config(page_title="Casecast | Disease Trend Forecasting", page_icon="◈", layout="wide")
st.markdown(
    """
<style>
.stApp {background: #F5F7FA;}
.block-container {padding-top: 3.8rem; max-width: 1500px;}
h1,h2,h3 {letter-spacing: -.035em; color: #182C3F;}
h1 {font-size: 3.1rem !important; font-weight: 750 !important;}
[data-testid="stSidebar"] {background: white; border-right: 1px solid #E1E7ED;}
[data-testid="stMetric"] {background:white; border:1px solid #E1E7ED;
 border-radius: 12px; padding: 18px 20px; min-height:115px;}
[data-testid="stMetricLabel"] {color:#62768A; font-size: .82rem;}
[data-testid="stMetricValue"] {font-size:1.8rem; color:#182C3F;}
.eyebrow {font-size: .73rem; font-weight:700; letter-spacing:.16em; color:#087F8C;}
.subtitle {color:#607589; font-size:1.04rem; max-width:850px; line-height:1.65;}
.pill {display:inline-block; padding:5px 12px; border:1px solid #C5DDDF;
 border-radius:20px; font-size:.74rem; color:#087F8C; background:#EDF6F5; margin-right:6px;}
.note {padding:14px 18px; border-left:3px solid #BD5D26; background:#FFF8EE;
 color:#69533B; font-size:.85rem; line-height:1.6; border-radius:0 8px 8px 0;}
.brand {font-size:1.7rem; font-weight:750; color:#182C3F; letter-spacing:-.05em;}
.small {font-size:.8rem; color:#697E90; line-height:1.6;}
.section-note {font-size:.84rem;color:#607589;line-height:1.65;}
div[data-baseweb="tab-list"] {gap:26px; background:transparent;}
button[data-baseweb="tab"] {font-weight:600;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_artifacts():
    data = pd.read_csv(ROOT / "data/processed/weekly_cases.csv", parse_dates=["date"])
    data = data.set_index("date")
    latest = pd.read_csv(
        ROOT / "reports/latest_forecasts.csv", parse_dates=["origin", "target_date"]
    )
    test = pd.read_csv(ROOT / "reports/test_predictions.csv", parse_dates=["origin", "target_date"])
    scores = pd.read_csv(ROOT / "reports/test_metrics.csv")
    metadata = json.loads((ROOT / "reports/run_metadata.json").read_text())
    importance = pd.read_csv(ROOT / "reports/feature_importance.csv")
    return data, latest, test, scores, metadata, importance


try:
    data, latest, test, scores, metadata, importance = load_artifacts()
except (OSError, ValueError, KeyError) as error:
    st.error("Forecast artifacts are unavailable or invalid. Run `disease-forecast all` first.")
    st.code(str(error))
    st.stop()

selected = metadata["selected_model"]
with st.sidebar:
    st.markdown(
        '<div class="brand">◈ casecast<span style="color:#087F8C">.</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("DISEASE TREND FORECASTING")
    st.divider()
    st.markdown("**Analysis controls**")
    mode = st.radio("Forecast view", ["Archive forecast", "Backtest explorer"])
    models = ["Naive", "Seasonal naive", "Damped ETS", "Random Forest"]
    model = st.selectbox("Forecast model", models, index=models.index(selected))
    horizon = st.select_slider("Horizon (weeks ahead)", options=[1, 2, 4], value=4)
    history_weeks = st.selectbox("History window", [26, 52, 104, "All observations"], index=1)
    st.divider()
    st.markdown("**Study scope**")
    st.markdown("California, United States  \nCOVID-19 · weekly reported cases")
    st.caption("Confirmed and probable cases where reported. Counts are by reporting week.")
    st.markdown("**Source**")
    st.link_button("CDC public surveillance ↗", "https://data.cdc.gov/d/pwn4-m3yp")
    st.caption(f"{len(data)} observations · {metadata['data_start']} → {metadata['data_through']}")
    st.markdown(
        '<div class="small">A retrospective portfolio study.<br>'
        "No patient information or personal risk estimates.</div>",
        unsafe_allow_html=True,
    )

left, right = st.columns([5, 2])
with left:
    st.markdown(
        '<div class="eyebrow">PUBLIC HEALTH INTELLIGENCE / PROJECT B</div>', unsafe_allow_html=True
    )
    st.title("See the trend. Understand the uncertainty.")
    st.markdown(
        '<div class="subtitle">A reproducible forecasting study of California’s weekly '
        "COVID-19 reports. Compare four approaches, inspect historical forecasts, and "
        "see how often prediction intervals captured reality.</div>",
        unsafe_allow_html=True,
    )
with right:
    st.markdown(
        '<br><span class="pill">● REAL CDC DATA</span><span class="pill">HISTORICAL STUDY</span>',
        unsafe_allow_html=True,
    )
    st.caption(
        "DATA THROUGH MAY 10, 2023  \nWeekly case reporting ended in 2023. These are not current forecasts."
    )
st.write("")
st.markdown(
    f'<div class="note"><strong>Population trends, not a diagnosis.</strong> {NOTICE}</div>',
    unsafe_allow_html=True,
)
st.write("")

model_scores = scores[(scores.model == model) & (scores.horizon == horizon)].iloc[0]
cols = st.columns(4)
cols[0].metric(
    "LAST REPORTED WEEK",
    f"{data.cases.iloc[-1]:,}",
    help="Reported cases, not current infections",
)
cols[1].metric(
    f"{horizon}-WEEK TEST MAE",
    f"{model_scores.mae:,.0f}",
    help="Mean absolute error in weekly case counts; lower is better",
)
cols[2].metric(
    "95% TEST COVERAGE",
    f"{model_scores.coverage_95:.0%}",
    help="Observed coverage on held-out targets; compare with the nominal 95%",
)
cols[3].metric(
    "SELECTED ON VALIDATION",
    selected,
    help="Lowest mean validation MAE across 1-, 2-, and 4-week horizons",
)
st.write("")

forecast_tab, compare_tab, data_tab, method_tab = st.tabs(
    ["Forecast studio", "Model comparison", "Data observatory", "Method & limitations"]
)
with forecast_tab:
    st.subheader("A forecast is a range of possibilities")
    if mode == "Archive forecast":
        origin = data.index[-1]
        predictions = latest[(latest.model == model) & (latest.horizon <= horizon)].copy()
        st.caption(
            f"Historical projection from {origin:%b %d, %Y} · {model} · up to {horizon} weeks ahead"
        )
        history = data if isinstance(history_weeks, str) else data.tail(history_weeks)
    else:
        available = test[(test.model == model) & (test.horizon == horizon)].origin.drop_duplicates()
        chosen = st.select_slider(
            "Historical forecast origin",
            options=available.dt.strftime("%Y-%m-%d").tolist(),
            value=available.dt.strftime("%Y-%m-%d").iloc[-1],
        )
        origin = pd.Timestamp(chosen)
        predictions = test[
            (test.model == model) & (test.origin == origin) & (test.horizon <= horizon)
        ].copy()
        st.caption(
            "The model saw observations only through the dotted line. Observations to its right are held-out outcomes."
        )
        history = (
            data.loc[:origin]
            if isinstance(history_weeks, str)
            else data.loc[:origin].tail(history_weeks)
        )
        # Add held-out actuals to the chart, without making them available to the model.
    chart = forecast_chart(history, predictions, origin)
    if len(predictions) == 1:
        row = predictions.iloc[0]
        chart.update_traces(
            selector=dict(name="Forecast"),
            error_y=dict(
                type="data",
                symmetric=False,
                array=[row.upper_95 - row.prediction],
                arrayminus=[row.prediction - row.lower_95],
                color=TEAL,
                thickness=2,
                width=8,
            ),
        )
    if mode == "Backtest explorer":
        observed = data.loc[origin : predictions.target_date.max()]
        chart.add_trace(
            go.Scatter(
                x=observed.index,
                y=observed.cases,
                name="Held-out actuals",
                line=dict(color="#BD5D26", dash="dot", width=2),
            )
        )
    st.plotly_chart(chart, width="stretch")
    st.caption(
        "Shaded bands: 80% and 95% prediction intervals. Predictions are shown at weeks 1, 2, and 4; connecting lines are visual guides, not additional weekly predictions."
    )
    display = predictions[
        ["target_date", "horizon", "prediction", "lower_80", "upper_80", "lower_95", "upper_95"]
    ].copy()
    display["target_date"] = display.target_date.dt.strftime("%b %d, %Y")
    display.columns = [
        "Target week",
        "Weeks ahead",
        "Forecast",
        "80% lower",
        "80% upper",
        "95% lower",
        "95% upper",
    ]
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        column_config={
            name: st.column_config.NumberColumn(format="%,.0f") for name in display.columns[2:]
        },
    )
    st.download_button(
        "↓ Download this forecast",
        predictions.to_csv(index=False),
        file_name=f"casecast_{mode.replace(' ', '_').lower()}_{origin:%Y%m%d}.csv",
        mime="text/csv",
    )
    st.info(
        "Wide intervals are a finding: outbreak-driven changes and reporting shifts make precise case forecasts difficult. Nominal coverage is not a guarantee.",
        icon="ℹ️",
    )

with compare_tab:
    st.subheader("Do complex models earn their complexity?")
    st.caption(
        "Final test period · identical origins and targets for all models · selection uses validation only"
    )
    metric = st.radio("Error measure", ["MAE", "RMSE", "MASE"], horizontal=True)
    st.plotly_chart(comparison_chart(scores, metric.lower()), width="stretch")
    table = scores.copy()
    st.dataframe(table.round(3), hide_index=True, width="stretch")
    st.caption(
        "MAE and RMSE are in reported cases. MASE uses a 52-week seasonal difference scale calculated from each origin’s training history. Coverage columns are proportions; interval widths are case counts."
    )
    st.download_button(
        "↓ Download model metrics", scores.to_csv(index=False), "model_metrics.csv", "text/csv"
    )
    st.markdown("#### Prediction interval reliability")
    coverage = scores[scores.horizon == horizon]
    fig = go.Figure()
    for level, color in [(80, TEAL), (95, NAVY)]:
        fig.add_bar(
            x=coverage.model,
            y=coverage[f"coverage_{level}"] * 100,
            name=f"{level}% interval",
            marker_color=color,
        )
        fig.add_hline(y=level, line_dash="dot", line_color=color)
    style(fig)
    fig.update_layout(yaxis_title="Observed coverage (%)", xaxis_title="Model", barmode="group")
    fig.update_yaxes(range=[0, 105])
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Dotted lines show nominal 80% and 95% levels. Coverage uses a small, temporally dependent test sample; it is descriptive, not a statistical guarantee."
    )

with data_tab:
    st.subheader("The signal behind the models")
    st.caption("Source: CDC · variable: new_cases · California · week ending Wednesday")
    fig = style(
        go.Figure(
            go.Scatter(
                x=data.index,
                y=data.cases,
                line=dict(color=NAVY, width=2),
                fill="tozeroy",
                fillcolor="rgba(34,59,83,.07)",
            )
        )
    )
    st.plotly_chart(fig, width="stretch")
    a, b, c = st.columns(3)
    a.metric("REPORTING WEEKS", len(data))
    b.metric("MISSING WEEKS", "0")
    c.metric("PEAK WEEKLY REPORTED CASES", f"{data.cases.max():,}")
    st.markdown(
        "**Integrity policy:** missing reports are never converted to zero. Duplicate weeks, missing weeks, non-finite values, negative counts, and partial reporting periods stop the pipeline. Outbreak peaks are retained."
    )
    st.dataframe(data.reset_index(), hide_index=True, width="stretch", height=250)
    st.download_button(
        "↓ Download processed CDC series", data.to_csv(), "california_weekly_cases.csv", "text/csv"
    )
    st.caption(
        "No synthetic observations. Reported counts include probable cases where supplied by jurisdictions. They do not measure all infections or infection-onset dates."
    )

with method_tab:
    st.subheader("Built to be inspected")
    st.markdown("""
**1 · Chronological evaluation.** An initial training period is followed by 26 weeks for
validation, 39 weeks for interval calibration, and a final 26-week test period. All models
use identical weekly forecast origins. Origins whose 4-week targets cross a period boundary
are excluded. Each model is refitted using observations available at that origin.

**2 · Four approaches.** Last-observation naive; 52-week seasonal naive; damped additive
trend exponential smoothing on log(1 + cases); and direct Random Forest regressors for
1, 2, and 4 weeks ahead. Two forest configurations are compared only on validation data.

**3 · Honest uncertainty.** Separate rolling calibration errors produce model- and
horizon-specific absolute-error quantiles. Bands are frozen before testing and clipped
at zero. These are prediction intervals for future reported counts, not confidence intervals
for a model parameter. Serial dependence and distribution shifts can break calibration assumptions.

**4 · Frozen selection, evolving history.** Model selection and interval calibration never
use test errors. Later test-origin fits can use earlier observed test weeks, as in weekly
deployment. This is retrospective evaluation on a revised data extract, not a real-time
historical-vintage experiment.
""")
    st.json(metadata["periods"])
    st.markdown("#### What drives the Random Forest?")
    imp = (
        importance[importance.horizon == horizon]
        .nlargest(8, "importance")
        .sort_values("importance")
    )
    fig = go.Figure(go.Bar(x=imp.importance, y=imp.feature, orientation="h", marker_color=TEAL))
    style(fig)
    fig.update_layout(
        yaxis_title="Feature", xaxis_title="Impurity importance (final refit)", height=330
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Descriptive impurity importance from the full-data refit. Correlated lags share credit; importance is not causal evidence, a clinical explanation, or held-out feature validation."
    )
    st.markdown("""
#### Limits that matter
- Only 173 weekly observations and roughly 1.6 years of initial training: too short to establish stable annual seasonality.
- Testing access, home tests, variants, policy, and reporting practices change the relationship between reports and infections.
- Revised data may make retrospective results more optimistic than real-time forecasting.
- Random Forest cannot reliably extrapolate beyond the target values seen during training.
- Absolute-error intervals can become very wide after an outbreak and may fail during new surges.
- This archive ended in 2023; it cannot support a current public health forecast.

#### Why a forecast is not a diagnosis
The target is an aggregate weekly count for a state. The inputs contain no symptoms,
individual exposure history, examination, or diagnostic test results. A population trend
cannot determine whether a person has a disease. Clinical decisions require individual
assessment by qualified professionals.
""")
    st.caption(f"Snapshot SHA-256: {metadata['snapshot_sha256']}")

st.divider()
st.caption(
    "CASECAST / PROJECT B · Reproducible public-data research · CDC source attribution · Not for clinical use"
)
