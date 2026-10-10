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

CREATE_REPOS = """
CREATE TABLE IF NOT EXISTS watched_repos (
    id INTEGER PRIMARY KEY,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(owner, repo)
)
"""
CREATE_JOBS = """
CREATE TABLE IF NOT EXISTS review_jobs (
    id INTEGER PRIMARY KEY,
    pr_url TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT,
    created_at TEXT NOT NULL
)
"""
CREATE_MODE = """
CREATE TABLE IF NOT EXISTS cockpit_state (
    id INTEGER PRIMARY KEY,
    mode TEXT NOT NULL
)
"""
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
            connection.execute(CREATE_REPOS)
            connection.execute(CREATE_JOBS)
            connection.execute(CREATE_TABLE)
            connection.execute(CREATE_MODE)
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

    def add_repo(self, owner: str, repo: str):
        created_at = datetime.now(timezone.utc).isoformat()
        statement = "INSERT INTO watched_repos (owner, repo, created_at) VALUES (?, ?, ?)"
        with self._connect() as connection:
            connection.execute(_sql(statement, self.url), (owner, repo, created_at))
            connection.commit()

    def remove_repo(self, owner: str, repo: str):
        statement = "DELETE FROM watched_repos WHERE owner = ? AND repo = ?"
        with self._connect() as connection:
            connection.execute(_sql(statement, self.url), (owner, repo))
            connection.commit()

    def enqueue(self, pr_url: str, command: str) -> int:
        """Return the running job when the same command is already active."""
        active = (
            "SELECT id FROM review_jobs WHERE pr_url = ? AND command = ? AND status IN ('排队', '运行中') "
            "ORDER BY id DESC LIMIT 1"
        )
        insert = "INSERT INTO review_jobs (pr_url, command, status, summary, created_at) VALUES (?, ?, '排队', '', ?)"
        with self._connect() as connection:
            row = connection.execute(_sql(active, self.url), (pr_url, command)).fetchone()
            if row:
                return int(row[0])
            created = datetime.now(timezone.utc).isoformat()
            cursor = connection.execute(_sql(insert, self.url), (pr_url, command, created))
            connection.commit()
            return int(cursor.lastrowid)

    def finish_job(self, job_id: int, status: str, summary: str):
        statement = "UPDATE review_jobs SET status = ?, summary = ? WHERE id = ?"
        with self._connect() as connection:
            connection.execute(_sql(statement, self.url), (status, summary[:500], job_id))
            connection.commit()

    def jobs_for(self, pr_url: str) -> list[tuple]:
        statement = "SELECT id, command, status, summary, created_at FROM review_jobs WHERE pr_url = ? ORDER BY id"
        with self._connect() as connection:
            return connection.execute(_sql(statement, self.url), (pr_url,)).fetchall()

    def get_mode(self) -> str:
        """Return the cockpit mode. An empty database stays on the manual setting."""
        self.setup()
        statement = "SELECT mode FROM cockpit_state WHERE id = 1"
        with self._connect() as connection:
            row = connection.execute(statement).fetchone()
        mode = row[0] if row else ""
        if mode not in ("人工加速", "辅助驾驶", "自动驾驶"):
            return "人工加速"
        return mode

    def set_mode(self, mode: str):
        if mode not in ("人工加速", "辅助驾驶", "自动驾驶"):
            raise ValueError("未知驾驶模式")
        delete = "DELETE FROM cockpit_state WHERE id = 1"
        insert = "INSERT INTO cockpit_state (id, mode) VALUES (1, ?)"
        with self._connect() as connection:
            connection.execute(_sql(delete, self.url))
            connection.execute(_sql(insert, self.url), (mode,))
            connection.commit()

    def repos(self) -> list[tuple[str, str]]:
        statement = "SELECT owner, repo FROM watched_repos ORDER BY id DESC"
        with self._connect() as connection:
            return connection.execute(_sql(statement, self.url)).fetchall()

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
