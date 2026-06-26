from app.config import get_settings
from app.llm.openrouter import call_openrouter
from app.llm.prompts import SYSTEM_PROMPT, build_draft_prompt
from app.models.enums import CaseType, EvidenceVerdict, Language
from app.templates.replies import draft_agent_summary, draft_customer_reply, draft_next_action


async def draft_response_text(
    complaint: str,
    case_type: CaseType,
    evidence: EvidenceVerdict,
    txn_id: str | None,
    amount: float | None,
    counterparty: str,
    language: Language,
    human_review: bool,
    confidence: float,
) -> tuple[str, str, str]:
    agent_summary = draft_agent_summary(
        case_type, txn_id, amount, counterparty, evidence, complaint[:120]
    )
    next_action = draft_next_action(case_type, txn_id, evidence, human_review)
    customer_reply = draft_customer_reply(case_type, txn_id, language, evidence)

    settings = get_settings()
    if not settings.llm_enabled or confidence >= settings.llm_confidence_threshold:
        return agent_summary, next_action, customer_reply

    if not settings.openrouter_api_key:
        return agent_summary, next_action, customer_reply

    prompt = build_draft_prompt(
        complaint=complaint,
        case_type=case_type.value,
        evidence_verdict=evidence.value,
        txn_id=txn_id,
        language=language.value,
        agent_summary=agent_summary,
        recommended_next_action=next_action,
        customer_reply=customer_reply,
    )

    result = await call_openrouter(SYSTEM_PROMPT, prompt)
    if not result:
        return agent_summary, next_action, customer_reply

    return (
        str(result.get("agent_summary", agent_summary)),
        str(result.get("recommended_next_action", next_action)),
        str(result.get("customer_reply", customer_reply)),
    )
