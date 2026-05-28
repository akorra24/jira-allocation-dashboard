# Jira Allocation Dashboard

Streamlit dashboard for the ECOMM Cheeseburger team's sprint allocation reporting.

The dashboard pulls Jira sprint tickets, lets you manually map tickets or epics to allocation categories, and compares actual sprint work against target allocation percentages. It is designed to feel like a Google Looker Studio resource planning dashboard, with KPI cards, filtered tables, trend analysis, and exports.

## What the dashboard answers

- How much of the sprint went to Product/BPL, Marketing, Security, platform work, and maintenance?
- Which categories are above or below target?
- Is the sprint over the fixed team capacity?
- Which tickets are still unmapped?
- Are targets realistic across multiple sprints?

## Allocation formulas

The dashboard uses a fixed sprint capacity denominator of **55 story points**.

Actual allocation percentage is calculated as:

```text
actual allocation % = category story points / 55 * 100
```

Target story points are calculated as:

```text
target story points = target percentage / 100 * 55
```

Variance is calculated as:

```text
variance % = actual allocation % - target %
variance story points = actual story points - target story points
```

The denominator stays fixed at 55 points so every sprint is compared against the same capacity baseline, even if the sprint contains more or fewer pointed tickets. This makes over-capacity work visible instead of normalizing it away.

## Allocation targets

| Category | Target |
| --- | ---: |
| Product/BPL | 45% |
| Product/Non-BPL | 0% |
| ETO System Feature | 10% |
| Marketing | 35% |
| ETO System Maintenance | 5% |
| Security | 5% |

`Unmapped` work is shown separately and excluded from target variance calculations.

## Manual ticket and epic mapping

Manual mappings are stored in `data/allocation_mapping.csv`.

Columns:

- `mapping_level`: `Ticket` or `Epic`
- `jira_key`: ticket key or epic key
- `summary`
- `allocation_category`
- `notes`
- `last_updated`

Mapping precedence:

1. Ticket-level mapping wins.
2. If no ticket mapping exists, epic-level mapping is used.
3. If neither exists, the ticket is marked `Unmapped`.

Use the **Ticket Mapping** page to pull a sprint, select allocation categories in the editable table, add notes, and save mappings.

## Sample data fallback

If Jira is not configured or an API call fails, the app can use realistic sample Cheeseburger sprint data.

Use the sidebar checkbox:

```text
Use sample Cheeseburger sprint data
```

The sample sprint is `S215`, has 12 tickets, totals 65 story points, exceeds the 55-point capacity, includes BPL above target, and includes unmapped tickets. This is useful for testing the dashboard without Jira access.

## Setup

1. Create a virtual environment:

```bash
cd jira-allocation-dashboard
python3 -m venv .venv
source .venv/bin/activate
```

2. Install requirements:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

4. Add Jira credentials to `.env`:

```dotenv
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=ECOMM
JIRA_BOARD_ID=your-board-id
STORY_POINTS_FIELD=your-story-points-field-id
SPRINT_FIELD=your-sprint-field-id
EPIC_FIELD=your-epic-field-id
JIRA_DEFAULT_SPRINT=S215
```

Do not commit `.env`; it is ignored by git.

5. Run the Streamlit app:

```bash
streamlit run app.py
```

## Jira custom field discovery

Jira Cloud uses custom field IDs for fields such as Story Points and Sprint.

Use the **Jira Field Discovery** page to:

- Confirm whether Jira credentials are configured.
- Test the Jira connection with the `/myself` endpoint.
- Load Jira fields from the fields endpoint.
- Search field names using terms like `story`, `points`, `sprint`, or `epic`.

Copy the relevant field IDs into `.env`:

```dotenv
STORY_POINTS_FIELD=customfield_10016
SPRINT_FIELD=customfield_10020
EPIC_FIELD=customfield_10014
```

If `STORY_POINTS_FIELD` is missing, live Jira tickets default to `0` story points and the app shows a warning.

## Exporting reports

Use the **Settings / Export** page and click **Generate export files**.

The app writes files to `outputs/`:

- Current sprint ticket detail CSV
- Current sprint allocation summary CSV
- Sprint history CSV
- Current sprint Excel summary with two tabs:
  - `Allocation Summary`
  - `Ticket Detail`

Excel exports include bold headers, frozen top rows, percent formatting, story point number formatting, and auto-sized columns where possible.

Exports contain allocation and ticket data only. Jira credentials and environment variables are not exported.

## Multi-sprint trends

The Dashboard includes a **Trend Analysis** section.

- Save the current sprint to `data/sprint_history.csv`.
- Select one or more historical sprints.
- Review actual allocation percentages over time by category.
- Compare actual lines against target lines.
- Review average actual allocation, average variance, number of sprints over target, and target realism recommendations.

## Project structure

```text
jira-allocation-dashboard/
  app.py
  jira_client.py
  analytics.py
  config.py
  styles.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  data/
    allocation_mapping.csv
    sprint_targets.csv
    sprint_history.csv
  outputs/
```

## Troubleshooting

### API token issues

Symptoms:

- Jira connection test fails.
- Jira returns authentication errors.

Checks:

- Confirm `JIRA_EMAIL` matches the Atlassian account that owns the token.
- Generate a Jira API token from Atlassian account settings.
- Confirm `JIRA_BASE_URL` uses your Atlassian domain, for example `https://your-domain.atlassian.net`.

### Missing Story Points

Symptoms:

- Tickets load, but story points are all `0`.
- The dashboard warns that `STORY_POINTS_FIELD` is not configured.

Fix:

- Open **Jira Field Discovery**.
- Search for `story` or `points`.
- Copy the matching field ID, usually something like `customfield_10016`, into `.env`.
- Restart Streamlit.

### Sprint not found

Symptoms:

- Jira returns bad JQL.
- No tickets load for a sprint.

Checks:

- Confirm the sprint name or ID exactly matches Jira.
- Confirm `JIRA_PROJECT_KEY` is correct.
- Confirm the Jira user can view the board/project.

### No tickets returned

Symptoms:

- The app shows an empty dashboard or "no tickets" warning.

Checks:

- Verify the sprint has issues in Jira.
- Verify the sprint field is searchable in Jira JQL.
- Try the sample data checkbox to confirm the dashboard UI works.

### Unmapped tickets

Symptoms:

- KPI card shows unmapped story points.
- Ticket detail table contains `Unmapped`.

Fix:

- Open **Ticket Mapping**.
- Assign categories for unmapped tickets.
- Save allocation mappings.
- If many tickets share one epic, add or preserve an epic-level mapping in `data/allocation_mapping.csv`.

