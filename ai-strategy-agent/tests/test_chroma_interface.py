import pytest
import os
from chroma_interface import ChromaInterface
from unittest.mock import MagicMock, patch

@pytest.fixture
def chroma_interface_fixture():
    # Mock the embedding function to avoid actual API calls
    with patch('chroma_interface.embedding_functions.DefaultEmbeddingFunction') as mock_embedding_fn:
        mock_embedding_fn.return_value = MagicMock()
        interface = ChromaInterface()
        yield interface

def test_add_feedback_entry(chroma_interface_fixture):
    strategy_id = "test_strategy"
    feedback_payload = {
        "strategy_id": strategy_id,
        "timestamp": "2025-01-01T00:00:00Z",
        "recommendation": "Test recommendation",
        "decision": "approved",
        "outcome": "+$100"
    }

    chroma_interface_fixture.add_feedback_entry(strategy_id, feedback_payload)

    # Query the collection to verify the entry was added
    results = chroma_interface_fixture.collection.get(where={"strategy_id": strategy_id})
    assert len(results['ids']) == 1
    assert results['metadatas'][0] == feedback_payload

def test_query_similar_feedback(chroma_interface_fixture):
    strategy_id = "test_strategy"
    feedback_payload1 = {"strategy_id": strategy_id, "timestamp": "2025-01-01T00:00:00Z", "recommendation": "recommendation 1"}
    feedback_payload2 = {"strategy_id": strategy_id, "timestamp": "2025-01-01T01:00:00Z", "recommendation": "recommendation 2"}

    chroma_interface_fixture.add_feedback_entry(strategy_id, feedback_payload1)
    chroma_interface_fixture.add_feedback_entry(strategy_id, feedback_payload2)

    # Mock the query to return a predictable result
    with patch.object(chroma_interface_fixture.collection, 'query', return_value={'documents': [['doc1']]}) as mock_query:
        results = chroma_interface_fixture.query_similar_feedback(strategy_id, "query")
        mock_query.assert_called_once()
        assert results is not None
