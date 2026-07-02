import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Path where we store the compiled vector index
# __file__ is backend/app/services/rag_service.py. We go up 3 levels to get to backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# We go up 4 levels to get to the project root directory
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

INDEX_PATH = os.path.join(BACKEND_DIR, "knowledge_base_index.json")
KB_DIR = os.path.join(PROJECT_ROOT, "knowledge_base")

class RAGService:
    def __init__(self):
        self.openai_client = None
        self.chunks = []      # List of strings (text chunks)
        self.embeddings = []  # List of lists of floats (vectors)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and not api_key.startswith("your_openai"):
            self.openai_client = OpenAI(api_key=api_key)
            
        # Build or load the index on startup
        self.load_or_build_index()

    def get_embedding(self, text: str) -> list:
        """Fetch vector embedding for a piece of text using OpenAI."""
        if not self.openai_client:
            return []
        try:
            response = self.openai_client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[RAG] Error getting embedding from OpenAI: {e}")
            return []

    def load_or_build_index(self):
        """Loads index from file if it exists, otherwise compiles it from scratch."""
        if os.path.exists(INDEX_PATH):
            try:
                with open(INDEX_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self.embeddings = data.get("embeddings", [])
                print(f"[RAG] Loaded index from {INDEX_PATH} ({len(self.chunks)} chunks)")
                return
            except Exception as e:
                print(f"[RAG] Failed to load index, rebuilding... Error: {e}")

        self.rebuild_index()

    def rebuild_index(self):
        """Reads markdown files, splits them into logical chunks, and gets embeddings."""
        print("[RAG] Index file not found. Compiling knowledge base index...")
        self.chunks = []
        self.embeddings = []
        
        if not os.path.exists(KB_DIR):
            print(f"[RAG] Knowledge base directory {KB_DIR} not found. Creating empty one.")
            os.makedirs(KB_DIR, exist_ok=True)
            return

        # 1. Read files and split into chunks
        for filename in os.listdir(KB_DIR):
            if filename.endswith(".md") or filename.endswith(".txt"):
                filepath = os.path.join(KB_DIR, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Split files by double newlines (paragraphs/headers)
                raw_chunks = content.split("\n\n")
                for rc in raw_chunks:
                    rc_clean = rc.strip()
                    if rc_clean and not rc_clean.startswith("# "): # Skip bare main titles
                        self.chunks.append(f"Source file ({filename}):\n{rc_clean}")

        # 2. Get embeddings if OpenAI is configured
        if self.openai_client and self.chunks:
            print(f"[RAG] Fetching embeddings for {len(self.chunks)} chunks from OpenAI...")
            for chunk in self.chunks:
                vector = self.get_embedding(chunk)
                if vector:
                    self.embeddings.append(vector)
                else:
                    self.embeddings.append([]) # Fallback for errors
        else:
            print("[RAG] OpenAI API key not configured or no files found. Indexing chunks in text-only mode.")
            # Embeddings will be empty lists, we'll fall back to keyword matching

        # 3. Save to disk
        try:
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "chunks": self.chunks,
                    "embeddings": self.embeddings
                }, f, indent=2)
            print(f"[RAG] Successfully built and saved index to {INDEX_PATH}")
        except Exception as e:
            print(f"[RAG] Failed to save index: {e}")

    def search(self, query: str, top_k: int = 2) -> list:
        """
        Search the index.
        Uses OpenAI semantic search if key is active, otherwise falls back to a clean keyword-match.
        """
        if not self.chunks:
            return []

        # Case A: Real Semantic Search (OpenAI Embeddings)
        query_vector = self.get_embedding(query)
        if query_vector and self.embeddings and len(self.embeddings[0]) > 0:
            print(f"[RAG] Running semantic search for query: '{query}'")
            scored_chunks = []
            for chunk, vector in zip(self.chunks, self.embeddings):
                if not vector:
                    continue
                # Calculate cosine similarity (Dot Product since vectors are normalized)
                score = sum(q * v for q, v in zip(query_vector, vector))
                scored_chunks.append((score, chunk))
                
            # Sort by highest score
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            return [chunk for score, chunk in scored_chunks[:top_k]]

        # Case B: Mock Fallback - Keyword Search
        # Excellent for teaching search algorithms and running without an API key!
        print(f"[RAG] Running keyword fallback search for query: '{query}'")
        query_words = set(query.lower().replace("?", "").replace(",", "").split())
        scored_chunks = []
        
        for chunk in self.chunks:
            chunk_lower = chunk.lower()
            score = 0
            # Count word matches
            for word in query_words:
                if len(word) > 2: # Ignore small words like 'a', 'to', 'the'
                    if word in chunk_lower:
                        score += 1
            if score > 0:
                scored_chunks.append((score, chunk))
                
        # Sort by match score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [chunk for score, chunk in scored_chunks[:top_k]]
        
        # If no keyword matches, return the top 2 default FAQ snippets as fallback
        if not results:
            return self.chunks[:top_k]
            
        return results

# Initialize a global singleton service instance
rag_service = RAGService()
