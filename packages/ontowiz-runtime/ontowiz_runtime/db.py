"""Thin database wrapper (Tier A) — the engine seam for the catalog stores.

Ported from market_zero `db.py` (psycopg2 → sqlite3). One small surface —
``execute`` / ``fetch_one`` / ``fetch_all`` / ``transaction`` — over a single
connection, returning rows as plain dicts. ADR-016 selects the engine *through*
this seam: SQLite for dev/test/verify-audit (hermetic), Postgres for production
via DSN. Call sites (CommentStore, UsageStore) never see the engine.

SQLite uses ``?`` placeholders; a future Postgres ``Database`` subclass would
translate to ``%s`` and open a psycopg2 connection — same method contract.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

Params = Sequence[Any]


class Database:
    """A single-connection SQLite wrapper returning dict rows.

    ``dsn`` is a filesystem path to the database file (parent dirs are created)
    or the sentinel ``":memory:"``. Opened eagerly; autocommit by default, with
    ``transaction()`` for grouping writes into one atomic unit.
    """

    def __init__(self, dsn: str | Path) -> None:
        self.dsn = str(dsn)
        if self.dsn != ":memory:":
            Path(self.dsn).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: the serve app runs endpoints in a threadpool and
        # shares one store. A lock serialises access; isolation_level=None gives
        # autocommit, with transaction() issuing explicit BEGIN/COMMIT.
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.dsn, isolation_level=None, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA busy_timeout = 5000")

    def execute(self, sql: str, params: Params = ()) -> None:
        """Run a statement (DDL or write); committed immediately unless in a transaction."""
        with self._lock:
            self._conn.execute(sql, tuple(params))

    def fetch_one(self, sql: str, params: Params = ()) -> dict[str, Any] | None:
        """Return the first row as a dict, or None if the query matched nothing."""
        with self._lock:
            row = self._conn.execute(sql, tuple(params)).fetchone()
        return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: Params = ()) -> list[dict[str, Any]]:
        """Return all matching rows as a list of dicts (empty list if none)."""
        with self._lock:
            rows = self._conn.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Group writes into one atomic unit — commit on success, rollback on error."""
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                yield
            except Exception:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()
