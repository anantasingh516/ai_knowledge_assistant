import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
from core.search_engine import VectorSearchEngine
from fastapi import UploadFile, File, BackgroundTasks
import shutil
app = FastAPI(
    title="AI Knowledge Assistant API (Ollama Powered)",
    description="Grounded Generation Engine using Local Vector Indexing and Ollama"
)
search_engine = VectorSearchEngine()
class QueryRequest(BaseModel):
    question: str
    top_k: int = 2

class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list

@app.post("/ask", response_model=QueryResponse)
async def ask_knowledge_assistant(payload: QueryRequest):
    """
    RAG Query Flow Endpoint powered by Ollama
    """
    user_question = payload.question
    
    try:
        matched_chunks = search_engine.search(user_question, top_k=payload.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector index search failure: {str(e)}")
        
    if not matched_chunks:
        return QueryResponse(
            question=user_question,
            answer="I couldn't find any relevant documents in the knowledge base to answer this.",
            citations=[]
        )
    context_accumulator = ""
    citations_list = []
    for chunk in matched_chunks:
        doc_title = chunk["metadata"].get("title", "Unknown System Log")
        chunk_id = chunk["chunk_id"]
        
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
    return QueryResponse(
        question=user_question,
        answer=clean_answer,
        citations=citations_list
    )
@app.post("/upload")
def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Accepts a file stream synchronously, writes it to disk immediately, 
    and offloads the heavy vector embedding math to a background worker thread.
    """
    import os
    import shutil

    # Define absolute target data vault path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(base_dir, "data")
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, file.filename)
    
    try:
        # Write incoming file bytes to disk instantly
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"[FASTAPI] File saved to {file_path}. Handing off indexing to background thread...")
        
        # 🔥 SOLUTION: Delegate the heavy embedding calculations to a background thread worker
        background_tasks.add_task(search_engine.index_processed_vault)
        
        # Instantly reply to Streamlit so the UI never times out or freezes
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