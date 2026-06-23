# Local enterprise-grade RAG Knowledge Assistant 🤖🛡️

An advanced, locally hosted Retrieval-Augmented Generation (RAG) assistant designed to ingest, process, parse, index, and safely analyze internal academic materials and compliance documents. Built with a production-first mindset, this application delivers **100% data privacy** using local vector indexing and open-source models powered by an on-premise **Ollama node**.

---

## 🏗️ System Topography & Data Architecture

The structural flow charts show how streaming information circles through access layers, token isolation networks, and context boundary walls before rendering:

```text
       [ USER PORTAL ]
      Streamlit Frontend
              │
    (Encrypted Handshake) ──► Passes X-API-Token Header Validation
              │
              ▼
      [ SECURED NODE ]
       FastAPI Backend
              │
              ├──► [ COMPLIANCE REGEX ENGINE ] ──► Scrubs PII (Emails, Phone numbers, IDs)
              │
              ├──► [ RETRIEVAL LAYER ] ──► Queries ChromaDB (Dynamic Top-K Sliders)
              │
              ▼
    [ GROUNDED INFERENCE ]
    Ollama (Llama3.1 Node) ◄── (Low-Temp Context Guardrails Prevent Hallucinations)