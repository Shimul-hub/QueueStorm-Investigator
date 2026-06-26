from app.models.enums import CaseType, Department, Severity
from app.rules.base import CaseRule, NLUSignals


class PhishingRule(CaseRule):
    case_type = CaseType.PHISHING_OR_SOCIAL_ENGINEERING

    def match_signals(self, text: str, signals: NLUSignals) -> float:
        lower = text.lower()
        asking_for_creds = any(
            p in lower
            for p in ["asked for my otp", "asked for otp", "asked for pin", "share otp", "share pin"]
        )
        reporting_scam = any(
            p in lower
            for p in ["is this real", "someone called", "claiming to be", "scam", "phishing", "fake call"]
        )
        if signals.mentions_phishing or asking_for_creds or reporting_scam:
            return 0.95
        return 0.0

    def default_department(self) -> Department:
        return Department.FRAUD_RISK

    def default_severity(self) -> Severity:
        return Severity.CRITICAL
