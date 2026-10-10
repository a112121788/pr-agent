import pytest

from pr_agent.dashboard.actions import parse_repo, pull_detail
from pr_agent.dashboard.drive import execute_registered, merge_pull
from pr_agent.dashboard.store import FactoryRecord, FactoryStore


def test_repo_form_accepts_owner_and_name():
    assert parse_repo(" eclouddev/hlzs_web ") == ("eclouddev", "hlzs_web")


@pytest.mark.parametrize("value", ["", "owner", "owner/name?x=1", "../repo", "owner/name/extra"])
def test_repo_form_rejects_values_that_could_escape_the_repository(value):
    with pytest.raises(ValueError, match="owner/repo"):
        parse_repo(value)


def test_pull_detail_names_the_open_request(monkeypatch):
    class Fake:
        def request(self, method, path, params=None):
            assert method == "GET"
            assert path == "/repos/eclouddev/hlzs_web/pulls/2896"
            return {
                "number": 2896,
                "title": "fix:教学活动",
                "state": "open",
                "user": {"login": "appler2233"},
                "head": {"ref": "intern_manage"},
                "base": {"ref": "master"},
                "html_url": "https://gitee.com/eclouddev/hlzs_web/pulls/2896",
            }

    monkeypatch.setattr("pr_agent.dashboard.actions._client", lambda: Fake())
    detail = pull_detail("https://e.gitee.com/eclouddev/repos/eclouddev/hlzs_web/pulls/2896")

    assert detail["title"] == "fix:教学活动"
    assert detail["author"] == "appler2233"
    assert detail["head"] == "intern_manage"
    assert detail["state_label"] == "开放中"


def test_fetch_submit_returns_the_pipeline_without_a_new_page(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    monkeypatch.setattr(
        "pr_agent.dashboard.page.pull_comments",
        lambda _pr_url: [{
            "body": "Failed to review PR",
            "user": {"login": "bot"},
            "created_at": "2026-10-10T09:42:18+08:00",
        }],
    )

    async def _finished(_pr_url, _command):
        return "已完成"

    monkeypatch.setattr("pr_agent.servers.gitee_app.run_review", _finished)
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    client = TestClient(app)
    response = client.post(
        "/dashboard/run",
        data={"pr_url": "https://gitee.com/eclouddev/hlzs_web/pulls/2896", "command": "review"},
        headers={"X-Requested-With": "fetch"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert response.headers["x-job-id"].isdigit()
    assert "审查失败" in response.text
    assert "审查没有完成" in response.text
    assert "<!doctype" not in response.text.lower()
    assert response.headers.get("location") is None


class _DriveEffects:
    def __init__(self, calls):
        self.calls = calls

    def write_intake(self, intent, head_sha):
        self.calls.append(("受理", intent, head_sha))

    def collect_evidence(self, head_sha):
        self.calls.append(("取证", head_sha))

    def write_verdict(self, verdict, head_sha):
        self.calls.append(("判定", verdict, head_sha))

    def merge(self, head_sha):
        self.calls.append(("汇入", head_sha))


def _store(tmp_path):
    store = FactoryStore(f"sqlite:///{tmp_path}/factory.db")
    store.setup()
    store.add_repo("eclouddev", "hlzs_web")
    return store


def _pull(title="意图：旧版迭代", sha="abc1234567"):
    return {
        "number": 1,
        "title": title,
        "body": "",
        "url": "https://gitee.com/o/r/pulls/1",
        "sha": sha,
    }


def test_autopilot_does_not_merge_a_return_or_invent_an_intent(tmp_path):
    store = _store(tmp_path)
    calls = []
    returned = [
        {"body": "## 受理记录\n\n- 意图：旧版迭代"},
        {"body": "提交号：abc1234567\n\n## PR 审查指南"},
        {"body": "## 判定记录\n\n判定：退回\n提交号：abc1234567"},
    ]
    found = execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull()],
        comments_for=lambda _url: returned,
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )

    assert calls == []
    assert found[0][1].merge is False
    assert "不能汇入" in found[0][1].reason

    calls.clear()
    fresh = execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull("修复晨会")],
        comments_for=lambda _url: [],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )
    assert calls == [("取证", "abc1234567")]
    assert fresh[0][1].collect_evidence is True


