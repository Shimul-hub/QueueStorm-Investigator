import logging

from app.models.enums import CaseType, Language
from app.models.request import TicketRequest
from app.models.response import AnalyzeTicketResponse
from app.pipeline.classifier import classify_case
from app.pipeline.confidence import compute_confidence
from app.pipeline.drafter import draft_response_text
from app.pipeline.evidence import evaluate_evidence
from app.pipeline.normalizer import normalize_complaint
from app.pipeline.nlu import extract_nlu
from app.pipeline.safety import contains_injection, sanitize_text
from app.pipeline.transaction_matcher import match_transaction
from app.rules.registry import pick_case_type

logger = logging.getLogger(__name__)


class TicketAnalyzer:
    async def analyze(self, ticket: TicketRequest) -> AnalyzeTicketResponse:
        norm = normalize_complaint(ticket.complaint, ticket.language)
        if contains_injection(ticket.complaint):
            logger.info("Injection pattern detected in ticket %s — rules enforced", ticket.ticket_id)

        signals, _ = extract_nlu(ticket.complaint, ticket.language)
        ut = ticket.user_type.value if ticket.user_type else None
        intent = pick_case_type(signals, ut, ticket.complaint.lower())

        match = match_transaction(ticket.transaction_history, signals, intent)
        evidence = evaluate_evidence(signals, intent, match, ticket.transaction_history)

        case_type, department, severity, human_review, reason_codes = classify_case(
            signals,
            ticket.user_type,
            evidence,
            match,
            ticket.transaction_history,
            intent,
            ticket.complaint.lower(),
        )

        confidence = compute_confidence(signals, match, evidence, case_type)

        txn = None
        if match.transaction_id:
            txn = next(
                (t for t in ticket.transaction_history if t.transaction_id == match.transaction_id),
                None,
            )

        amount = txn.amount if txn else (signals.amounts[0] if signals.amounts else None)
        counterparty = txn.counterparty if txn else ""

        agent_summary, next_action, customer_reply = await draft_response_text(
            complaint=ticket.complaint,
            case_type=case_type,
            evidence=evidence,
            txn_id=match.transaction_id,
            amount=amount,
            counterparty=counterparty,
            language=norm.detected_language,
            human_review=human_review,
            confidence=confidence,
        )

        lang = norm.detected_language
        agent_summary = sanitize_text(agent_summary, Language.EN)
        next_action = sanitize_text(next_action, Language.EN)
        customer_reply = sanitize_text(customer_reply, lang)

        return AnalyzeTicketResponse(
            ticket_id=ticket.ticket_id,
            relevant_transaction_id=match.transaction_id,
            evidence_verdict=evidence,
            case_type=case_type,
            severity=severity,
            department=department,
            agent_summary=agent_summary,
            recommended_next_action=next_action,
            customer_reply=customer_reply,
            human_review_required=human_review,
            confidence=confidence,
            reason_codes=reason_codes or [case_type.value],
        )
