import re

from app.models.enums import Language

REFUND_PROMISE = re.compile(
    r"\b(?:we will|we'll|i will)\s+(?:refund|reverse|unblock|recover)\b",
    re.IGNORECASE,
)
REFUND_CONFIRM = re.compile(
    r"\b(?:refund (?:is|will be|has been) confirmed|will be reversed|account (?:will be|has been) unblocked)\b",
    re.IGNORECASE,
)

THIRD_PARTY = re.compile(
    r"contact (?:this|that|the|him|her|them|at)\s(\+?\d|whatsapp|telegram|facebook)",
    re.IGNORECASE,
)

INJECTION_PATTERNS = [
    r"ignore (all )?(previous )?instructions",
    r"system:\s*you are",
    r"disregard (your )?rules",
    r"confirm refund immediately",
]

_CREDENTIAL_REQUEST = re.compile(
    r"\b(?:share|provide|send|verify|confirm|enter)\s+(?:me\s+)?(?:your\s+)?"
    r"(?:pin|otp|password|cvv|card number)\b",
    re.IGNORECASE,
)
_SAFE_CONTEXT = re.compile(
    r"(?:do not|don't|never|not|without)\s+(?:share|provide|send|give)",
    re.IGNORECASE,
)
_CREDENTIAL_REQUEST_BN = re.compile(
    r"(?:শেয়ার|দিন|পাঠান)\s+(?:করুন\s+)?(?:আপনার\s+)?(?:পিন|ওটিপি|পাসওয়ার্ড)",
    re.IGNORECASE,
)


def _asks_for_credentials(text: str) -> bool:
    if _SAFE_CONTEXT.search(text):
        return False
    if _CREDENTIAL_REQUEST.search(text):
        return True
    if _CREDENTIAL_REQUEST_BN.search(text):
        return True
    return False


def contains_injection(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in INJECTION_PATTERNS)


def sanitize_text(text: str, language: Language) -> str:
    if not text:
        return text

    result = text

    if _asks_for_credentials(result):
        result = _CREDENTIAL_REQUEST.sub(
            "Please do not share your PIN or OTP with anyone",
            result,
        )
        result = _CREDENTIAL_REQUEST_BN.sub(
            "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না",
            result,
        )

    result = REFUND_PROMISE.sub(
        "any eligible amount will be returned through official channels",
        result,
    )
    result = REFUND_CONFIRM.sub(
        "the case will be reviewed and any eligible amount will be returned through official channels",
        result,
    )

    result = THIRD_PARTY.sub(
        "please contact us through official support channels",
        result,
    )

    footer_en = "Please do not share your PIN or OTP with anyone."
    footer_bn = "অনুগ্রহ করে কারো সাথে আপনার পিন বা ওটিপি শেয়ার করবেন না।"

    if language == Language.BN:
        if footer_bn not in result:
            result = result.rstrip() + " " + footer_bn
    elif language == Language.MIXED:
        if footer_bn not in result and footer_en.lower() not in result.lower():
            result = result.rstrip() + " " + footer_bn
    else:
        if footer_en.lower() not in result.lower():
            result = result.rstrip() + " " + footer_en

    return re.sub(r"\s+", " ", result).strip()


def is_safe_customer_reply(text: str) -> bool:
    if _asks_for_credentials(text):
        return False
    lower = text.lower()
    if re.search(r"\bwe will refund\b", lower):
        return False
    if re.search(r"\bwill be reversed\b", lower) and "eligible" not in lower:
        return False
    return True
