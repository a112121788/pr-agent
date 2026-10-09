from types import SimpleNamespace

from pr_agent.algo.factory_record import (
    bind_commit,
    latest_intake_intent,
    latest_verdict,
    parse_verdict,
    render_merge_check,
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


def test_only_an_explicit_dual_line_intake_blocks_review():
    comments = [_comment("## 受理记录\n\n- 意图：双线")]

    assert latest_intake_intent(comments) == "双线"
    findings = review_rule_findings([], "", latest_intake_intent(comments))
    assert findings[0].summary.startswith("这是双线变更")
    assert review_rule_findings([], "同时改旧字段和新汇总") == []
