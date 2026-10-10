from types import SimpleNamespace

from pr_agent.algo.factory_record import decide_drive
from pr_agent.algo.review_policy import review_rule_findings, review_sections


def _file(name, patch="", head=""):
    return SimpleNamespace(filename=name, patch=patch, head_file=head)


def test_added_anchor_and_button_tags_block_the_review():
    findings = review_rule_findings([
        _file("app.js", "+const link = '<a href=\"/x\"></a>';\n"),
        _file("view.html", "+<button type=\"button\"></button>\n"),
        _file("README.md", "+<a href=\"/docs\"></a>\n"),
    ])

    assert len(findings) == 2
    assert all("不给予通过" in finding.summary for finding in findings)


def test_feature_change_without_spec_is_blocking():
    findings = review_rule_findings([_file("app.rb", "+value = 1\n")], "feat: add activity form")

    assert findings[0].summary.startswith("本次功能更新缺失 spec 文件")


def test_feature_change_with_matching_spec_passes():
    findings = review_rule_findings([
        _file("specs/activity.md", "", "SPEC-12 requires the activity form"),
        _file("app.rb", "+# SPEC-12 implemented\n"),
    ], "feat: add activity form")

    assert findings == []


def test_dual_line_rules_and_an_approval_word_do_not_open_the_merge_gate():
    findings = review_rule_findings([], "", "双线")
    comments = [
        SimpleNamespace(body="## 审查结论\n\n结论：批准\n提交号：abc1234567"),
        SimpleNamespace(body="提交号：abc1234567\n\n## PR 审查指南"),
        SimpleNamespace(body="## 受理记录\n\n- 意图：双线"),
    ]

    decision = decide_drive("自动驾驶", comments, "abc1234567", rule_findings=findings)

    assert findings[0].summary.startswith("这是双线变更")
    assert decision.merge is False
    assert decision.verdict != "放行"
    assert decision.write_verdict is False


def test_review_sections_put_blocking_issues_first_and_state_no_blockers():
    rendered = review_sections({
        "merge_recommendation": "safe_to_merge",
        "key_issues_to_review": [],
        "strengths": ["测试覆盖了边界条件"],
    })

    assert "结论：批准" in rendered
    assert "无阻塞项" in rendered
    assert "测试覆盖了边界条件" in rendered
