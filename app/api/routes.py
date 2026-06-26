from fastapi import APIRouter, Depends

from app.models.request import TicketRequest
from app.models.response import AnalyzeTicketResponse, HealthResponse
from app.pipeline.analyzer import TicketAnalyzer

router = APIRouter()


def get_analyzer() -> TicketAnalyzer:
    return TicketAnalyzer()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/analyze-ticket",
    response_model=AnalyzeTicketResponse,
    tags=["Analysis"],
)
async def analyze_ticket(
    ticket: TicketRequest,
    analyzer: TicketAnalyzer = Depends(get_analyzer),
) -> AnalyzeTicketResponse:
    complaint = ticket.complaint.strip()
    if not complaint:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Complaint cannot be empty")
    return await analyzer.analyze(ticket)
