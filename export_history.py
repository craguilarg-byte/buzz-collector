#!/usr/bin/env python3
"""
export_history.py — one-time seed: dump the desktop's buzz_history.db into
data/mentions/<day>.csv so the repo starts with the full Jul-2026+ history.

Run ONCE from this folder on the desktop, before the first push:
    python export_history.py "C:\\Users\\maide\\buzz_screener\\buzz_history.db"
"""
import csv
import os
import sqlite3
import sys

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mentions")
FIELDS = ["ts", "day", "ticker", "mentions", "upvotes", "rank"]


def main(db: str) -> int:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    days = [r[0] for r in con.execute("SELECT DISTINCT day FROM mentions ORDER BY day")]
    for day in days:
        rows = con.execute("SELECT ts, day, ticker, mentions, upvotes, rank FROM mentions "
                           "WHERE day=? ORDER BY ticker", (day,)).fetchall()
        with open(os.path.join(OUT_DIR, f"{day}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)
            w.writerows(rows)
    print(f"exported {len(days)} day-files to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "buzz_history.db"))
