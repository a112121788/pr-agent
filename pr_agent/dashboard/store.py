"""Persist factory stage records in SQLite or PostgreSQL.

The table shape is the same for both databases. SQLite is the default because a container can
run it without another service; PostgreSQL is selected by changing the database URL.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS factory_records (
    id INTEGER PRIMARY KEY,
    pr_url TEXT NOT NULL,
    record_type TEXT NOT NULL,
    stage TEXT NOT NULL,
    intent TEXT,
    verdict TEXT,
    head_sha TEXT,
    summary TEXT,
    created_at TEXT NOT NULL
)
"""


@dataclass(frozen=True)
class FactoryRecord:
    pr_url: str
    record_type: str
    stage: str
    intent: str = ""
    verdict: str = ""
    head_sha: str = ""
    summary: str = ""
    created_at: str = ""


def database_url() -> str:
    """Return the configured database URL, defaulting to the container data volume."""
    configured = get_settings().get("DASHBOARD.DATABASE_URL", "")
    return configured or "sqlite:////data/factory.db"


def _postgres(url: str) -> bool:
    return url.startswith("postgres://") or url.startswith("postgresql://")


class FactoryStore:
    """Write and read the small set of records shown on the dashboard."""

    def __init__(self, url: str):
        self.url = url

    def setup(self):
        with self._connect() as connection:
            connection.execute(CREATE_TABLE)
            connection.commit()

    def add(self, record: FactoryRecord):
        created_at = record.created_at or datetime.now(timezone.utc).isoformat()
        values = (
            record.pr_url, record.record_type, record.stage, record.intent,
            record.verdict, record.head_sha, record.summary, created_at,
        )
        statement = (
            "INSERT INTO factory_records "
            "(pr_url, record_type, stage, intent, verdict, head_sha, summary, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with self._connect() as connection:
            connection.execute(_sql(statement, self.url), values)
            connection.commit()

    def latest(self, limit: int = 50) -> list[FactoryRecord]:
        self.setup()
        statement = (
            "SELECT pr_url, record_type, stage, intent, verdict, head_sha, summary, created_at "
            "FROM factory_records ORDER BY id DESC LIMIT ?"
        )
        with self._connect() as connection:
            rows = connection.execute(_sql(statement, self.url), (limit,)).fetchall()
        return [FactoryRecord(*row) for row in rows]

    def _connect(self):
        if self.url.startswith("sqlite:///"):
            path = self.url.removeprefix("sqlite:///")
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            return sqlite3.connect(path)
        if _postgres(self.url):
            import psycopg

            return psycopg.connect(self.url)
        raise ValueError("数据库地址必须以 sqlite:/// 或 postgresql:// 开头")


def _sql(statement: str, url: str) -> str:
    return statement.replace("?", "%s") if _postgres(url) else statement


def record_factory_event(record: FactoryRecord):
    """Save one dashboard row. A database problem must not stop the review command."""
    try:
        store = FactoryStore(database_url())
        store.setup()
        store.add(record)
    except Exception as error:
        get_logger().warning(f"工厂看板未写入：{error}")
