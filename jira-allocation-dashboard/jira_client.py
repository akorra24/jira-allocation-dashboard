"""Small Jira API client with sample-data fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests

import config


SAMPLE_ISSUES = [
    {
        "sprint_name": "Sample Sprint 24.10",
        "issue_key": "ECOMM-101",
        "issue_type": "Story",
        "summary": "Launch cheeseburger bundle merchandising",
        "epic_key": "ECOMM-10",
        "epic_name": "BPL Cheeseburger Experience",
        "status": "Done",
        "assignee": "Avery Chen",
        "story_points": 13,
        "allocation_category": "Product/BPL",
    },
    {
        "sprint_name": "Sample Sprint 24.10",
        "issue_key": "ECOMM-102",
        "issue_type": "Story",
        "summary": "Build hero module for national burger campaign",
        "epic_key": "ECOMM-20",
        "epic_name": "Marketing Campaign Enablement",
        "status": "In Progress",
        "assignee": "Jordan Lee",
        "story_points": 8,
        "allocation_category": "Marketing",
    },
    {
        "sprint_name": "Sample Sprint 24.10",
        "issue_key": "ECOMM-103",
        "issue_type": "Task",
        "summary": "Refactor pricing service cache invalidation",
        "epic_key": "ECOMM-30",
        "epic_name": "Commerce Platform Features",
        "status": "In Review",
        "assignee": "Sam Rivera",
        "story_points": 5,
        "allocation_category": "ETO System Feature",
    },
    {
        "sprint_name": "Sample Sprint 24.10",
        "issue_key": "ECOMM-104",
        "issue_type": "Bug",
        "summary": "Patch dependency vulnerability in checkout widget",
        "epic_key": "ECOMM-40",
        "epic_name": "Security Remediation",
        "status": "Done",
        "assignee": "Priya Patel",
        "story_points": 3,
        "allocation_category": "Security",
    },
    {
        "sprint_name": "Sample Sprint 24.10",
        "issue_key": "ECOMM-105",
        "issue_type": "Task",
        "summary": "Update burger image ingestion runbook",
        "epic_key": "ECOMM-50",
        "epic_name": "Operational Maintenance",
        "status": "To Do",
        "assignee": "Morgan Diaz",
        "story_points": 2,
        "allocation_category": "ETO System Maintenance",
    },
    {
        "sprint_name": "Sample Sprint 24.10",
        "issue_key": "ECOMM-106",
        "issue_type": "Story",
        "summary": "Add reusable PDP badge component",
        "epic_key": "ECOMM-10",
        "epic_name": "BPL Cheeseburger Experience",
        "status": "Done",
        "assignee": "Avery Chen",
        "story_points": 8,
        "allocation_category": "Product/BPL",
    },
]


@dataclass(frozen=True)
class JiraSettings:
    """Connection details loaded from environment variables."""

    base_url: str = config.JIRA_BASE_URL
    email: str = config.JIRA_EMAIL
    api_token: str = config.JIRA_API_TOKEN
    project_key: str = config.JIRA_PROJECT_KEY
    verify_ssl: bool = config.JIRA_VERIFY_SSL

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.email and self.api_token)


class JiraClient:
    """Thin wrapper around Jira's search endpoint."""

    def __init__(self, settings: JiraSettings | None = None) -> None:
        self.settings = settings or JiraSettings()

    def fetch_issues_for_sprint(self, sprint_name: str | None = None) -> pd.DataFrame:
        """Return sprint issues from Jira, or sample issues when Jira is not configured."""
        if not self.settings.is_configured:
            return sample_issues(sprint_name)

        issues = self._search_issues(sprint_name)
        if not issues:
            return sample_issues(sprint_name)

        return pd.DataFrame([self._normalize_issue(issue, sprint_name) for issue in issues])

    def _search_issues(self, sprint_name: str | None) -> list[dict[str, Any]]:
        fields = [
            "summary",
            "issuetype",
            "status",
            "assignee",
            "customfield_10016",
            "parent",
            "sprint",
        ]
        jql_parts = []
        if self.settings.project_key:
            jql_parts.append(f"project = {self.settings.project_key}")
        if sprint_name:
            jql_parts.append(f'Sprint = "{sprint_name}"')

        jql = " AND ".join(jql_parts) if jql_parts else "ORDER BY updated DESC"
        url = f"{self.settings.base_url}/rest/api/3/search"
        auth = (self.settings.email, self.settings.api_token)

        collected: list[dict[str, Any]] = []
        start_at = 0
        page_size = 100

        while True:
            response = requests.get(
                url,
                auth=auth,
                params={
                    "jql": jql,
                    "fields": ",".join(fields),
                    "startAt": start_at,
                    "maxResults": page_size,
                },
                timeout=30,
                verify=self.settings.verify_ssl,
            )
            response.raise_for_status()
            payload = response.json()
            batch = payload.get("issues", [])
            collected.extend(batch)

            if start_at + len(batch) >= payload.get("total", 0) or not batch:
                break
            start_at += len(batch)

        return collected

    @staticmethod
    def _normalize_issue(issue: dict[str, Any], sprint_name: str | None) -> dict[str, Any]:
        fields = issue.get("fields", {})
        parent = fields.get("parent") or {}
        parent_fields = parent.get("fields", {})
        assignee = fields.get("assignee") or {}

        return {
            "sprint_name": sprint_name or "",
            "issue_key": issue.get("key", ""),
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "summary": fields.get("summary", ""),
            "epic_key": parent.get("key", ""),
            "epic_name": parent_fields.get("summary", ""),
            "status": (fields.get("status") or {}).get("name", ""),
            "assignee": assignee.get("displayName", "Unassigned"),
            "story_points": fields.get("customfield_10016") or 0,
            "allocation_category": "",
        }


def sample_issues(sprint_name: str | None = None) -> pd.DataFrame:
    """Return bundled sample issues so the app is useful before Jira setup."""
    data = [issue.copy() for issue in SAMPLE_ISSUES]
    if sprint_name:
        for issue in data:
            issue["sprint_name"] = sprint_name
    return pd.DataFrame(data)

