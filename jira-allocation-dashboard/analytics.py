"""Analytics helpers for sprint allocation reporting."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import config


MAPPING_COLUMNS = ["mapping_type", "mapping_key", "allocation_category", "notes"]
TARGET_COLUMNS = ["allocation_category", "target_percentage"]


def load_allocation_mapping(path: Path = config.ALLOCATION_MAPPING_PATH) -> pd.DataFrame:
    if path.exists():
        mapping = pd.read_csv(path)
    else:
        mapping = pd.DataFrame(columns=MAPPING_COLUMNS)

    for column in MAPPING_COLUMNS:
        if column not in mapping.columns:
            mapping[column] = ""
    return mapping[MAPPING_COLUMNS].fillna("")


def save_allocation_mapping(mapping: pd.DataFrame, path: Path = config.ALLOCATION_MAPPING_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mapping = mapping[MAPPING_COLUMNS].drop_duplicates(["mapping_type", "mapping_key"], keep="last")
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
    """Apply epic-level mappings first, then issue-level overrides."""
    issues = ensure_issue_schema(issues).copy()
    mapping = mapping.fillna("")

    epic_map = _mapping_dict(mapping, "epic")
    issue_map = _mapping_dict(mapping, "issue")

    issues["mapped_allocation_category"] = issues["allocation_category"].fillna("")
    issues.loc[issues["mapped_allocation_category"] == "", "mapped_allocation_category"] = issues[
        "epic_key"
    ].map(epic_map)
    issues["mapped_allocation_category"] = issues["mapped_allocation_category"].fillna("")

    issue_assignments = issues["issue_key"].map(issue_map)
    issues.loc[issue_assignments.notna() & (issue_assignments != ""), "mapped_allocation_category"] = (
        issue_assignments
    )
    issues.loc[
        ~issues["mapped_allocation_category"].isin(config.ALLOCATION_CATEGORIES),
        "mapped_allocation_category",
    ] = "Unassigned"

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
        "issue_key",
        "issue_type",
        "summary",
        "epic_key",
        "epic_name",
        "status",
        "assignee",
        "story_points",
        "mapped_allocation_category",
    ]
    return ensure_issue_schema(issues)[columns]


def mappings_from_editor(edited_issues: pd.DataFrame, edited_epics: pd.DataFrame) -> pd.DataFrame:
    issue_rows = pd.DataFrame(
        {
            "mapping_type": "issue",
            "mapping_key": edited_issues["issue_key"],
            "allocation_category": edited_issues["mapped_allocation_category"],
            "notes": "",
        }
    )

    epic_rows = pd.DataFrame(
        {
            "mapping_type": "epic",
            "mapping_key": edited_epics["epic_key"],
            "allocation_category": edited_epics["mapped_allocation_category"],
            "notes": "",
        }
    )

    mapping = pd.concat([issue_rows, epic_rows], ignore_index=True)
    mapping = mapping[mapping["allocation_category"].isin(config.ALLOCATION_CATEGORIES)]
    mapping = mapping[mapping["mapping_key"].astype(str).str.len() > 0]
    return mapping[MAPPING_COLUMNS].drop_duplicates(["mapping_type", "mapping_key"], keep="last")


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
        "issue_key": "",
        "issue_type": "",
        "summary": "",
        "epic_key": "",
        "epic_name": "",
        "status": "",
        "assignee": "",
        "story_points": 0,
        "allocation_category": "",
        "mapped_allocation_category": "",
    }
    issues = issues.copy()
    for column, default in expected_columns.items():
        if column not in issues.columns:
            issues[column] = default
    return issues


def _mapping_dict(mapping: pd.DataFrame, mapping_type: str) -> dict[str, str]:
    filtered = mapping[mapping["mapping_type"].str.lower() == mapping_type]
    filtered = filtered[filtered["allocation_category"].isin(config.ALLOCATION_CATEGORIES)]
    return dict(zip(filtered["mapping_key"], filtered["allocation_category"], strict=False))

