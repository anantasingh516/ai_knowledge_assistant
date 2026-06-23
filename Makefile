# ⚙️ AI Knowledge Assistant Automation Workflow Engine
.PHONY: help install reindex run eval clean

help:
	@echo "======================================================================"
	@echo " 🤖 Local RAG Assistant Command Interface Workflow"
	@echo "======================================================================"
	@echo "  make install   - Installs all local virtual environment dependencies"
	@echo "  make reindex   - Triggers the search engine vector database compiler"
	@echo "  make run       - Bootstraps FastAPI backend and Streamlit UI simultaneously"
	@echo "  make eval      - Programmatically runs the automated metric suite"
	@echo "  make clean     - Flushes cached logs and temp Python artifacts safely"
	@echo "======================================================================"

install:
	pip install -r requirements.txt

reindex:
	python -c "from core.search_engine import VectorSearchEngine; VectorSearchEngine().index_processed_vault()"

run:
	@echo "🚀 Initializing Multi-Tier Production Stack..."
	@echo "🤖 Booting FastAPI secured node on Port 8000 in background..."
	start /b python run.py
	@echo "🎨 Launching Streamlit Portal Interface..."
	streamlit run app.py

eval:
	python core/evaluator.py

clean:
	@echo "🧼 Purging transient workspace cache streams..."
	if exist logs\eval_metrics_summary.json del /q logs\eval_metrics_summary.json
	if exist logs\query_history.jsonl del /q logs\query_history.jsonl
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"