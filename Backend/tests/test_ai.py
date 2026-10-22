import io
import json

from app.core.config import settings
from app.services.ai import analyst


def test_auto_order_prefers_free_then_paid_then_local(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "auto")
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")
    monkeypatch.setattr(settings, "openai_api_key", "oa-key")
    monkeypatch.setattr(settings, "ollama_base_url", "http://localhost:11434")

    assert analyst.provider_order() == ["openrouter", "openai", "ollama"]
    assert analyst.active_provider() == "openrouter"


def test_auto_order_skips_unconfigured_cloud_providers(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "auto")
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)

    assert analyst.provider_order() == ["ollama"]
    assert analyst.active_provider() == "ollama"


def test_forced_provider_goes_first(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")
    monkeypatch.setattr(settings, "openai_api_key", "oa-key")

    assert analyst.provider_order() == ["openai", "openrouter", "ollama"]


def test_forced_unconfigured_provider_falls_back(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")
    monkeypatch.setattr(settings, "openai_api_key", None)

    assert analyst.provider_order() == ["openrouter", "ollama"]


def test_none_disables_llm_calls(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "none")
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")

    assert analyst.provider_order() == []
    assert analyst.active_provider() == "none"
    assert analyst._call_llm("prompt") is None


def test_extract_json_accepts_plain_and_fenced_output():
    assert analyst._extract_json('{"summary": "ok"}') == {"summary": "ok"}
    assert analyst._extract_json('```json\n{"summary": "ok"}\n```') == {"summary": "ok"}
    assert analyst._extract_json("not json") is None
    assert analyst._extract_json('{"summary": ') is None


def test_llm_falls_through_providers_until_one_succeeds(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "auto")
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")
    monkeypatch.setattr(settings, "openai_api_key", "oa-key")

    calls = []

    def unavailable(prompt: str):
        calls.append("openrouter")

    def available(prompt: str):
        calls.append("openai")
        return {"summary": "from openai"}

    monkeypatch.setitem(analyst._CALLERS, "openrouter", unavailable)
    monkeypatch.setitem(analyst._CALLERS, "openai", available)
    monkeypatch.setitem(analyst._CALLERS, "ollama", lambda prompt: calls.append("ollama"))

    assert analyst._call_llm("prompt") == {"summary": "from openai"}
    assert calls == ["openrouter", "openai"]


def test_openrouter_request_and_response(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")
    monkeypatch.setattr(settings, "openrouter_model", "vendor/model:free")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        payload = {"choices": [{"message": {"content": '{"summary": "free model"}'}}]}
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(analyst.urllib.request, "urlopen", fake_urlopen)

    assert analyst._call_openrouter("prompt") == {"summary": "free model"}
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["body"]["model"] == "vendor/model:free"
    assert captured["body"]["messages"] == [{"role": "user", "content": "prompt"}]


def test_openrouter_missing_content_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")

    def fake_urlopen(request, timeout):
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": None}}]}).encode())

    monkeypatch.setattr(analyst.urllib.request, "urlopen", fake_urlopen)

    assert analyst._call_openrouter("prompt") is None


def test_openrouter_failure_returns_none(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "or-key")

    def fake_urlopen(request, timeout):
        raise OSError("network down")

    monkeypatch.setattr(analyst.urllib.request, "urlopen", fake_urlopen)

    assert analyst._call_openrouter("prompt") is None


def test_openrouter_is_skipped_without_a_key(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    assert analyst._call_openrouter("prompt") is None
