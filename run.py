import os
import time
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Header
from pydantic import BaseModel
import shutil
from ollama import Client
from core.search_engine import VectorSearchEngine
from core.compliance import ComplianceSanitizer  # 🔐 Import compliance sanitizer
from dotenv import load_dotenv

# Load security parameters straight from local root environment
load_dotenv()
EXPECTED_TOKEN = os.getenv("APP_SECRET_TOKEN", "fallback_default_token")
OLLAMA_HOST_ADDR = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

app = FastAPI(
    title="AI Knowledge Assistant API (Secured Node)",
    description="Grounded Generation Engine using Local Vector Indexing, Token Guardrails, and PII Compliance Filtering"
)

search_engine = VectorSearchEngine()
ollama_client = Client(host=OLLAMA_HOST_ADDR)
sanitizer = ComplianceSanitizer()

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "query_history.jsonl")

class QueryRequest(BaseModel):
    question: str
    top_k: int = 2
    temperature: float = 0.2

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list
    metrics: dict

def verify_access_token(token: str):
    """Internal validation guardrail checking API client identity headers."""
    if not token or token != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access request. Invalid or missing X-API-Token header.")

@app.post("/ask", response_model=QueryResponse)
async def ask_knowledge_assistant(payload: QueryRequest, x_api_token: str = Header(None)):
    """
    Secured RAG Query Endnode. Redacts PII patterns and enforces header security checks live.
    """
    # 1. Enforce access authorization check
    verify_access_token(x_api_token)
    
    start_time = time.time()
    
    # 2. Sanitize user queries right at entry barrier line
    raw_question = payload.question
    sanitized_question = sanitizer.sanitize_text(raw_question)
    
    try:
        matched_chunks = search_engine.search(sanitized_question, top_k=payload.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector index search failure: {str(e)}")
        
    if not matched_chunks:
        latency = time.time() - start_time
        return QueryResponse(
            question=sanitized_question,
            answer="I couldn't find any relevant documents in the knowledge base to answer this.",
            citations=[],
            metrics={"latency": round(latency, 3), "grounding_overlap": 0.0}
        )

    context_accumulator = ""
    citations_list = []
    retrieved_chunk_ids = []
    
    for chunk in matched_chunks:
        doc_title = chunk["metadata"].get("title", "Unknown System Log")
        chunk_id = chunk.get("chunk_id", "unknown_chunk")
        retrieved_chunk_ids.append(chunk_id)
        
        context_accumulator += f"\n[Document Reference: {doc_title}]\nContent: {chunk['text']}\n"
        
        citations_list.append({
            "id": chunk_id,
            "source": doc_title,
            "match_score": round(float(chunk["distance_score"]), 4),
            "text": chunk["text"]
        })

    system_instructions = (
        "You are an expert internal AI assistant. Your task is to accurately answer the user's question "
        "using ONLY the provided document context. Prioritize structural lists, numbered points, and sequential steps exactly as they are written in the text. "
        "If the answer truly cannot be found, state that you do not know. Never hallucinate facts."
    )
    
    user_prompt = (
        f"--- CONTEXT START ---\n{context_accumulator}\n--- CONTEXT END ---\n\n"
        f"Using the context above, provide a comprehensive, numbered list answering this exact question:\n"
        f"Question: {sanitized_question}"
    )
    
    try:
        response = ollama_client.chat(
            model="llama3.1", 
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": payload.temperature}
        )
        clean_answer = response["message"]["content"].strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama local generation error: {str(e)}")
    
    latency = time.time() - start_time
    timestamp = datetime.now().isoformat()
    
    context_words = set(context_accumulator.lower().split())
    response_words = set(clean_answer.lower().split())
    overlap_ratio = len(context_words.intersection(response_words)) / len(response_words) if response_words else 0.0

    # Sanitize logged inputs completely to maintain security standards on local storage disk
    log_entry = {
        "timestamp": timestamp,
        "query": sanitized_question,
        "response": clean_answer,
        "latency_seconds": round(latency, 3),
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "context_word_overlap_ratio": round(overlap_ratio, 3),
        "applied_top_k": payload.top_k,
        "applied_temperature": payload.temperature
    }
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log_out:
            log_out.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[METRIC LOGGING ERROR] Could not commit performance record to disk: {str(e)}")

    return QueryResponse(
        question=sanitized_question,
        answer=clean_answer,
        citations=citations_list,
        metrics={"latency": round(latency, 3), "grounding_overlap": round(overlap_ratio, 3)}
    )

@app.post("/upload")
def upload_document(file: UploadFile = File(...), x_api_token: str = Header(None), background_tasks: BackgroundTasks = BackgroundTasks()):
    # Enforce token validation check before processing upload
    verify_access_token(x_api_token)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "data")
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"[FASTAPI] File saved to {file_path}. Handing off indexing to background thread...")
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