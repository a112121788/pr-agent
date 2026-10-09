"""Record the author's stated intent without asking a model to rewrite it."""

from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider

INTENTS = ("新业务", "旧版迭代", "新版升级", "双线")


def parse_intake(args) -> tuple[str, str]:
    """Return one allowed intent and the untouched remainder of the author's words."""
    words = [str(arg).strip() for arg in args or [] if str(arg).strip()]
    if not words or words[0] not in INTENTS:
        allowed = "、".join(INTENTS)
        raise ValueError(f"请使用 /intake {allowed}，并在后面写下原话")
    return words[0], " ".join(words[1:])


def render_intake(intent: str, statement: str, base_ref: str, head_sha: str) -> str:
    """Render the intake record. The statement is copied, never rewritten."""
    lines = [
        "## 受理记录",
        "",
        f"- 意图：{intent}",
        f"- 目标分支：{base_ref or '未读取'}",
        f"- 提交号：{head_sha or '未读取'}",
        "",
        "### 原话",
        "",
        statement or "（未填写）",
    ]
    return "\n".join(lines)


class PRIntake:
    """Publish one intake comment and do not call a model."""

    def __init__(self, pr_url: str, args=None, ai_handler=None):
        self.git_provider = get_git_provider()(pr_url)
        self.intent, self.statement = parse_intake(args)

    async def run(self):
        comment = render_intake(
            self.intent,
            self.statement,
            self.git_provider.get_pr_branch(),
            self.git_provider.get_pr_head_sha(),
        )
        if get_settings().config.publish_output:
            self.git_provider.publish_comment(comment)
            self.git_provider.remove_initial_comment()
        return comment
