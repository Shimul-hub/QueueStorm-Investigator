import pytest


@pytest.mark.asyncio
async def test_missing_ticket_id(client):
    response = await client.post("/analyze-ticket", json={"complaint": "help"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_empty_complaint(client):
    response = await client.post("/analyze-ticket", json={"ticket_id": "T1", "complaint": "   "})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_malformed_json(client):
    response = await client.post(
        "/analyze-ticket",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
