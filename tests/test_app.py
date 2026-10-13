from fastapi.testclient import TestClient

from trusttrace.app import app


def test_local_mock_ui_and_abstention():
    client = TestClient(app)
    assert client.get("/health").json()["mode"] == "synthetic-mock"
    assert "No authentication" in client.get("/").text
    answer = client.post("/ask", json={"text": "shipment packages"})
    assert answer.status_code == 200
    assert answer.json()["review_item"]["status"] == "pending"
    assert client.post("/ask", json={"text": "no-retrievable-evidence"}).status_code == 422
    assert client.post("/ask", json={"text": ""}).status_code == 422
