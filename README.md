# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot built with FastAPI, LangChain, ChromaDB, and Streamlit.

## Project Structure

```
rag-chatbot/
├── app/                    # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration and settings
│   ├── dependencies.py     # Dependency injection
│   ├── api/                # API route handlers
│   ├── core/               # Core RAG logic
│   ├── models/             # Pydantic data models
│   └── services/           # Business logic layer
├── data/
│   ├── raw/                # Raw uploaded documents
│   ├── processed/          # Processed document chunks
│   └── chroma_db/          # ChromaDB vector store
├── frontend/
│   └── streamlit_app.py    # Streamlit UI
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your API keys

## Running

**Backend:**
```bash
uvicorn app.main:app --reload
```

**Frontend:**
```bash
streamlit run frontend/streamlit_app.py
```

**Ingest documents:**
```bash
python scripts/ingest_documents.py
```
