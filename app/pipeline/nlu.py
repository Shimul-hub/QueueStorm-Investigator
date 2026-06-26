from app.pipeline.normalizer import extract_word_amounts, normalize_complaint
from app.rules.registry import score_intents, pick_case_type
from app.rules.base import NLUSignals


def extract_nlu(complaint: str, language_hint=None) -> tuple[NLUSignals, str]:
    norm = normalize_complaint(complaint, language_hint)
    signals = score_intents(norm.normalized)
    word_amounts = extract_word_amounts(norm.normalized)
    for amt in word_amounts:
        if amt not in signals.amounts:
            signals.amounts.append(amt)
    return signals, norm.normalized
