import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.search_engine import SearchEngine
se = SearchEngine()
EVAL_QUESTION_SET = [
    {
        "query": "What are the 7 stages of problem solving?",
        "expected_chunks": ["unit_1_daa_chunk_0"]  
    },
    {
        "query": "What is the company hybrid work policy and remote days?",
        "expected_chunks": ["company_faqs_chunk_0"]
    },
    {
        "query": "What are the rules regarding code freeze windows for production?",
        "expected_chunks": ["sops_best_practices_chunk_0"]
    }
]

def run_automated_evaluation(k=3):
    print("🤖 Starting Local RAG Automated Matrix Evaluation Benchmark...\n")
    results_summary = []
    
    total_recall = 0.0
    total_citation_coverage = 0.0
    
    for item in EVAL_QUESTION_SET:
        query = item["query"]
        expected_targets = item["expected_chunks"]
        retrieval_res = se.query(query, top_k=k)
        retrieved_ids = retrieval_res.get("ids", [])
        hits = 0
        for expected in expected_targets:
            if any(expected in rid for rid in retrieved_ids):
                hits += 1
        recall_score = hits / len(expected_targets) if expected_targets else 0
        total_recall += recall_score
        valid_citations = sum(1 for rid in retrieved_ids if "_" in rid)
        citation_score = valid_citations / len(retrieved_ids) if retrieved_ids else 0
        total_citation_coverage += citation_score
        
        results_summary.append({
            "query": query,
            "recall_score": recall_score,
            "citation_coverage": citation_score,
            "retrieved_ids": retrieved_ids
        })
        
    num_queries = len(EVAL_QUESTION_SET)
    final_metrics = {
        "avg_recall_at_k": round(total_recall / num_queries, 2),
        "avg_citation_coverage": round(total_citation_coverage / num_queries, 2),
        "evaluated_at_k": k
    }
    os.makedirs("logs", exist_ok=True)
    with open("logs/eval_metrics_summary.json", "w", encoding="utf-8") as out:
        import json
        json.dump(final_metrics, out, indent=4)
        
    print("System Benchmarking Complete! Metrics exported to logs/eval_metrics_summary.json")
    return final_metrics

if __name__ == "__main__":
    run_automated_evaluation()