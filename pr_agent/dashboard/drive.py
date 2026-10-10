"""Run one cockpit pass. Writing and merging happen only after decide_drive allows them."""

from __future__ import annotations

from types import SimpleNamespace

from pr_agent.algo.factory_record import (
    DriveDecision,
    apply_drive,
    decide_drive,
    explicit_intent,
    render_verdict,
)
from pr_agent.algo.review_policy import review_rule_findings
from pr_agent.dashboard.actions import open_pulls, pull_comments
from pr_agent.dashboard.store import FactoryRecord, FactoryStore, database_url, record_factory_event
from pr_agent.git_providers import get_git_provider
from pr_agent.log import get_logger
from pr_agent.tools.pr_intake import render_intake


def merge_pull(pr_url: str, expected_sha: str, provider=None) -> bool:
    """Merge only when Gitee still points at the commit the gate already checked."""
    provider = provider or get_git_provider()(pr_url)
    current = provider.get_pr_head_sha() or ""
    if not expected_sha or current != expected_sha:
        return False
    provider.merge_pull_request()
    return True


def load_rules(pr_url: str, intent: str):
    """Read deterministic review rules. A failure leaves the verdict to a person."""
    try:
        provider = get_git_provider()(pr_url)
        pull = getattr(provider, "pr", None)
        title = pull.get("title") if isinstance(pull, dict) else ""
        return review_rule_findings(provider.get_diff_files(), title or "", intent)
    except Exception as error:
        get_logger().warning(f"驾驶舱没有读到规则：{error}")
        return None


class GiteeEffects:
    """Publish the one record a decision already allowed."""

    def __init__(self, pr_url: str, start_review=None):
        self.pr_url = pr_url
        self.start_review = start_review

    def write_intake(self, intent, head_sha):
        comment = render_intake(intent, "驾驶舱按显式意图受理", "", head_sha)
        self._publish(comment)
        record_factory_event(FactoryRecord(
            self.pr_url, "受理", "受理", intent, "", head_sha, "驾驶舱按显式意图受理",
        ))

    def collect_evidence(self, head_sha):
        store = FactoryStore(database_url())
        store.setup()
        job_id = store.enqueue(self.pr_url, "review")
        if self.start_review:
            self.start_review(self.pr_url, job_id, head_sha)

    def write_verdict(self, verdict, head_sha):
        comment = render_verdict(verdict, head_sha, "驾驶舱")
        self._publish(comment)
        record_factory_event(FactoryRecord(
            self.pr_url, "判定", "判定", "", verdict, head_sha, "驾驶舱",
        ))

    def merge(self, head_sha):
        merge_pull(self.pr_url, head_sha)

    def _publish(self, comment: str):
        get_git_provider()(self.pr_url).publish_comment(comment)


def _remember(decision: DriveDecision):
    """A comment the next decision can read after this step is published."""
    if decision.write_intake:
        body = render_intake(decision.intent, "驾驶舱按显式意图受理", "", decision.head_sha)
        return SimpleNamespace(body=body)
    if decision.write_verdict:
        return SimpleNamespace(body=render_verdict(decision.verdict, decision.head_sha, "驾驶舱"))
    return None


def _settle(mode, pull, comments, confirmed, rules_for, effects=None):
    """Apply the next automatic step. Autopilot continues until evidence or a hold."""
    decision = _decision_for(mode, pull, comments, confirmed, rules_for)
    if effects is None:
        return decision
    for _ in range(4):
        done = apply_drive(decision, effects)
        if mode != "自动驾驶" or not done or "取证" in done or "汇入" in done:
            return decision
        remembered = _remember(decision)
        if remembered is None:
            return decision
        comments.insert(0, remembered)
        decision = _decision_for(mode, pull, comments, confirmed, rules_for)
    return decision


def _decision_for(mode, pull, comments, confirmed: bool, rules_for) -> DriveDecision:
    """Ask the pure decision, and load rules only when a verdict is otherwise impossible."""
    sha = pull.get("sha") or ""
    stated = explicit_intent(f"{pull.get('title') or ''}\n{pull.get('body') or ''}")
    url = pull.get("url") or ""
    decision = decide_drive(
        mode, comments, sha, stated_intent=stated, confirmed=confirmed,
    )
    if decision.reason.startswith("无法判定"):
        decision = decide_drive(
            mode, comments, sha, stated_intent=stated, confirmed=confirmed,
            rule_findings=rules_for(url, decision.intent),
        )
    return decision


def preview_registered(
    store: FactoryStore, pulls_for=None, comments_for=None, rules_for=None,
) -> list[tuple[str, DriveDecision]]:
    """Show the next step for open pull requests without writing or merging."""
    return _walk(
        store, confirmed_url="", pulls_for=pulls_for, comments_for=comments_for, rules_for=rules_for,
    )


def execute_registered(
    store: FactoryStore, confirmed_url: str = "", start_review=None,
    pulls_for=None, comments_for=None, rules_for=None, effects_for=None,
) -> list[tuple[str, DriveDecision]]:
    """Walk registered repositories and apply only the steps decide_drive allows."""
    def build(url):
        return GiteeEffects(url, start_review)

    return _walk(
        store, confirmed_url=confirmed_url, pulls_for=pulls_for, comments_for=comments_for,
        rules_for=rules_for, effects_for=effects_for or build, apply=True,
    )


def _walk(store, confirmed_url, pulls_for, comments_for, rules_for=None, effects_for=None, apply=False):
    mode = store.get_mode()
    pulls_for = pulls_for or open_pulls
    comments_for = comments_for or pull_comments
    rules_for = rules_for or load_rules
    found = []
    for owner, repo in store.repos():
        try:
            pulls = pulls_for(owner, repo)
        except Exception as error:
            found.append((f"{owner}/{repo}", DriveDecision(mode, "留给人工", f"没有读到打开的拉取请求：{error}")))
            continue
        for pull in pulls:
            url = pull.get("url") or ""
            try:
                comments = list(reversed(comments_for(url) or []))
                confirmed = bool(confirmed_url) and url == confirmed_url and mode == "辅助驾驶"
                effects = effects_for(url) if apply and effects_for else None
                decision = _settle(mode, pull, comments, confirmed, rules_for, effects)
                found.append((url, decision))
            except Exception as error:
                get_logger().warning(f"驾驶舱跳过 {url}：{error}")
                found.append((url, DriveDecision(mode, "留给人工", "这一张没有处理", head_sha=pull.get("sha") or "")))
    return found


def continue_pull(store: FactoryStore, pr_url: str, head_sha: str, comments_for=None, rules_for=None, effects_for=None):
    """Judge one pull after its evidence job finishes, then merge only when the gate allows."""
    if store.get_mode() != "自动驾驶" or not head_sha:
        return []
    comments_for = comments_for or pull_comments
    rules_for = rules_for or load_rules
    effects = (effects_for or (lambda url: GiteeEffects(url)))(pr_url)
    pull = {"url": pr_url, "sha": head_sha, "title": "", "body": ""}
    comments = list(reversed(comments_for(pr_url) or []))
    decision = _settle(store.get_mode(), pull, comments, False, rules_for, effects)
    return [(pr_url, decision)]
