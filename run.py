import os
import time
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
import shutil
import ollama
from core.search_engine import VectorSearchEngine

app = FastAPI(
    title="AI Knowledge Assistant API (Ollama Powered)",
    description="Grounded Generation Engine using Local Vector Indexing and Ollama with Live Telemetry Logging"
)

search_engine = VectorSearchEngine()

# Ensure a dedicated logs directory exists
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "query_history.jsonl")

class QueryRequest(BaseModel):
    question: str
    top_k: int = 2

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list
    metrics: dict  # Added to return latency and grounding overlap to the frontend uploader dashboard

@app.post("/ask", response_model=QueryResponse)
async def ask_knowledge_assistant(payload: QueryRequest):
    """
    RAG Query Flow Endpoint powered by Ollama with precise telemetry tracking
    """
    start_time = time.time()  # Start telemetry timing clock
    user_question = payload.question
    
    try:
        # 1. Query the local Vector Engine
        matched_chunks = search_engine.search(user_question, top_k=payload.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector index search failure: {str(e)}")
        
    if not matched_chunks:
        latency = time.time() - start_time
        return QueryResponse(
            question=user_question,
            answer="I couldn't find any relevant documents in the knowledge base to answer this.",
            citations=[],
            metrics={"latency": round(latency, 3), "grounding_overlap": 0.0}
        )

    context_accumulator = ""
    citations_list = []
    retrieved_chunk_ids = []
    
    # 2. Structure context block and extract citation details
    for chunk in matched_chunks:
        doc_title = chunk["metadata"].get("title", "Unknown System Log")
        chunk_id = chunk.get("chunk_id", "unknown_chunk")
        retrieved_chunk_ids.append(chunk_id)
        
        context_accumulator += f"\n[Document Reference: {doc_title}]\nContent: {chunk['text']}\n"
        
        citations_list.append({
            "id": chunk_id,
            "source": doc_title,
            "match_score": round(float(chunk["distance_score"]), 4)
        })

    system_instructions = (
        "You are an expert internal AI assistant. Answer the user's question accurately using ONLY the provided document context. "
        "If the answer cannot be found or deduced from the context, state clearly that you do not know. Do not hallucinate."
    )
    
    user_prompt = f"--- CONTEXT START ---\n{context_accumulator}\n--- CONTEXT END ---\n\nQuestion: {user_question}"
    
    try:
        # 3. Generate response using local LLM
        response = ollama.chat(
            model="llama3.1", 
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": 0.2 
            }
        )
        clean_answer = response["message"]["content"].strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama local generation error: {str(e)}")
    
    # Calculate Latency Metrics
    latency = time.time() - start_time
    timestamp = datetime.now().isoformat()
    
    # Calculate Answer Grounding Overlap (Intersection over response unique vocabulary tokens)
    context_words = set(context_accumulator.lower().split())
    response_words = set(clean_answer.lower().split())
    
    # Basic protection against zero division if answer is completely empty
    if response_words:
        overlap_ratio = len(context_words.intersection(response_words)) / len(response_words)
    else:
        overlap_ratio = 0.0

    # 4. Pack telemetry metrics entry array
    log_entry = {
        "timestamp": timestamp,
        "query": user_question,
        "response": clean_answer,
        "latency_seconds": round(latency, 3),
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "context_word_overlap_ratio": round(overlap_ratio, 3)
    }
    
    # 5. Commit structure directly to disk in JSON Lines format (.jsonl)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log_out:
            log_out.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[METRIC LOGGING ERROR] Could not commit performance record to disk: {str(e)}")

    return QueryResponse(
        question=user_question,
        answer=clean_answer,
        citations=citations_list,
        metrics={"latency": round(latency, 3), "grounding_overlap": round(overlap_ratio, 3)}
    )

@app.post("/upload")
def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Accepts a file stream synchronously, writes it to disk immediately, 
    and offloads the heavy vector embedding math to a background worker thread.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "data")
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, file.filename)
    
    try:
        # Write incoming file bytes to disk instantly
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"[FASTAPI] File saved to {file_path}. Handing off indexing to background thread...")
        
        # Delegate heavy computational matrix work over to background thread pools
        background_tasks.add_task(search_engine.index_processed_vault)
        
        return {
            "status": "success", 
            "message": f"'{file.filename}' received safely! The embedding engine is indexing it in the background."
        }
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload initialization failure: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)