import pytest
from fastapi.testclient import TestClient
from main import app
import os
import json

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def create_test_journal_files():
    journal_dir = "journal/TestDegradationStrategy"
    os.makedirs(journal_dir, exist_ok=True)

    # Create 5 journal entries, 3 wrong, 2 correct
    for i in range(3):
        with open(f"{journal_dir}/2025-07-26_120{i}00.json", "w") as f:
            json.dump({"feedback_rating": "wrong"}, f)
    for i in range(2):
        with open(f"{journal_dir}/2025-07-26_120{i+3}00.json", "w") as f:
            json.dump({"feedback_rating": "correct"}, f)

    yield

    # Clean up
    for i in range(5):
        os.remove(f"{journal_dir}/2025-07-26_120{i}00.json")
    os.rmdir(journal_dir)


def test_degradation_endpoint():
    response = client.get("/journal/summary/TestDegradationStrategy")
    assert response.status_code == 200
    data = response.json()
    assert data["degraded"] == True
    assert data["degradation_score"] == 0.6
    assert data["degradation_reason"] == "3 out of last 5 feedback ratings marked 'wrong'"
