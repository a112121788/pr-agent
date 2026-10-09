from types import SimpleNamespace

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


def test_review_sections_put_blocking_issues_first_and_state_no_blockers():
    rendered = review_sections({
        "merge_recommendation": "safe_to_merge",
        "key_issues_to_review": [],
        "strengths": ["测试覆盖了边界条件"],
    })

    assert "结论：批准" in rendered
    assert "无阻塞项" in rendered
    assert "测试覆盖了边界条件" in rendered
