"""Configuration for the Jira allocation dashboard."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
OUTPUTS_DIR = APP_DIR / "outputs"

load_dotenv(APP_DIR / ".env")

REQUIRED_JIRA_ENV_VARS = [
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_PROJECT_KEY",
]

SPRINT_CAPACITY_POINTS = 55

ALLOCATION_TARGETS = {
    "Product/BPL": 45,
    "Product/Non-BPL": 0,
    "ETO System Feature": 10,
    "Marketing": 35,
    "ETO System Maintenance": 5,
    "Security": 5,
}

ALLOCATION_CATEGORIES = list(ALLOCATION_TARGETS.keys())

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")
JIRA_BOARD_ID = os.getenv("JIRA_BOARD_ID", "")
JIRA_DEFAULT_SPRINT = os.getenv("JIRA_DEFAULT_SPRINT", "")
JIRA_VERIFY_SSL = os.getenv("JIRA_VERIFY_SSL", "true").lower() not in {"0", "false", "no"}
STORY_POINTS_FIELD = os.getenv("STORY_POINTS_FIELD", "").strip()
SPRINT_FIELD = os.getenv("SPRINT_FIELD", "").strip()
EPIC_FIELD = os.getenv("EPIC_FIELD", "").strip()

ALLOCATION_MAPPING_PATH = DATA_DIR / "allocation_mapping.csv"
SPRINT_TARGETS_PATH = DATA_DIR / "sprint_targets.csv"
SPRINT_HISTORY_PATH = DATA_DIR / "sprint_history.csv"


def has_jira_credentials() -> bool:
    """Return whether all required Jira environment variables are configured."""
    return all(os.getenv(env_var, "").strip() for env_var in REQUIRED_JIRA_ENV_VARS)


def get_jira_auth() -> tuple[str, str]:
    """Return Jira basic-auth credentials for requests."""
    return (JIRA_EMAIL, JIRA_API_TOKEN)


def get_jira_base_url() -> str:
    """Return the Jira base URL without a trailing slash."""
    return JIRA_BASE_URL

