from app.models.enums import CaseType, EvidenceVerdict
from app.pipeline.transaction_matcher import MatchResult
from app.rules.base import NLUSignals


def compute_confidence(
    signals: NLUSignals,
    match: MatchResult,
    evidence: EvidenceVerdict,
    case_type: CaseType,
) -> float:
    base = 0.5

    if match.transaction_id:
        base += min(0.25, match.match_score / 200)
    elif match.ambiguous:
        base += 0.05

    if evidence == EvidenceVerdict.CONSISTENT:
        base += 0.15
    elif evidence == EvidenceVerdict.INCONSISTENT:
        base += 0.1
    elif evidence == EvidenceVerdict.INSUFFICIENT_DATA:
        base -= 0.1

    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        base = max(base, 0.9)

    if signals.nlu_confidence > 0.7:
        base += 0.05

    if signals.is_vague:
        base = min(base, 0.65)

    return round(max(0.0, min(1.0, base)), 2)
