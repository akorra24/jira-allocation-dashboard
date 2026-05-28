"""Shared visual styling for the Streamlit dashboard."""

from __future__ import annotations

import streamlit as st


LOOKER_COLORS = {
    "blue": "#1a73e8",
    "green": "#188038",
    "red": "#d93025",
    "yellow": "#fbbc04",
    "text": "#202124",
    "muted": "#5f6368",
    "border": "#dadce0",
    "surface": "#ffffff",
    "background": "#f8fafd",
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
            background: rgba(248, 250, 253, 0.9);
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
            border-radius: 14px;
            padding: 1rem;
            box-shadow: 0 1px 2px rgba(60, 64, 67, 0.15);
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

