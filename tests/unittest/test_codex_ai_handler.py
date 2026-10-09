import pytest

from pr_agent.algo.ai_handlers.codex_ai_handler import CodexAIHandler


class _Result:
    final_response = "中文审查"


class _Thread:
    def __init__(self):
        self.prompt = ""

    async def run(self, prompt):
        self.prompt = prompt
        return _Result()


class _Codex:
    def __init__(self):
        self.kwargs = {}
        self.thread = _Thread()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def thread_start(self, **kwargs):
        self.kwargs = kwargs
        return self.thread


@pytest.mark.asyncio
async def test_codex_handler_uses_one_read_only_turn(monkeypatch):
    codex = _Codex()
    monkeypatch.setattr("pr_agent.algo.ai_handlers.codex_ai_handler.AsyncCodex", lambda config=None: codex)
    monkeypatch.setattr(
        "pr_agent.algo.ai_handlers.codex_ai_handler.get_settings",
        lambda: type("Settings", (), {"get": lambda self, key, default=None: {
            "openai": {"key": "sk-test", "api_base": "https://gateway.example/v1"},
            "openai.key": "sk-test",
        }.get(key, default)})(),
    )
    handler = CodexAIHandler()

    answer, finish_reason = await handler.chat_completion("gpt-6.1-sol", "系统", "用户")

    assert answer == "中文审查"
    assert finish_reason == "stop"
    assert codex.kwargs["model"] == "gpt-6.1-sol"
    assert codex.kwargs["config"]["model_providers"]["gitee-pr-agent"]["base_url"] == "https://gateway.example/v1"
    assert codex.kwargs["sandbox"].value == "read-only"
    assert codex.kwargs["ephemeral"] is True
    assert "不要修改文件" in codex.kwargs["developer_instructions"]
    assert codex.thread.prompt == "系统\n\n用户"
