from pr_agent.dashboard.page import render_dashboard
from pr_agent.dashboard.store import FactoryRecord, FactoryStore


def _record():
    return FactoryRecord("https://gitee.com/o/r/pulls/1", "受理", "受理", "新业务", "", "abc123456789", "原话")


def test_sqlite_round_trip_and_dashboard(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    store.add(_record())

    assert store.latest()[0].intent == "新业务"
    store.add_repo("owner", "repo")
    assert store.repos() == [("owner", "repo")]
    store.remove_repo("owner", "repo")
    assert store.repos() == []
    first = store.enqueue("https://gitee.com/o/r/pulls/1", "review")
    second = store.enqueue("https://gitee.com/o/r/pulls/1", "review")
    assert first == second
    assert store.begin_job("https://gitee.com/o/r/pulls/1", "review") is None
    assert "https://gitee.com/o/r/pulls/1" in store.reviewing()
    store.finish_job(first, "完成", "已完成")
    assert store.reviewing() == set()
    assert store.begin_job("https://gitee.com/o/r/pulls/1", "review") is not None
    page = render_dashboard()
    assert "审核工厂驾驶舱" in page
    assert "新业务" in page
    assert "sqlite:///" not in page
    stuck = store.begin_job("https://gitee.com/o/r/pulls/9", "review")
    assert stuck is not None
    assert store.release_abandoned_jobs() == 2
    assert store.reviewing() == set()
    assert store.jobs_for("https://gitee.com/o/r/pulls/9")[-1][2] == "失败"
    monkeypatch.setenv("PR_AGENT_BUILD", "abc1234")
    assert "构建 abc1234" in render_dashboard()


def test_postgres_uses_the_same_insert_shape(monkeypatch):
    executed = []

    class Connection:
        def execute(self, statement, values=None):
            executed.append((statement, values))
            return self

        def fetchall(self):
            return []

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(
        "psycopg.connect",
        lambda url: Connection(),
        raising=False,
    )
    import psycopg
    monkeypatch.setattr(psycopg, "connect", lambda url: Connection(), raising=False)
    store = FactoryStore("postgresql://user:pass@db:5432/factory")
    store.setup()
    store.add(_record())

    assert "INSERT INTO factory_records" in executed[-1][0]
    assert "%s" in executed[-1][0]
