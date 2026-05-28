"""Analytics helpers for sprint allocation reporting."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import config


MAPPING_COLUMNS = ["mapping_level", "jira_key", "summary", "allocation_category", "notes", "last_updated"]
MAPPING_LEVELS = ["Ticket", "Epic"]
VALID_ALLOCATION_CATEGORIES = [*config.ALLOCATION_CATEGORIES, "Unmapped"]
TARGET_COLUMNS = ["allocation_category", "target_percentage"]


def load_allocation_mapping(path: Path = config.ALLOCATION_MAPPING_PATH) -> pd.DataFrame:
    if path.exists():
        mapping = pd.read_csv(path)
    else:
        mapping = pd.DataFrame(columns=MAPPING_COLUMNS)

    mapping = _migrate_legacy_mapping(mapping)
    for column in MAPPING_COLUMNS:
        if column not in mapping.columns:
            mapping[column] = ""
    return _clean_mapping(mapping)


def save_allocation_mapping(mapping: pd.DataFrame, path: Path = config.ALLOCATION_MAPPING_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mapping = _clean_mapping(mapping)
    mapping = mapping.drop_duplicates(["mapping_level", "jira_key"], keep="last")
    mapping.to_csv(path, index=False)


def load_sprint_targets(path: Path = config.SPRINT_TARGETS_PATH) -> pd.DataFrame:
    if path.exists():
        targets = pd.read_csv(path)
    else:
        targets = pd.DataFrame(
            {
                "allocation_category": list(config.ALLOCATION_TARGETS.keys()),
                "target_percentage": list(config.ALLOCATION_TARGETS.values()),
            }
        )

    targets["target_percentage"] = pd.to_numeric(targets["target_percentage"], errors="coerce").fillna(0)
    return targets[TARGET_COLUMNS]


def apply_allocation_mapping(issues: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Apply ticket mappings first, then epic mappings, otherwise mark as Unmapped."""
    issues = ensure_issue_schema(issues).copy()
    mapping = _clean_mapping(mapping)

    epic_map = _mapping_dict(mapping, "Epic")
    ticket_map = _mapping_dict(mapping, "Ticket")

    ticket_keys = issues["ticket_key"].fillna("").astype(str)
    epic_keys = issues["epic_key"].fillna("").astype(str)
    issues["allocation_category"] = ticket_keys.map(ticket_map)
    issues["allocation_category"] = issues["allocation_category"].fillna(epic_keys.map(epic_map))
    issues["allocation_category"] = issues["allocation_category"].fillna("Unmapped")

    issues.loc[
        ~issues["allocation_category"].isin(VALID_ALLOCATION_CATEGORIES),
        "allocation_category",
    ] = "Unmapped"
    issues["mapped_allocation_category"] = issues["allocation_category"]

    issues["story_points"] = pd.to_numeric(issues["story_points"], errors="coerce").fillna(0)
    return issues


def summarize_allocations(
    issues: pd.DataFrame,
    targets: pd.DataFrame,
    sprint_capacity: int = config.SPRINT_CAPACITY_POINTS,
) -> pd.DataFrame:
    grouped = (
        issues.groupby("mapped_allocation_category", dropna=False)["story_points"]
        .sum()
        .rename("actual_points")
        .reset_index()
        .rename(columns={"mapped_allocation_category": "allocation_category"})
    )

    target_categories = pd.DataFrame({"allocation_category": config.ALLOCATION_CATEGORIES})
    summary = target_categories.merge(grouped, how="left", on="allocation_category")
    summary["actual_points"] = summary["actual_points"].fillna(0)

    targets = targets.copy()
    targets["target_percentage"] = pd.to_numeric(targets["target_percentage"], errors="coerce").fillna(0)
    summary = summary.merge(targets, how="left", on="allocation_category")
    summary["target_percentage"] = summary["target_percentage"].fillna(0)
    summary["target_points"] = summary["target_percentage"] / 100 * sprint_capacity
    summary["actual_percentage"] = summary["actual_points"] / sprint_capacity * 100
    summary["variance_percentage"] = summary["actual_percentage"] - summary["target_percentage"]
    summary["variance_points"] = summary["actual_points"] - summary["target_points"]
    summary["status"] = summary["variance_percentage"].apply(classify_variance)

    return summary.sort_values("allocation_category").reset_index(drop=True)