def test_a_current_pass_merges_without_confirmation_and_evidence_uses_the_head(monkeypatch, tmp_path):
    monkeypatch.setattr("pr_agent.dashboard.drive.auto_merge_enabled", lambda: True)
    comments = [
        {"body": "## 受理记录\n\n- 意图：旧版迭代"},
        {"body": "提交号：abc1234567\n\n## PR 审查指南"},
        {"body": "## 判定记录\n\n判定：放行\n提交号：abc1234567"},
    ]
    held = []
    execute_registered(
        _store(tmp_path),
        pulls_for=lambda _owner, _repo: [_pull()],
        comments_for=lambda _url: comments,
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(held),
    )
    assert held == [("汇入", "abc1234567")]

    fresh = _store(tmp_path / "next")
    evidence = []
    execute_registered(
        fresh,
        pulls_for=lambda _owner, _repo: [_pull("意图：新业务")],
        comments_for=lambda _url: [{"body": "## 受理记录\n\n- 意图：新业务"}],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(evidence),
    )
    assert evidence == [("取证", "abc1234567")]


def test_merge_pull_stops_when_the_commit_moved():
    class Provider:
        def __init__(self, sha):
            self.sha = sha
            self.merged = False

        def get_pr_head_sha(self):
            return self.sha

        def merge_pull_request(self):
            self.merged = True

    moved = Provider("def1234567")
    assert merge_pull("https://gitee.com/o/r/pulls/1", "abc1234567", provider=moved) is False
    assert moved.merged is False
    current = Provider("abc1234567")
    assert merge_pull("https://gitee.com/o/r/pulls/1", "abc1234567", provider=current) is True
    assert current.merged is True


