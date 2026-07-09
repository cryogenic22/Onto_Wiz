"""F-DB1 — the thin SQLite Database wrapper (Tier A).

Ported from market_zero `db.py` (psycopg2 → sqlite3). The wrapper is the single
seam ADR-016 selects an engine through: SQLite for dev/test/verify-audit, Postgres
for production via DSN. Tests assert dict rows, persistence, and transactions.
"""

from __future__ import annotations

import pytest
from ontowiz_runtime import Database


def test_execute_and_fetch_one_returns_dict(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("CREATE TABLE t (id INTEGER, name TEXT)")
    db.execute("INSERT INTO t (id, name) VALUES (?, ?)", (1, "a"))
    assert db.fetch_one("SELECT id, name FROM t WHERE id = ?", (1,)) == {"id": 1, "name": "a"}
    db.close()


def test_fetch_all_and_empty_results(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("CREATE TABLE t (id INTEGER)")
    db.execute("INSERT INTO t (id) VALUES (1)")
    db.execute("INSERT INTO t (id) VALUES (2)")
    assert [r["id"] for r in db.fetch_all("SELECT id FROM t ORDER BY id")] == [1, 2]
    assert db.fetch_one("SELECT id FROM t WHERE id = 99") is None
    assert db.fetch_all("SELECT id FROM t WHERE id = 99") == []
    db.close()


def test_persists_across_instances(tmp_path):
    path = tmp_path / "t.db"
    d1 = Database(path)
    d1.execute("CREATE TABLE t (id INTEGER)")
    d1.execute("INSERT INTO t (id) VALUES (1)")
    d1.close()
    d2 = Database(path)
    assert d2.fetch_one("SELECT COUNT(*) AS n FROM t")["n"] == 1
    d2.close()


def test_transaction_commits_as_a_unit(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("CREATE TABLE t (id INTEGER)")
    with db.transaction():
        db.execute("INSERT INTO t (id) VALUES (1)")
        db.execute("INSERT INTO t (id) VALUES (2)")
    assert db.fetch_one("SELECT COUNT(*) AS n FROM t")["n"] == 2
    db.close()


def test_transaction_rolls_back_on_error(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("CREATE TABLE t (id INTEGER)")
    with pytest.raises(ValueError), db.transaction():
        db.execute("INSERT INTO t (id) VALUES (3)")
        raise ValueError("boom")
    assert db.fetch_one("SELECT COUNT(*) AS n FROM t")["n"] == 0
    db.close()


def test_creates_parent_directory(tmp_path):
    nested = tmp_path / "a" / "b" / "t.db"
    db = Database(nested)
    db.execute("CREATE TABLE t (id INTEGER)")
    assert nested.exists()
    db.close()
