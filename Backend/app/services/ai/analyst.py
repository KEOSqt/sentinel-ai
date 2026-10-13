import json
import re
import urllib.request

from app.core.config import settings
from app.models import AIAnalysis, Asset, Finding
from app.services.ai.rag import KnowledgeBase


def active_provider() -> str:
    """The provider ``_call_llm`` will actually try first.

    Note: ``SENTINEL_ANTHROPIC_API_KEY`` is accepted by the settings layer and
    documented in the README, but ``_call_llm`` never calls Anthropic. This
    deliberately reports only what the code really does rather than what an
    operator might expect from a configured key.
    """
    if settings.openai_api_key:
        return "openai"
    return "ollama"


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


def _call_llm(prompt: str) -> dict | None:
    """Try OpenAI-compatible, then Ollama. Returns parsed JSON dict or None."""
    if settings.openai_api_key:
        try:
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps({
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                }).encode(),
                headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            return _extract_json(data["choices"][0]["message"]["content"])
        except Exception:
            pass

    try:
        req = urllib.request.Request(
            f"{settings.ollama_base_url}/api/generate",
            data=json.dumps({"model": "llama3.1", "prompt": prompt, "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.load(resp)
        return _extract_json(data.get("response", ""))
    except Exception:
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

    parsed = _call_llm(_prompt(payload, context))
    if parsed is not None:
        try:
            return AIAnalysis.model_validate(parsed)
        except Exception:
            pass
    return _fallback_analysis(assets, findings)
