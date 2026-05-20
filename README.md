# iris_case_viz

A small Python script that pulls cases from a [DFIR-IRIS](https://dfir-iris.github.io/) instance and renders two matplotlib charts: cases opened per day, and cases broken down by who opened them.

## Requirements

- Python 3.9+
- `requests`
- `matplotlib`

## Install

```
py -3 -m pip install requests matplotlib
```

## Configuration

The script reads its configuration from environment variables.

| Variable           | Required | Description                                                                          |
| ------------------ | -------- | ------------------------------------------------------------------------------------ |
| `IRIS_URL`         | yes      | Base URL of your IRIS instance, e.g. `https://iris.example.local`                    |
| `IRIS_API_KEY`     | yes      | Bearer token. Get one from **My settings > API Key** in the IRIS web UI.             |
| `IRIS_VERIFY_SSL`  | no       | Set to `0` to disable TLS verification (useful for self-signed certs). Default: on.  |

## Run

PowerShell:

```powershell
$env:IRIS_URL = "https://iris.example.local"
$env:IRIS_API_KEY = "..."
# optional, only if the server uses a self-signed cert:
$env:IRIS_VERIFY_SSL = "0"
py -3 iris_case_viz.py
```

POSIX shell:

```sh
export IRIS_URL="https://iris.example.local"
export IRIS_API_KEY="..."
export IRIS_VERIFY_SSL=0   # optional
python3 iris_case_viz.py
```

## What you'll see

Two matplotlib windows open:

1. **Cases opened per day** — one bar per calendar day from the earliest to the latest `open_date`, with zero-bars filling any gap days so the timeline reads correctly.
2. **Cases by opener** — horizontal bar chart, one row per distinct `opened_by` username, sorted by count.

The script also prints how many cases it fetched and how many it skipped due to missing or malformed fields.

## Troubleshooting

- **`SSL error talking to IRIS`** — your instance probably uses a self-signed cert. Set `IRIS_VERIFY_SSL=0`.
- **`IRIS returned HTTP 401`** — bad or expired API key. Regenerate it in the IRIS UI.
- **`No cases returned` / `Nothing to chart`** — the IRIS instance has no cases (or none with usable `open_date` + `opened_by` fields).
- **`Could not find a case list in response...`** — the response wrapper shape differs from what we assumed. The error prints the keys it saw; adjust `unwrap_cases()` in [iris_case_viz.py](iris_case_viz.py).

## API reference

Built against the DFIR-IRIS [v2.0.2 API reference](https://docs.dfir-iris.org/_static/iris_api_reference_v2.0.2.html), endpoint `GET /manage/cases/list`.
