from pr_agent.dashboard.home import home_view
from pr_agent.dashboard.store import FactoryStore


def _client(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.dashboard.home.open_pulls", lambda *_args, **_kwargs: [])
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    return TestClient(app), FactoryStore(url)


def test_home_view_marks_one_running_review(tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    store = FactoryStore(url)
    store.setup()
    store.add_repo("eclouddev", "hlzs_web")
    pr = "https://gitee.com/o/r/pulls/8"
    job_id = store.begin_job(pr, "review")
    payload = home_view(store, pulls_for=lambda _owner, _repo: [{
        "number": 8, "title": "修复晨会", "url": pr,
    }])
    pull = payload["repos"][0]["pulls"][0]
    assert pull["reviewing"] is True
    assert pull["job_id"] == job_id
    assert pull["status"] == "排队"


def test_dashboard_shell_loads_the_client_without_embedding_pulls(monkeypatch, tmp_path):
    client, store = _client(monkeypatch, tmp_path)
    store.setup()
    store.add_repo("eclouddev", "hlzs_web")

    page = client.get("/dashboard")
    script = client.get("/dashboard/static/home.js")
    icon = client.get("/dashboard/static/favicon.svg")

    assert page.status_code == 200
    assert "/dashboard/static/home.js" in page.text
    assert "/dashboard/static/favicon.svg" in page.text
    assert icon.status_code == 200
    assert b"<svg" in icon.content
    assert "https://gitee.com" not in page.text
    assert page.text.index("登记") < page.text.index("批量审查")
    assert script.status_code == 200
    assert "location.reload" not in script.text
    assert "location.href" not in script.text
    assert "/dashboard/api/run" in script.text
    assert "run-mark" in script.text
    assert "preventDefault" in script.text


def test_api_run_queues_one_job_and_reports_it(monkeypatch, tmp_path):
    client, store = _client(monkeypatch, tmp_path)
    store.setup()
    calls = []

    async def _review(_pr_url, _command):
        calls.append(_command)
        return "已完成 review"

    monkeypatch.setattr("pr_agent.servers.gitee_app.run_review", _review)
    pr = "https://gitee.com/o/r/pulls/8"
    first = client.post("/dashboard/api/run", json={"pr_url": pr, "command": "review"})
    assert first.status_code == 200
    assert first.headers["content-type"].startswith("application/json")
    body = first.json()
    assert body["created"] is True
    assert body["status"] == "排队"
    assert calls == ["review"]
    job = client.get(f"/dashboard/api/jobs/{body['job_id']}")
    assert job.status_code == 200
    assert job.json()["status"] == "完成"
    assert job.json()["pr_url"] == pr


def test_pipeline_api_returns_json_and_the_shell_omits_the_feed(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.dashboard.page.pull_comments", lambda _pr: [{
        "body": "## 审查要点\n\n<script>alert(1)</script>\n",
        "user": {"login": "bot"},
        "created_at": "2026-10-10T09:42:18+08:00",
    }])
    monkeypatch.setattr("pr_agent.dashboard.page.pull_detail", lambda _pr: {
        "number": 4, "title": "修复", "author": "ada", "head": "topic", "base": "master",
        "url": "https://gitee.com/o/r/pulls/4", "state_label": "开放中",
    })
    store = FactoryStore(url)
    store.setup()
    pr = "https://gitee.com/o/r/pulls/4"
    job_id = store.begin_job(pr, "review")
    store.finish_job(job_id, "运行中", "正在审查")
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    client = TestClient(app)
    payload = client.get("/dashboard/api/pr", params={"url": pr}).json()
    page = client.get("/dashboard/pr", params={"url": pr}).text
    script = client.get("/dashboard/static/pipeline.js").text
    comment = next(item for item in payload["messages"] if item["kind"] != "审查")

    assert payload["reviewing"] is True
    assert payload["identity"]["title"] == "修复"
    assert any(item["stage"] == "运行中" for item in payload["messages"])
    assert "<h2>审查要点</h2>" in comment["html"]
    assert "<script>" not in comment["html"]
    assert "&lt;script&gt;" in comment["html"]
    assert "/dashboard/static/pipeline.js" in page
    assert "审查要点" not in page
    assert "location.reload" not in script
    assert "/dashboard/api/pr" in script
    assert "run-mark" in script
    assert "preventDefault" in script


def test_api_register_and_remove_return_json(monkeypatch, tmp_path):
    client, _store = _client(monkeypatch, tmp_path)
    added = client.post("/dashboard/api/repos", json={"repo": "eclouddev/hlzs_web"})
    assert added.status_code == 200
    assert added.json()["repos"] == [{
        "owner": "eclouddev", "repo": "hlzs_web", "error": "", "pulls": [],
    }]
    removed = client.post(
        "/dashboard/api/repos/remove",
        json={"owner": "eclouddev", "repo": "hlzs_web"},
    )
    assert removed.status_code == 200
    assert removed.json()["repos"] == []
