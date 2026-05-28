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


def calculate_allocation_summary(issues_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate target, actual, and variance metrics by allocation category."""
    issues = ensure_issue_schema(issues_df)
    issues["story_points"] = pd.to_numeric(issues["story_points"], errors="coerce").fillna(0)
    issues["allocation_category"] = issues["allocation_category"].fillna("Unmapped")
    issues.loc[
        ~issues["allocation_category"].isin(VALID_ALLOCATION_CATEGORIES),
        "allocation_category",
    ] = "Unmapped"

    grouped = (
        issues.groupby("allocation_category", dropna=False)
        .agg(
            actual_story_points=("story_points", "sum"),
            ticket_count=("ticket_key", "count"),
        )
        .reset_index()
    )

    target_rows = pd.DataFrame(
        {
            "allocation_category": config.ALLOCATION_CATEGORIES,
            "target_percent": [config.ALLOCATION_TARGETS[category] for category in config.ALLOCATION_CATEGORIES],
        }
    )
    summary = target_rows.merge(grouped, how="left", on="allocation_category")
    summary["actual_story_points"] = summary["actual_story_points"].fillna(0)
    summary["ticket_count"] = summary["ticket_count"].fillna(0).astype(int)
    summary["target_story_points"] = summary["target_percent"] / 100 * config.SPRINT_CAPACITY_POINTS
    summary["actual_percent_of_capacity"] = (
        summary["actual_story_points"] / config.SPRINT_CAPACITY_POINTS * 100
    )
    summary["variance_percent"] = summary["actual_percent_of_capacity"] - summary["target_percent"]
    summary["variance_story_points"] = summary["actual_story_points"] - summary["target_story_points"]

    unmapped = grouped[grouped["allocation_category"] == "Unmapped"]
    if not unmapped.empty:
        unmapped_row = unmapped.iloc[0]
        summary = pd.concat(
            [
                summary,
                pd.DataFrame(
                    [
                        {
                            "allocation_category": "Unmapped",
                            "target_percent": 0,
                            "target_story_points": 0,
                            "actual_story_points": unmapped_row["actual_story_points"],
                            "actual_percent_of_capacity": (
                                unmapped_row["actual_story_points"] / config.SPRINT_CAPACITY_POINTS * 100
                            ),
                            "variance_percent": pd.NA,
                            "variance_story_points": pd.NA,
                            "ticket_count": int(unmapped_row["ticket_count"]),
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return summary[
        [
            "allocation_category",
            "target_percent",
            "target_story_points",
            "actual_story_points",
            "actual_percent_of_capacity",
            "variance_percent",
            "variance_story_points",
            "ticket_count",
        ]
    ]


def calculate_total_capacity_usage(issues_df: pd.DataFrame) -> dict[str, float]:
    """Calculate total sprint point usage against the fixed sprint capacity."""
    issues = ensure_issue_schema(issues_df)
    total_story_points = pd.to_numeric(issues["story_points"], errors="coerce").fillna(0).sum()
    sprint_capacity_points = config.SPRINT_CAPACITY_POINTS
    total_capacity_percent = total_story_points / sprint_capacity_points * 100
    over_under_capacity_story_points = total_story_points - sprint_capacity_points
    over_under_capacity_percent = total_capacity_percent - 100

    return {
        "total_story_points": float(total_story_points),
        "sprint_capacity_points": float(sprint_capacity_points),
        "total_capacity_percent": float(total_capacity_percent),
        "over_under_capacity_story_points": float(over_under_capacity_story_points),
        "over_under_capacity_percent": float(over_under_capacity_percent),
    }


def calculate_sprint_health(summary_df: pd.DataFrame) -> pd.DataFrame:
    """Add allocation health status by category using variance percentage thresholds."""
    summary = summary_df.copy()
    summary["health_status"] = summary.apply(_health_status, axis=1)
    return summary


def summarize_allocations(
    issues: pd.DataFrame,
    targets: pd.DataFrame,
    sprint_capacity: int = config.SPRINT_CAPACITY_POINTS,
) -> pd.DataFrame:
    del targets, sprint_capacity
    summary = calculate_sprint_health(calculate_allocation_summary(issues))
    summary = summary.rename(
        columns={
            "actual_story_points": "actual_points",
            "target_story_points": "target_points",
            "target_percent": "target_percentage",
            "actual_percent_of_capacity": "actual_percentage",
            "variance_percent": "variance_percentage",
            "variance_story_points": "variance_points",
            "health_status": "status",
        }
    )

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
    if pd.isna(variance_percentage):
        return "unmapped"
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


def _health_status(row: pd.Series) -> str:
    if row.get("allocation_category") == "Unmapped" or pd.isna(row.get("variance_percent")):
        return "unmapped"

    variance = float(row["variance_percent"])
    if abs(variance) <= 5:
        return "healthy"
    if 5 < variance <= 15:
        return "watch"
    if variance > 15:
        return "over target"
    if variance < -10:
        return "under target"
    return "watch"

