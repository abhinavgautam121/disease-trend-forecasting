"""Shared interactive charts used by reports and the application."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

TEAL = "#087F8C"
NAVY = "#223B53"
ORANGE = "#BD5D26"


def style(figure: go.Figure, title: str = "") -> go.Figure:
    figure.update_layout(
        title=title,
        template="plotly_white",
        font=dict(family="Arial", color=NAVY, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=55 if title else 20, b=20),
        height=430,
        legend=dict(orientation="h", y=1.12),
        hovermode="x unified",
        yaxis_title="Reported cases / week",
        xaxis_title="Week ending (Wednesday)",
    )
    figure.update_yaxes(gridcolor="#E4EAF0", rangemode="tozero")
    return figure


def forecast_chart(history: pd.DataFrame, predictions: pd.DataFrame, origin=None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=history.index, y=history.cases, name="Observed cases", line=dict(color=NAVY, width=2)
        )
    )
    rows = predictions.sort_values("target_date")
    for level, color in [(95, "rgba(8,127,140,0.10)"), (80, "rgba(8,127,140,0.22)")]:
        fig.add_trace(
            go.Scatter(
                x=rows.target_date,
                y=rows[f"upper_{level}"],
                mode="lines",
                line_width=0,
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=rows.target_date,
                y=rows[f"lower_{level}"],
                fill="tonexty",
                fillcolor=color,
                mode="lines",
                line_width=0,
                name=f"{level}% prediction interval",
                hoverinfo="skip",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=rows.target_date,
            y=rows.prediction,
            name="Forecast",
            mode="lines+markers",
            line=dict(color=TEAL, width=3),
        )
    )
    if origin is not None:
        fig.add_vline(x=pd.Timestamp(origin).timestamp() * 1000, line_dash="dot", line_color=ORANGE)
    return style(fig)


def comparison_chart(scores: pd.DataFrame, metric="mae") -> go.Figure:
    fig = go.Figure()
    colors = [NAVY, "#668297", ORANGE, TEAL]
    for color, (model, group) in zip(colors, scores.groupby("model", sort=True)):
        fig.add_bar(
            x=[f"{h}-week" for h in group.horizon], y=group[metric], name=model, marker_color=color
        )
    style(fig)
    fig.update_layout(barmode="group", yaxis_title=metric.upper(), xaxis_title="Forecast horizon")
    return fig


def export_figures(root: Path, data, test, latest, scores, selected):
    figures = root / "reports/figures"
    figures.mkdir(parents=True, exist_ok=True)
    selected_latest = latest[latest.model == selected]
    chart = forecast_chart(data.tail(52), selected_latest, data.index[-1])
    chart.update_layout(title=f"{selected} · historical forecast from May 10, 2023")
    chart.write_html(figures / "forecast.html", include_plotlyjs="cdn")
    comparison_chart(scores).write_html(figures / "model_comparison.html", include_plotlyjs="cdn")
    full = style(
        go.Figure(go.Scatter(x=data.index, y=data.cases, line_color=NAVY)),
        "California · CDC weekly reported COVID-19 cases",
    )
    full.write_html(figures / "historical_cases.html", include_plotlyjs="cdn")
