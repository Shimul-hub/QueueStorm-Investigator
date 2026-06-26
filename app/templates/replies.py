from app.models.enums import CaseType, EvidenceVerdict, Language


def draft_agent_summary(
    case_type: CaseType,
    txn_id: str | None,
    amount: float | None,
    counterparty: str,
    evidence: EvidenceVerdict,
    complaint_snippet: str,
) -> str:
    amt_str = f"{int(amount)} BDT" if amount else "unknown amount"
    txn_part = f" via {txn_id}" if txn_id else ""

    summaries = {
        CaseType.WRONG_TRANSFER: (
            f"Customer reports a wrong transfer{txn_part} ({amt_str} to {counterparty or 'unknown recipient'}). "
            f"Evidence is {evidence.value.replace('_', ' ')}."
        ),
        CaseType.PAYMENT_FAILED: (
            f"Customer reports a failed payment{txn_part} ({amt_str}) with possible balance deduction. "
            f"Requires payments operations investigation."
        ),
        CaseType.REFUND_REQUEST: (
            f"Customer requests refund{txn_part} ({amt_str}). Not necessarily a service failure."
        ),
        CaseType.DUPLICATE_PAYMENT: (
            f"Customer reports duplicate payment{txn_part} ({amt_str} to {counterparty or 'biller'})."
        ),
        CaseType.MERCHANT_SETTLEMENT_DELAY: (
            f"Merchant reports delayed settlement{txn_part} ({amt_str}). Settlement may still be pending."
        ),
        CaseType.AGENT_CASH_IN_ISSUE: (
            f"Customer reports cash-in{txn_part} ({amt_str} via {counterparty or 'agent'}) not reflected in balance."
        ),
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING: (
            "Customer reports a suspicious contact asking for credentials. Likely social engineering attempt."
        ),
        CaseType.OTHER: (
            "Customer report is vague or lacks specifics needed to identify a relevant transaction."
        ),
    }
    return summaries.get(case_type, summaries[CaseType.OTHER])


def draft_next_action(
    case_type: CaseType,
    txn_id: str | None,
    evidence: EvidenceVerdict,
    human_review: bool,
) -> str:
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return (
            "Escalate to fraud_risk team immediately. Confirm the company never asks for OTP. "
            "Log the reported number for fraud pattern analysis."
        )
    if evidence == EvidenceVerdict.INSUFFICIENT_DATA and case_type == CaseType.OTHER:
        return (
            "Reply to customer asking for specific details: transaction ID, amount, "
            "what went wrong, and approximate time."
        )
    if evidence == EvidenceVerdict.INSUFFICIENT_DATA and case_type == CaseType.WRONG_TRANSFER:
        return (
            "Reply to customer asking for the recipient's number to identify the correct transaction. "
            "Do not initiate dispute until the transaction is confirmed."
        )
    if case_type == CaseType.WRONG_TRANSFER:
        if evidence == EvidenceVerdict.INCONSISTENT:
            return (
                "Flag for human review. Verify with the customer whether this was genuinely a wrong transfer "
                "given the established transaction pattern with this recipient."
            )
        return f"Verify {txn_id} details with the customer and initiate the wrong-transfer dispute workflow per policy."
    if case_type == CaseType.PAYMENT_FAILED:
        return (
            f"Investigate {txn_id} ledger status. If balance was deducted on a failed payment, "
            "initiate the automatic reversal flow within standard SLA."
        )
    if case_type == CaseType.DUPLICATE_PAYMENT:
        return (
            f"Verify the duplicate with payments_ops. If the biller confirms only one payment was received, "
            f"initiate reversal of {txn_id}."
        )
    if case_type == CaseType.REFUND_REQUEST:
        return (
            "Inform the customer that refund eligibility depends on the merchant's own policy. "
            "Provide guidance on contacting the merchant directly for a refund."
        )
    if case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
        return (
            "Route to merchant_operations to verify settlement batch status. "
            "If the batch is delayed, communicate a revised ETA to the merchant."
        )
    if case_type == CaseType.AGENT_CASH_IN_ISSUE:
        return (
            f"Investigate {txn_id} pending status with agent operations. "
            "Confirm settlement state and resolve within the standard cash-in SLA."
        )
    return "Route to customer_support for clarification and follow standard support workflow."


