import pytest

from pr_agent.dashboard.actions import parse_repo, pull_detail


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
