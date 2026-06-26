import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "complaint,expected_case",
    [
        ("amar balance kata gese kintu payment failed dekhay 1200 taka", "payment_failed"),
        ("vul number e 2000 pathaisilam please help", "wrong_transfer"),
        ("duibar cut hoise 850 taka electricity bill", "duplicate_payment"),
    ],
)
async def test_banglish_cases(client, complaint, expected_case):
    history = []
    if expected_case == "payment_failed":
        history = [
            {
                "transaction_id": "TXN-BN1",
                "timestamp": "2026-04-14T10:00:00Z",
                "type": "payment",
                "amount": 1200,
                "counterparty": "MERCH",
                "status": "failed",
            }
        ]
    elif expected_case == "wrong_transfer":
        history = [
            {
                "transaction_id": "TXN-BN2",
                "timestamp": "2026-04-14T10:00:00Z",
                "type": "transfer",
                "amount": 2000,
                "counterparty": "+8801711111111",
                "status": "completed",
            }
        ]
    elif expected_case == "duplicate_payment":
        history = [
            {
                "transaction_id": "TXN-BN3A",
                "timestamp": "2026-04-14T08:15:30Z",
                "type": "payment",
                "amount": 850,
                "counterparty": "BILLER",
                "status": "completed",
            },
            {
                "transaction_id": "TXN-BN3B",
                "timestamp": "2026-04-14T08:15:42Z",
                "type": "payment",
                "amount": 850,
                "counterparty": "BILLER",
                "status": "completed",
            },
        ]

    response = await client.post(
        "/analyze-ticket",
        json={"ticket_id": "TKT-BN", "complaint": complaint, "transaction_history": history},
    )
    assert response.status_code == 200
    assert response.json()["case_type"] == expected_case
