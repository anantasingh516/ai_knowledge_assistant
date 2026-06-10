import os
import json
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
VAULT_PATH = os.path.join(DATA_DIR, "processed_vault.json")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
class VectorSearchEngine:
    def __init__(self):
        print("[INIT] Loading Sentence-Transformer embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[INIT] Initializing persistent local ChromaDB...")
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.chroma_client.get_or_create_collection(name="knowledge_vault")
    def index_processed_vault(self):
        """Loads chunks from processed_vault.json, embeds them, and stores them in Chroma."""
        if not os.path.exists(VAULT_PATH):
            print(f"[ERROR] Could not find {VAULT_PATH}. Please run core/ingest.py first!")
            return
        with open(VAULT_PATH, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        if not chunks:
            print("[WARN] Your processed_vault.json is empty. Nothing to index.")
            return

        print(f"\n[INDEX] Preparing to vectorize {len(chunks)} text chunks...")
        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            documents.append(chunk["text"])
            ids.append(chunk["chunk_id"])
            meta = chunk["metadata"].copy()
            if "tags" in meta and isinstance(meta["tags"], list):
                meta["tags"] = ", ".join(meta["tags"])
            metadatas.append(meta)

        print("[INDEX] Generating embeddings (converting text to mathematical vectors)...")
        embeddings = self.model.encode(documents).tolist()

        print("[INDEX] Saving vectors and tracking metadata inside ChromaDB...")
        self.collection.upsert(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Vector Indexing Complete! Stored securely in: data/chroma_db/")

    def search(self, query_text, top_k=2):
        """Converts user query to a vector and retrieves the top-k most semantically similar chunks."""
        print(f"\n [SEARCH QUERY] '{query_text}'")
        query_embedding = self.model.encode([query_text]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        retrieved_chunks = []
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            distances = results['distances'][0]
            ids = results['ids'][0]
            
            for i in range(len(docs)):
                chunk_data = {
                    "chunk_id": ids[i],
                    "text": docs[i],
                    "metadata": metas[i],
                    "distance_score": distances[i] 
                }
                retrieved_chunks.append(chunk_data)
                
        return retrieved_chunks

if __name__ == "__main__":
    engine = VectorSearchEngine()
    engine.index_processed_vault()
    test_query = "Tell me about the code freeze rules for production releases."
    results = engine.search(test_query, top_k=1)
    
    print("\n--- Top Retrieved Search Result ---")
    for res in results:
        print(f"ID: {res['chunk_id']}")
        print(f"Source Document: {res['metadata'].get('title', 'Unknown')}")
        print(f"Closeness Score: {res['distance_score']:.4f}")
        print(f"Extracted Content: {res['text']}")