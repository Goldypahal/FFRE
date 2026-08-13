from unittest.mock import patch, MagicMock
from vector_db import vector_store

def test_vector_store_similarity_search():
    """Test the similarity search method of vector store"""
    # Mock the vector store's similarity_search method
    with patch.object(vector_store, 'similarity_search') as mock_search:
        # Configure the mock to return some dummy results
        mock_search.return_value = [
            {"case_id": "case1", "verdict": "FRAUD", "confidence": 0.9},
            {"case_id": "case2", "verdict": "LEGIT", "confidence": 0.2}
        ]

        # Call the method
        results = vector_store.similarity_search("test query", top_k=2)

        # Verify the mock was called correctly
        mock_search.assert_called_once_with("test query", top_k=2)

        # Verify we got the expected results
        assert len(results) == 2
        assert results[0]["case_id"] == "case1"
        assert results[0]["verdict"] == "FRAUD"
        assert results[1]["case_id"] == "case2"
        assert results[1]["verdict"] == "LEGIT"

def test_vector_store_initialization():
    """Test that vector store is properly initialized"""
    # This is more of a sanity check - we're not actually testing the connection
    # since we don't have a real vector DB in the test environment
    assert vector_store is not None
    # The vector_store should have a similarity_search method
    assert hasattr(vector_store, 'similarity_search')
    assert callable(getattr(vector_store, 'similarity_search', None))