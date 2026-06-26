"""Detailed sample case validation against SUST_Preli_Sample_Cases.json."""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from httpx import ASGITransport, AsyncClient

from app.main import app

SAMPLES = ROOT / "SUST_Preli_Sample_Cases.json"
HARD_FIELDS = [
    "relevant_transaction_id",
    "evidence_verdict",
    "case_type",
    "department",
    "human_review_required",
]


async def main() -> int:
    with open(SAMPLES, encoding="utf-8") as f:
        cases = json.load(f)["cases"]

    transport = ASGITransport(app=app)
    failed = 0

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for case in cases:
            resp = await client.post("/analyze-ticket", json=case["input"])
            if resp.status_code != 200:
                print(f"FAIL {case['id']}: HTTP {resp.status_code}")
                failed += 1
                continue

            body = resp.json()
            expected = case["expected_output"]
            case_ok = True

            for field in HARD_FIELDS:
                if body.get(field) != expected.get(field):
                    print(
                        f"FAIL {case['id']} {field}: "
                        f"got {body.get(field)!r} expected {expected.get(field)!r}"
                    )
                    case_ok = False

            if body.get("ticket_id") != expected.get("ticket_id"):
                print(f"FAIL {case['id']} ticket_id mismatch")
                case_ok = False

            if "confidence" not in body or "reason_codes" not in body:
                print(f"FAIL {case['id']}: missing confidence or reason_codes")
                case_ok = False

            from app.pipeline.safety import is_safe_customer_reply

            if not is_safe_customer_reply(body.get("customer_reply", "")):
                print(f"FAIL {case['id']}: unsafe customer_reply")
                case_ok = False

            if case_ok:
                print(f"PASS {case['id']} — {case['label']}")
            else:
                failed += 1

    print(f"\n{'All passed!' if failed == 0 else f'{failed} case(s) failed.'}")
    return failed


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
