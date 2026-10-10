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


def _store(tmp_path, mode="自动驾驶"):
    store = FactoryStore(f"sqlite:///{tmp_path}/factory.db")
    store.setup()
    store.add_repo("eclouddev", "hlzs_web")
    store.set_mode(mode)
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
    unknown = execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull("修复晨会")],
        comments_for=lambda _url: [],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )
    assert calls == []
    assert unknown[0][1].action == "留给人工"


def test_assisted_merge_waits_for_confirmation_and_autopilot_binds_evidence(tmp_path):
    comments = [
        {"body": "## 受理记录\n\n- 意图：旧版迭代"},
        {"body": "提交号：abc1234567\n\n## PR 审查指南"},
        {"body": "## 判定记录\n\n判定：放行\n提交号：abc1234567"},
    ]
    assisted = _store(tmp_path, "辅助驾驶")
    held = []
    execute_registered(
        assisted,
        pulls_for=lambda _owner, _repo: [_pull()],
        comments_for=lambda _url: comments,
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(held),
    )
    assert held == []

    execute_registered(
        assisted,
        confirmed_url="https://gitee.com/o/r/pulls/1",
        pulls_for=lambda _owner, _repo: [_pull()],
        comments_for=lambda _url: comments,
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(held),
    )
    assert held == [("汇入", "abc1234567")]

    fresh = _store(tmp_path / "next", "自动驾驶")
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
        assert "人工加速" in body
        assert "辅助驾驶" in body
        assert "自动驾驶" in body
        assert "不能汇入" in body
        assert "已汇入" not in body
        assert "已合并" not in body


def test_autopilot_intake_continues_into_evidence_and_stops_before_merge(tmp_path):
    store = _store(tmp_path)
    calls = []
    execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull("意图：新业务")],
        comments_for=lambda _url: [],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(calls),
    )
    assert calls == [("受理", "新业务", "abc1234567"), ("取证", "abc1234567")]

    dual = []
    execute_registered(
        store,
        pulls_for=lambda _owner, _repo: [_pull("意图：双线")],
        comments_for=lambda _url: [],
        rules_for=lambda *_args: [],
        effects_for=lambda _url: _DriveEffects(dual),
    )
    assert dual == [("受理", "双线", "abc1234567")]


def test_review_completion_judges_and_merges_only_a_current_pass(monkeypatch, tmp_path):
    import asyncio

    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    store.set_mode("自动驾驶")
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


def test_assisted_dashboard_proposes_a_verdict_without_writing_it(monkeypatch, tmp_path):
    url = f"sqlite:///{tmp_path}/factory.db"
    monkeypatch.setattr("pr_agent.dashboard.page.database_url", lambda: url)
    store = FactoryStore(url)
    store.setup()
    store.set_mode("辅助驾驶")
    pr = "https://gitee.com/o/r/pulls/3"
    sha = "abc1234567"
    store.add(FactoryRecord(pr, "受理", "受理", "旧版迭代", "", sha, "原话"))
    store.add(FactoryRecord(pr, "审查", "取证", "", "", sha, "证据"))
    monkeypatch.setattr("pr_agent.dashboard.page.load_rules", lambda _pr_url, _intent: [])

    def forbid(*_args, **_kwargs):
        raise AssertionError("dashboard GET wrote")

    monkeypatch.setattr("pr_agent.dashboard.drive.GiteeEffects.write_verdict", forbid)
    monkeypatch.setattr("pr_agent.dashboard.drive.GiteeEffects.merge", forbid)
    from pr_agent.dashboard.page import render_dashboard

    before = [(row.stage, row.verdict) for row in store.latest()]
    html = render_dashboard()
    assert "提案" in html
    assert "确认这一步" in html
    assert "建议判定为放行" in html
    assert [(row.stage, row.verdict) for row in store.latest()] == before

    from fastapi.testclient import TestClient

    from pr_agent.servers.gitee_app import app

    monkeypatch.setattr("pr_agent.servers.gitee_app.database_url", lambda: url)
    page = TestClient(app).get("/dashboard").text
    assert "确认这一步" in page
    assert "提案" in page
    assert [(row.stage, row.verdict) for row in store.latest()] == before


def test_autopilot_mode_switch_reviews_then_merges_only_the_current_pass(monkeypatch, tmp_path):
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

    response = TestClient(app).post("/dashboard/mode", data={"mode": "自动驾驶"}, follow_redirects=False)

    assert response.status_code == 303
    assert any("受理记录" in comment and "意图：新业务" in comment for comment in published)
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