def draft_customer_reply(
    case_type: CaseType,
    txn_id: str | None,
    language: Language,
    evidence: EvidenceVerdict,
) -> str:
    en = _customer_reply_en(case_type, txn_id, evidence)
    bn = _customer_reply_bn(case_type, txn_id, evidence)

    if language == Language.BN:
        return bn
    if language == Language.MIXED:
        return bn
    return en


def _customer_reply_en(case_type: CaseType, txn_id: str | None, evidence: EvidenceVerdict) -> str:
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return (
            "Thank you for reaching out before sharing any information. "
            "We never ask for your PIN, OTP, or password under any circumstances. "
            "Please do not share these with anyone, even if they claim to be from us. "
            "Our fraud team has been notified of this incident."
        )
    if case_type == CaseType.OTHER and evidence == EvidenceVerdict.INSUFFICIENT_DATA:
        return (
            "Thank you for reaching out. To help you faster, please share the transaction ID, "
            "the amount involved, and a short description of what went wrong. "
            "Please do not share your PIN or OTP with anyone."
        )
    if case_type == CaseType.WRONG_TRANSFER and evidence == EvidenceVerdict.INSUFFICIENT_DATA:
        return (
            "Thank you for reaching out. We see multiple transactions that may match your description. "
            "Could you share the recipient's number so we can identify the right transaction? "
            "Please do not share your PIN or OTP with anyone."
        )
    if case_type == CaseType.REFUND_REQUEST:
        return (
            "Thank you for reaching out. Refunds for completed merchant payments depend on the merchant's own policy. "
            "We recommend contacting the merchant directly. If you need help reaching them, please reply and we will guide you. "
            "Please do not share your PIN or OTP with anyone."
        )
    if case_type in (CaseType.PAYMENT_FAILED, CaseType.DUPLICATE_PAYMENT):
        txn_ref = f"transaction {txn_id}" if txn_id else "your transaction"
        return (
            f"We have noted the possible issue for {txn_ref}. "
            "Our payments team will verify the case and any eligible amount will be returned through official channels. "
            "Please do not share your PIN or OTP with anyone."
        )
    if case_type == CaseType.MERCHANT_SETTLEMENT_DELAY:
        return (
            f"We have noted your concern about settlement {txn_id}. "
            "Our merchant operations team will check the batch status and update you on the expected settlement time "
            "through official channels."
        )
    if case_type == CaseType.AGENT_CASH_IN_ISSUE:
        return (
            f"We have noted your concern regarding transaction {txn_id}. "
            "Our agent operations team will review this promptly and contact you through official support channels. "
            "Please do not share your PIN or OTP with anyone."
        )
    txn_ref = f"transaction {txn_id}" if txn_id else "your case"
    return (
        f"We have noted your concern about {txn_ref}. "
        "Please do not share your PIN or OTP with anyone. "
        "Our dispute team will review the case and contact you through official support channels."
    )


def _customer_reply_bn(case_type: CaseType, txn_id: str | None, evidence: EvidenceVerdict) -> str:
    if case_type == CaseType.AGENT_CASH_IN_ISSUE:
        return (
            f"আপনার লেনদেন {txn_id} এর বিষয়ে আমরা অবগত হয়েছি। "
            "আমাদের এজেন্ট অপারেশন্স দল এটি দ্রুত যাচাই করবে এবং অফিসিয়াল চ্যানেলে আপনাকে জানাবে। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        )
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return (
            "তথ্য শেয়ার করার আগে যোগাযোগ করার জন্য ধন্যবাদ। "
            "আমরা কখনোই আপনার পিন, ওটিপি বা পাসওয়ার্ড চাই না। "
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"
        )
    return _customer_reply_en(case_type, txn_id, evidence)
