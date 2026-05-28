"""Shared visual styling for the Streamlit dashboard."""

from __future__ import annotations

import streamlit as st


LOOKER_COLORS = {
    "blue": "#1a73e8",
    "green": "#188038",
    "red": "#d93025",
    "yellow": "#f9ab00",
    "gray": "#80868b",
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

