"""Offline unit tests for the Gitee git provider.

Every test stubs the provider's HTTP client, so the suite never reaches gitee.com: the request
shapes asserted here come from Gitee's OpenAPI v5 swagger document and from read-only probes of
the live API, which are run separately by hand.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pr_agent.algo.types import EDIT_TYPE
from pr_agent.config_loader import global_settings
from pr_agent.git_providers import _GIT_PROVIDERS
from pr_agent.git_providers.git_provider import (
    FilePatchInfo,
    GitProvider,
    IncompleteProviderPullRequestFilesError,
    IncrementalPR,
)
from pr_agent.git_providers.gitee_provider import (
    DEFAULT_GITEE_URL,
    MAX_COMMENT_CHARS,
    GiteeApiError,
    GiteeComment,
    GiteeProvider,
    GiteePullRequest,
    IncompleteGiteePullRequestFilesError,
    _GiteeApiClient,
    _GiteeCommitAdapter,
)

PULLS_PATH = "/repos/owner/repo/pulls/7"
PR_COMMITS_PATH = f"{PULLS_PATH}/commits"
PR_COMMENTS_PATH = f"{PULLS_PATH}/comments"
PATCH = "@@ -1,2 +1,2 @@\n a\n-b\n+c\n"


def _provider(**overrides) -> GiteeProvider:
    provider = GiteeProvider.__new__(GiteeProvider)
    provider.logger = MagicMock()
    provider.base_url = "https://gitee.example"
    provider.api_base = "https://gitee.example/api/v5"
    provider.gitee_access_token = "token"
    provider.repo_settings = ".pr_agent.toml"
    provider.owner = "owner"
    provider.repo = "repo"
    provider.pr_number = 7
    provider.issue_number = None
    provider.enabled_pr = True
    provider.enabled_issue = False
    provider.pr_url = "https://gitee.example/owner/repo/pulls/7"
    provider.issue_url = ""
    provider.pr = None
    provider.sha = "head-sha"
    provider.base_sha = "base-sha"
    provider.base_ref = "main"
    provider.git_files = None
    provider.diff_files = None
    provider.file_contents = {}
    provider.filtered_diff_file_names = []
    provider.incremental = IncrementalPR(False)
    provider.comments_list = []
    provider.temp_comments = []
    provider.pr_commits = None
    provider.last_commit = None
    provider.last_commit_id = None
    provider.unreviewed_files_map = {}
    provider.max_comment_chars = MAX_COMMENT_CHARS
    provider._user_login = None
    provider.api = MagicMock()
    for key, value in overrides.items():
        setattr(provider, key, value)
    return provider


def _changed_file(filename: str, **patch_info) -> dict:
    patch_info.setdefault("diff", PATCH)
    return {"filename": filename, "additions": "1", "deletions": "1", "patch": patch_info}


def _diff_file() -> FilePatchInfo:
    return FilePatchInfo(
        base_file="a\nb\n",
        head_file="a\nc\n",
        patch=PATCH,
        filename="app.py",
        num_minus_lines=1,
        num_plus_lines=1,
        edit_type=EDIT_TYPE.MODIFIED,
        old_filename=None,
    )


def _file_by_name(diff_files) -> dict:
    return {file.filename: file for file in diff_files}


class TestRegistration:
    def test_provider_is_registered_under_gitee(self):
        assert _GIT_PROVIDERS["gitee"] is GiteeProvider
        assert issubclass(GiteeProvider, GitProvider)

    def test_is_supported_blocks_only_push_code(self):
        provider = _provider()

        assert provider.is_supported("push_code") is False
        assert provider.is_supported("gfm_markdown") is True
        assert provider.is_supported("get_labels") is True


class TestUrlParsing:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://gitee.com/owner/repo/pulls/7", ("owner", "repo", 7)),
            ("https://gitee.com/owner/repo/pulls/7/files", ("owner", "repo", 7)),
            ("https://gitee.example/gitee/owner/repo/pulls/7/", ("owner", "repo", 7)),
        ],
    )
    def test_parse_pr_url_locates_the_marker(self, url, expected):
        provider = _provider()

        assert provider._parse_pr_url(url) == expected

    @pytest.mark.parametrize(
        "url",
        [
            "https://gitee.com/owner/repo/issues/3",
            "https://gitee.com/owner/repo/pulls/not-a-number",
        ],
    )
    def test_parse_pr_url_rejects_urls_it_cannot_read(self, url):
        provider = _provider()

        with pytest.raises(ValueError):
            provider._parse_pr_url(url)

    def test_parse_issue_url(self):
        provider = _provider()

        assert provider._parse_issue_url("https://gitee.com/owner/repo/issues/3") == ("owner", "repo", 3)


class TestConstructor:
    @patch("pr_agent.git_providers.gitee_provider._GiteeApiClient")
    @patch("pr_agent.git_providers.gitee_provider.get_settings")
    def test_pull_request_init_reads_metadata_diff_shas_and_commits(self, mock_get_settings, mock_client_cls):
        mock_get_settings.return_value.get.side_effect = lambda key, default=None: {
            "GITEE.URL": "https://gitee.example",
            "GITEE.PERSONAL_ACCESS_TOKEN": "token",
        }.get(key, default)
        pr_payload = {
            "title": "Add feature",
            "body": "Body",
            "html_url": "https://gitee.example/owner/repo/pulls/7",
            "user": {"login": "author"},
            "head": {"ref": "feature", "sha": "head-sha"},
            "base": {"ref": "main", "sha": "base-sha"},
        }
        client = mock_client_cls.return_value
        client.request.side_effect = lambda method, path, **_kwargs: (
            pr_payload if path.endswith("/pulls/7") else [{"sha": "head-sha", "commit": {"message": "msg"}}]
        )

        provider = GiteeProvider("https://gitee.example/owner/repo/pulls/7")

        assert (provider.owner, provider.repo, provider.pr_number) == ("owner", "repo", 7)
        assert provider.enabled_pr is True and provider.enabled_issue is False
        assert provider.sha == "head-sha"
        assert provider.base_sha == "base-sha"
        assert provider.base_ref == "main"
        assert provider.get_pr_branch() == "feature"
        assert provider.get_pr_description_full() == "Body"
        # Tools read the pull request by attribute (git_provider.pr.title), so the payload the
        # constructor stores has to answer both spellings.
        assert provider.pr.title == "Add feature"
        assert provider.pr.head.ref == "feature"
        assert provider.last_commit.sha == "head-sha"
        assert provider.api_base == "https://gitee.example/api/v5"
        assert provider.max_comment_chars == MAX_COMMENT_CHARS

    @patch("pr_agent.git_providers.gitee_provider._GiteeApiClient")
    @patch("pr_agent.git_providers.gitee_provider.get_settings")
    def test_issue_init_stops_before_pull_request_calls(self, mock_get_settings, mock_client_cls):
        mock_get_settings.return_value.get.side_effect = lambda key, default=None: {
            "GITEE.URL": "https://gitee.example",
            "GITEE.PERSONAL_ACCESS_TOKEN": "token",
        }.get(key, default)

        provider = GiteeProvider("https://gitee.example/owner/repo/issues/3")

        assert provider.enabled_issue is True and provider.enabled_pr is False
        assert provider.issue_number == 3
        mock_client_cls.return_value.request.assert_not_called()

    @patch("pr_agent.git_providers.gitee_provider._GiteeApiClient")
    @patch("pr_agent.git_providers.gitee_provider.get_settings")
    def test_missing_pull_request_leaves_the_provider_empty(self, mock_get_settings, mock_client_cls):
        mock_get_settings.return_value.get.side_effect = lambda key, default=None: {
            "GITEE.URL": "https://gitee.example",
            "GITEE.PERSONAL_ACCESS_TOKEN": "token",
        }.get(key, default)
        mock_client_cls.return_value.request.return_value = None

        provider = GiteeProvider("https://gitee.example/owner/repo/pulls/7")

        assert provider.sha == ""
        assert provider.pr is None

    @patch("pr_agent.git_providers.gitee_provider.get_settings")
    def test_init_requires_url_and_token(self, mock_get_settings, monkeypatch):
        # GITEE_ACCESS_TOKEN is an accepted fallback, so clear it to exercise the missing-token path.
        monkeypatch.delenv("GITEE_ACCESS_TOKEN", raising=False)
        mock_get_settings.return_value.get.side_effect = lambda key, default=None: {
            "GITEE.URL": "https://gitee.example",
        }.get(key, default)

        with pytest.raises(ValueError, match="PR URL not provided"):
            GiteeProvider("")
        with pytest.raises(ValueError, match="access token not found"):
            GiteeProvider("https://gitee.example/owner/repo/pulls/7")

    def test_api_base_defaults_to_the_url_plus_v5(self):
        with patch("pr_agent.git_providers.gitee_provider.get_settings") as mock_get_settings:
            mock_get_settings.return_value.get.side_effect = lambda key, default=None: {
                "GITEE.PERSONAL_ACCESS_TOKEN": "token",
            }.get(key, default)
            with patch("pr_agent.git_providers.gitee_provider._GiteeApiClient") as client_cls:
                client_cls.return_value.request.return_value = None

                GiteeProvider("https://gitee.example/owner/repo/pulls/7")

        assert client_cls.call_args.args[:2] == (f"{DEFAULT_GITEE_URL}/api/v5", "token")

    def test_read_token_falls_back_to_the_environment(self, monkeypatch):
        monkeypatch.setenv("GITEE_ACCESS_TOKEN", "env-token")
        with patch("pr_agent.git_providers.gitee_provider.get_settings") as mock_get_settings:
            mock_get_settings.return_value.get.return_value = None
            assert GiteeProvider._read_token() == "env-token"
            mock_get_settings.return_value.get.return_value = "settings-token"
            assert GiteeProvider._read_token() == "settings-token"


class TestApiClient:
    def test_build_url_carries_the_token_and_skips_empty_parameters(self):
        client = _GiteeApiClient("https://gitee.example/api/v5", "tok")

        url = client._build_url("/repos/o/r/pulls/1", {"page": 2, "direction": None, "labels": ["a", "b"]})

        assert url.startswith("https://gitee.example/api/v5/repos/o/r/pulls/1?")
        query = url.split("?", 1)[1]
        assert "access_token=tok" in query
        assert "page=2" in query
        assert "direction" not in query
        assert "labels=a&labels=b" in query

    def test_request_returns_none_for_an_allowed_missing_resource(self):
        client = _GiteeApiClient("https://gitee.example/api/v5", "tok")
        client._pool = MagicMock()
        client._pool.request.return_value = SimpleNamespace(status=404, data=b'{"message":"path"}')

        assert client.request("GET", "/repos/o/r/raw/missing.py", allow_404=True) is None

    def test_request_raises_with_the_status_and_body_on_error(self):
        client = _GiteeApiClient("https://gitee.example/api/v5", "tok")
        client._pool = MagicMock()
        client._pool.request.return_value = SimpleNamespace(status=422, data=b'{"message":"bad position"}')

        with pytest.raises(GiteeApiError) as error:
            client.request("POST", "/repos/o/r/pulls/1/comments", body={"body": "x"})

        assert error.value.status == 422
        assert error.value.method == "POST"
        assert "bad position" in error.value.detail

    def test_request_places_writes_in_the_form_body_and_reads_in_the_query(self):
        client = _GiteeApiClient("https://gitee.example/api/v5", "tok")
        client._pool = MagicMock()
        client._pool.request.return_value = SimpleNamespace(status=201, data=b'{"id":1}')

        client.request("POST", "/repos/o/r/pulls/1/comments", body={"body": "x", "position": 3})
        post_call = client._pool.request.call_args
        assert post_call.args[:2] == ("POST", "https://gitee.example/api/v5/repos/o/r/pulls/1/comments?access_token=tok")
        assert post_call.kwargs["fields"] == {"body": "x", "position": 3}
        assert "body" not in post_call.kwargs

        client._pool.request.reset_mock()
        client._pool.request.return_value = SimpleNamespace(status=200, data=b"[]")
        client.request("DELETE", "/repos/o/r/pulls/comments/5")
        delete_call = client._pool.request.call_args
        assert "access_token=tok" in delete_call.args[1]
        assert "fields" not in delete_call.kwargs

    def test_request_sends_a_json_body_when_asked(self):
        client = _GiteeApiClient("https://gitee.example/api/v5", "tok")
        client._pool = MagicMock()
        client._pool.request.return_value = SimpleNamespace(status=201, data=b"[]")

        client.request("POST", "/repos/o/r/pulls/1/labels", json_body=["bug"])

        call = client._pool.request.call_args
        assert json.loads(call.kwargs["body"]) == ["bug"]
        assert call.kwargs["headers"]["Content-Type"] == "application/json"

    def test_transport_errors_are_redacted(self):
        import urllib3

        client = _GiteeApiClient("https://gitee.example/api/v5", "secret-token")
        client._pool = MagicMock()
        client._pool.request.side_effect = urllib3.exceptions.MaxRetryError(
            None, "https://gitee.example/api/v5?access_token=secret-token"
        )

        with pytest.raises(GiteeApiError) as error:
            client.request("GET", "/user")

        # The token rides in the query string, so it must be scrubbed from the message that
        # reaches the log rather than relying on redact_credentials, which only handles userinfo.
        assert "secret-token" not in str(error.value)
        assert "<redacted>" in str(error.value)

    def test_request_bytes_returns_none_for_a_missing_path(self):
        client = _GiteeApiClient("https://gitee.example/api/v5", "tok")
        client._pool = MagicMock()
        client._pool.request.return_value = SimpleNamespace(status=404, data=b'{"message":"path"}')

        assert client.request_bytes("GET", "/repos/o/r/raw/gone.py", allow_404=True) is None


class TestCommits:
    def test_pr_commits_are_reversed_into_oldest_first_order(self):
        provider = _provider()
        provider.api.request.return_value = [
            {"sha": "newest", "commit": {"message": "newest"}},
            {"sha": "head-sha", "commit": {"message": "head"}},
            {"sha": "oldest", "commit": {"message": "oldest"}},
        ]

        provider._set_pr_commits()

        assert [commit.sha for commit in provider.pr_commits] == ["oldest", "head-sha", "newest"]
        assert provider.last_commit.sha == "head-sha"
        assert provider.last_commit_id is provider.last_commit
        provider.api.request.assert_called_once_with("GET", PR_COMMITS_PATH)

    def test_commit_messages_are_numbered_newest_first(self):
        # Gitea parity: the messages are numbered from the head commit backwards, the same
        # order GiteaProvider produces (see test_gitea_provider.py::TestGiteaCommitMessages).
        provider = _provider()
        provider.api.request.return_value = [
            {"sha": "newest", "commit": {"message": "second commit"}},
            {"sha": "oldest", "commit": {"message": "first commit"}},
        ]
        provider._set_pr_commits()

        assert provider.get_commit_messages() == "1. second commit\n2. first commit"

    def test_commit_messages_are_empty_without_commits(self):
        provider = _provider()
        provider.api.request.return_value = []

        provider._set_pr_commits()

        assert provider.get_commit_messages() == ""
        assert provider.last_commit.sha == "head-sha"

    def test_commit_adapter_tolerates_a_missing_message(self):
        assert _GiteeCommitAdapter({"sha": "s"}).message == ""
        assert _GiteeCommitAdapter({"sha": "s", "commit": {"message": "  "}}).message == ""
        assert _GiteeCommitAdapter(None).sha == ""

    def test_latest_commit_url_and_head_sha(self):
        provider = _provider(last_commit=_GiteeCommitAdapter({"sha": "abc123"}))

        assert provider.get_latest_commit_url() == "https://gitee.example/owner/repo/commit/abc123"
        assert provider.get_pr_head_sha() == "head-sha"
        assert provider.get_pr_id() == "repo/7"
        assert provider.get_git_repo_url("") == "https://gitee.example/owner/repo.git"

    def test_latest_commit_url_is_empty_without_a_commit(self):
        assert _provider().get_latest_commit_url() == ""


class TestDiffFiles:
    def test_patch_object_is_normalised_into_edit_type_and_line_counts(self):
        provider = _provider()
        provider.api.request.return_value = [
            _changed_file("app.py"),
            _changed_file("added.py", diff="@@ -0,0 +1 @@\n+new\n", new_file=True),
            _changed_file("gone.py", diff="@@ -1 +0,0 @@\n-old\n", deleted_file=True),
            _changed_file("moved.py", renamed_file=True, old_path="was_moved.py"),
        ]
        provider.api.request_bytes.return_value = b"content\n"

        files = _file_by_name(provider.get_diff_files())

        assert set(files) == {"app.py", "added.py", "gone.py", "moved.py"}
        assert files["app.py"].edit_type is EDIT_TYPE.MODIFIED
        assert files["app.py"].patch == PATCH
        assert files["app.py"].num_plus_lines == 1 and files["app.py"].num_minus_lines == 1
        assert type(files["app.py"].num_plus_lines) is int
        assert files["added.py"].edit_type is EDIT_TYPE.ADDED
        assert files["added.py"].base_file == ""
        assert files["gone.py"].edit_type is EDIT_TYPE.DELETED
        assert files["gone.py"].head_file == ""
        assert files["moved.py"].edit_type is EDIT_TYPE.RENAMED
        assert files["moved.py"].old_filename == "was_moved.py"
        assert files["app.py"].head_file == "content\n"
        assert files["app.py"].base_file == "content\n"

    def test_an_empty_patch_with_equal_revisions_stays_unknown(self):
        provider = _provider()
        provider.api.request.return_value = [_changed_file("app.py", diff="")]
        provider.api.request_bytes.return_value = b"same\n"

        files = _file_by_name(provider.get_diff_files())

        assert files["app.py"].edit_type is EDIT_TYPE.UNKNOWN
        assert files["app.py"].patch == ""

    def test_a_missing_patch_is_rebuilt_from_both_revisions(self):
        provider = _provider()
        provider.api.request.return_value = [_changed_file("app.py", diff="")]
        provider.api.request_bytes.side_effect = lambda method, path, **kwargs: (
            b"old\n" if (kwargs.get("params") or {}).get("ref") == "base-sha" else b"new\n"
        )

        files = _file_by_name(provider.get_diff_files())

        assert files["app.py"].patch.startswith("--- a/app.py\n+++ b/app.py\n")
        assert "-old\n" in files["app.py"].patch
        assert "+new\n" in files["app.py"].patch
        assert files["app.py"].edit_type is EDIT_TYPE.MODIFIED

    def test_files_past_the_full_content_limit_skip_both_revisions(self, monkeypatch):
        import pr_agent.git_providers.gitee_provider as gitee_provider

        monkeypatch.setattr(gitee_provider, "MAX_FILES_ALLOWED_FULL", 1)
        provider = _provider()
        provider.api.request.return_value = [_changed_file("app.py"), _changed_file("second.py")]

        files = _file_by_name(provider.get_diff_files())

        assert files["app.py"].head_file == "" and files["app.py"].base_file == ""
        provider.api.request_bytes.assert_not_called()

    def test_invalid_extensions_are_reported_and_dropped(self):
        provider = _provider()
        provider.api.request.return_value = [_changed_file("app.py"), _changed_file("logo.png")]
        provider.api.request_bytes.return_value = b"content\n"

        assert [file.filename for file in provider.get_diff_files()] == ["app.py"]
        assert provider.filtered_diff_file_names == ["logo.png"]

    def test_ignore_rules_apply_to_gitee_filenames(self, monkeypatch):
        monkeypatch.setattr(global_settings.ignore, "glob", ["*.png", "docs/**"])
        provider = _provider()
        provider.api.request.return_value = [
            _changed_file("app.py"),
            _changed_file("logo.png"),
            _changed_file("docs/guide.md"),
        ]
        provider.api.request_bytes.return_value = b"content\n"

        assert [file.filename for file in provider.get_diff_files()] == ["app.py"]

    def test_inventory_is_cached_and_incomplete_payloads_raise(self):
        provider = _provider()
        provider.api.request.return_value = {"message": "temporarily unavailable"}

        with pytest.raises(IncompleteGiteePullRequestFilesError) as error:
            provider.get_diff_files()

        assert provider.git_files is None
        # The marker is a separate attribute; pr_agent/agent/pr_agent.py matches it to avoid
        # reposting the same notice, and the notice body itself does not embed it.
        assert error.value.notice_marker == "<!-- pr-agent:gitee-incomplete-files -->"
        assert isinstance(error.value, IncompleteProviderPullRequestFilesError)

    def test_an_empty_inventory_is_cached_and_answers_files_and_counts(self):
        provider = _provider()
        provider.api.request.return_value = []

        assert provider.get_files() == []
        assert provider.get_num_of_files() == 0
        provider.api.request.assert_called_once_with("GET", f"{PULLS_PATH}/files")

    def test_diff_files_are_cached_after_the_first_fetch(self):
        provider = _provider()
        provider.api.request.return_value = [_changed_file("app.py")]
        provider.api.request_bytes.return_value = b"content\n"

        assert provider.get_diff_files() is provider.get_diff_files()
        provider.api.request.assert_called_once()


class TestLanguagesAndLabels:
    def test_languages_are_read_from_the_envelope_list(self):
        # Live Gitee answers {"languages": [{"language": "Ruby", "percent": ..., "bytes": ...}, ...]}.
        # The result must be a {name: size} map: get_main_pr_language() and
        # sort_files_by_main_languages() both rank its values.
        provider = _provider()
        provider.api.request.return_value = {"languages": [
            {"language": "Ruby", "color": "#701516", "percent": 68.6, "bytes": 570125},
            {"language": "CSS", "color": "#563d7c", "percent": 6.2, "bytes": 51191},
        ]}

        assert provider.get_languages() == {"Ruby": 570125, "CSS": 51191}
        assert provider.get_languages() == {"Ruby": 570125, "CSS": 51191}
        provider.api.request.assert_called_once_with("GET", "/repos/owner/repo/languages")

    def test_languages_fall_back_to_the_percentage_without_bytes(self):
        provider = _provider()
        provider.api.request.return_value = {"languages": [{"language": "Ruby", "percent": 68.6}]}

        assert provider.get_languages() == {"Ruby": 68.6}

    def test_languages_tolerate_a_flat_map(self):
        provider = _provider()
        provider.api.request.return_value = {"Go": 100.0}

        assert provider.get_languages() == {"Go": 100.0}

    def test_malformed_language_entries_do_not_leak_into_the_map(self):
        provider = _provider()
        provider.api.request.return_value = {"languages": [
            {"language": "Go", "bytes": 10}, {"percent": 1}, "invalid", None, {"language": ""},
        ]}

        assert provider.get_languages() == {"Go": 10}

    def test_an_unexpected_languages_payload_is_empty_and_logged(self):
        provider = _provider()
        provider.api.request.return_value = "not json"

        assert provider.get_languages() == {}
        provider.logger.error.assert_called_once()

    def test_labels_are_read_by_name_and_missing_entries_are_dropped(self):
        provider = _provider()
        provider.api.request.return_value = [{"name": "bug"}, {"name": None}, "invalid"]

        assert provider.get_pr_labels() == ["bug"]

    def test_labels_are_published_as_a_json_array(self):
        provider = _provider()
        provider.api.request.return_value = [{"id": 1}]

        provider.publish_labels(["bug", "", "security"])

        provider.api.request.assert_called_once_with("POST", f"{PULLS_PATH}/labels", json_body=["bug", "security"])

    def test_publishing_no_labels_makes_no_request(self):
        provider = _provider()

        provider.publish_labels([])

        provider.api.request.assert_not_called()

    def test_a_failed_label_request_is_logged_not_raised(self):
        provider = _provider()
        provider.api.request.side_effect = GiteeApiError(403, "POST", f"{PULLS_PATH}/labels", "forbidden")

        provider.publish_labels(["bug"])

        provider.logger.error.assert_called_once()


class TestDescription:
    def test_description_is_published_with_title_and_body(self):
        provider = _provider(pr={"title": "old", "body": "old"})
        provider.api.request.return_value = {"id": 7}

        provider.publish_description("AI title", "New body")

        provider.api.request.assert_called_once_with(
            "PATCH", PULLS_PATH, body={"body": "New body", "title": "AI title"}
        )
        assert provider.pr == {"title": "AI title", "body": "New body"}

    def test_description_only_updates_the_title_when_one_is_given(self):
        provider = _provider(pr={"title": "keep", "body": "old"})
        provider.api.request.return_value = {"id": 7}

        provider.publish_description(None, "New body")

        provider.api.request.assert_called_once_with("PATCH", PULLS_PATH, body={"body": "New body"})

    def test_description_failure_raises(self):
        provider = _provider(pr={"title": "old", "body": "old"})
        provider.api.request.return_value = None

        with pytest.raises(RuntimeError, match="Failed to publish PR description"):
            provider.publish_description("AI title", "New body")


class TestComments:
    def test_comments_read_the_mapping_and_the_attribute_form(self):
        comment = GiteeComment({"id": 5, "body": "hello"})

        assert comment["body"] == "hello"
        assert comment.body == "hello"
        assert comment.raw == {"id": 5, "body": "hello"}
        assert dict(comment) == {"id": 5, "body": "hello"}
        with pytest.raises(AttributeError):
            _ = comment.missing

    def test_comments_are_paginated_oldest_first(self, monkeypatch):
        monkeypatch.setattr("pr_agent.git_providers.gitee_provider.COMMENTS_PER_PAGE", 2)
        provider = _provider()
        pages = {
            1: [{"id": 1, "body": "one"}, {"id": 2, "body": "two"}],
            2: [{"id": 3, "body": "three"}],
        }
        provider.api.request.side_effect = lambda method, path, **kwargs: pages.get(kwargs["params"]["page"], [])

        comments = provider.get_issue_comments()

        assert [comment.body for comment in comments] == ["one", "two", "three"]
        assert provider.api.request.call_args_list[0].kwargs["params"] == {
            "page": 1, "per_page": 2, "direction": "asc",
        }

    def test_comments_stop_at_the_first_empty_page(self):
        provider = _provider()
        provider.api.request.return_value = []

        assert provider.get_issue_comments() == []
        provider.api.request.assert_called_once()

    def test_comments_stop_at_the_page_cap_and_warn(self, monkeypatch):
        monkeypatch.setattr("pr_agent.git_providers.gitee_provider.COMMENTS_PER_PAGE", 1)
        monkeypatch.setattr("pr_agent.git_providers.gitee_provider.MAX_COMMENT_PAGES", 2)
        provider = _provider()
        provider.api.request.return_value = [{"id": 1, "body": "one"}]

        comments = provider.get_issue_comments()

        assert len(comments) == 2
        provider.logger.warning.assert_called_once()

    def test_comments_need_a_pull_request_or_issue_number(self):
        provider = _provider(enabled_pr=False, enabled_issue=False)

        assert provider.get_issue_comments() == []
        provider.api.request.assert_not_called()

    def test_publishing_a_comment_records_it(self):
        provider = _provider()
        provider.api.request.return_value = {"id": 42}

        result = provider.publish_comment("body")

        provider.api.request.assert_called_once_with("POST", PR_COMMENTS_PATH, body={"body": "body"})
        assert result == {"is_temporary": False, "comment": "body", "comment_id": 42}
        assert provider.comments_list == [result]

    def test_a_temporary_comment_is_skipped_when_progress_is_off(self):
        provider = _provider()
        with patch("pr_agent.git_providers.gitee_provider.get_settings") as mock_get_settings:
            mock_get_settings.return_value.config.publish_output_progress = False
            result = provider.publish_comment("progress", is_temporary=True)

        assert result is None
        provider.api.request.assert_not_called()

    def test_a_long_comment_is_truncated_before_it_is_sent(self):
        provider = _provider(max_comment_chars=10)
        provider.api.request.return_value = {"id": 1}

        provider.publish_comment("x" * 500)

        assert provider.api.request.call_args.kwargs["body"] == {"body": "x" * 7 + "..."}

    def test_a_failed_comment_publish_returns_none(self):
        provider = _provider()
        provider.api.request.side_effect = GiteeApiError(500, "POST", PR_COMMENTS_PATH, "boom")

        assert provider.publish_comment("body") is None
        assert provider.comments_list == []

    def test_comment_url_prefers_the_html_url(self):
        provider = _provider(pr={"html_url": "https://gitee.example/owner/repo/pulls/7"})

        assert provider.get_comment_url({"html_url": "https://gitee.example/c/1"}) == "https://gitee.example/c/1"
        assert provider.get_comment_url({"id": 9}) == "https://gitee.example/owner/repo/pulls/7#note_9"
        assert provider.get_comment_url({}) == "https://gitee.example/owner/repo/pulls/7"
        assert provider.get_pr_url() == "https://gitee.example/owner/repo/pulls/7"

    def test_editing_a_comment_targets_its_id(self):
        provider = _provider()
        provider.api.request.return_value = {"id": 5}

        assert provider.edit_comment({"id": 5}, "updated") is True

        provider.api.request.assert_called_once_with(
            "PATCH", "/repos/owner/repo/pulls/comments/5", body={"body": "updated"}
        )

    def test_editing_without_an_id_makes_no_request(self):
        provider = _provider()

        assert provider.edit_comment({"body": "x"}, "updated") is False
        provider.api.request.assert_not_called()

    def test_a_failed_edit_returns_false(self):
        provider = _provider()
        provider.api.request.side_effect = GiteeApiError(404, "PATCH", "/repos/owner/repo/pulls/comments/5", "gone")

        assert provider.edit_comment({"comment_id": 5}, "updated") is False

    def test_removing_a_comment_drops_it_from_the_local_list(self):
        provider = _provider(comments_list=[{"comment_id": 5}])
        provider.api.request.return_value = None

        provider.remove_comment({"comment_id": 5})

        provider.api.request.assert_called_once_with("DELETE", "/repos/owner/repo/pulls/comments/5")
        assert provider.comments_list == []

    def test_a_failed_removal_is_reraised(self):
        provider = _provider()
        provider.api.request.side_effect = GiteeApiError(500, "DELETE", "/repos/owner/repo/pulls/comments/5", "boom")

        with pytest.raises(GiteeApiError):
            provider.remove_comment({"id": 5})

    def test_initial_comment_removal_only_drops_temporary_comments(self):
        temporary_a = {"is_temporary": True, "comment_id": 1}
        permanent = {"is_temporary": False, "comment_id": 2}
        temporary_b = {"is_temporary": True, "comment_id": 3}
        provider = _provider(comments_list=[temporary_a, permanent, temporary_b])
        provider.api.request.return_value = None

        provider.remove_initial_comment()

        assert provider.comments_list == [permanent]

    def test_reaction_removal_reports_success_without_a_backend_call(self):
        provider = _provider()

        assert provider.remove_reaction(1, 2) is True
        provider.api.request.assert_not_called()


class TestInlineComments:
    def test_position_is_resolved_from_an_absolute_line_and_from_content(self):
        provider = _provider(diff_files=[_diff_file()])

        assert provider._inline_position("app.py", 2) == 3
        assert provider._inline_position("`app.py`", "+c") == 3

    def test_position_ignores_the_file_header_of_a_rebuilt_patch(self):
        # A diff rebuilt from both revisions starts with the ---/+++ header. Gitee counts
        # from the line below the first @@ header, so that header must not shift the anchor.
        diff_file = _diff_file()
        diff_file.patch = "--- a/app.py\n+++ b/app.py\n" + PATCH
        provider = _provider(diff_files=[diff_file])

        assert provider._inline_position("app.py", 2) == 3

    def test_position_is_minus_one_for_an_unknown_file(self):
        provider = _provider(diff_files=[_diff_file()])

        assert provider._inline_position("other.py", 2) == -1
        assert provider._inline_position("app.py", None) == -1

    def test_publishing_an_inline_comment_posts_the_diff_position(self):
        provider = _provider(diff_files=[_diff_file()])
        provider.api.request.return_value = {"id": 3}

        assert provider.publish_inline_comment("body", "app.py", 2) is True

        provider.api.request.assert_called_once_with(
            "POST",
            PR_COMMENTS_PATH,
            body={"body": "body", "commit_id": "head-sha", "path": "app.py", "position": 3},
        )

    def test_an_unfindable_line_makes_no_request(self):
        provider = _provider(diff_files=[_diff_file()])

        assert provider.publish_inline_comment("body", "other.py", 2) is False
        provider.api.request.assert_not_called()

    def test_a_failed_inline_publish_returns_false(self):
        provider = _provider(diff_files=[_diff_file()])
        provider.api.request.side_effect = GiteeApiError(400, "POST", PR_COMMENTS_PATH, "bad position")

        assert provider.publish_inline_comment("body", "app.py", 2) is False

    def test_a_partial_inline_failure_still_reports_success(self):
        provider = _provider(diff_files=[_diff_file()])
        provider.api.request.return_value = {"id": 3}

        published = provider.publish_inline_comments([
            {"body": "found", "relevant_file": "app.py", "relevant_line_in_file": 2},
            {"body": "missing", "relevant_file": "other.py", "relevant_line_in_file": 2},
        ])

        assert published is True
        provider.api.request.assert_called_once()

    def test_inline_publishing_reports_failure_when_every_comment_misses(self):
        provider = _provider(diff_files=[_diff_file()])

        assert provider.publish_inline_comments([
            {"body": "missing", "relevant_file": "other.py", "relevant_line_in_file": 2},
        ]) is False

    def test_inline_publishing_of_nothing_is_not_a_failure(self):
        provider = _provider(diff_files=[_diff_file()])

        assert provider.publish_inline_comments([]) is True
        assert provider.publish_inline_comments([{"body": "no file"}]) is True

    def test_code_suggestion_payload_maps_onto_the_inline_comment_keys(self):
        provider = _provider()

        payload = provider._build_code_suggestion_payload({
            "body": "use a constant",
            "relevant_file": "app.py",
            "relevant_lines_start": 12,
            "relevant_lines_end": 12,
        })

        assert payload == {"body": "use a constant", "relevant_file": "app.py", "relevant_line_in_file": 12}

    def test_code_suggestions_are_published_through_the_shared_flow(self):
        provider = _provider(diff_files=[_diff_file()])
        provider.api.request.return_value = {"id": 3}

        published = provider.publish_code_suggestions([{
            "body": "use a constant",
            "relevant_file": "app.py",
            "relevant_lines_start": 2,
            "relevant_lines_end": 2,
        }])

        assert published is True
        assert provider.api.request.call_args.kwargs["body"]["position"] == 3


class TestRepositorySettings:
    def test_local_settings_are_read_from_the_target_ref(self):
        provider = _provider()
        provider._get_global_repo_settings = MagicMock(return_value="")
        provider.api.request_bytes.return_value = b'key = "value"\n'

        assert provider.get_repo_settings() == [("local", b'key = "value"\n')]
        assert provider.api.request_bytes.call_args.kwargs["params"] == {"ref": "base-sha"}

    def test_global_settings_come_first(self):
        provider = _provider()
        provider._get_global_repo_settings = MagicMock(return_value=b"global\n")
        provider.api.request_bytes.return_value = b"local\n"

        assert provider.get_repo_settings() == [("global", b"global\n"), ("local", b"local\n")]

    def test_missing_local_settings_return_the_global_list_alone(self):
        provider = _provider()
        provider._get_global_repo_settings = MagicMock(return_value=b"global\n")
        provider.api.request_bytes.return_value = None

        assert provider.get_repo_settings() == [("global", b"global\n")]

    def test_settings_need_a_target_ref(self):
        provider = _provider(base_sha="", base_ref="")
        provider._get_global_repo_settings = MagicMock(return_value="")

        assert provider.get_repo_settings() == ""
        provider.api.request_bytes.assert_not_called()

    def test_global_settings_are_fetched_from_the_namespace_repository(self):
        provider = _provider()
        provider.api.request.return_value = {"default_branch": "master"}
        provider.api.request_bytes.return_value = b"global\n"

        assert provider._fetch_global_repo_settings("owner", "settings-repo") == b"global\n"
        provider.api.request.assert_called_once_with("GET", "/repos/owner/settings-repo", allow_404=True)
        assert provider.api.request_bytes.call_args.kwargs["params"] == {"ref": "master"}

    def test_a_missing_global_settings_repository_is_empty(self):
        provider = _provider()
        provider.api.request.return_value = None

        assert provider._fetch_global_repo_settings("owner", "settings-repo") == ""

    def test_namespace_and_cache_key_are_gitee_scoped(self):
        provider = _provider()

        assert provider.get_owning_namespace() == "owner"
        assert provider._get_global_settings_cache_key("owner") == "gitee:https://gitee.example/api/v5:owner"

    def test_repo_file_content_reads_the_target_ref_by_default(self):
        provider = _provider()
        provider.api.request_bytes.return_value = b"file\n"

        assert provider.get_repo_file_content("docs/readme.md") == "file\n"
        assert provider.api.request_bytes.call_args.args[1].endswith("/raw/docs/readme.md")
        assert provider.api.request_bytes.call_args.kwargs["params"] == {"ref": "base-sha"}

    def test_repo_file_content_can_read_the_default_branch(self):
        provider = _provider()
        provider.api.request.return_value = {"default_branch": "master"}
        provider.api.request_bytes.return_value = b"file\n"

        assert provider.get_repo_file_content("docs/readme.md", from_default_branch=True) == "file\n"
        assert provider.api.request_bytes.call_args.kwargs["params"] == {"ref": "master"}

    def test_repo_context_ref_follows_the_same_refs(self):
        provider = _provider()

        assert provider.get_repo_context_ref() == "base-sha"
        assert _provider(base_sha="", base_ref="main").get_repo_context_ref() == "main"

    def test_missing_files_read_as_empty_without_raising(self):
        provider = _provider()
        provider.api.request_bytes.return_value = None

        assert provider._get_file_content("gone.py", "base-sha") == ""


class TestPullRequestPayload:
    def test_the_same_payload_reads_by_key_and_by_attribute(self):
        provider = _provider(pr=GiteePullRequest({"title": "Add feature", "head": {"ref": "feature"}}))

        assert provider.pr.title == "Add feature"
        assert provider.pr["title"] == "Add feature"
        assert provider.pr.head.ref == "feature"
        assert provider.pr.get("title") == "Add feature"
        # Wrapping must not change what callers compare the payload against.
        assert provider.pr == {"title": "Add feature", "head": {"ref": "feature"}}

    def test_an_absent_field_raises_attribute_error(self):
        provider = _provider(pr=GiteePullRequest({"title": "Add feature"}))

        with pytest.raises(AttributeError):
            _ = provider.pr.missing


class TestIdentityAndPolicy:
    def test_user_id_is_read_once_and_cached(self):
        provider = _provider()
        provider.api.request.return_value = {"login": "pr-agent-bot"}

        assert provider.get_user_id() == "pr-agent-bot"
        assert provider.get_user_id() == "pr-agent-bot"
        provider.api.request.assert_called_once_with("GET", "/user")

    def test_user_id_falls_back_to_the_pull_request_author(self):
        provider = _provider(pr={"user": {"login": "author"}})
        provider.api.request.side_effect = GiteeApiError(403, "GET", "/user", "forbidden")

        assert provider.get_user_id() == "author"
        provider.logger.warning.assert_called_once()

    def test_identity_predicates_stay_conservative(self):
        provider = GitProvider.__new__(GiteeProvider)

        assert provider.supports_review_comment_identity() is False
        assert provider.supports_review_finding_state() is False
        assert provider.supports_thread_resolution() is False

    def test_policy_metadata_is_read_from_the_pull_request_payload(self):
        provider = _provider(pr={
            "title": "Add feature",
            "user": {"login": "author"},
            "head": {"ref": "feature"},
            "base": {"ref": "main"},
        })

        metadata = provider.get_request_policy_metadata(set())

        assert metadata == {
            "title": "Add feature",
            "sender": "author",
            "repo_full_name": "owner/repo",
            "source_branch": "feature",
            "target_branch": "main",
            "labels": (),
        }
        provider.api.request.assert_not_called()

    def test_policy_metadata_reads_labels_only_when_asked(self):
        provider = _provider(pr={"title": "t", "user": {}, "head": {}, "base": {}})
        provider.api.request.return_value = [{"name": "bug"}]

        assert provider.get_request_policy_metadata({"labels"})["labels"] == ["bug"]
        provider.api.request.assert_called_once()

    def test_policy_metadata_without_a_pull_request_is_empty(self):
        provider = _provider()

        metadata = provider.get_request_policy_metadata(set())

        assert metadata["title"] == "" and metadata["repo_full_name"] == "owner/repo"


class TestCloneUrl:
    def test_credentials_are_embedded_for_private_repositories(self):
        provider = _provider(_user_login="pr-agent-bot")

        url = provider._prepare_clone_url_with_token("https://gitee.example/owner/repo.git")

        assert url == "https://pr-agent-bot:token@gitee.example/owner/repo.git"

    def test_the_token_alone_is_enough_to_clone(self):
        provider = _provider(_user_login="")

        url = provider._prepare_clone_url_with_token("https://gitee.example/owner/repo.git")

        assert url == "https://token@gitee.example/owner/repo.git"

    def test_a_foreign_host_is_rejected(self):
        provider = _provider(_user_login="bot")

        assert provider._prepare_clone_url_with_token("https://github.com/owner/repo.git") is None
        provider.logger.error.assert_called_once()

    def test_a_missing_token_is_rejected(self):
        provider = _provider(gitee_access_token="")

        assert provider._prepare_clone_url_with_token("https://gitee.example/owner/repo.git") is None


class TestLineLinks:
    def test_line_link_targets_the_pr_branch(self):
        provider = _provider(pr={"head": {"ref": "feature/x"}})

        assert provider.get_line_link("src/app.py", -1) == (
            "https://gitee.example/owner/repo/blob/feature/x/src/app.py"
        )
        assert provider.get_line_link("src/app.py", 7) == (
            "https://gitee.example/owner/repo/blob/feature/x/src/app.py#L7"
        )
        assert provider.get_line_link("src/app.py", 4, 10) == (
            "https://gitee.example/owner/repo/blob/feature/x/src/app.py#L4-L10"
        )
