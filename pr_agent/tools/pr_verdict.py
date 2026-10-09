"""Publish one human verdict without interpreting model output."""

from pr_agent.algo.factory_record import parse_verdict, render_verdict
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider


class PRVerdict:
    """Record 放行, 退回, or 等待 against the current commit."""

    def __init__(self, pr_url: str, args=None, ai_handler=None):
        self.git_provider = get_git_provider()(pr_url)
        self.verdict = parse_verdict(args)

    async def run(self):
        author = ""
        get_user_id = getattr(self.git_provider, "get_user_id", None)
        if callable(get_user_id):
            author = str(get_user_id() or "")
        comment = render_verdict(self.verdict, self.git_provider.get_pr_head_sha(), author)
        if get_settings().config.publish_output:
            self.git_provider.publish_comment(comment)
            self.git_provider.remove_initial_comment()
        return comment
