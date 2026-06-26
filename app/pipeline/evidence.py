from app.models.enums import CaseType, EvidenceVerdict, TransactionStatus
from app.models.request import Transaction
from app.pipeline.transaction_matcher import MatchResult
from app.rules.base import NLUSignals


def count_prior_to_counterparty(history: list[Transaction], counterparty: str, exclude_id: str) -> int:
    count = 0
    for txn in history:
        if txn.transaction_id == exclude_id:
            continue
        if txn.counterparty == counterparty and txn.status == TransactionStatus.COMPLETED:
            count += 1
    return count


def evaluate_evidence(
    signals: NLUSignals,
    intent: CaseType,
    match: MatchResult,
    history: list[Transaction],
) -> EvidenceVerdict:
    if intent == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return EvidenceVerdict.INSUFFICIENT_DATA

    if signals.is_vague:
        return EvidenceVerdict.INSUFFICIENT_DATA

    if match.ambiguous or (match.transaction_id is None and match.match_score >= 40):
        return EvidenceVerdict.INSUFFICIENT_DATA

    if match.transaction_id is None:
        return EvidenceVerdict.INSUFFICIENT_DATA

    txn = next((t for t in history if t.transaction_id == match.transaction_id), None)
    if txn is None:
        return EvidenceVerdict.INSUFFICIENT_DATA

    if intent == CaseType.WRONG_TRANSFER:
        prior = count_prior_to_counterparty(history, txn.counterparty, txn.transaction_id)
        if prior >= 2:
            return EvidenceVerdict.INCONSISTENT
        return EvidenceVerdict.CONSISTENT

    if intent == CaseType.PAYMENT_FAILED:
        if txn.status == TransactionStatus.FAILED:
            return EvidenceVerdict.CONSISTENT
        return EvidenceVerdict.INSUFFICIENT_DATA

    if intent == CaseType.DUPLICATE_PAYMENT and match.duplicate_pair:
        return EvidenceVerdict.CONSISTENT

    if intent == CaseType.AGENT_CASH_IN_ISSUE:
        if txn.type and txn.type.value == "cash_in":
            return EvidenceVerdict.CONSISTENT

    if intent == CaseType.MERCHANT_SETTLEMENT_DELAY:
        if txn.type and txn.type.value == "settlement":
            return EvidenceVerdict.CONSISTENT

    if intent == CaseType.REFUND_REQUEST:
        return EvidenceVerdict.CONSISTENT

    if match.match_score >= 55:
        return EvidenceVerdict.CONSISTENT

    return EvidenceVerdict.INSUFFICIENT_DATA
