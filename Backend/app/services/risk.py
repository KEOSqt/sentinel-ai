from app.models import Confidence, Severity

SEVERITY_BASE = {
    Severity.INFO: 10,
    Severity.LOW: 25,
    Severity.MEDIUM: 45,
    Severity.HIGH: 70,
    Severity.CRITICAL: 90,
}

CONFIDENCE_FACTOR = {
    Confidence.CONFIRMED: 1.0,
    Confidence.PROBABLE: 0.85,
    Confidence.POSSIBLE: 0.6,
    Confidence.UNKNOWN: 0.5,
}

EXPOSURE_FACTOR = {
    "public": 1.0,
    "internal": 0.7,
    "unknown": 0.8,
}


def score_risk(severity: Severity, confidence: Confidence, exposure: str = "unknown") -> float:
    """Deterministic risk score in [0, 100].

    Formula: base(severity) * confidence_factor * exposure_factor
    Mapping: 0-19 INFO, 20-39 LOW, 40-59 MEDIUM, 60-79 HIGH, 80-100 CRITICAL
    """
    base = SEVERITY_BASE[severity]
    score = base * CONFIDENCE_FACTOR[confidence] * EXPOSURE_FACTOR.get(exposure, 0.8)
    return round(max(0.0, min(100.0, score)), 1)


def band_for(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 40:
        return Severity.MEDIUM
    if score >= 20:
        return Severity.LOW
    return Severity.INFO
