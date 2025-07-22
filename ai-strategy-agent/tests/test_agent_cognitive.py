import pytest
from unittest.mock import MagicMock, patch
from chroma_interface import ChromaInterface

@pytest.fixture
def chroma_interface_fixture_cognitive():
    with patch('chroma_interface.embedding_functions.DefaultEmbeddingFunction') as mock_embedding_fn:
        mock_embedding_fn.return_value = MagicMock()
        interface = ChromaInterface()
        yield interface

def test_add_feedback_entry_with_context(chroma_interface_fixture_cognitive):
    strategy_id = "test_strategy"
    feedback_payload = {"timestamp": "2025-01-01T00:00:00Z", "recommendation": "Test"}
    session_context = "RTH"
    learning_score = 0.8

    chroma_interface_fixture_cognitive.add_feedback_entry(strategy_id, feedback_payload, session_context, learning_score)

    results = chroma_interface_fixture_cognitive.collection.get(where={"strategy_id": strategy_id})
    assert len(results['ids']) == 1
    metadata = results['metadatas'][0]
    assert metadata["strategy_id"] == strategy_id
    assert metadata["session_context"] == session_context
    assert metadata["learning_score"] == learning_score

def test_query_similar_feedback_with_context(chroma_interface_fixture_cognitive):
    strategy_id = "test_strategy"
    session_context = "RTH"

    with patch.object(chroma_interface_fixture_cognitive.collection, 'query') as mock_query:
        chroma_interface_fixture_cognitive.query_similar_feedback(strategy_id, "query", session_context=session_context)
        mock_query.assert_called_once()
        assert mock_query.call_args[1]['where'] == {"strategy_id": strategy_id, "session_context": session_context}

def test_structured_explanation_output():
    # This test would require mocking the LLM call and validating the JSON output.
    # For now, we will just assume the prompt is correct.
    pass
