"""Gitee (gitee.com) git provider.

Implements the ``GitProvider`` contract against Gitee's OpenAPI v5
(``https://gitee.com/api/v5``). Gitee's surface is GitHub-shaped, but several response
details differ from GitHub - and from Gitea, which is a different host with its own
``/api/v1`` - so this module normalises each one:

* the changed-files ``patch`` field is an object (``diff`` plus ``new_file`` /
  ``renamed_file`` / ``deleted_file`` / ``too_large`` flags) rather than a unified-diff
  string, and ``diff`` comes back empty for very large files, so those files fall back to
  fetching both revisions and rebuilding the diff;
* ``additions`` / ``deletions`` are strings and ``status`` is usually absent, so the edit
  type is derived from the ``patch`` flags;
* ``languages`` is wrapped in a ``{"languages": {...}}`` envelope;
* reading a path that does not exist answers HTTP 404 from ``/raw/{path}`` (unlike
  ``/contents/{path}``, which answers HTTP 200 with a ``[]`` body);
* a PR has no separate issue-comments route: ``/pulls/{number}/comments`` returns the whole
  timeline and its ``comment_type`` separates diff comments from ordinary ones.
"""

from __future__ import annotations

import difflib
import json
import os
from collections.abc import Iterator, Mapping
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode, urlparse

import urllib3

from pr_agent.agent.request_policy import policy_metadata, policy_value
from pr_agent.algo.file_filter import filter_ignored
from pr_agent.algo.git_patch_processing import decode_if_bytes
from pr_agent.algo.language_handler import is_valid_file
from pr_agent.algo.token_budget import clip_tokens
from pr_agent.algo.types import EDIT_TYPE
from pr_agent.algo.utils import find_line_number_of_relevant_line_in_file
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.git_provider import (
    MAX_FILES_ALLOWED_FULL,
    FilePatchInfo,
    GitProvider,
    IncompleteProviderPullRequestFilesError,
    IncrementalPR,
    cache_languages,
    redact_credentials,
)
from pr_agent.git_providers.request_timeout import get_http_request_timeout
from pr_agent.log import get_logger

# Shipped default for the [gitee] url setting in configuration.toml.
DEFAULT_GITEE_URL = "https://gitee.com"
# API path appended to [gitee] url when [gitee] api_base is not set.
GITEE_API_PATH = "/api/v5"
# Gitee comment bodies are plain markdown; the cap keeps a single request from growing unbounded.
MAX_COMMENT_CHARS = 65000
# Gitee caps per_page at 100; the page cap bounds a pathologically chatty PR.
COMMENTS_PER_PAGE = 100
MAX_COMMENT_PAGES = 20


class GiteeApiError(RuntimeError):
    """A non-2xx answer from the Gitee API."""

    def __init__(self, status: int, method: str, path: str, detail: str = ""):
        self.status = status
        self.method = method
        self.path = path
        self.detail = detail
        super().__init__(f"Gitee API {method} {path} failed with HTTP {status}: {detail[:300]}")


class IncompleteGiteePullRequestFilesError(IncompleteProviderPullRequestFilesError):
    """Represent an unavailable or malformed Gitee changed-file inventory."""

    notice = (
        "## PR-Agent command was not run\n\n"
        "Gitee returned incomplete or unavailable pull-request change data, so PR-Agent stopped "
        "instead of analyzing only part of it.\n\n"
        "Retry the command and check the pull request's changed files and diff in Gitee if the problem persists."
    )
    notice_marker = "<!-- pr-agent:gitee-incomplete-files -->"


class GiteeComment(Mapping):
    """A Gitee comment that reads both as a mapping and through attributes.

    Callers in this repo address comments both ways: the shared persistent-comment code uses
    ``comment.get("body")`` or ``getattr(comment, "body")``, while tools written for
    GitHub-shaped objects use ``comment.body``.
    """

    __slots__ = ("_raw",)

    def __init__(self, raw: Optional[Mapping[str, Any]] = None):
        object.__setattr__(self, "_raw", dict(raw or {}))

    def __getitem__(self, key: str) -> Any:
        return self._raw[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._raw)

    def __len__(self) -> int:
        return len(self._raw)

    def __getattr__(self, name: str) -> Any:
        # Guard the slot itself: without this, reading `_raw` before __init__ has run would
        # recurse through __getattr__ instead of failing.
        if name == "_raw":
            raise AttributeError(name)
        try:
            return object.__getattribute__(self, "_raw")[name]
        except KeyError as e:
            raise AttributeError(name) from e

    @property
    def raw(self) -> Dict[str, Any]:
        return self._raw


class GiteePullRequest(dict):
    """The pull-request payload with both mapping and attribute access.

    Tools read the provider's pull request by attribute (``git_provider.pr.title``) while this
    provider reads the same payload as a mapping (``pr["title"]``, ``pr.get("head")``), so the
    payload is wrapped once and both spellings work. Nested objects are wrapped on access.
    """

    def __getattr__(self, name: str) -> Any:
        # Dunder lookups (copy, pickle) must fail normally rather than resolve a payload key.
        if name.startswith("__"):
            raise AttributeError(name)
        try:
            value = self[name]
        except KeyError as e:
            raise AttributeError(name) from e
        return GiteePullRequest(value) if isinstance(value, Mapping) else value


