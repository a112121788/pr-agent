"""Show the current factory stage without changing any record."""

from pr_agent.algo.factory_record import (
    latest_evidence_sha,
    latest_intake_intent,
    latest_verdict,
    render_status,
)
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import get_git_provider


class PRStatus:
    """Read intake, evidence, and verdict comments, then name the next stage."""

    def __init__(self, pr_url: str, args=None, ai_handler=None):
        self.git_provider = get_git_provider()(pr_url)

    async def run(self):
        comments = self.git_provider.get_issue_comments_newest_first()
        verdict, verdict_sha = latest_verdict(comments)
        comment = render_status(
            latest_intake_intent(comments),
            latest_evidence_sha(comments),
            verdict,
            verdict_sha,
            self.git_provider.get_pr_head_sha(),
        )
        if get_settings().config.publish_output:
            self.git_provider.publish_comment(comment)
            self.git_provider.remove_initial_comment()
        return comment
