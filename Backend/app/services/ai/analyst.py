import json
import logging
import re
import urllib.request
from collections.abc import Callable

from app.core.config import settings
from app.core.logging import get_request_id
from app.models import AIAnalysis, Asset, Finding
from app.services.ai.rag import KnowledgeBase

logger = logging.getLogger(__name__)

PROVIDERS = ("openrouter", "openai", "ollama")


def _configured(provider: str) -> bool:
    if provider == "openrouter":
        return bool(settings.openrouter_api_key)
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "ollama":
        return bool(settings.ollama_base_url)
    return False


def provider_order() -> list[str]:
    """Providers to try, in order, for the current settings and keys."""
    if settings.llm_provider == "none":
        return []
    if settings.llm_provider == "auto":
        return [provider for provider in PROVIDERS if _configured(provider)]

    forced = [settings.llm_provider] if _configured(settings.llm_provider) else []
    return forced + [provider for provider in PROVIDERS if provider not in forced and _configured(provider)]


def active_provider() -> str:
    """The provider ``_call_llm`` will try first, or ``none`` when disabled."""
    order = provider_order()
    return order[0] if order else "none"


def build_payload(assets: list[Asset], findings: list[Finding]) -> dict:
    return {
        "assets": [a.model_dump(mode="json") for a in assets],
        "findings": [
            {
                "title": f.title,
                "severity": f.severity.value,
                "risk_score": f.risk_score,
                "confidence": f.confidence.value,
                "asset": f.asset.ip if f.asset else None,
                "service": f"{f.affected_service.service}:{f.affected_service.port}" if f.affected_service else None,
                "rationale": f.rationale,
            }
            for f in findings
        ],
        "risk_score": max((f.risk_score for f in findings), default=0),
    }


def _prompt(payload: dict, context: list[str]) -> str:
    return (
        "You are a cybersecurity analyst. Analyze the structured security data and return ONLY valid JSON with keys: "
        "summary, risk_assessment, priority_findings (list), attack_paths (list), recommendations (list), missing_information (list).\n\n"
        f"Relevant knowledge:\n{chr(10).join(context)}\n\n"
        f"Data:\n{json.dumps(payload)}"
    )


def _extract_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None


