from app.models.enums import CaseType, Department, EvidenceVerdict, Severity, UserType
from app.models.request import Transaction
from app.pipeline.transaction_matcher import MatchResult
from app.rules.base import NLUSignals
from app.rules.registry import pick_case_type, RULES


DEPARTMENT_MAP: dict[CaseType, Department] = {
    CaseType.WRONG_TRANSFER: Department.DISPUTE_RESOLUTION,
    CaseType.PAYMENT_FAILED: Department.PAYMENTS_OPS,
    CaseType.DUPLICATE_PAYMENT: Department.PAYMENTS_OPS,
    CaseType.REFUND_REQUEST: Department.CUSTOMER_SUPPORT,
    CaseType.MERCHANT_SETTLEMENT_DELAY: Department.MERCHANT_OPERATIONS,
    CaseType.AGENT_CASH_IN_ISSUE: Department.AGENT_OPERATIONS,
    CaseType.PHISHING_OR_SOCIAL_ENGINEERING: Department.FRAUD_RISK,
    CaseType.OTHER: Department.CUSTOMER_SUPPORT,
}


def classify_case(
    signals: NLUSignals,
    user_type: UserType | None,
    evidence: EvidenceVerdict,
    match: MatchResult,
    history: list[Transaction],
    intent: CaseType,
    complaint_lower: str = "",
) -> tuple[CaseType, Department, Severity, bool, list[str]]:
    ut = user_type.value if user_type else None
    case_type = intent if intent != CaseType.OTHER else pick_case_type(signals, ut, complaint_lower)

    if signals.is_vague and evidence == EvidenceVerdict.INSUFFICIENT_DATA:
        if case_type not in (CaseType.WRONG_TRANSFER,):
            case_type = CaseType.OTHER

    if match.ambiguous and CaseType.WRONG_TRANSFER in signals.intents:
        case_type = CaseType.WRONG_TRANSFER

    department = DEPARTMENT_MAP.get(case_type, Department.CUSTOMER_SUPPORT)

    rule = next((r for r in RULES if r.case_type == case_type), None)
    severity = rule.default_severity() if rule else Severity.MEDIUM

    if case_type == CaseType.WRONG_TRANSFER and evidence == EvidenceVerdict.INCONSISTENT:
        severity = Severity.MEDIUM

    if case_type == CaseType.OTHER:
        severity = Severity.LOW

    reason_codes: list[str] = []
    if rule:
        reason_codes.extend(rule.reason_codes())

    if evidence == EvidenceVerdict.INCONSISTENT:
        reason_codes.append("evidence_inconsistent")
    if evidence == EvidenceVerdict.INSUFFICIENT_DATA:
        if signals.is_vague:
            reason_codes.append("vague_complaint")
            reason_codes.append("needs_clarification")
        elif match.ambiguous:
            reason_codes.append("ambiguous_match")
            reason_codes.append("needs_clarification")
    if match.transaction_id:
        reason_codes.append("transaction_match")
    if match.duplicate_pair:
        reason_codes.append("duplicate_payment")

    human_review = _requires_human_review(
        case_type, evidence, match, history, severity
    )

    return case_type, department, severity, human_review, list(dict.fromkeys(reason_codes))


def _requires_human_review(
    case_type: CaseType,
    evidence: EvidenceVerdict,
    match: MatchResult,
    history: list[Transaction],
    severity: Severity,
) -> bool:
    if severity == Severity.CRITICAL:
        return True
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return True
    if evidence == EvidenceVerdict.INCONSISTENT:
        return True
    if case_type == CaseType.WRONG_TRANSFER and evidence == EvidenceVerdict.CONSISTENT:
        return True
    if case_type == CaseType.DUPLICATE_PAYMENT and evidence == EvidenceVerdict.CONSISTENT:
        return True
    if case_type == CaseType.AGENT_CASH_IN_ISSUE and evidence == EvidenceVerdict.CONSISTENT:
        return True

    if match.transaction_id:
        txn = next((t for t in history if t.transaction_id == match.transaction_id), None)
        if txn and txn.amount >= 10000 and case_type in (
            CaseType.WRONG_TRANSFER,
            CaseType.DUPLICATE_PAYMENT,
            CaseType.PAYMENT_FAILED,
        ):
            return True

    if any(t.amount >= 50000 for t in history) and case_type in (
        CaseType.WRONG_TRANSFER,
        CaseType.DUPLICATE_PAYMENT,
    ):
        return True

    return False
