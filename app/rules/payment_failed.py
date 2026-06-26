from app.models.enums import CaseType, Department, Severity
from app.rules.base import CaseRule, NLUSignals


class PaymentFailedRule(CaseRule):
    case_type = CaseType.PAYMENT_FAILED

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        if signals.mentions_failed:
            return 0.9
        return 0.0

    def default_department(self) -> Department:
        return Department.PAYMENTS_OPS

    def default_severity(self) -> Severity:
        return Severity.HIGH
