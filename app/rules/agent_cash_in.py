from app.models.enums import CaseType, Department, Severity
from app.rules.base import CaseRule, NLUSignals


class AgentCashInRule(CaseRule):
    case_type = CaseType.AGENT_CASH_IN_ISSUE

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        if signals.mentions_cash_in:
            return 0.88
        return 0.0

    def default_department(self) -> Department:
        return Department.AGENT_OPERATIONS

    def default_severity(self) -> Severity:
        return Severity.HIGH
