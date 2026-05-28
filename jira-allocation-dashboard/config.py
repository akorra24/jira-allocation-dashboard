"""Configuration for the Jira allocation dashboard."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
OUTPUTS_DIR = APP_DIR / "outputs"

load_dotenv(APP_DIR / ".env")

SPRINT_CAPACITY_POINTS = 55

ALLOCATION_TARGETS = {
    "Product/BPL": 0.45,
    "Product/Non-BPL": 0.00,
    "ETO System Feature": 0.10,
    "Marketing": 0.35,
    "ETO System Maintenance": 0.05,
    "Security": 0.05,
}

ALLOCATION_CATEGORIES = list(ALLOCATION_TARGETS.keys())

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")
JIRA_BOARD_ID = os.getenv("JIRA_BOARD_ID", "")
JIRA_DEFAULT_SPRINT = os.getenv("JIRA_DEFAULT_SPRINT", "")
JIRA_VERIFY_SSL = os.getenv("JIRA_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}

ALLOCATION_MAPPING_PATH = DATA_DIR / "allocation_mapping.csv"
SPRINT_TARGETS_PATH = DATA_DIR / "sprint_targets.csv"