def _call_openai_compatible(
    url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: float,
    extra_headers: dict[str, str] | None = None,
) -> dict | None:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    request = urllib.request.Request(
        url,
        data=json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
        content = data["choices"][0]["message"].get("content")
        if not isinstance(content, str):
            logger.error(
                "llm_call_failed",
                extra={
                    "provider": model,
                    "reason": "empty_or_invalid_content",
                    "request_id": get_request_id(),
                },
            )
            return None
        return _extract_json(content)
    except Exception:
        logger.error(
            "llm_call_failed",
            extra={
                "provider": model,
                "reason": "network_or_parse_error",
                "request_id": get_request_id(),
            },
        )
        return None


def _call_openrouter(prompt: str) -> dict | None:
    if not settings.openrouter_api_key:
        return None
    logger.debug(
        "llm_call_start",
        extra={"provider": "openrouter", "request_id": get_request_id()},
    )
    try:
        return _call_openai_compatible(
            "https://openrouter.ai/api/v1/chat/completions",
            settings.openrouter_api_key,
            settings.openrouter_model,
            prompt,
            timeout=60,
            extra_headers={
                "HTTP-Referer": "https://github.com/KEOSqt/sentinel-ai",
                "X-Title": "Sentinel-AI",
            },
        )
    except Exception:
        logger.error(
            "llm_call_failed",
            extra={"provider": "openrouter", "request_id": get_request_id()},
        )
        return None


def _call_openai(prompt: str) -> dict | None:
    if not settings.openai_api_key:
        return None
    logger.debug(
        "llm_call_start",
        extra={"provider": "openai", "request_id": get_request_id()},
    )
    try:
        return _call_openai_compatible(
            "https://api.openai.com/v1/chat/completions",
            settings.openai_api_key,
            settings.openai_model,
            prompt,
            timeout=60,
        )
    except Exception:
        logger.error(
            "llm_call_failed",
            extra={"provider": "openai", "request_id": get_request_id()},
        )
        return None


def _call_ollama(prompt: str) -> dict | None:
    logger.debug(
        "llm_call_start",
        extra={"provider": "ollama", "request_id": get_request_id()},
    )
    try:
        request = urllib.request.Request(
            f"{settings.ollama_base_url}/api/generate",
            data=json.dumps({"model": settings.ollama_model, "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.load(response)
        return _extract_json(data.get("response", ""))
    except Exception:
        logger.error(
            "llm_call_failed",
            extra={"provider": "ollama", "request_id": get_request_id()},
        )
        return None


_CALLERS: dict[str, Callable[[str], dict | None]] = {
    "openrouter": _call_openrouter,
    "openai": _call_openai,
    "ollama": _call_ollama,
}


def _call_llm(prompt: str) -> dict | None:
    """Try each configured provider in order. Returns parsed JSON or None."""
    for provider in provider_order():
        logger.debug(
            "llm_trying_provider",
            extra={"provider": provider, "request_id": get_request_id()},
        )
        parsed = _CALLERS[provider](prompt)
        if parsed is not None:
            logger.info(
                "llm_call_success",
                extra={"provider": provider, "request_id": get_request_id()},
            )
            return parsed
    logger.warning(
        "llm_all_providers_failed",
        extra={"request_id": get_request_id()},
    )
    return None


def _fallback_analysis(assets: list[Asset], findings: list[Finding]) -> AIAnalysis:
    if not findings:
        return AIAnalysis(
            summary="No findings were identified from the provided evidence.",
            risk_assessment="Overall risk is low based on available evidence.",
            recommendations=["Collect additional evidence (credentialed scans, logs) to improve coverage."],
            missing_information=["Authentication logs", "Vulnerability scan results"],
        )
    critical = [f for f in findings if f.severity.value in ("CRITICAL", "HIGH")]
    return AIAnalysis(
        summary=f"Analyzed {len(assets)} asset(s) and {len(findings)} finding(s); {len(critical)} require urgent attention.",
        risk_assessment=f"Highest risk score observed: {max(f.risk_score for f in findings)}.",
        priority_findings=[f.title for f in findings[:5]],
        attack_paths=_infer_attack_paths(findings),
        recommendations=[f.remediation for f in findings[:5] if f.remediation],
        missing_information=["Asset network exposure context", "Patch management history"],
    )


def _infer_attack_paths(findings: list[Finding]) -> list[str]:
    paths = []
    titles = " ".join(f.title.lower() for f in findings)
    if "rdp" in titles or "remote desktop" in titles:
        paths.append("External RDP exposure enables brute-force and wormable RCE (BlueKeep).")
    if "openssh" in titles:
        paths.append("Outdated SSH may allow information disclosure or agent abuse prior to lateral movement.")
    if "apache" in titles or "nginx" in titles:
        paths.append("Vulnerable web server can be leveraged for remote code execution and initial access.")
    return paths


def analyze_security_posture(assets: list[Asset], findings: list[Finding]) -> AIAnalysis:
    payload = build_payload(assets, findings)
    kb = KnowledgeBase()
    query = " ".join(f.title for f in findings[:5]) or "security posture"
    context = kb.retrieve(query)

    logger.info(
        "analyze_security_posture_start",
        extra={
            "asset_count": len(assets),
            "finding_count": len(findings),
            "request_id": get_request_id(),
        },
    )

    parsed = _call_llm(_prompt(payload, context))
    if parsed is not None:
        try:
            return AIAnalysis.model_validate(parsed)
        except Exception:
            logger.error(
                "llm_invalid_response",
                extra={"request_id": get_request_id()},
            )
    return _fallback_analysis(assets, findings)
