"""
Runs the reconciliation bridge against data/comm_log.db and prints it as a table.

Every number in the bridge is produced by executing the corresponding file in
sql/bridge/ -- nothing is hard-coded except the Finance target (22), which the
script asserts against at the end.

Usage:
    python run_bridge.py            # bridge + per-root breakdown + trap check
    python run_bridge.py --db path  # run against a different SQLite file

No third-party dependencies (stdlib sqlite3 only).
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SQL_DIR = ROOT / "sql"
FINANCE_TARGET = 22

# (sql file, short description, one-line reason) -- in the order I discovered them.
BRIDGE_STEPS = [
    ("00_naive.sql",
     "Naive count of communication_log rows",
     "starting point"),
    ("01_scope.sql",
     "Apply reporting scope (merchant 501, type '2', Oct-2026)",
     "no change here, but the definition must be encoded, not assumed"),
    ("02_eligible_campaigns.sql",
     "Drop campaigns that have not cleared the reporting gate",
     "9004 is approval_awaiting: 4 log rows (C11..C14) exist but are not reportable"),
    ("03_collapse_family_a.sql",
     "Collapse retry chain 9001 -> {9002 -> 9003}: count distinct customers",
     "C2 needed 2 attempts, C3 needed 3; same underlying communication = count once (13 rows -> 10)"),
    ("04_final.sql",
     "Collapse retry chain 9201 -> 9202 the same way; keep standalone 9101 at row level",
     "D1 needed 2 attempts (6 rows -> 5). 9101 has no chain, so C20's two sends both count"),
]

TRAPS = [
    ("T1_delivered_only.sql", "count rows with delivery_status = 900"),
    ("T2_delivered_and_eligible.sql", "delivered rows on eligible campaigns  <-- also returns 22, still wrong"),
    ("T3_dedupe_customer_per_campaign.sql", "distinct (campaign, customer) on eligible campaigns"),
    ("T4_collapse_before_eligibility.sql", "collapse chains BEFORE applying eligibility"),
    ("T5_distinct_customers_overall.sql", "count distinct customer_id overall"),
]


def scalar(con: sqlite3.Connection, sql_path: Path) -> int:
    (value,) = con.execute(sql_path.read_text()).fetchone()
    return int(value)


def print_bridge(con: sqlite3.Connection) -> int:
    print("\nRECONCILIATION BRIDGE  (merchant 501, Oct-2026, Diwali campaigns)\n")
    header = f"{'Step':<5}{'Description':<78}{'Result':>7}  {'Delta':>6}  Reason"
    print(header)
    print("-" * len(header) + "-" * 40)
    prev = None
    result = None
    for i, (fname, desc, reason) in enumerate(BRIDGE_STEPS):
        result = scalar(con, SQL_DIR / "bridge" / fname)
        delta = "" if prev is None else f"{result - prev:+d}"
        print(f"{i:<5}{desc:<78}{result:>7}  {delta:>6}  {reason}")
        prev = result
    print(f"{'final':<5}{'':<78}{result:>7}")
    return result


def print_breakdown(con: sqlite3.Connection) -> None:
    print("\nPER-ROOT BREAKDOWN (sql/bridge/04_final_breakdown.sql)\n")
    rows = con.execute((SQL_DIR / "bridge" / "04_final_breakdown.sql").read_text()).fetchall()
    print(f"{'root':<6}{'name':<36}{'retries?':<10}{'raw rows':>9}{'distinct cust':>15}{'qualifying':>12}")
    for root, name, has_retries, raw, distinct, q in rows:
        print(f"{root:<6}{name:<36}{'yes' if has_retries else 'no':<10}{raw:>9}{distinct:>15}{q:>12}")
    print(f"{'':<61}{'total':>15}{sum(r[-1] for r in rows):>12}")


def print_traps(con: sqlite3.Connection) -> None:
    print("\nWRONG ROUTES I RULED OUT (sql/traps/)\n")
    for fname, desc in TRAPS:
        print(f"{scalar(con, SQL_DIR / 'traps' / fname):>5}   {desc}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "comm_log.db"))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    final = print_bridge(con)
    print_breakdown(con)
    print_traps(con)

    print()
    if final == FINANCE_TARGET:
        print(f"OK: final target_base = {final} matches Finance ({FINANCE_TARGET}).")
    else:
        raise SystemExit(f"MISMATCH: final target_base = {final}, Finance says {FINANCE_TARGET}.")


if __name__ == "__main__":
    main()
