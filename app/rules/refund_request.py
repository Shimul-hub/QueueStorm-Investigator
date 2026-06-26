from app.models.enums import CaseType, Department, Severity
from app.rules.base import CaseRule, NLUSignals


class RefundRequestRule(CaseRule):
    case_type = CaseType.REFUND_REQUEST

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        if signals.mentions_refund and not signals.mentions_failed:
            return 0.85
        return 0.0

    def default_department(self) -> Department:
        return Department.CUSTOMER_SUPPORT

    def default_severity(self) -> Severity:
        return Severity.LOW