class _GiteeCommitAdapter:
    """Mimics the PyGithub ``Commit`` shape (``.sha``, ``.html_url``, ``.message``)."""

    def __init__(self, raw: Optional[Mapping[str, Any]] = None):
        raw = raw or {}
        self.sha = raw.get("sha") or ""
        self.html_url = raw.get("html_url") or ""
        # Gitee nests the commit subject under `commit`, mirroring the GitHub payload.
        commit = raw.get("commit")
        message = commit.get("message") if isinstance(commit, Mapping) else None
        self.message = message if isinstance(message, str) and message.strip() else ""


class _GiteeApiClient:
    """Thin urllib3 client for Gitee OpenAPI v5.

    Gitee documents the personal access token as an ``access_token`` query parameter, so the
    token travels in the query string while every other parameter follows the location the
    endpoint declares (query string or form body).
    """

    # urllib3 encodes fields into the query string for these methods and into the body otherwise.
    _URL_ENCODED_METHODS = frozenset({"GET", "HEAD", "DELETE", "OPTIONS"})

    def __init__(self, api_base: str, token: str, *, verify_ssl: bool = True, ca_cert: Optional[str] = None):
        self.api_base = api_base.rstrip("/")
        self.token = token
        self._pool = urllib3.PoolManager(
            cert_reqs="CERT_REQUIRED" if verify_ssl else "CERT_NONE",
            ca_certs=ca_cert or None,
            retries=urllib3.Retry(total=2, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)),
        )
        self._logger = get_logger()

    def _redact(self, text: Any) -> str:
        """Remove the access token from text that may reach a log line.

        Gitee takes the token as a query parameter rather than a header, so a urllib3 error
        carrying the request URL - or an error body echoing it - would otherwise leak it.
        """
        if not text:
            return ""
        return str(text).replace(self.token, "<redacted>") if self.token else str(text)

    def _build_url(self, path: str, params: Optional[Mapping[str, Any]]) -> str:
        query: Dict[str, Any] = {"access_token": self.token}
        for key, value in (params or {}).items():
            if value is not None:
                query[key] = value
        return f"{self.api_base}{path}?{urlencode(query, doseq=True)}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        body: Optional[Mapping[str, Any]] = None,
        json_body: Any = None,
        expect_json: bool = True,
        allow_404: bool = False,
    ) -> Any:
        """Call one v5 endpoint.

        ``allow_404`` turns a missing resource into ``None`` for callers that treat absence as
        an empty answer (a file that does not exist at the requested revision, a settings
        repository that is not configured).
        """
        method = method.upper()
        url = self._build_url(path, params)
        timeout = urllib3.Timeout(connect=get_http_request_timeout(), read=get_http_request_timeout())
        kwargs: Dict[str, Any] = {"timeout": timeout, "headers": {"Accept": "application/json"}}
        if method not in self._URL_ENCODED_METHODS:
            if json_body is not None:
                kwargs["body"] = json.dumps(json_body).encode("utf-8")
                kwargs["headers"] = {**kwargs["headers"], "Content-Type": "application/json"}
            else:
                kwargs["fields"] = {k: v for k, v in (body or {}).items() if v is not None}
        try:
            response = self._pool.request(method, url, **kwargs)
        except urllib3.exceptions.HTTPError as e:
            raise GiteeApiError(0, method, path, self._redact(redact_credentials(str(e)))) from e

        if allow_404 and response.status == 404:
            return None
        if response.status >= 400:
            raise GiteeApiError(response.status, method, path, self._redact(decode_if_bytes(response.data)))
        if not expect_json or response.status == 204 or not response.data:
            return None
        try:
            return json.loads(response.data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise GiteeApiError(response.status, method, path, "response was not valid JSON") from e

    def request_bytes(self, method: str, path: str, *, params: Optional[Mapping[str, Any]] = None,
                      allow_404: bool = False) -> Optional[bytes]:
        """Call an endpoint that answers with raw text (``/raw/{path}``)."""
        url = self._build_url(path, params)
        try:
            response = self._pool.request(
                method.upper(), url,
                timeout=urllib3.Timeout(connect=get_http_request_timeout(), read=get_http_request_timeout()),
                headers={"Accept": "text/plain, */*"},
            )
        except urllib3.exceptions.HTTPError as e:
            raise GiteeApiError(0, method, path, self._redact(redact_credentials(str(e)))) from e
        if allow_404 and response.status == 404:
            return None
        if response.status >= 400:
            raise GiteeApiError(response.status, method, path, self._redact(decode_if_bytes(response.data)))
        return response.data


class GiteeProvider(GitProvider):
    def __init__(self, url: Optional[str] = None):
        super().__init__()
        self.logger = get_logger()

        if not url:
            self.logger.error("PR URL not provided.")
            raise ValueError("PR URL not provided.")

        self.base_url = str(get_settings().get("GITEE.URL", DEFAULT_GITEE_URL) or DEFAULT_GITEE_URL).rstrip("/")
        api_base = get_settings().get("GITEE.API_BASE", None)
        self.api_base = str(api_base).rstrip("/") if api_base else f"{self.base_url}{GITEE_API_PATH}"
        self.gitee_access_token = self._read_token()
        if not self.gitee_access_token:
            self.logger.error("Gitee access token not found in settings.")
            raise ValueError("Gitee access token not found in settings.")
        self.repo_settings = get_settings().get("GITEE.REPO_SETTING", ".pr_agent.toml")

        self.api = _GiteeApiClient(
            self.api_base,
            self.gitee_access_token,
            verify_ssl=not get_settings().get("GITEE.SKIP_SSL_VERIFICATION", False),
            ca_cert=get_settings().get("GITEE.SSL_CA_CERT", None),
        )

        self.pr_url = ""
        self.issue_url = ""
        self.owner: Optional[str] = None
        self.repo: Optional[str] = None
        self.pr_number: Optional[int] = None
        self.issue_number: Optional[int] = None
        self.enabled_pr = False
        self.enabled_issue = False
        self.pr: Optional[GiteePullRequest] = None
        self.git_files: Optional[List[Dict[str, Any]]] = None
        self.file_contents: Dict[str, str] = {}
        self.sha = ""
        self.base_sha = ""
        self.base_ref = ""
        self.diff_files: Optional[List[FilePatchInfo]] = None
        self.filtered_diff_file_names: List[str] = []
        self.incremental = IncrementalPR(False)
        self.comments_list: List[Dict[str, Any]] = []
        self.temp_comments: List[str] = []
        self.pr_commits: Optional[List[_GiteeCommitAdapter]] = None
        self.last_commit: Optional[_GiteeCommitAdapter] = None
        self.last_commit_id: Optional[_GiteeCommitAdapter] = None
        self.unreviewed_files_map: Dict[str, str] = {}
        self.max_comment_chars = MAX_COMMENT_CHARS
        self._user_login: Optional[str] = None

        if "pulls" in url:
            self.pr_url = url
            self._set_repo_and_owner_from_pr()
            self.enabled_pr = True
            payload = self.api.request(
                "GET", f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}", allow_404=True
            )
            self.pr = GiteePullRequest(payload) if isinstance(payload, Mapping) else None
            if not self.pr:
                self.logger.error(f"Failed to fetch Gitee pull request: {url}")
                return
            self.sha = self._head_field("sha")
            self.base_sha = self._base_field("sha")
            self.base_ref = self._base_field("ref")
            self._set_pr_commits()
        elif "issues" in url:
            self.issue_url = url
            self._set_repo_and_owner_from_issue()
            self.enabled_issue = True
        else:
            self.logger.error(f"Unsupported Gitee URL, expected a pull request or issue URL: {url}")

    def get_request_policy_metadata(self, required_fields: set[str]) -> dict:
        pr = self.pr
        if not isinstance(pr, Mapping):
            return policy_metadata(title="", sender="", repo_full_name=f"{self.owner}/{self.repo}",
                                   source_branch="", target_branch="")
        return policy_metadata(title=pr.get("title"), sender=policy_value(pr, "user", "login"),
                               repo_full_name=f"{self.owner}/{self.repo}",
                               source_branch=policy_value(pr, "head", "ref"),
                               target_branch=policy_value(pr, "base", "ref"),
                               labels=self.get_pr_labels() if "labels" in required_fields else ())

    # ------------------------------------------------------------------ setup helpers

    @staticmethod
    def _read_token() -> Optional[str]:
        """Read the Gitee personal access token.

        ``GITEE.PERSONAL_ACCESS_TOKEN`` is the documented setting (``GITEE__PERSONAL_ACCESS_TOKEN``
        as an environment variable). The flat ``GITEE_ACCESS_TOKEN`` variable is accepted as a
        fallback because it is the name Gitee's own tooling exports.
        """
        token = get_settings().get("GITEE.PERSONAL_ACCESS_TOKEN", None)
        if not token:
            token = os.environ.get("GITEE_ACCESS_TOKEN")
        token = str(token).strip() if token else ""
        return token or None

    @staticmethod
    def _url_path_parts(url: str) -> List[str]:
        return [part for part in urlparse(url).path.strip("/").split("/") if part]

    @classmethod
    def _parse_marker_url(cls, url: str, marker: str) -> Tuple[str, str, int]:
        """Parse ``.../{owner}/{repo}/{marker}/{number}``, tolerating a host install subpath.

        The marker is located by name rather than by fixed index so an instance served under a
        subpath (``https://host/gitee/owner/repo/pulls/1``) and URLs carrying extra trailing
        segments (``/pulls/1/files``) both resolve.
        """
        parts = cls._url_path_parts(url)
        indexes = [index for index, part in enumerate(parts) if part == marker]
        if not indexes:
            raise ValueError(f"The provided URL does not appear to be a Gitee {marker} URL")
        index = indexes[0]
        if index < 2 or index + 1 >= len(parts):
            raise ValueError(f"The provided URL does not appear to be a Gitee {marker} URL")
        owner, repo = parts[index - 2], parts[index - 1]
        try:
            number = int(parts[index + 1])
        except ValueError as e:
            raise ValueError(f"Unable to convert {marker} number to integer") from e
        return owner, repo, number

    def _parse_pr_url(self, pr_url: str) -> Tuple[str, str, int]:
        return self._parse_marker_url(pr_url, "pulls")

    def _parse_issue_url(self, issue_url: str) -> Tuple[str, str, int]:
        return self._parse_marker_url(issue_url, "issues")

    def _set_repo_and_owner_from_pr(self) -> None:
        try:
            self.owner, self.repo, self.pr_number = self._parse_pr_url(self.pr_url)
            self.logger.info(f"Owner: {self.owner}, Repo: {self.repo}, PR Number: {self.pr_number}")
        except ValueError as e:
            self.logger.error(f"Error parsing PR URL: {e}")

    def _set_repo_and_owner_from_issue(self) -> None:
        try:
            self.owner, self.repo, self.issue_number = self._parse_issue_url(self.issue_url)
            self.logger.info(f"Owner: {self.owner}, Repo: {self.repo}, Issue Number: {self.issue_number}")
        except ValueError as e:
            self.logger.error(f"Error parsing issue URL: {e}")

    def _head_field(self, field: str) -> str:
        head = (self.pr or {}).get("head") or {}
        return head.get(field) or ""

    def _base_field(self, field: str) -> str:
        base = (self.pr or {}).get("base") or {}
        return base.get(field) or ""

    def _set_pr_commits(self) -> None:
        """Load the commits of the PR itself, not the commits of the repository's default branch."""
        raw_commits = self.api.request(
            "GET", f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}/commits"
        ) or []
        if not isinstance(raw_commits, list):
            self.logger.error(f"Unexpected PR commits payload type: {type(raw_commits)}")
            raw_commits = []
        # Gitee returns PR commits newest-first; oldest-first matches GitHub iteration order.
        self.pr_commits = [
            _GiteeCommitAdapter(commit) for commit in reversed(raw_commits) if isinstance(commit, Mapping)
        ]
        if not self.pr_commits:
            self.logger.error("Failed to get PR commits")
        # Fall back to a commit wrapping the PR head SHA rather than None, so callers that
        # dereference the last commit always have a valid .sha.
        self.last_commit = next(
            (commit for commit in self.pr_commits if commit.sha and commit.sha == self.sha),
            self.pr_commits[-1] if self.pr_commits else _GiteeCommitAdapter({"sha": self.sha}),
        )
        self.last_commit_id = self.last_commit

    # ------------------------------------------------------------------ identity and links

    def get_user_id(self) -> str:
        """Return the login of the authenticated user, falling back to the PR author."""
        if self._user_login is None:
            self._user_login = ""
            try:
                user = self.api.request("GET", "/user")
                if isinstance(user, Mapping):
                    self._user_login = user.get("login") or ""
            except GiteeApiError as e:
                self.logger.warning(f"Could not read the authenticated Gitee user: {e}")
        if self._user_login:
            return self._user_login
        return str(((self.pr or {}).get("user") or {}).get("login") or "")

    def get_pr_url(self) -> str:
        html_url = (self.pr or {}).get("html_url")
        if html_url:
            return html_url
        if not (self.owner and self.repo and self.pr_number):
            return self.pr_url
        return f"{self.base_url}/{self.owner}/{self.repo}/pulls/{self.pr_number}"

    def get_latest_commit_url(self) -> str:
        if not (self.last_commit and self.last_commit.sha):
            return ""
        return f"{self.base_url}/{self.owner}/{self.repo}/commit/{self.last_commit.sha}"

    def get_pr_head_sha(self) -> str:
        return self.sha or ""

    def get_comment_url(self, comment) -> str:
        html_url = self._comment_field(comment, "html_url")
        if isinstance(html_url, str) and html_url:
            return html_url
        comment_id = self._comment_id(comment)
        if comment_id and self.owner and self.repo:
            return f"{self.get_pr_url()}#note_{comment_id}"
        return self.get_pr_url()

    def get_pr_id(self) -> str:
        if not (self.repo and self.pr_number):
            return ""
        return f"{self.repo}/{self.pr_number}"

    def get_line_link(self, relevant_file: str, relevant_line_start: int, relevant_line_end: int = None) -> str:
        branch = quote(self.get_pr_branch())
        encoded_file = quote(relevant_file, safe="/")
        link = f"{self.base_url}/{self.owner}/{self.repo}/blob/{branch}/{encoded_file}"
        relevant_line_start, relevant_line_end = self._normalize_line_range(
            relevant_line_start, relevant_line_end
        )
        if relevant_line_start == -1:
            return link
        if relevant_line_end:
            return link + f"#L{relevant_line_start}-L{relevant_line_end}"
        return link + f"#L{relevant_line_start}"

    def get_git_repo_url(self, issues_or_pr_url: str) -> str:
        return f"{self.base_url}/{self.owner}/{self.repo}.git"

    def is_supported(self, capability: str) -> bool:
        """Report which capabilities are wired up for Gitee.

        Gitee's OpenAPI v5 exposes no endpoint that writes files or commits, so ``push_code``
        stays off and tools that would push (for example ``/update_changelog``) degrade to
        their read-only output.
        """
        return capability != "push_code"

    # ------------------------------------------------------------------ pull request reading

    def get_files(self) -> List[str]:
        return [file["filename"] for file in self._get_changed_files()]

    def get_num_of_files(self) -> int:
        return len(self._get_changed_files())

    def _get_changed_files(self) -> List[Dict[str, Any]]:
        """Cache only a complete changed-file inventory, including a valid empty one."""
        if self.git_files is None:
            files = self.api.request("GET", f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}/files")
            if not isinstance(files, list):
                raise IncompleteGiteePullRequestFilesError(
                    "Gitee changed-file inventory is unavailable or incomplete"
                )
            self.git_files = files
        return self.git_files

    @staticmethod
    def _edit_type_from_patch_info(patch_info: Mapping[str, Any], patch: str) -> EDIT_TYPE:
        """Derive the edit type from the patch flags, since ``status`` is usually absent."""
        if patch_info.get("new_file"):
            return EDIT_TYPE.ADDED
        if patch_info.get("deleted_file"):
            return EDIT_TYPE.DELETED
        if patch_info.get("renamed_file"):
            return EDIT_TYPE.RENAMED
        if patch:
            return EDIT_TYPE.MODIFIED
        return EDIT_TYPE.UNKNOWN

    def _get_file_content(self, file_path: str, ref: Optional[str]) -> str:
        """Read one revision of a file, caching per (ref, path).

        ``/raw/{path}`` answers 404 for a path that does not exist at ``ref``, which is the
        expected "absent at this revision" signal for added and deleted files.
        """
        if not file_path or not ref or not is_valid_file(file_path):
            return ""
        cache_key = f"{ref}:{file_path}"
        if cache_key in self.file_contents:
            return self.file_contents[cache_key]
        content = ""
        try:
            data = self.api.request_bytes(
                "GET",
                f"/repos/{self.owner}/{self.repo}/raw/{quote(file_path, safe='/')}",
                params={"ref": ref},
                allow_404=True,
            )
            if data:
                content = decode_if_bytes(data)
        except GiteeApiError as e:
            # Keep the diff reviewable rather than aborting the whole run on one unreadable file.
            self.logger.warning(f"Could not read {file_path} at {ref}: {e}")
        self.file_contents[cache_key] = content
        return content

    @staticmethod
    def _rebuild_patch(filename: str, base_file: str, head_file: str) -> str:
        """Rebuild a unified diff when Gitee omits ``patch.diff`` (very large files)."""
        if not base_file and not head_file:
            return ""
        base_lines = base_file.splitlines(keepends=True)
        head_lines = head_file.splitlines(keepends=True)
        diff = difflib.unified_diff(base_lines, head_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
        patch = "".join(diff)
        if patch and not patch.endswith("\n"):
            patch += "\n"
        return patch

    def get_diff_files(self) -> List[FilePatchInfo]:
        """Get the files modified by the PR, together with both revisions where needed."""
        if self.diff_files is not None:
            return self.diff_files

        # Apply [ignore] rules at diff time, after apply_repo_settings() has merged the
        # repository-level .pr_agent.toml (the provider is constructed before those settings
        # exist). This matches the other providers, which filter lazily inside their diff fetch.
        diff_git_files = filter_ignored(list(self._get_changed_files()), platform="gitee")

        invalid_files_names: List[str] = []
        counter_valid = 0
        diff_files: List[FilePatchInfo] = []
        for file in diff_git_files:
            filename = file.get("filename")
            if not filename:
                continue
            if not is_valid_file(filename):
                invalid_files_names.append(filename)
                continue

            counter_valid += 1
            patch_info = file.get("patch") or {}
            if not isinstance(patch_info, Mapping):
                patch_info = {}
            patch = patch_info.get("diff") or ""
            edit_type = self._edit_type_from_patch_info(patch_info, patch)

            avoid_load = False
            if counter_valid >= MAX_FILES_ALLOWED_FULL and patch and not self.incremental.is_incremental:
                avoid_load = True
                if counter_valid == MAX_FILES_ALLOWED_FULL:
                    self.logger.info("Too many files in PR, will avoid loading full content for rest of files")

            head_file = ""
            base_file = ""
            if not avoid_load:
                if edit_type != EDIT_TYPE.DELETED:
                    head_file = self._get_file_content(filename, self.sha)

            if self.incremental.is_incremental and self.unreviewed_files_map:
                base_file = self._get_file_content(filename, self.last_commit.sha if self.last_commit else self.sha)
                self.unreviewed_files_map[filename] = patch
            # An added file cannot exist at the base revision, so reading it there only costs a
            # request and a warning. Mirrors GithubProvider.get_diff_files().
            elif avoid_load or edit_type == EDIT_TYPE.ADDED:
                base_file = ""
            else:
                base_file = self._get_file_content(filename, self.base_sha)

            if not patch and not avoid_load:
                patch = self._rebuild_patch(filename, base_file, head_file)
                if not patch and base_file == head_file:
                    # Both revisions read successfully and match: the file is unchanged, so an
                    # empty patch is the honest answer instead of an invented diff.
                    pass
                elif patch:
                    edit_type = self._edit_type_from_patch_info(patch_info, patch)

            num_plus_lines = int(file.get("additions") or 0)
            num_minus_lines = int(file.get("deletions") or 0)

            old_filename = None
            if patch_info.get("renamed_file"):
                old_filename = patch_info.get("old_path") or None

            diff_files.append(
                FilePatchInfo(
                    base_file=base_file,
                    head_file=head_file,
                    patch=patch,
                    filename=filename,
                    num_minus_lines=num_minus_lines,
                    num_plus_lines=num_plus_lines,
                    edit_type=edit_type,
                    old_filename=old_filename,
                )
            )

        if invalid_files_names:
            self.logger.info(f"Filtered out files with invalid extensions: {invalid_files_names}")

        self.filtered_diff_file_names = invalid_files_names
        self.diff_files = diff_files
        return diff_files

    def get_pr_branch(self) -> str:
        return self._head_field("ref")

    def get_pr_description_full(self) -> str:
        body = (self.pr or {}).get("body")
        return body if isinstance(body, str) else ""

    @cache_languages
    def get_languages(self) -> Dict[str, float]:
        """Get the repository's languages as a ``{name: size}`` map.

        Gitee answers
        ``{"languages": [{"language": "Ruby", "color": ..., "percent": 68.6, "bytes": 570125}, ...]}``.
        The byte count is reported, matching the size the other providers return, with the
        percentage as a fallback. A flat name -> size map is tolerated too.
        """
        response = self.api.request("GET", f"/repos/{self.owner}/{self.repo}/languages")
        # A mapping without the envelope key is read as a flat name -> size map.
        entries = response.get("languages", response) if isinstance(response, Mapping) else response
        if isinstance(entries, Mapping):
            return {name: size for name, size in entries.items() if isinstance(name, str)}
        if isinstance(entries, list):
            languages: Dict[str, float] = {}
            for entry in entries:
                if not isinstance(entry, Mapping):
                    continue
                name = entry.get("language")
                if not isinstance(name, str) or not name:
                    continue
                size = entry.get("bytes", entry.get("percent", 0))
                languages[name] = size if isinstance(size, (int, float)) else 0
            return languages
        self.logger.error(f"Unexpected languages payload type: {type(entries)}")
        return {}

    def get_commit_messages(self) -> str:
        max_tokens = get_settings().get("CONFIG.MAX_COMMITS_TOKENS", None)
        if not self.pr_commits:
            self.logger.error("Failed to get commit messages")
            return ""
        try:
            commit_messages = [commit.message for commit in reversed(self.pr_commits) if commit.message]
            if not commit_messages:
                self.logger.error("No commit messages found")
                return ""
            commit_message = "\n".join(f"{i + 1}. {message}" for i, message in enumerate(commit_messages))
            if max_tokens:
                commit_message = clip_tokens(commit_message, max_tokens)
            return commit_message
        except Exception as e:
            self.logger.error(f"Error processing commit messages: {str(e)}")
            return ""

    # ------------------------------------------------------------------ labels

    def get_pr_labels(self, update=False) -> List[str]:
        labels = self.api.request("GET", f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}/labels")
        if not isinstance(labels, list):
            self.logger.error("Failed to get PR labels")
            return []
        names = [label.get("name") for label in labels if isinstance(label, Mapping)]
        return [name for name in names if isinstance(name, str) and name]

    def publish_labels(self, labels: List[str]) -> None:
        """Add labels to the PR.

        Gitee takes the label names as a JSON array. Only additive publishing is used so an
        existing label set is never replaced by an incomplete one.
        """
        names = [name for name in (labels or []) if isinstance(name, str) and name]
        if not names:
            self.logger.error("No labels provided to publish")
            return
        try:
            self.api.request(
                "POST", f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}/labels", json_body=names
            )
            self.logger.info(f"Labels added: {names}")
        except GiteeApiError as e:
            self.logger.error(f"Error publishing labels: {e}")

    # ------------------------------------------------------------------ settings

    def get_repo_settings(self):
        """Get repository settings (namespace-global first, then the repo-local file)."""
        settings_files = []
        global_settings = self._get_global_repo_settings()
        if global_settings:
            settings_files.append(("global", global_settings))

        if not self.repo_settings:
            self.logger.error("Repository settings path is not configured")
            return settings_files if settings_files else ""

        # Only trust the PR target (base) ref, matching the other providers: a PR must not be
        # able to point its own review at instruction files it introduced.
        target_ref = self.base_sha or self.base_ref
        if not target_ref:
            self.logger.warning("Cannot get repository settings: no target/base ref available")
            return settings_files if settings_files else ""

        response = self.api.request_bytes(
            "GET",
            f"/repos/{self.owner}/{self.repo}/raw/{quote(self.repo_settings, safe='/')}",
            params={"ref": target_ref},
            allow_404=True,
        )
        if not response:
            self.logger.error("Failed to get repository settings")
        else:
            settings_files.append(("local", response))

        return settings_files if settings_files else ""

    def get_owning_namespace(self) -> Optional[str]:
        return self.owner

    def _get_global_settings_cache_key(self, namespace: str) -> str:
        return f"gitee:{self.api_base}:{namespace}"

    def _fetch_global_repo_settings(self, namespace: str, settings_repo: str):
        # Namespace-wide global settings live in `<namespace>/<settings_repo>`. A missing
        # repository or file (404) is an expected fallback -> return "" (which is cached).
        repo = self.api.request("GET", f"/repos/{namespace}/{settings_repo}", allow_404=True)
        if not repo:
            return ""
        default_branch = repo.get("default_branch")
        if not default_branch:
            return ""
        return self.api.request_bytes(
            "GET",
            f"/repos/{namespace}/{settings_repo}/raw/{quote('.pr_agent.toml', safe='/')}",
            params={"ref": default_branch},
            allow_404=True,
        ) or ""

    def get_repo_file_content(self, file_path: str, from_default_branch: bool = False) -> str:
        """Read a repo file from the PR target branch, or from the default branch on request.

        Repo-context files must not come from the PR head, so a pull request cannot supply its
        own instruction files to influence its own review.
        """
        if not (self.owner and self.repo):
            self.logger.warning("Cannot get repo file content: owner or repo not set")
            return ""
        if from_default_branch:
            ref = self._default_branch()
        else:
            ref = self.base_sha or self.base_ref
        if not ref:
            self.logger.warning("Cannot get repo file content: no target/base ref available")
            return ""
        return self._get_file_content(file_path, ref)

    def get_repo_context_ref(self, from_default_branch: bool = False) -> Optional[str]:
        if from_default_branch:
            return self._default_branch() or None
        return self.base_sha or self.base_ref or None

    def _default_branch(self) -> str:
        repo = self.api.request("GET", f"/repos/{self.owner}/{self.repo}", allow_404=True)
        if isinstance(repo, Mapping):
            return repo.get("default_branch") or ""
        return ""

    # ------------------------------------------------------------------ comments

    @staticmethod
    def _comment_field(comment, field: str) -> Any:
        if isinstance(comment, Mapping):
            return comment.get(field)
        return getattr(comment, field, None)

    @classmethod
    def _comment_id(cls, comment) -> Optional[int]:
        comment_id = cls._comment_field(comment, "id")
        if comment_id is None:
            comment_id = cls._comment_field(comment, "comment_id")
        try:
            return int(comment_id)
        except (TypeError, ValueError):
            return None

    def _comments_index(self) -> Optional[int]:
        if self.enabled_issue:
            return self.issue_number
        if self.enabled_pr:
            return self.pr_number
        return None

    def get_issue_comments(self) -> List[GiteeComment]:
        """Return every comment on the PR, oldest first.

        Gitee keeps a PR's timeline and its diff comments on the same route and marks them with
        ``comment_type``; both are returned so identity-marker lookups see the whole history.
        """
        index = self._comments_index()
        if index is None:
            self.logger.error("Neither PR nor issue URL provided.")
            return []
        comments: List[GiteeComment] = []
        for page in range(1, MAX_COMMENT_PAGES + 1):
            batch = self.api.request(
                "GET",
                f"/repos/{self.owner}/{self.repo}/pulls/{index}/comments",
                params={"page": page, "per_page": COMMENTS_PER_PAGE, "direction": "asc"},
            )
            if not isinstance(batch, list) or not batch:
                break
            comments.extend(GiteeComment(item) for item in batch if isinstance(item, Mapping))
            if len(batch) < COMMENTS_PER_PAGE:
                break
        else:
            self.logger.warning(
                f"Stopped reading PR comments after {MAX_COMMENT_PAGES} pages; older comments were not scanned"
            )
        return comments

    def publish_comment(self, comment: str, is_temporary: bool = False) -> Optional[Dict[str, Any]]:
        if is_temporary and not get_settings().config.publish_output_progress:
            self.logger.debug("Skipping publish_comment for temporary comment")
            return None

        index = self._comments_index()
        if index is None:
            self.logger.error("Neither PR nor issue URL provided.")
            return None

        comment = self.limit_output_characters(comment, self.max_comment_chars)
        try:
            response = self.api.request(
                "POST", f"/repos/{self.owner}/{self.repo}/pulls/{index}/comments", body={"body": comment}
            )
        except GiteeApiError as e:
            self.logger.error(f"Failed to publish comment: {e}")
            return None

        if not response:
            self.logger.error("Failed to publish comment")
            return None

        if is_temporary:
            self.temp_comments.append(comment)

        comment_obj = {
            "is_temporary": is_temporary,
            "comment": comment,
            "comment_id": (response or {}).get("id") if isinstance(response, Mapping) else None,
        }
        self.comments_list.append(comment_obj)
        self.logger.info("Comment published")
        return comment_obj

    def edit_comment(self, comment, body: str) -> bool:
        comment_id = self._comment_id(comment)
        if not comment_id:
            self.logger.error("Comment ID not found")
            return False
        body = self.limit_output_characters(body, self.max_comment_chars)
        try:
            self.api.request(
                "PATCH", f"/repos/{self.owner}/{self.repo}/pulls/comments/{comment_id}", body={"body": body}
            )
        except GiteeApiError as e:
            self.logger.error(f"Error editing comment: {e}")
            return False
        return True

    def remove_comment(self, comment) -> None:
        if not comment:
            return
        comment_id = self._comment_id(comment)
        if not comment_id:
            self.logger.error("Comment ID not found")
            return
        try:
            self.api.request("DELETE", f"/repos/{self.owner}/{self.repo}/pulls/comments/{comment_id}")
        except GiteeApiError as e:
            self.logger.error(f"Error removing comment: {e}")
            raise
        if self.comments_list and comment in self.comments_list:
            self.comments_list.remove(comment)
        self.logger.info(f"Comment removed successfully: {comment_id}")

    def remove_initial_comment(self) -> None:
        # Iterate over a snapshot: remove_comment() drops the comment from comments_list, so
        # mutating it mid-iteration would skip every other temporary comment.
        for comment in list(self.comments_list):
            try:
                if not comment.get("is_temporary"):
                    continue
                self.remove_comment(comment)
            except Exception as e:
                self.logger.error(f"Error removing comment: {e}")
                continue

    def remove_reaction(self, issue_comment_id: int, reaction_id: int) -> bool:
        """Report success without a backend call: Gitee's v5 API exposes no reaction endpoint.

        The base class treats ``True`` as "nothing to remove", which is what an operator
        configured with ``reaction_on_start``/``reaction_on_success`` should observe here.
        """
        return True

    # ------------------------------------------------------------------ publishing

    def publish_description(self, pr_title: str, pr_body: str) -> None:
        payload: Dict[str, Any] = {"body": pr_body}
        if pr_title is not None:
            payload["title"] = pr_title
        response = self.api.request(
            "PATCH", f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}", body=payload
        )
        if not response:
            self.logger.error("Failed to publish PR description")
            raise RuntimeError("Failed to publish PR description")
        # Keep the cached copy in step so later reads in the same run see what was published.
        # An omitted title must not overwrite the cached one with None.
        if self.pr is not None:
            if pr_title is not None:
                self.pr["title"] = pr_title
            self.pr["body"] = pr_body
        self.logger.info("PR description published successfully")

    def _build_code_suggestion_payload(self, suggestion: dict) -> dict:
        """Map a shared code suggestion onto the keys ``publish_inline_comments`` consumes."""
        return {
            "body": suggestion["body"],
            "relevant_file": suggestion["relevant_file"],
            "relevant_line_in_file": suggestion["relevant_lines_start"],
        }

    def _inline_position(self, relevant_file: str, relevant_line_in_file) -> int:
        """Return the diff-relative position Gitee anchors an inline comment to.

        The shared code-suggestion path passes the target line's absolute number in the new
        file, while direct callers pass the line's text; ``position`` is the line's index
        inside the diff, so an absolute line number is resolved through ``absolute_position``.
        """
        diff_files = self.diff_files or self.get_diff_files()
        relevant_file = relevant_file.strip("`")
        line = relevant_line_in_file
        if isinstance(line, bool):
            line = None
        if isinstance(line, int):
            absolute_position = line
        elif isinstance(line, str) and line.lstrip("-").isdigit():
            absolute_position = int(line)
        else:
            absolute_position = None
        position, _ = find_line_number_of_relevant_line_in_file(
            diff_files, relevant_file, "" if absolute_position is not None else line, absolute_position
        )
        if position == -1:
            return -1
        # Gitee counts lines below the first hunk header. The shared finder returns the patch
        # line index, which includes the `---`/`+++` file header of a rebuilt diff.
        patch = next(
            (diff_file.patch or "" for diff_file in diff_files if (diff_file.filename or "").strip() == relevant_file),
            "",
        )
        first_hunk = next(
            (index for index, patch_line in enumerate(patch.splitlines()) if patch_line.startswith("@@")),
            None,
        )
        if first_hunk is None or position <= first_hunk:
            return -1
        return position - first_hunk

    def publish_inline_comment(self, body: str, relevant_file: str, relevant_line_in_file: str,
                               original_suggestion=None) -> bool:
        body = self.limit_output_characters(body, self.max_comment_chars)
        position = self._inline_position(relevant_file, relevant_line_in_file)
        if position == -1:
            self.logger.info(f"Could not find position for {relevant_file} {relevant_line_in_file}")
            return False
        try:
            response = self.api.request(
                "POST",
                f"/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}/comments",
                body={
                    "body": body,
                    "commit_id": self.sha,
                    "path": relevant_file,
                    "position": position,
                },
            )
        except GiteeApiError as e:
            self.logger.error(f"Failed to publish inline comment: {e}")
            return False
        if not response:
            self.logger.error("Failed to publish inline comment")
            return False
        return True

    def publish_inline_comments(self, comments: list[dict]) -> bool:
        """Publish inline comments, reporting success when at least one landed.

        A partial failure must not report failure: the caller would republish the whole list
        and post the accepted comments twice.
        """
        publishable_count = 0
        published_count = 0
        for comment in comments or []:
            if not isinstance(comment, Mapping):
                continue
            relevant_file = comment.get("relevant_file")
            body = comment.get("body")
            if not (relevant_file and body):
                continue
            relevant_line = comment.get("relevant_line_in_file")
            publishable_count += 1
            if self.publish_inline_comment(body, relevant_file, relevant_line):
                published_count += 1
        return published_count > 0 or publishable_count == 0

    # ------------------------------------------------------------------ clone

    def _prepare_clone_url_with_token(self, repo_url_to_clone: str) -> Optional[str]:
        """Embed the token so private repositories can be cloned.

        Gitee accepts ``https://<login>:<token>@host/...``, and the login is read once from the
        authenticated-user endpoint and cached.
        """
        parsed = urlparse(self.base_url)
        host = parsed.netloc
        scheme = parsed.scheme
        if not (self.gitee_access_token and host and scheme):
            self.logger.error("Either missing auth token or missing base url")
            return None
        if host not in repo_url_to_clone:
            self.logger.error(
                f"url to clone: {redact_credentials(repo_url_to_clone)} "
                f"does not contain {redact_credentials(self.base_url)}"
            )
            return None
        remainder = repo_url_to_clone.split(f"{scheme}://", 1)[-1]
        repo_full_name = remainder.split(host, 1)[-1]
        if not repo_full_name:
            self.logger.error(f"url to clone: {redact_credentials(repo_url_to_clone)} is malformed")
            return None
        credentials = quote(self.gitee_access_token, safe="")
        login = self.get_user_id()
        if login:
            credentials = f"{quote(login, safe='')}:{credentials}"
        return f"{scheme}://{credentials}@{host}{repo_full_name}"
