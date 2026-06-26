import re

from app.models.enums import CaseType
from app.rules.base import CaseRule, NLUSignals
from app.rules.wrong_transfer import WrongTransferRule
from app.rules.payment_failed import PaymentFailedRule
from app.rules.duplicate_payment import DuplicatePaymentRule
from app.rules.refund_request import RefundRequestRule
from app.rules.merchant_settlement import MerchantSettlementRule
from app.rules.agent_cash_in import AgentCashInRule
from app.rules.phishing import PhishingRule

RULES: list[CaseRule] = [
    PhishingRule(),
    DuplicatePaymentRule(),
    PaymentFailedRule(),
    WrongTransferRule(),
    AgentCashInRule(),
    MerchantSettlementRule(),
    RefundRequestRule(),
]

INTENT_KEYWORDS: dict[CaseType, list[str]] = {
    CaseType.PHISHING_OR_SOCIAL_ENGINEERING: [
        "otp", "pin", "password", "scam", "phishing", "fake", "fraud",
        "blocked", "verify your account", "share your", "ওটিপি", "পিন", "পাসওয়ার্ড",
        "প্রতারণা", "ভুয়া", "called me saying",
    ],
    CaseType.WRONG_TRANSFER: [
        "wrong number", "wrong person", "wrong recipient", "mistake transfer",
        "typed wrong", "vul number", "ভুল নম্বর", "ভুল নম্বরে", "wrong transfer",
        "didn't get it", "did not get", "not received", "not get it", "he says he didn't",
        "pathaisilam", "sent to my",
    ],
    CaseType.PAYMENT_FAILED: [
        "failed", "balance deducted", "balance was deducted", "kata gese",
        "cut hoise", "deducted twice", "showed failed", "payment failed",
        "balance not reflected", "failed but", "dekhay failed",
    ],
    CaseType.DUPLICATE_PAYMENT: [
        "twice", "duplicate", "double", "deducted twice", "paid once",
        "duibar", "দুইবার", "double deduct",
    ],
    CaseType.REFUND_REQUEST: [
        "refund", "change my mind", "don't want", "return my money",
        "রিফান্ড", "ফেরত",
    ],
    CaseType.MERCHANT_SETTLEMENT_DELAY: [
        "settlement", "not been settled", "settlement delay", "sales have not",
        "settled to my account", "batch", "সেটেলমেন্ট",
    ],
    CaseType.AGENT_CASH_IN_ISSUE: [
        "cash in", "cash-in", "agent", "balance not", "not reflected",
        "ক্যাশ ইন", "এজেন্ট", "ব্যালেন্সে টাকা আসেনি",
    ],
}


def score_intents(text: str) -> NLUSignals:
    lower = text.lower()
    signals = NLUSignals()

    amounts = re.findall(r"\b(\d+(?:\.\d+)?)\b", lower)
    signals.amounts = [float(a) for a in amounts]

    phone_patterns = re.findall(r"(?:\+880|880|0)(1[3-9]\d{8})", text)
    signals.phones = list(dict.fromkeys(phone_patterns))

    for case_type, keywords in INTENT_KEYWORDS.items():
        if any(kw in lower or kw in text for kw in keywords):
            signals.intents.append(case_type)

    signals.mentions_refund = any(k in lower for k in ["refund", "return my", "ফেরত", "রিফান্ড"])
    signals.mentions_otp_pin = bool(
        re.search(r"\b(otp|pin|password|cvv|card number)\b", lower)
        or re.search(r"(ওটিপি|পিন|পাসওয়ার্ড)", text)
    )
    signals.mentions_duplicate = CaseType.DUPLICATE_PAYMENT in signals.intents
    signals.mentions_failed = CaseType.PAYMENT_FAILED in signals.intents
    signals.mentions_wrong_transfer = CaseType.WRONG_TRANSFER in signals.intents
    signals.mentions_settlement = CaseType.MERCHANT_SETTLEMENT_DELAY in signals.intents
    signals.mentions_cash_in = CaseType.AGENT_CASH_IN_ISSUE in signals.intents
    signals.mentions_phishing = CaseType.PHISHING_OR_SOCIAL_ENGINEERING in signals.intents

    vague_patterns = [
        "something is wrong", "please check", "help me", "wrong with my money",
        "কিছু সমস্যা", "দেখুন",
    ]
    word_count = len(text.split())
    signals.is_vague = word_count < 12 and any(p in lower for p in vague_patterns)

    if signals.intents:
        signals.nlu_confidence = min(0.95, 0.6 + 0.1 * len(signals.intents))
    elif signals.is_vague:
        signals.nlu_confidence = 0.55
    else:
        signals.nlu_confidence = 0.45

    return signals


def pick_case_type(signals: NLUSignals, user_type: str | None = None, complaint_lower: str = "") -> CaseType:
    if signals.mentions_phishing or (
        signals.mentions_otp_pin
        and CaseType.PHISHING_OR_SOCIAL_ENGINEERING in signals.intents
    ):
        return CaseType.PHISHING_OR_SOCIAL_ENGINEERING

    if CaseType.PAYMENT_FAILED in signals.intents and any(
        k in complaint_lower for k in ("failed", "showed failed", "payment failed", "dekhay failed")
    ):
        return CaseType.PAYMENT_FAILED

    if signals.mentions_refund and CaseType.REFUND_REQUEST in signals.intents:
        return CaseType.REFUND_REQUEST

    priority = [
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        CaseType.DUPLICATE_PAYMENT,
        CaseType.AGENT_CASH_IN_ISSUE,
        CaseType.MERCHANT_SETTLEMENT_DELAY,
        CaseType.PAYMENT_FAILED,
        CaseType.WRONG_TRANSFER,
        CaseType.REFUND_REQUEST,
    ]
    for ct in priority:
        if ct in signals.intents:
            return ct

    if user_type == "merchant":
        return CaseType.MERCHANT_SETTLEMENT_DELAY
    if signals.is_vague:
        return CaseType.OTHER
    return CaseType.OTHER
