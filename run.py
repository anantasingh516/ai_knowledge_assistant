import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
from core.search_engine import VectorSearchEngine
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
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)