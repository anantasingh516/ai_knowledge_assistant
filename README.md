AI KNOWLEDGE ASSISTANT
An intelligent, modular system built to process internal documents, answer natural language questions about their contents, and provide precise references to where the answers were found.
Project Architecture & Components
This project is built using a decoupled, modular design to ensure scalability as features grow:
* **`core/`**: The brain of the assistant. Contains logic for document processing, semantic search, and AI prompt engineering.
* **`ui/`**: User interface components for interacting with the assistant.
* **`api/`**: API routes, controller logic, and backend request handlers (FastAPI/Flask).
* **`data/`**: Storage management, database helper scripts, and mockup datasets/vector indices.