def epic_rollup(issues: pd.DataFrame) -> pd.DataFrame:
    return (
        issues.groupby(["epic_key", "epic_name", "mapped_allocation_category"], dropna=False)
        .agg(issue_count=("issue_key", "count"), story_points=("story_points", "sum"))
        .reset_index()
        .sort_values(["mapped_allocation_category", "story_points"], ascending=[True, False])
    )


def issue_editor_rows(issues: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "ticket_key",
        "issue_type",
        "summary",
        "epic_key",
        "epic_name",
        "status",
        "assignee",
        "story_points",
        "allocation_category",
        "notes",
    ]
    return ensure_issue_schema(issues)[columns]


def classify_variance(variance_percentage: float) -> str:
    absolute_variance = abs(variance_percentage)
    if absolute_variance <= 2:
        return "On target"
    if variance_percentage > 0:
        return "Over target"
    return "Under target"


def ensure_issue_schema(issues: pd.DataFrame) -> pd.DataFrame:
    expected_columns = {
        "sprint_name": "",
        "sprint": "",
        "ticket_key": "",
        "issue_key": "",
        "issue_type": "",
        "summary": "",
        "epic_key": "",
        "epic_name": "",
        "status": "",
        "assignee": "",
        "story_points": 0,
        "allocation_category": "Unmapped",
        "mapped_allocation_category": "Unmapped",
        "notes": "",
    }
    issues = issues.copy()
    for column, default in expected_columns.items():
        if column not in issues.columns:
            issues[column] = default
    issues["ticket_key"] = issues["ticket_key"].fillna("")
    issues.loc[issues["ticket_key"] == "", "ticket_key"] = issues["issue_key"]
    issues["issue_key"] = issues["issue_key"].fillna("")
    issues.loc[issues["issue_key"] == "", "issue_key"] = issues["ticket_key"]
    return issues


def _mapping_dict(mapping: pd.DataFrame, mapping_level: str) -> dict[str, str]:
    filtered = mapping[mapping["mapping_level"] == mapping_level]
    filtered = filtered[filtered["allocation_category"].isin(VALID_ALLOCATION_CATEGORIES)]
    return dict(zip(filtered["jira_key"], filtered["allocation_category"], strict=False))


def _clean_mapping(mapping: pd.DataFrame) -> pd.DataFrame:
    mapping = mapping.copy().fillna("")
    for column in MAPPING_COLUMNS:
        if column not in mapping.columns:
            mapping[column] = ""
    mapping["mapping_level"] = mapping["mapping_level"].map(_normalize_mapping_level)
    mapping["allocation_category"] = mapping["allocation_category"].map(_normalize_allocation_category)
    mapping["jira_key"] = mapping["jira_key"].astype(str).str.strip()
    mapping = mapping[mapping["mapping_level"].isin(MAPPING_LEVELS)]
    mapping = mapping[mapping["jira_key"] != ""]
    return mapping[MAPPING_COLUMNS].fillna("")


def _migrate_legacy_mapping(mapping: pd.DataFrame) -> pd.DataFrame:
    if {"mapping_type", "mapping_key"}.issubset(mapping.columns) and "mapping_level" not in mapping.columns:
        migrated = pd.DataFrame(
            {
                "mapping_level": mapping["mapping_type"].map(_normalize_mapping_level),
                "jira_key": mapping["mapping_key"],
                "summary": "",
                "allocation_category": mapping.get("allocation_category", ""),
                "notes": mapping.get("notes", ""),
                "last_updated": "",
            }
        )
        return migrated
    return mapping


def _normalize_mapping_level(value: object) -> str:
    text = str(value).strip().lower()
    if text in {"ticket", "issue"}:
        return "Ticket"
    if text == "epic":
        return "Epic"
    return str(value).strip()


def _normalize_allocation_category(value: object) -> str:
    text = str(value).strip()
    return text if text in VALID_ALLOCATION_CATEGORIES else "Unmapped"

