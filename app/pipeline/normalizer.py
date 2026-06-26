import re
from dataclasses import dataclass

from app.models.enums import Language

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

BN_WORD_NUMBERS = {
    "এক": 1, "দুই": 2, "তিন": 3, "চার": 4, "পাঁচ": 5,
    "ছয়": 6, "সাত": 7, "আট": 8, "নয়": 9, "দশ": 10,
    "hajar": 1000, "hazar": 1000, "হাজার": 1000,
}


@dataclass
class NormalizedText:
    original: str
    normalized: str
    detected_language: Language


def normalize_bengali_numerals(text: str) -> str:
    return text.translate(BN_DIGITS)


def detect_language(text: str, hint: Language | None) -> Language:
    if hint is not None:
        return hint
    bengali_chars = len(re.findall(r"[\u0980-\u09FF]", text))
    latin_chars = len(re.findall(r"[A-Za-z]", text))
    total = bengali_chars + latin_chars
    if total == 0:
        return Language.EN
    if bengali_chars / total > 0.3 and latin_chars / total > 0.15:
        return Language.MIXED
    if bengali_chars / total > 0.3:
        return Language.BN
    return Language.EN


def normalize_complaint(text: str, language_hint: Language | None = None) -> NormalizedText:
    normalized = normalize_bengali_numerals(text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    detected = detect_language(text, language_hint)
    return NormalizedText(original=text, normalized=normalized, detected_language=detected)


def extract_word_amounts(text: str) -> list[float]:
    amounts: list[float] = []
    lower = text.lower()
    for word, val in BN_WORD_NUMBERS.items():
        if word in lower or word in text:
            if val >= 1000:
                match = re.search(rf"(\d+)\s*{re.escape(word)}", lower)
                if match:
                    amounts.append(float(match.group(1)) * val)
            else:
                amounts.append(float(val))
    return amounts
