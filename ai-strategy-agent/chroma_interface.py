import chromadb
from chromadb.utils import embedding_functions
import os
from datetime import datetime, timezone

class ChromaInterface:
    def __init__(self):
        # Using an in-memory implementation of ChromaDB
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("strategy_feedback_history")

        # Set up the embedding function
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key=api_key)
        else:
            # Fallback to a default embedding function if no API key is provided
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    def add_feedback_entry(self, strategy_id, feedback_payload, session_context, learning_score):
        document = self._format_document(feedback_payload)
        embedding = self.embedding_fn([document])[0]

        metadata = feedback_payload.copy()
        metadata.update({
            "strategy_id": strategy_id,
            "session_context": session_context,
            "learning_score": learning_score
        })

        self.collection.add(
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
            ids=[f"{strategy_id}_{feedback_payload['timestamp']}"]
        )

    def query_similar_feedback(self, strategy_id, input_query, top_k=5, session_context=None):
        query_embedding = self.embedding_fn([input_query])[0]

        where_clause = {"strategy_id": strategy_id}
        if session_context:
            where_clause["session_context"] = session_context

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )

        # Apply a simple time-based decay to the learning score
        for i, metadata in enumerate(results['metadatas'][0]):
            timestamp = datetime.fromisoformat(metadata['timestamp'].replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - timestamp).total_seconds()
            decay_factor = 0.99 ** (age / 3600) # Decay per hour
            results['metadatas'][0][i]['learning_score'] *= decay_factor

        return results

    def _format_document(self, payload):
        # Combine the payload into a single string for embedding
        parts = []
        for key, value in payload.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts)

chroma_interface = ChromaInterface()
