import json
from pathlib import Path

import pytest

SAMPLES_PATH = Path(__file__).resolve().parent.parent / "SUST_Preli_Sample_Cases.json"

HARD_FIELDS = [
    "relevant_transaction_id",
    "evidence_verdict",
    "case_type",
    "department",
    "human_review_required",
]


@pytest.fixture
def sample_cases():
    with open(SAMPLES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", [f"SAMPLE-{i:02d}" for i in range(1, 11)])
async def test_public_sample_cases(client, sample_cases, case_id):
    case = next(c for c in sample_cases if c["id"] == case_id)
    response = await client.post("/analyze-ticket", json=case["input"])
    assert response.status_code == 200, response.text
    body = response.json()
    expected = case["expected_output"]

    for field in HARD_FIELDS:
        assert body[field] == expected[field], f"{case_id} {field}: got {body[field]!r}, expected {expected[field]!r}"

    assert "confidence" in body
    assert isinstance(body["confidence"], (int, float))
    assert 0 <= body["confidence"] <= 1
    assert "reason_codes" in body
    assert isinstance(body["reason_codes"], list)
    assert body["ticket_id"] == expected["ticket_id"]

    from app.pipeline.safety import is_safe_customer_reply
    assert is_safe_customer_reply(body["customer_reply"])
