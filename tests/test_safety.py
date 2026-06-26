from app.models.enums import Language
from app.pipeline.safety import is_safe_customer_reply, sanitize_text

UNSAFE_SAMPLES = [
    "Please share your OTP to verify your account.",
    "Kindly provide your PIN for security verification.",
    "Send me your password to proceed.",
    "We will refund you within 24 hours.",
    "Your account will be unblocked immediately after verification.",
    "Contact this number on WhatsApp: 01712345678",
    "Please share your OTP.",
    "Provide your PIN now.",
    "We will reverse the transaction and refund you.",
    "Share your CVV to confirm.",
    "Enter your card number for verification.",
    "We will refund the full amount today.",
    "Your refund will be processed immediately.",
    "Call him at this number for faster refund.",
    "Send your OTP to complete recovery.",
    "We will unblock your account now.",
    "Please give your password.",
    "Refund confirmed — money will return in 1 hour.",
    "Contact telegram support for refund.",
    "Verify by sharing OTP with our agent.",
]


def test_safety_sanitizer_blocks_unsafe_content():
    for sample in UNSAFE_SAMPLES:
        cleaned = sanitize_text(sample, Language.EN)
        assert is_safe_customer_reply(cleaned), f"Still unsafe: {cleaned}"
