import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.search_engine import VectorSearchEngine

def run_automated_evaluation(k=2):
    """
    Executes an automated validation suite against a ground-truth question set.
    Measures Recall@k and Citation Coverage based on the active vector store index.
    """
    print("====================================================")
    print(" 📊 Running RAG System Automated Evaluation Matrix ")
    print("====================================================\n")
    try:
        se = VectorSearchEngine()
    except Exception as e:
        print(f"[ERROR] Failed to initialize VectorSearchEngine: {str(e)}")
        return
    # 🎯 Match this exact structure inside core/evaluator.py
    EVAL_QUESTION_SET = [
        {
            "query": "What are the 7 stages of problem solving?",
            "expected_sources": ["unit 1 DAA.pdf"]  # Look strictly for the true file name metadata
        },
        {
            "query": "What is the company hybrid work policy and remote days?",
            "expected_sources": ["company_faqs"]
        },
        {
            "query": "What are the rules regarding code freeze windows for production?",
            "expected_sources": ["sops_best_practices"]
        }
    ]
    total_queries = len(EVAL_QUESTION_SET)
    sum_recall = 0.0
    sum_citation_coverage = 0.0
    detailed_results = []
    
    for item in EVAL_QUESTION_SET:
        query = item["query"]
        expected_targets = item["expected_sources"]
        
        print(f"🔍 Testing Query: '{query}'")
        
        try:
            matched_chunks = se.search(query, top_k=k)
        except Exception as e:
            print(f"  └── [ERROR] Search failed for query: {str(e)}")
            continue
            
        retrieved_sources = []
        valid_citations_count = 0
        
        for chunk in matched_chunks:
            title = chunk.get("metadata", {}).get("title", "").lower()
            source = chunk.get("metadata", {}).get("source", "").lower()
            chunk_id = chunk.get("chunk_id", "")
            
            retrieved_sources.append(f"{title} | {source} | {chunk_id}".lower())
            
            if chunk_id or title or source:
                valid_citations_count += 1
        hits = 0
        for expected in expected_targets:
            expected_lower = expected.lower()
            if any(expected_lower in src for src in retrieved_sources):
                hits += 1
                
        recall_score = hits / len(expected_targets) if expected_targets else 0.0
        sum_recall += recall_score
        sidebar_coverage = valid_citations_count / len(matched_chunks) if matched_chunks else 0.0
        sum_citation_coverage += sidebar_coverage
        
        print(f"  └── Result: Recall@{k} = {round(recall_score, 2)} | Citation Coverage = {round(sidebar_coverage, 2)}")
        print(f"  └── Retrieved IDs: {[c.get('chunk_id') for c in matched_chunks]}\n" + "-"*60)
        
        detailed_results.append({
            "query": query,
            "recall": round(recall_score, 3),
            "citation_coverage": round(sidebar_coverage, 3)
        })
        
    avg_recall = sum_recall / total_queries if total_queries else 0.0
    avg_citation = sum_citation_coverage / total_queries if total_queries else 0.0
    
    final_report = {
        "avg_recall_at_k": round(avg_recall, 3),
        "avg_citation_coverage": round(avg_citation, 3),
        "evaluated_at_k": k,
        "total_queries_tested": total_queries,
        "detailed_breakdown": detailed_results
    }
    
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    summary_file = os.path.join(logs_dir, "eval_metrics_summary.json")
    
    with open(summary_file, "w", encoding="utf-8") as out_f:
        json.dump(final_report, out_f, indent=4)
        
    print(f"\n✅ Benchmarking Complete! Metrics summary saved to: {summary_file}")
    return final_report

if __name__ == "__main__":
    run_automated_evaluation(k=2)