#!/usr/bin/env python3
"""
collect_mentions.py — ApeWisdom snapshot -> data/mentions/<UTC day>.csv
=====================================================================
Runs on GitHub Actions twice a day (see .github/workflows/collect.yml) so
the mention baseline keeps accumulating when the desktop is asleep.

Same semantics as buzz_screener.store_snapshot: one row per ticker per UTC
day, keeping the MAX mentions/upvotes and MIN rank seen that day. The
screener merges these files into its local SQLite with the same rule
(buzz_screener.sync_from_github), so desktop and cloud collections are
unioned, never overwritten.

Dependencies: requests only.
"""
import csv
import datetime as dt
import os
import sys
import time

import requests

URL = "https://apewisdom.io/api/v1.0/filter/{flt}/page/{page}"
FILTER = os.environ.get("APEWISDOM_FILTER", "all-stocks")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mentions")
FIELDS = ["ts", "day", "ticker", "mentions", "upvotes", "rank"]


def to_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0


def fetch(flt: str) -> list[dict]:
    rows, page, pages = [], 1, 1
    while page <= pages:
        for attempt in range(3):
            try:
                r = requests.get(URL.format(flt=flt, page=page), timeout=30)
                r.raise_for_status()
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    raise
                print(f"  page {page}: {e} — retrying")
                time.sleep(5)
        data = r.json()
        pages = int(data.get("pages", 1))
        for it in data.get("results", []):
            tk = str(it.get("ticker", "")).upper().strip()
            if tk:
                rows.append({"ticker": tk, "mentions": to_int(it.get("mentions")),
                             "upvotes": to_int(it.get("upvotes")),
                             "rank": to_int(it.get("rank"))})
        page += 1
        time.sleep(0.4)
    if not rows:
        raise RuntimeError("ApeWisdom returned no data")
    return rows


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    ts, day = now.isoformat(timespec="seconds"), now.strftime("%Y-%m-%d")
    path = os.path.join(OUT_DIR, f"{day}.csv")
    os.makedirs(OUT_DIR, exist_ok=True)

    existing: dict[str, dict] = {}
    if os.path.exists(path):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                existing[r["ticker"]] = r

    fresh = fetch(FILTER)
    merged = dict(existing)
    for r in fresh:
        old = existing.get(r["ticker"])
        merged[r["ticker"]] = {
            "ts": ts, "day": day, "ticker": r["ticker"],
            "mentions": max(r["mentions"], to_int(old["mentions"]) if old else 0),
            "upvotes": max(r["upvotes"], to_int(old["upvotes"]) if old else 0),
            "rank": min(r["rank"], to_int(old["rank"])) if old and to_int(old["rank"]) else r["rank"],
        }
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for tk in sorted(merged):
            w.writerow({k: merged[tk][k] for k in FIELDS})
    print(f"{ts}: {len(fresh)} tickers fetched, {len(merged)} rows in {os.path.basename(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
