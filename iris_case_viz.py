"""Pull cases from a DFIR-IRIS instance and chart them by open date and opener."""

import os
import sys
from collections import Counter
from datetime import datetime, timedelta

import requests
import matplotlib.pyplot as plt


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def get_env():
    url = os.environ.get("IRIS_URL")
    key = os.environ.get("IRIS_API_KEY")
    if not url:
        die("IRIS_URL is not set. Example: https://iris.example.local")
    if not key:
        die("IRIS_API_KEY is not set. Get one from 'My settings > API Key' in IRIS.")
    verify = os.environ.get("IRIS_VERIFY_SSL", "1") not in ("0", "false", "False", "no")
    return url.rstrip("/"), key, verify


def fetch_cases(base_url, api_key, verify_ssl):
    endpoint = f"{base_url}/manage/cases/list"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    try:
        resp = requests.get(endpoint, headers=headers, verify=verify_ssl, timeout=30)
    except requests.exceptions.SSLError as e:
        die(f"SSL error talking to IRIS: {e}\nIf the server uses a self-signed cert, set IRIS_VERIFY_SSL=0.")
    except requests.exceptions.RequestException as e:
        die(f"Network error talking to IRIS: {e}")

    if resp.status_code != 200:
        die(f"IRIS returned HTTP {resp.status_code}: {resp.text[:300]}")

    try:
        payload = resp.json()
    except ValueError:
        die(f"IRIS response was not JSON. First 300 chars:\n{resp.text[:300]}")

    if isinstance(payload, dict) and payload.get("status") and payload["status"] != "success":
        die(f"IRIS API reported failure: status={payload.get('status')} message={payload.get('message')}")

    return unwrap_cases(payload)


def unwrap_cases(payload):
    """The /manage/cases/list response wrapper isn't fully pinned down in the docs.
    Probe the common shapes: data=[...], data={'cases':[...]}, or a bare list."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        die(f"Unexpected response type: {type(payload).__name__}")

    data = payload.get("data", payload)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("cases", "list", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        die(f"Could not find a case list in response. Top-level keys: {list(payload.keys())}; data keys: {list(data.keys())}")
    die(f"Could not interpret response. Top-level keys: {list(payload.keys())}")


def aggregate(cases):
    per_day = Counter()
    per_opener = Counter()
    skipped = 0
    for c in cases:
        open_date = c.get("open_date")
        opened_by = c.get("opened_by")
        if not open_date or not opened_by:
            skipped += 1
            continue
        try:
            d = datetime.strptime(open_date, "%Y-%m-%d").date()
        except ValueError:
            skipped += 1
            continue
        per_day[d] += 1
        per_opener[opened_by] += 1
    return per_day, per_opener, skipped


def fill_date_range(per_day):
    """Return (sorted_dates, counts) with zero-filled gaps between min and max."""
    if not per_day:
        return [], []
    start = min(per_day)
    end = max(per_day)
    dates = []
    counts = []
    cur = start
    while cur <= end:
        dates.append(cur)
        counts.append(per_day.get(cur, 0))
        cur += timedelta(days=1)
    return dates, counts


def plot_per_day(per_day):
    dates, counts = fill_date_range(per_day)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([d.isoformat() for d in dates], counts, color="steelblue")
    ax.set_title("IRIS cases opened per day")
    ax.set_xlabel("Open date")
    ax.set_ylabel("Cases opened")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()


def plot_per_opener(per_opener):
    items = sorted(per_opener.items(), key=lambda kv: kv[1])
    names = [k for k, _ in items]
    counts = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(10, max(3, 0.4 * len(names) + 1)))
    ax.barh(names, counts, color="darkorange")
    ax.set_title("IRIS cases by opener")
    ax.set_xlabel("Cases opened")
    ax.set_ylabel("Opened by")
    fig.tight_layout()


def main():
    base_url, api_key, verify_ssl = get_env()
    cases = fetch_cases(base_url, api_key, verify_ssl)

    if not cases:
        print("No cases returned.")
        return 0

    per_day, per_opener, skipped = aggregate(cases)
    print(f"Fetched {len(cases)} cases ({skipped} skipped due to missing/invalid fields).")
    print(f"Distinct open dates: {len(per_day)}; distinct openers: {len(per_opener)}.")

    if not per_day and not per_opener:
        print("Nothing to chart.")
        return 0

    plot_per_day(per_day)
    plot_per_opener(per_opener)
    plt.show()
    return 0


if __name__ == "__main__":
    sys.exit(main())
