from app.models.enums import CaseType, Department, Severity
from app.rules.base import CaseRule, NLUSignals


class MerchantSettlementRule(CaseRule):
    case_type = CaseType.MERCHANT_SETTLEMENT_DELAY

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        if signals.mentions_settlement:
            return 0.9
        return 0.0

    def default_department(self) -> Department:
        return Department.MERCHANT_OPERATIONS

    def default_severity(self) -> Severity:
        return Severity.MEDIUM
