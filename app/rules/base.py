from dataclasses import dataclass, field

from app.models.enums import CaseType, Department, Severity


@dataclass
class NLUSignals:
    amounts: list[float] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    intents: list[CaseType] = field(default_factory=list)
    mentions_refund: bool = False
    mentions_otp_pin: bool = False
    mentions_duplicate: bool = False
    mentions_failed: bool = False
    mentions_wrong_transfer: bool = False
    mentions_settlement: bool = False
    mentions_cash_in: bool = False
    mentions_phishing: bool = False
    is_vague: bool = False
    nlu_confidence: float = 0.5


class CaseRule:
    case_type: CaseType

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        raise NotImplementedError

    def default_department(self) -> Department:
        raise NotImplementedError

    def default_severity(self) -> Severity:
        return Severity.MEDIUM

    def reason_codes(self) -> list[str]:
        return [self.case_type.value]
