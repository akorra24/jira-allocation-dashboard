"""Shared visual styling for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st


LOOKER_COLORS = {
    "blue": "#1a73e8",
    "green": "#188038",
    "red": "#d93025",
    "yellow": "#f9ab00",
    "gray": "#80868b",
    "light_gray": "#f1f3f4",
    "light_blue": "#e8f0fe",
    "light_yellow": "#fef7e0",
    "light_red": "#fce8e6",
    "light_green": "#e6f4ea",
    "text": "#202124",
    "muted": "#5f6368",
    "border": "#dadce0",
    "surface": "#ffffff",
    "background": "#ffffff",
    "section": "#f1f3f4",
}


PLOTLY_TEMPLATE = {
    "layout": {
        "font": {"family": "Arial, sans-serif", "color": LOOKER_COLORS["text"]},
        "paper_bgcolor": LOOKER_COLORS["surface"],
        "plot_bgcolor": LOOKER_COLORS["surface"],
        "colorway": [
            LOOKER_COLORS["blue"],
            LOOKER_COLORS["green"],
            LOOKER_COLORS["yellow"],
            LOOKER_COLORS["red"],
            "#9334e6",
            "#12b5cb",
        ],
        "margin": {"l": 40, "r": 20, "t": 50, "b": 40},
    }
}


def apply_page_styles() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {LOOKER_COLORS["background"]};
        }}
        [data-testid="stHeader"] {{
            background: rgba(255, 255, 255, 0.9);
        }}
        section[data-testid="stSidebar"] {{
            background: #f8f9fa;
            border-right: 1px solid {LOOKER_COLORS["border"]};
        }}
        .dashboard-title {{
            color: {LOOKER_COLORS["text"]};
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0;
        }}
        .dashboard-subtitle {{
            color: {LOOKER_COLORS["muted"]};
            margin-top: 0.2rem;
            margin-bottom: 1.5rem;
        }}
        div[data-testid="metric-container"] {{
            background: {LOOKER_COLORS["surface"]};
            border: 1px solid {LOOKER_COLORS["border"]};
            border-radius: 6px;
            padding: 1rem;
            box-shadow: none;
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}
        .looker-section {{
            background: {LOOKER_COLORS["section"]};
            border: 1px solid {LOOKER_COLORS["border"]};
            border-radius: 4px;
            color: {LOOKER_COLORS["text"]};
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            margin: 1.25rem 0 0.75rem;
            padding: 0.65rem 0.85rem;
        }}
        .kpi-card {{
            background: {LOOKER_COLORS["surface"]};
            border: 1px solid {LOOKER_COLORS["border"]};
            border-radius: 6px;
            min-height: 96px;
            padding: 0.8rem 0.9rem;
        }}
        .kpi-label {{
            color: {LOOKER_COLORS["muted"]};
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}
        .kpi-value {{
            color: {LOOKER_COLORS["text"]};
            font-size: 1.45rem;
            font-weight: 700;
            margin-top: 0.35rem;
        }}
        .kpi-delta {{
            color: {LOOKER_COLORS["muted"]};
            font-size: 0.82rem;
            margin-top: 0.2rem;
        }}
        .status-pill {{
            border-radius: 999px;
            color: #ffffff;
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            min-width: 74px;
            padding: 0.2rem 0.55rem;
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_color(value: object, metric_type: str) -> str:
    """Return a muted Looker-style color for a status or numeric metric."""
    if metric_type == "capacity":
        return capacity_color(_to_float(value))
    if metric_type == "variance":
        return variance_color(_to_float(value))

    normalized = str(value).lower()
    if normalized in {"healthy", "on target"}:
        return LOOKER_COLORS["green"]
    if normalized == "watch":
        return LOOKER_COLORS["yellow"]
    if normalized in {"over target", "over capacity", "over"}:
        return LOOKER_COLORS["red"]
    if normalized == "under target":
        return LOOKER_COLORS["gray"]
    return LOOKER_COLORS["gray"]


def capacity_color(capacity_percent: object) -> str:
    """Capacity usage color: low usage neutral, partial yellow, at/over capacity red."""
    value = _to_float(capacity_percent)
    if pd.isna(value) or value < 50:
        return LOOKER_COLORS["light_gray"]
    if value < 100:
        return LOOKER_COLORS["yellow"]
    return LOOKER_COLORS["red"]


def variance_color(variance_percent: object) -> str:
    """Variance color based on percentage-point difference from target."""
    value = _to_float(variance_percent)
    if pd.isna(value):
        return LOOKER_COLORS["gray"]
    if abs(value) <= 5:
        return LOOKER_COLORS["green"]
    if 5 < value <= 15:
        return LOOKER_COLORS["yellow"]
    if value > 15:
        return LOOKER_COLORS["red"]
    if value < -10:
        return LOOKER_COLORS["light_blue"]
    return LOOKER_COLORS["gray"]


def format_percent(value: object) -> str:
    """Format percentages as whole percents with signs for variances."""
    numeric = _to_float(value)
    if pd.isna(numeric):
        return "-"
    if numeric > 0:
        return f"+{numeric:.0f}%"
    return f"{numeric:.0f}%"


def format_points(value: object) -> str:
    """Format story points with at most one decimal and signed negatives/positives."""
    numeric = _to_float(value)
    if pd.isna(numeric):
        return "-"
    formatted = f"{numeric:+.1f}" if numeric < 0 else f"{numeric:.1f}"
    if formatted.endswith(".0"):
        formatted = formatted[:-2]
    return formatted


def _to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")

