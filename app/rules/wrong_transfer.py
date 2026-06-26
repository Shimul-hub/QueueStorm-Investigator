from app.models.enums import CaseType, Department, Severity
from app.rules.base import CaseRule, NLUSignals


class WrongTransferRule(CaseRule):
    case_type = CaseType.WRONG_TRANSFER

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        if signals.mentions_wrong_transfer:
            return 0.9
        return 0.0

    def default_department(self) -> Department:
        return Department.DISPUTE_RESOLUTION

    def default_severity(self) -> Severity:
        return Severity.HIGH
