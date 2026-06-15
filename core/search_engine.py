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
        """
        Regenerates processed_vault.json from the data folder, 
        then synchronizes those chunks into the ChromaDB vector collections.
        """
        import os
        import json
        from core.ingest import DataIngestionPipeline
        
        print("[INDEX] Initializing raw data folder scan...")
        pipeline = DataIngestionPipeline(chunk_size=500, chunk_overlap=50)
        pipeline.scan_and_ingest_data_vault()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vault_path = os.path.join(base_dir, "data", "processed_vault.json")
        
        if not os.path.exists(vault_path):
            print(f"[ERROR] Processed vault missing at: {vault_path}")
            return
            
        with open(vault_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            
        print(f"[INDEX] Synchronizing {len(chunks)} text chunks to ChromaDB...")
        
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            if not isinstance(meta, dict) or len(meta) == 0:
                fallback_source = chunk["chunk_id"].split("_chunk_")[0]
                meta = {"source": fallback_source}
            self.collection.upsert(
                ids=[chunk["chunk_id"]],
                documents=[chunk["text"]],
                metadatas=[meta] # <-- Uses our safe, non-empty dictionary
            )
            
        print("Vector Index Syncing Complete!")

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