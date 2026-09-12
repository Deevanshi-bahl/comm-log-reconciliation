"""
Two kinds of tests:

1. Against the real data/comm_log.db: every bridge step returns the number
   claimed in the README, and the final query returns 22.

2. Against an ADVERSARIAL fixture built in-memory: three small additions that
   are all legal under the README's rules but break the "delivered + eligible"
   shortcut (sql/traps/T2) while the real query (sql/bridge/04_final.sql)
   still returns the correct, hand-computed answer.

Run:  python -m pytest -q      (or simply: python tests/test_reconciliation.py)
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"
DB = ROOT / "data" / "comm_log.db"


def run(con: sqlite3.Connection, rel: str) -> int:
    (v,) = con.execute((SQL / rel).read_text()).fetchone()
    return int(v)


# ---------------------------------------------------------------- real data --

def test_bridge_steps_on_real_data():
    con = sqlite3.connect(DB)
    assert run(con, "bridge/00_naive.sql") == 30
    assert run(con, "bridge/01_scope.sql") == 30
    assert run(con, "bridge/02_eligible_campaigns.sql") == 26
    assert run(con, "bridge/03_collapse_family_a.sql") == 23
    assert run(con, "bridge/04_final.sql") == 22


def test_trap_t2_coincides_on_real_data():
    """Documents the coincidence: the wrong method also returns 22 here."""
    con = sqlite3.connect(DB)
    assert run(con, "traps/T2_delivered_and_eligible.sql") == 22


# ---------------------------------------------------------- adversarial data --

def adversarial_db() -> sqlite3.Connection:
    """
    Copy of the real DB plus three perfectly legal situations:

      (a) Standalone 9101: customer C26 gets a FAILED send (1100) and is then
          re-sent and delivered. Standalone = every send is its own event, so
          both rows count (+2). T2 counts only the 900 (+1).

      (b) Retry family 9201: D2 was already delivered on 9201 but is ALSO sent
          (and delivered) on retry 9202 -- e.g. re-targeted after falling back
          into the audience. Same underlying communication, same customer ->
          still counts once (+0). T2 counts the extra 900 (+1).

      (c) Retry family 9001: customer C15 fails on 9001 AND on 9002 and is never
          delivered. Whether an undelivered customer is "reached" is a
          definitional question (see README, "Surprises"); under the README's
          literal definition -- distinct customers *targeted* by the underlying
          communication -- C15 counts once (+1). T2 counts 0.

    Correct answer: 22 + 2 + 0 + 1 = 25.   T2 answer: 22 + 1 + 1 + 0 = 24.
    """
    src = sqlite3.connect(DB)
    con = sqlite3.connect(":memory:")
    src.backup(con)
    src.close()

    rows = [
        # id, merchant, comm_id, customer, type, status, sent, scheduled, credit, channel
        (101, 501, 9101, "C26", "2", 1100, "2026-10-11 10:00:00", "2026-10-11 10:00:00", 1, "sms"),
        (102, 501, 9101, "C26", "2",  900, "2026-10-12 10:00:00", "2026-10-12 10:00:00", 1, "sms"),
        (103, 501, 9202, "D2",  "2",  900, "2026-10-08 10:00:00", "2026-10-08 10:00:00", 1, "sms"),
        (104, 501, 9001, "C15", "2", 1100, "2026-10-03 10:00:00", "2026-10-03 10:00:00", 1, "sms"),
        (105, 501, 9002, "C15", "2", 1100, "2026-10-04 10:00:00", "2026-10-04 10:00:00", 1, "sms"),
    ]
    con.executemany("INSERT INTO communication_log VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    return con


def test_final_query_is_robust_on_adversarial_data():
    con = adversarial_db()
    assert run(con, "bridge/04_final.sql") == 25


def test_trap_t2_breaks_on_adversarial_data():
    con = adversarial_db()
    assert run(con, "traps/T2_delivered_and_eligible.sql") == 24  # != 25


def test_deeper_chain_is_handled():
    """A 4-level chain (9003 -> 9005) with a customer delivered only at the
    bottom must still count that customer once for root 9001."""
    con = adversarial_db()
    con.execute("INSERT INTO campaign VALUES (9005, 501, 9003, 'Retry D', 'approved', 'processed')")
    con.executemany(
        "INSERT INTO communication_log VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (106, 501, 9001, "C16", "2", 1100, "2026-10-03 10:00:00", "2026-10-03 10:00:00", 1, "sms"),
            (107, 501, 9002, "C16", "2", 1100, "2026-10-04 10:00:00", "2026-10-04 10:00:00", 1, "sms"),
            (108, 501, 9003, "C16", "2", 1100, "2026-10-05 10:00:00", "2026-10-05 10:00:00", 1, "sms"),
            (109, 501, 9005, "C16", "2",  900, "2026-10-06 10:00:00", "2026-10-06 10:00:00", 1, "sms"),
        ],
    )
    con.commit()
    assert run(con, "bridge/04_final.sql") == 26  # 25 + C16 once


if __name__ == "__main__":  # allow running without pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS  {name}")
