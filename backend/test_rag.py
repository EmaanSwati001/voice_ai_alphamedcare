import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.rag_service import rag_service

def test_rag_retrieval():
    print("--- Starting Local RAG Service Test ---")
    
    # 1. Check if index was successfully initialized and chunks parsed
    assert len(rag_service.chunks) > 0, "No chunks found! Index build failed."
    print(f"Index successfully initialized. Found {len(rag_service.chunks)} chunks in the knowledge base.")
    
    # 2. Test CPT Code Lookup Query
    print("\nQuerying: 'What is CPT code 72148?'")
    results = rag_service.search("What is CPT code 72148?", top_k=1)
    assert len(results) > 0, "No search results returned!"
    print(f"Result Retrieved:\n{results[0]}")
    assert "72148" in results[0] and "lumbar spine" in results[0].lower(), "CPT 72148 search failed to retrieve lumbar spine MRI chunk!"
    print("  [SUCCESS] CPT 72148 query returned the correct information.")
    
    # 3. Test Policy / Denied Claims Appeal Query
    print("\nQuerying: 'How do I appeal a denied claim?'")
    results = rag_service.search("How do I appeal a denied claim?", top_k=1)
    assert len(results) > 0, "No search results returned!"
    print(f"Result Retrieved:\n{results[0]}")
    assert "appeal" in results[0].lower() or "denied" in results[0].lower(), "Appeal query failed to retrieve relevant FAQ!"
    print("  [SUCCESS] Appeal policy query returned the correct information.")

    print("\n--- All RAG Tests Passed Successfully! ---")

if __name__ == "__main__":
    test_rag_retrieval()
