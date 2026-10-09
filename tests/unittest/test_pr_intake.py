import pytest

from pr_agent.tools.pr_intake import parse_intake, render_intake


def test_intake_keeps_one_allowed_intent_and_the_original_words():
    intent, statement = parse_intake(["新业务", "增加", "出科确认"])

    assert intent == "新业务"
    assert statement == "增加 出科确认"


@pytest.mark.parametrize("args", [[], ["优化一下"], ["新业务之外"]])
def test_intake_rejects_words_that_are_not_one_of_the_four_intents(args):
    with pytest.raises(ValueError, match="请使用 /intake"):
        parse_intake(args)


def test_intake_record_binds_the_branch_and_commit_without_rewriting_the_statement():
    comment = render_intake("双线", "同时改旧字段和新汇总", "master", "abc123")

    assert comment.startswith("## 受理记录")
    assert "- 意图：双线" in comment
    assert "- 目标分支：master" in comment
    assert "- 提交号：abc123" in comment
    assert "同时改旧字段和新汇总" in comment
