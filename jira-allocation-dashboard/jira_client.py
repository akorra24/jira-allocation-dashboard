"""Jira Cloud API client for sprint allocation reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests

import config


class JiraClientError(RuntimeError):
    """Raised when Jira returns an actionable API error."""


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

    base_url: str = config.get_jira_base_url()
    email: str = config.JIRA_EMAIL
    api_token: str = config.JIRA_API_TOKEN
    project_key: str = config.JIRA_PROJECT_KEY
    board_id: str = config.JIRA_BOARD_ID
    verify_ssl: bool = config.JIRA_VERIFY_SSL
    story_points_field: str = config.STORY_POINTS_FIELD
    sprint_field: str = config.SPRINT_FIELD
    epic_field: str = config.EPIC_FIELD

    @property
    def is_configured(self) -> bool:
        return config.has_jira_credentials()


class JiraClient:
    """Thin wrapper around Jira Cloud REST API endpoints."""

    def __init__(self, settings: JiraSettings | None = None) -> None:
        self.settings = settings or JiraSettings()
        self.session = requests.Session()
        if self.settings.email and self.settings.api_token:
            self.session.auth = (self.settings.email, self.settings.api_token)

    def test_connection(self) -> dict[str, Any]:
        """Call Jira's myself endpoint and return connection status details."""
        if not self.settings.is_configured:
            return {
                "success": False,
                "user": None,
                "error": "Jira credentials are not fully configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY.",
            }

        try:
            user = self._request_json("GET", "/rest/api/3/myself")
        except JiraClientError as exc:
            return {"success": False, "user": None, "error": str(exc)}

        return {
            "success": True,
            "user": {
                "account_id": user.get("accountId", ""),
                "display_name": user.get("displayName", ""),
                "email": user.get("emailAddress", ""),
                "active": user.get("active", None),
            },
            "error": None,
        }

    def get_fields(self) -> pd.DataFrame:
        """Return Jira fields to help identify custom Story Points, Sprint, Epic, and Allocation fields."""
        fields = self._request_json("GET", "/rest/api/3/field")
        rows = []
        for field in fields:
            schema = field.get("schema") or {}
            rows.append(
                {
                    "field_name": field.get("name", ""),
                    "id": field.get("id", ""),
                    "schema_type": schema.get("type", ""),
                    "custom": bool(field.get("custom", False)),
                }
            )
        return pd.DataFrame(rows).sort_values(["custom", "field_name"], ascending=[False, True])

    def search_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        max_results: int = 1000,
    ) -> list[dict[str, Any]]:
        """Search Jira issues with pagination and return normalized issue dictionaries."""
        if not self.settings.is_configured:
            return normalize_sample_issues(sample_issues())

        selected_fields = fields or self._default_issue_fields()
        collected: list[dict[str, Any]] = []
        start_at = 0
        page_size = min(100, max_results)

        while len(collected) < max_results:
            payload = self._request_json(
                "GET",
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "fields": ",".join(selected_fields),
                    "startAt": start_at,
                    "maxResults": min(page_size, max_results - len(collected)),
                },
            )
            batch = payload.get("issues", [])
            collected.extend(self.normalize_issue(issue) for issue in batch)

            if not batch or start_at + len(batch) >= payload.get("total", 0):
                break
            start_at += len(batch)

        return collected

    def get_issues_for_sprint(
        self,
        sprint_name_or_id: str,
        project_key: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return normalized, non-sub-task Jira issues for a project sprint."""
        if not self.settings.is_configured:
            return normalize_sample_issues(sample_issues(sprint_name_or_id))

        project = project_key or self.settings.project_key
        if not project:
            raise JiraClientError("JIRA_PROJECT_KEY is required to fetch sprint issues.")

        jql = (
            f"project = {project} "
            f'AND Sprint = "{_escape_jql_value(str(sprint_name_or_id))}" '
            "AND issuetype not in (Sub-task)"
        )
        return self.search_issues(jql, fields=self._default_issue_fields())

    def normalize_issue(self, issue: dict[str, Any]) -> dict[str, Any]:
        """Convert Jira issue JSON into a flat dict for dashboard use."""
        fields = issue.get("fields") or {}
        parent = self._extract_parent(fields)
        assignee = fields.get("assignee") or {}
        components = fields.get("components") or []
        labels = fields.get("labels") or []
        story_points = fields.get(self.settings.story_points_field) if self.settings.story_points_field else 0
        sprint = self._extract_sprint(fields)
        ticket_key = issue.get("key", "")

        normalized = {
            "ticket_key": ticket_key,
            "summary": fields.get("summary", ""),
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "status": (fields.get("status") or {}).get("name", ""),
            "assignee": assignee.get("displayName", "Unassigned"),
            "story_points": story_points or 0,
            "sprint": sprint,
            "epic_key": parent.get("key", ""),
            "epic_name": parent.get("name", ""),
            "labels": labels,
            "components": [component.get("name", "") for component in components if component.get("name")],
            "jira_url": f"{self.settings.base_url}/browse/{ticket_key}" if self.settings.base_url and ticket_key else "",
        }
        normalized["sprint_name"] = sprint
        normalized["issue_key"] = ticket_key
        normalized["allocation_category"] = ""
        return normalized

    def fetch_issues_for_sprint(self, sprint_name: str | None = None) -> pd.DataFrame:
        """Backward-compatible DataFrame wrapper used by the Streamlit app."""
        return pd.DataFrame(self.get_issues_for_sprint(sprint_name or config.JIRA_DEFAULT_SPRINT))

    def _default_issue_fields(self) -> list[str]:
        fields = [
            "summary",
            "issuetype",
            "status",
            "assignee",
            "parent",
            "labels",
            "components",
        ]
        for optional_field in [self.settings.story_points_field, self.settings.sprint_field, self.settings.epic_field]:
            if optional_field and optional_field not in fields:
                fields.append(optional_field)
        return fields

    def _extract_parent(self, fields: dict[str, Any]) -> dict[str, str]:
        parent = fields.get("parent") or {}
        parent_fields = parent.get("fields") or {}
        epic_value = fields.get(self.settings.epic_field) if self.settings.epic_field else None

        if isinstance(epic_value, dict):
            epic_fields = epic_value.get("fields") or {}
            return {
                "key": epic_value.get("key", parent.get("key", "")),
                "name": epic_fields.get("summary", parent_fields.get("summary", "")),
            }
        if isinstance(epic_value, str):
            return {"key": epic_value, "name": parent_fields.get("summary", "")}

        return {
            "key": parent.get("key", ""),
            "name": parent_fields.get("summary", ""),
        }

    def _extract_sprint(self, fields: dict[str, Any]) -> str:
        if not self.settings.sprint_field:
            return ""

        sprint_value = fields.get(self.settings.sprint_field)
        if isinstance(sprint_value, list):
            if not sprint_value:
                return ""
            latest_sprint = sprint_value[-1]
            if isinstance(latest_sprint, dict):
                return latest_sprint.get("name", "")
            return str(latest_sprint)
        if isinstance(sprint_value, dict):
            return sprint_value.get("name", "")
        return str(sprint_value or "")

    def _request_json(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self.settings.base_url:
            raise JiraClientError("JIRA_BASE_URL is not configured.")

        url = f"{self.settings.base_url}{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                params=params,
                timeout=30,
                verify=self.settings.verify_ssl,
                headers={"Accept": "application/json"},
            )
        except requests.RequestException as exc:
            raise JiraClientError(f"Could not connect to Jira: {exc}") from exc

        if response.status_code == 401:
            raise JiraClientError("Jira authentication failed. Check JIRA_EMAIL and JIRA_API_TOKEN.")
        if response.status_code == 403:
            raise JiraClientError("Jira permission denied. Confirm the user has access to this project, board, and fields.")
        if response.status_code == 400:
            raise JiraClientError(f"Jira rejected the request, likely due to bad JQL or field ids: {_response_message(response)}")
        if response.status_code >= 400:
            raise JiraClientError(f"Jira API request failed with HTTP {response.status_code}: {_response_message(response)}")

        try:
            return response.json()
        except ValueError as exc:
            raise JiraClientError("Jira returned a non-JSON response.") from exc


def sample_issues(sprint_name: str | None = None) -> pd.DataFrame:
    """Return bundled sample issues so the app is useful before Jira setup."""
    data = [issue.copy() for issue in SAMPLE_ISSUES]
    if sprint_name:
        for issue in data:
            issue["sprint_name"] = sprint_name
    return pd.DataFrame(data)


def normalize_sample_issues(issues: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for row in issues.to_dict("records"):
        ticket_key = row.get("issue_key", "")
        rows.append(
            {
                "ticket_key": ticket_key,
                "issue_key": ticket_key,
                "summary": row.get("summary", ""),
                "issue_type": row.get("issue_type", ""),
                "status": row.get("status", ""),
                "assignee": row.get("assignee", ""),
                "story_points": row.get("story_points", 0),
                "sprint": row.get("sprint_name", ""),
                "sprint_name": row.get("sprint_name", ""),
                "epic_key": row.get("epic_key", ""),
                "epic_name": row.get("epic_name", ""),
                "labels": [],
                "components": [],
                "jira_url": "",
                "allocation_category": row.get("allocation_category", ""),
            }
        )
    return rows


def _escape_jql_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _response_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]

    messages = payload.get("errorMessages") or []
    field_errors = payload.get("errors") or {}
    if field_errors:
        messages.extend(f"{field}: {message}" for field, message in field_errors.items())
    return "; ".join(messages) or response.text[:500]

