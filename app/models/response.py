from pydantic import BaseModel, Field

from app.models.enums import (
    CaseType,
    Department,
    EvidenceVerdict,
    Severity,
)


class AnalyzeTicketResponse(BaseModel):
    ticket_id: str
    relevant_transaction_id: str | None
    evidence_verdict: EvidenceVerdict
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    recommended_next_action: str
    customer_reply: str
    human_review_required: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason_codes: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