def test_dashboard_shows_three_modes_and_does_not_present_a_return_as_merged(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    store.add(FactoryRecord(
        "https://gitee.com/o/r/pulls/9", "判定", "判定", "", "退回", "abc1234567", "退回",
    ))
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    client = TestClient(app)
    first = client.get("/dashboard")
    second = client.get("/dashboard")

    assert first.status_code == 200
    assert first.text == second.text
    for body in (first.text, second.text):
        assert "点审查" not in body
        assert "人做抽查" not in body
        assert "运行本轮" not in body
        assert "人工加速" not in body
        assert "辅助驾驶" not in body
        assert "确认这一步" not in body
        assert "判定 退回" in body
        assert "已汇入" not in body
        assert "已合并" not in body


def test_batch_review_button_sits_after_register_and_starts_one_pass(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    started = []
    monkeypatch.setattr(
        "pr_agent.servers.gitee_app.execute_registered",
        lambda *args, **kwargs: started.append(1),
    )
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    client = TestClient(app)
    page = client.get("/dashboard").text
    assert page.index("登记") < page.index("批量审查")
    assert started == []
    response = client.post("/dashboard/drive", follow_redirects=False)
    assert response.status_code == 303
    assert started == [1]


def test_opening_the_dashboard_does_not_start_a_review(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    started = []
    monkeypatch.setattr(
        "pr_agent.servers.gitee_app.execute_registered",
        lambda *args, **kwargs: started.append(1),
    )
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    assert TestClient(app).get("/dashboard").status_code == 200
    assert started == []


def test_a_running_review_is_not_started_again(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    monkeypatch.setattr(
        "pr_agent.dashboard.page.open_pulls",
        lambda _owner, _repo: [{
            "number": 8, "title": "修复晨会", "url": "https://gitee.com/o/r/pulls/8", "sha": "abc1234567",
        }],
    )
    store = FactoryStore(url)
    store.setup()
    store.add_repo("eclouddev", "hlzs_web")
    pr = "https://gitee.com/o/r/pulls/8"
    assert store.begin_job(pr, "review") is not None
    calls = []

    async def _review(_pr_url, _command):
        calls.append("review")
        return "已完成 review"

    monkeypatch.setattr("pr_agent.servers.gitee_app.run_review", _review)
    from fastapi.testclient import TestClient

    from pr_agent.dashboard.page import render_dashboard
    from pr_agent.servers.gitee_app import app

    page = render_dashboard()
    assert "审查中" in page
    assert "移除" in page
    assert "disabled" in page
    response = TestClient(app).post(
        "/dashboard/run", data={"pr_url": pr, "command": "review"}, follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers.get("x-job-id") is None
    assert calls == []


def test_batch_review_starts_without_intent_and_skips_a_recorded_dual_line(tmp_path):
    store = _store(tmp_path)
    calls = []
    execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull("修复晨会"), _pull("意图：双线")],
        comments_for=lambda _url: [],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )
    assert calls == [("取证", "abc1234567"), ("取证", "abc1234567")]

    recorded = []
    execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull("任意标题")],
        comments_for=lambda _url: [{"body": "## 受理记录\n\n- 意图：双线"}],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(recorded),
    )
    assert recorded == []


def test_review_completion_judges_and_merges_only_a_current_pass(monkeypatch, tmp_path):
    monkeypatch.setattr("pr_agent.dashboard.drive.auto_merge_enabled", lambda: True)
    import asyncio

    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    pr = "https://gitee.com/o/r/pulls/1"
    evidence = [
        {"body": "## 受理记录\n\n- 意图：旧版迭代"},
        {"body": "提交号：abc1234567\n\n## PR 审查指南"},
    ]
    published = []
    merged = []
    monkeypatch.setattr("pr_agent.dashboard.drive.pull_comments", lambda _url: evidence)
    monkeypatch.setattr("pr_agent.dashboard.drive.load_rules", lambda _url, _intent: [])
    monkeypatch.setattr(
        "pr_agent.dashboard.drive.merge_pull",
        lambda pr_url, sha, provider=None: merged.append((pr_url, sha)) or True,
    )
    monkeypatch.setattr(
        "pr_agent.dashboard.drive.GiteeEffects._publish",
        lambda self, comment: published.append(comment),
    )

    async def _done(_pr_url, _command):
        return "已完成 review"

    monkeypatch.setattr("pr_agent.servers.gitee_app.run_review", _done)
    from pr_agent.servers.gitee_app import _finish_review_job

    asyncio.run(_finish_review_job(1, pr, "review", "abc1234567"))
    assert any("判定：放行" in comment for comment in published)
    assert merged == [(pr, "abc1234567")]

    published.clear()
    merged.clear()
    monkeypatch.setattr("pr_agent.dashboard.drive.load_rules", lambda _url, _intent: ["严重问题"])
    asyncio.run(_finish_review_job(1, pr, "review", "abc1234567"))
    assert any("判定：退回" in comment for comment in published)
    assert merged == []

    published.clear()
    dual = [
        {"body": "## 受理记录\n\n- 意图：双线"},
        {"body": "提交号：abc1234567\n\n## PR 审查指南"},
    ]
    monkeypatch.setattr("pr_agent.dashboard.drive.pull_comments", lambda _url: dual)
    monkeypatch.setattr("pr_agent.dashboard.drive.load_rules", lambda _url, _intent: [])
    asyncio.run(_finish_review_job(1, pr, "review", "abc1234567"))
    assert published == []
    assert merged == []


def test_newer_return_past_the_first_comment_page_is_not_merged(monkeypatch, tmp_path):
    pages = {
        1: [
            {"body": "## 受理记录\n\n- 意图：旧版迭代"},
            {"body": "提交号：abc1234567\n\n## PR 审查指南"},
            {"body": "## 判定记录\n\n判定：放行\n提交号：abc1234567"},
            *({"body": "普通讨论"} for _ in range(97)),
        ],
        2: [{"body": "## 判定记录\n\n判定：退回\n提交号：abc1234567"}],
    }

    class Fake:
        def request(self, method, path, params=None):
            params = params or {}
            assert params.get("direction") == "asc"
            assert params.get("per_page") == 100
            return pages.get(params.get("page"), [])

    monkeypatch.setattr("pr_agent.dashboard.actions._client", lambda: Fake())
    calls = []
    found = execute_registered(
        _store(tmp_path),
        pulls_for=lambda _owner, _repo: [_pull()],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )
    assert found[0][1].merge is False
    assert "退回" in found[0][1].reason
    assert calls == []


def test_default_batch_review_does_not_merge(tmp_path):
    comments = [
        {"body": "## 受理记录\n\n- 意图：旧版迭代"},
        {"body": "提交号：abc1234567\n\n## PR 审查指南"},
        {"body": "## 判定记录\n\n判定：放行\n提交号：abc1234567"},
    ]
    calls = []
    found = execute_registered(
        _store(tmp_path),
        pulls_for=lambda _owner, _repo: [_pull()],
        comments_for=lambda _url: comments,
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )
    assert calls == []
    assert found[0][1].merge is False
    assert "不自动汇入" in found[0][1].reason


def test_verdict_from_the_conversation_does_not_merge(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    for target in (
        "pr_agent.servers.gitee_app.database_url",
        "pr_agent.dashboard.store.database_url",
    ):
        monkeypatch.setattr(target, lambda: url)
    published = []

    class Provider:
        def get_pr_head_sha(self):
            return "abc1234567"

        def publish_comment(self, comment):
            published.append(comment)

        def merge_pull_request(self):
            raise AssertionError("merged")

    monkeypatch.setattr("pr_agent.git_providers.get_git_provider", lambda: (lambda _pr: Provider()))
    from fastapi.testclient import TestClient

    from pr_agent.dashboard.store import FactoryStore
    from pr_agent.servers.gitee_app import app

    pr = "https://gitee.com/o/r/pulls/4"
    response = TestClient(app).post(
        "/dashboard/verdict", data={"pr_url": pr, "verdict": "退回"}, follow_redirects=False,
    )
    assert response.status_code == 303
    assert any("判定：退回" in comment for comment in published)
    assert FactoryStore(url).latest()[0].verdict == "退回"


def test_pipeline_distinguishes_a_running_review_from_a_finished_one(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr("pr_agent.dashboard.page.pull_comments", lambda _pr: [])
    monkeypatch.setattr("pr_agent.dashboard.page.pull_detail", lambda _pr: {
        "number": 4, "title": "修复", "author": "ada", "head": "topic", "base": "master",
        "url": "https://gitee.com/o/r/pulls/4", "state_label": "开放中",
    })
    store = FactoryStore(url)
    store.setup()
    pr = "https://gitee.com/o/r/pulls/4"
    job_id = store.begin_job(pr, "review")
    store.finish_job(job_id, "运行中", "正在审查")
    from pr_agent.dashboard.page import render_conversation, render_conversation_body

    running = render_conversation_body(pr)
    assert "运行中" in running
    assert "完成" not in running
    page = render_conversation(pr)
    assert 'value="放行"' in page
    assert 'value="退回"' in page
    assert 'value="等待"' in page
    store.finish_job(job_id, "完成", "已完成 review")
    finished = render_conversation_body(pr)
    assert "完成" in finished
    assert "运行中" not in finished


def test_failed_review_keeps_the_error_and_frees_the_button(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    pr = "https://gitee.com/o/r/pulls/4"
    job_id = store.begin_job(pr, "review")

    async def _boom(_pr_url, _command):
        raise RuntimeError("模型超时")

    monkeypatch.setattr("pr_agent.servers.gitee_app.run_review", _boom)
    import asyncio

    from pr_agent.servers.gitee_app import _finish_review_job

    asyncio.run(_finish_review_job(job_id, pr, "review"))
    _job, _command, status, summary, _created = store.jobs_for(pr)[-1]
    assert status == "失败"
    assert "模型超时" in summary
    assert pr not in store.reviewing()


def test_gitee_comment_is_rendered_as_markdown(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    monkeypatch.setattr(
        "pr_agent.dashboard.page.pull_comments",
        lambda _pr_url: [{
            "body": (
                "## 审查要点\n\n<script>alert(1)</script>\n\n**通过** `name`\n\n"
                "| 项 | 结果 |\n| --- | --- |\n| 测试 | 有 |\n"
            ),
            "user": {"login": "bot"},
            "created_at": "2026-10-10T09:42:18+08:00",
        }],
    )
    from pr_agent.dashboard.page import render_conversation_body

    html = render_conversation_body("https://gitee.com/eclouddev/hlzs_web/pulls/2896")

    assert "<h2>审查要点</h2>" in html
    assert "<strong>通过</strong>" in html
    assert "<code>name</code>" in html
    assert "<table>" in html
    assert "<td>有</td>" in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_assisted_dashboard_proposes_a_verdict_without_writing_it(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    pr = "https://gitee.com/o/r/pulls/3"
    sha = "abc1234567"
    store.add(FactoryRecord(pr, "受理", "受理", "旧版迭代", "", sha, "原话"))
    store.add(FactoryRecord(pr, "审查", "取证", "", "", sha, "证据"))

    def forbid(*_args, **_kwargs):
        raise AssertionError("dashboard GET wrote")

    monkeypatch.setattr("pr_agent.dashboard.drive.GiteeEffects.write_verdict", forbid)
    monkeypatch.setattr("pr_agent.dashboard.drive.GiteeEffects.merge", forbid)
    from pr_agent.dashboard.page import render_dashboard

    before = [(row.stage, row.verdict) for row in store.latest()]
    html = render_dashboard()
    assert "提交后直接审查" not in html
    assert "判定为放行" not in html
    assert [(row.stage, row.verdict) for row in store.latest()] == before

    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    page = TestClient(app).get("/dashboard").text
    assert "提交后直接审查" not in page
    assert [(row.stage, row.verdict) for row in store.latest()] == before


def test_drive_pass_reviews_then_merges_only_the_current_pass(monkeypatch, tmp_path):
    monkeypatch.setattr("pr_agent.dashboard.drive.auto_merge_enabled", lambda: True)
    url = f"sqlite:///{tmp_path}/factory.db"
    for target in (
        "pr_agent.servers.gitee_app.database_url",
        "pr_agent.dashboard.drive.database_url",
        "pr_agent.dashboard.store.database_url",
    ):
        monkeypatch.setattr(target, lambda: url)
    store = FactoryStore(url)
    store.setup()
    store.add_repo("eclouddev", "hlzs_web")
    comments = []
    published = []
    merged = []

    monkeypatch.setattr("pr_agent.dashboard.drive.open_pulls", lambda _owner, _repo: [_pull("意图：新业务")])
    monkeypatch.setattr("pr_agent.dashboard.drive.pull_comments", lambda _pr_url: list(comments))
    monkeypatch.setattr("pr_agent.dashboard.drive.load_rules", lambda _pr_url, _intent: [])
    monkeypatch.setattr(
        "pr_agent.dashboard.drive.merge_pull",
        lambda pr_url, sha, provider=None: merged.append((pr_url, sha)) or True,
    )

    def _publish(self, comment):
        published.append(comment)
        comments.append({"body": comment})

    monkeypatch.setattr("pr_agent.dashboard.drive.GiteeEffects._publish", _publish)

    async def _review(_pr_url, _command):
        comments.append({"body": "提交号：abc1234567\n\n## PR 审查指南"})
        return "已完成 review"

    monkeypatch.setattr("pr_agent.servers.gitee_app.run_review", _review)
    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    response = TestClient(app).post("/dashboard/drive", follow_redirects=False)
    missing = TestClient(app).post("/dashboard/mode", data={"mode": "人工加速"}, follow_redirects=False)
    assert missing.status_code == 404

    assert response.status_code == 303
    assert not any("受理记录" in comment for comment in published)
    assert any("判定：放行" in comment for comment in published)
    assert merged == [("https://gitee.com/o/r/pulls/1", "abc1234567")]

    published.clear()
    merged.clear()
    comments.clear()
    comments.append({"body": "## 受理记录\n\n- 意图：双线"})
    comments.append({"body": "提交号：abc1234567\n\n## PR 审查指南"})
    monkeypatch.setattr("pr_agent.dashboard.drive.open_pulls", lambda _owner, _repo: [_pull("意图：双线")])
    again = TestClient(app).post("/dashboard/drive", follow_redirects=False)
    assert again.status_code == 303
    assert merged == []
    assert not any("判定：放行" in comment for comment in published)
