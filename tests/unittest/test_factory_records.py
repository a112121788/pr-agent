from types import SimpleNamespace

from pr_agent.algo.factory_record import (
    apply_drive,
    bind_commit,
    decide_drive,
    latest_evidence_sha,
    latest_intake_intent,
    latest_verdict,
    parse_verdict,
    render_merge_check,
    render_status,
    render_verdict,
)
from pr_agent.algo.review_policy import review_rule_findings


def _comment(body):
    return SimpleNamespace(body=body)


def test_evidence_is_prefixed_with_the_current_commit_once():
    body = bind_commit("## PR 审查指南", "abc1234567")

    assert body.startswith("提交号：abc1234567")
    assert bind_commit(body, "fff") == body


def test_only_the_three_verdict_words_are_accepted():
    assert parse_verdict(["放行"]) == "放行"
    for words in (["批准"], ["放行", "吧"], []):
        try:
            parse_verdict(words)
        except ValueError:
            continue
        raise AssertionError(words)


def test_review_prose_cannot_authorize_merge():
    comments = [_comment("## 审查结论\n\n结论：批准\n提交号：abc1234567")]

    assert latest_verdict(comments) == (None, "")
    assert "不能汇入" in render_merge_check(None, "", "abc1234567")


def test_matching_pass_verdict_allows_a_person_to_merge():
    comments = [_comment("## 判定记录\n\n判定：放行\n提交号：abc1234567")]

    assert latest_verdict(comments) == ("放行", "abc1234567")
    assert "可以由人合并" in render_merge_check("放行", "abc1234567", "abc1234567")
    assert "不能汇入" in render_merge_check("放行", "abc1234567", "def1234567")
    assert "不能汇入" in render_merge_check("退回", "abc1234567", "abc1234567")


def test_gitee_comments_become_pipeline_records():
    from pr_agent.algo.factory_record import comment_feed, records_from_comments

    comments = [
        {"body": "提交号：abc1234567\n\n## PR 审查指南", "user": {"login": "bot"}, "created_at": "t1"},
        {"body": "普通讨论，不是审核记录", "user": {"login": "ada"}},
        {"body": "Failed to review PR", "user": {"login": "bot"}},
    ]
    records = records_from_comments("https://gitee.com/o/r/pulls/1", comments)

    assert [record.record_type for record in records] == ["审查"]
    assert records[0].stage == "取证"
    feed = comment_feed(comments)
    assert [item["kind"] for item in feed] == ["审查", "评论", "审查失败"]
    assert feed[2]["stage"] == "失败"
    assert feed[2]["text"] == "审查没有完成。"
    assert "提交号：" not in feed[0]["text"]


def test_status_names_the_missing_stage_and_ignores_review_approval():
    comments = [
        _comment("## 审查结论\n\n结论：批准\n提交号：abc1234567"),
        _comment("## 受理记录\n\n- 意图：旧版迭代"),
    ]

    assert latest_evidence_sha(comments) == ""
    status = render_status("旧版迭代", "", None, "", "abc1234567")
    assert "- 当前段：取证" in status

    complete = render_status("旧版迭代", "abc1234567", "放行", "abc1234567", "abc1234567")
    assert "- 当前段：汇入" in complete


class _Effects:
    def __init__(self):
        self.calls = []

    def write_intake(self, intent, head_sha):
        self.calls.append(("受理", intent, head_sha))

    def collect_evidence(self, head_sha):
        self.calls.append(("取证", head_sha))

    def write_verdict(self, verdict, head_sha):
        self.calls.append(("判定", verdict, head_sha))

    def merge(self, head_sha):
        self.calls.append(("汇入", head_sha))


def _intake(intent="旧版迭代"):
    return _comment(f"## 受理记录\n\n- 意图：{intent}")


def _evidence(sha="abc1234567"):
    return _comment(f"提交号：{sha}\n\n## PR 审查指南")


def _verdict(verdict="放行", sha="abc1234567"):
    return _comment(f"## 判定记录\n\n判定：{verdict}\n提交号：{sha}")


def test_a_matching_pass_merges_without_a_human_mode_switch():
    ready = [_verdict(), _evidence(), _intake()]
    decision = decide_drive(ready, "abc1234567", allow_merge=True)

    assert decision.action == "汇入"
    assert decision.merge is True
    assert apply_drive(decision, _Effects()) == ["汇入"]
    held = decide_drive(ready, "abc1234567")
    assert held.merge is False
    assert apply_drive(held, _Effects()) == []


def test_a_new_pull_request_is_reviewed_without_an_intent():
    for text in ("", "大概是新功能", "意图：新业务", "意图：双线"):
        decision = decide_drive([], "abc1234567", stated_intent=text)
        effects = _Effects()
        assert decision.collect_evidence is True
        assert decision.write_intake is False
        assert apply_drive(decision, effects) == ["取证"]
        assert effects.calls == [("取证", "abc1234567")]


def test_dual_line_and_model_approval_never_become_a_pass():
    dual = [
        _comment("## 审查结论\n\n结论：批准\n提交号：abc1234567"),
        _intake("双线"),
    ]
    decision = decide_drive(dual, "abc1234567", rule_findings=[])
    assert decision.verdict != "放行"
    assert decision.merge is False
    assert "不能" in decision.reason

    approved = [
        _comment("## 审查结论\n\n结论：批准\n提交号：abc1234567"),
        _evidence(),
        _intake(),
    ]
    held = decide_drive(approved, "abc1234567")
    assert held.action == "留给人工"
    assert held.verdict != "放行"
    assert held.merge is False
    assert apply_drive(held, _Effects()) == []


def test_only_a_matching_pass_may_merge_and_evidence_uses_the_head():
    head = "abc1234567"

    def gate(verdict, sha):
        return decide_drive(
            [_verdict(verdict, sha), _evidence(head), _intake()], head, allow_merge=True,
        )

    assert gate("放行", head).merge is True
    for verdict, sha in (("退回", head), ("等待", head), ("放行", "def1234567")):
        decision = gate(verdict, sha)
        assert decision.merge is False
        assert "不能汇入" in decision.reason
        assert apply_drive(decision, _Effects()) == []

    missing = decide_drive([_intake()], head)
    assert missing.action == "取证"
    assert missing.collect_evidence is True
    assert apply_drive(missing, _Effects()) == ["取证"]

    published = render_verdict("放行", head, "驾驶舱")
    assert latest_verdict([_comment(published)]) == ("放行", head)


def test_checked_rules_choose_pass_or_return_without_using_the_approval_word():
    comments = [_evidence(), _intake(), _comment("## 审查结论\n\n结论：批准")]

    passed = decide_drive(comments, "abc1234567", rule_findings=[])
    blocked = decide_drive(comments, "abc1234567", rule_findings=["严重问题"])

    assert passed.verdict == "放行"
    assert passed.write_verdict is True
    assert passed.merge is False
    assert blocked.verdict == "退回"
    assert blocked.merge is False
    assert apply_drive(blocked, _Effects()) == ["判定"]


def test_only_an_explicit_dual_line_intake_blocks_review():
    comments = [_comment("## 受理记录\n\n- 意图：双线")]

    assert latest_intake_intent(comments) == "双线"
    findings = review_rule_findings([], "", latest_intake_intent(comments))
    assert findings[0].summary.startswith("这是双线变更")
    assert review_rule_findings([], "同时改旧字段和新汇总") == []
