from dataclasses import dataclass
from datetime import datetime, timezone

from app.models.enums import CaseType, TransactionStatus, TransactionType
from app.models.request import Transaction
from app.rules.base import NLUSignals


@dataclass
class MatchResult:
    transaction_id: str | None
    match_score: float
    ambiguous: bool
    duplicate_pair: bool
    scores: list[tuple[str, float]]


def _normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("880"):
        return digits[3:]
    if digits.startswith("0"):
        return digits[1:]
    return digits


def _type_aligns(intent: CaseType | None, txn_type: TransactionType | None) -> bool:
    if txn_type is None or intent is None:
        return False
    mapping = {
        CaseType.WRONG_TRANSFER: {TransactionType.TRANSFER},
        CaseType.PAYMENT_FAILED: {TransactionType.PAYMENT},
        CaseType.DUPLICATE_PAYMENT: {TransactionType.PAYMENT},
        CaseType.REFUND_REQUEST: {TransactionType.PAYMENT, TransactionType.REFUND},
        CaseType.MERCHANT_SETTLEMENT_DELAY: {TransactionType.SETTLEMENT},
        CaseType.AGENT_CASH_IN_ISSUE: {TransactionType.CASH_IN},
    }
    allowed = mapping.get(intent, set())
    return txn_type in allowed


def _status_bonus(intent: CaseType | None, status: TransactionStatus | None) -> float:
    if status is None or intent is None:
        return 0
    if intent == CaseType.PAYMENT_FAILED and status == TransactionStatus.FAILED:
        return 10
    if intent == CaseType.AGENT_CASH_IN_ISSUE and status == TransactionStatus.PENDING:
        return 10
    if intent == CaseType.MERCHANT_SETTLEMENT_DELAY and status == TransactionStatus.PENDING:
        return 10
    return 0


def find_duplicate_pair(history: list[Transaction]) -> Transaction | None:
    for i, a in enumerate(history):
        for b in history[i + 1:]:
            if (
                a.amount == b.amount
                and a.counterparty == b.counterparty
                and a.type == b.type
                and a.status == TransactionStatus.COMPLETED
                and b.status == TransactionStatus.COMPLETED
            ):
                try:
                    ta = datetime.fromisoformat(a.timestamp.replace("Z", "+00:00"))
                    tb = datetime.fromisoformat(b.timestamp.replace("Z", "+00:00"))
                    if abs((tb - ta).total_seconds()) <= 60:
                        return b if tb >= ta else a
                except ValueError:
                    return b
    return None


def score_transaction(
    txn: Transaction,
    signals: NLUSignals,
    intent: CaseType,
    index: int,
    total: int,
) -> float:
    score = 0.0
    if signals.amounts:
        for amt in signals.amounts:
            if txn.amount == amt:
                score += 40
                break
            if txn.amount > 0 and abs(txn.amount - amt) / txn.amount <= 0.05:
                score += 20
                break

    if _type_aligns(intent, txn.type):
        score += 15

    if signals.phones and txn.counterparty:
        txn_phone = _normalize_phone(txn.counterparty)
        for p in signals.phones:
            if _normalize_phone(p) == txn_phone or txn_phone.endswith(_normalize_phone(p)[-10:]):
                score += 30
                break

    score += _status_bonus(intent, txn.status)

    recency = (total - index) / max(total, 1)
    score += 5 * recency

    return score


def match_transaction(
    history: list[Transaction],
    signals: NLUSignals,
    intent: CaseType,
) -> MatchResult:
    if not history:
        return MatchResult(None, 0.0, False, False, [])

    if intent == CaseType.DUPLICATE_PAYMENT:
        dup = find_duplicate_pair(history)
        if dup:
            return MatchResult(
                dup.transaction_id,
                90.0,
                False,
                True,
                [(dup.transaction_id, 90.0)],
            )

    scores: list[tuple[str, float]] = []
    for idx, txn in enumerate(history):
        s = score_transaction(txn, signals, intent, idx, len(history))
        scores.append((txn.transaction_id, s))

    scores.sort(key=lambda x: x[1], reverse=True)
    if not scores:
        return MatchResult(None, 0.0, False, False, [])

    top_id, top_score = scores[0]
    second_score = scores[1][1] if len(scores) > 1 else 0.0

    same_amount_ambiguous = False
    if signals.amounts and len(scores) >= 2:
        target = signals.amounts[0]
        matching = [t for t in history if t.amount == target]
        if len(matching) >= 2 and not signals.phones:
            same_amount_ambiguous = True

    if same_amount_ambiguous:
        return MatchResult(None, top_score, True, False, scores)

    if top_score >= 55 and (top_score - second_score) >= 15:
        return MatchResult(top_id, top_score, False, False, scores)

    if top_score >= 40 and intent in (CaseType.PAYMENT_FAILED, CaseType.AGENT_CASH_IN_ISSUE, CaseType.MERCHANT_SETTLEMENT_DELAY):
        if len(scores) == 1 or (top_score - second_score) >= 10:
            return MatchResult(top_id, top_score, False, False, scores)

    if top_score >= 40 and intent == CaseType.REFUND_REQUEST and len(history) == 1:
        return MatchResult(top_id, top_score, False, False, scores)

    if top_score >= 40 and intent == CaseType.WRONG_TRANSFER and not same_amount_ambiguous:
        if top_score - second_score >= 10 or len(scores) == 1:
            return MatchResult(top_id, top_score, False, False, scores)

    return MatchResult(None, top_score, top_score >= 40, False, scores)
