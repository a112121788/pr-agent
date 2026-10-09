"""Run one evidence turn through the official openai-codex SDK.

The handler starts a fresh read-only thread for every prompt. It returns the final answer and
does not let Codex edit the repository, publish comments, or merge the pull request.
"""

from __future__ import annotations

from openai_codex import AsyncCodex, CodexConfig, Sandbox

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings


class CodexAIHandler(BaseAiHandler):
    """Adapt the existing prompt contract to one Codex thread turn."""

    deployment_id = None

    def __init__(self):
        self.main_pr_language = ""

    def _provider_config(self) -> dict:
        """Keep the existing OpenAI key and base URL without changing the selected model."""
        openai = get_settings().get("openai", {})
        api_key = str(openai.get("key", "") or "")
        base_url = str(openai.get("api_base", "") or "").rstrip("/")
        if not api_key and not base_url:
            return {}
        provider = {"name": "gitee-pr-agent", "wire_api": "responses"}
        if api_key:
            provider["env_key"] = "OPENAI_API_KEY"
        if base_url:
            provider["base_url"] = base_url
        return {"model_provider": "gitee-pr-agent", "model_providers": {"gitee-pr-agent": provider}}

    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2, img_path: str = None):
        selected_model = model or get_settings().config.model
        prompt = f"{system.rstrip()}\n\n{user.lstrip()}"
        provider_config = self._provider_config()
        api_key = str(get_settings().get("openai.key", "") or "")
        config = CodexConfig(env={"OPENAI_API_KEY": api_key}) if api_key else None
        async with AsyncCodex(config) as codex:
            thread = await codex.thread_start(
                model=selected_model,
                model_provider=provider_config.get("model_provider"),
                config=provider_config or None,
                developer_instructions="只返回本次审查所需的文本。不要修改文件，不要发布评论，不要合并代码。",
                sandbox=Sandbox.read_only,
                ephemeral=True,
            )
            result = await thread.run(prompt)
        answer = result.final_response or ""
        finish_reason = "stop" if answer else "length"
        return answer, finish_reason
