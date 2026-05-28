# Jira Allocation Dashboard

Streamlit dashboard for the ECOMM Cheeseburger team's sprint allocation reporting.

The app pulls Jira sprint tickets when credentials are configured, lets you assign tickets or epics to allocation categories, and compares actual story-point allocation against target percentages using a fixed sprint capacity of **55 story points**.

## Features

- Jira sprint issue pull via environment variables
- Bundled sample data fallback when Jira is not configured
- CSV-backed allocation mappings for issue-level or epic-level assignment
- Fixed sprint capacity denominator of 55 story points
- Target allocation comparison table
- Looker Studio-style scorecards, charts, heatmap, and detail tables
- Excel snapshot download

## Allocation targets

| Category | Target |
| --- | ---: |
| Product/BPL | 45% |
| Product/Non-BPL | 0% |
| ETO System Feature | 10% |
| Marketing | 35% |
| ETO System Maintenance | 5% |
| Security | 5% |

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
  outputs/
```

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
JIRA_BOARD_ID=123
STORY_POINTS_FIELD=customfield_10016
SPRINT_FIELD=Sprint
EPIC_FIELD=parent
```

Do not commit `.env`; it is ignored by git.

5. Run the Streamlit app:

```bash
streamlit run app.py
```

If Jira credentials are missing or a Jira request fails, the dashboard uses bundled sample tickets so the first version remains runnable.

## Data files

- `data/allocation_mapping.csv` stores manual mappings. `mapping_type` should be `issue` or `epic`.
- `data/sprint_targets.csv` stores target percentages and can be edited if targets change.

Issue-level mappings override epic-level mappings.

