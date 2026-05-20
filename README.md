# RAG Chatbot

A production-ready conversational AI application that lets users upload their own documents and have intelligent, context-aware conversations about them. Built on the Retrieval-Augmented Generation (RAG) pattern, it combines Google Gemini for both embeddings and generation with a persistent cloud vector database to deliver accurate, grounded answers — without hallucination.


---

## ✨ Features

### 1. **User Authentication & Isolation**
Secure, stateless identity management:
- **Registration & Login**: Users register with a username and password. Passwords are hashed with bcrypt (with a unique random salt per user) and never stored in plain text.
- **JWT Tokens**: After login, the server issues a signed JSON Web Token containing the user ID and expiry time. The client sends this token with every request; the server verifies the signature without a database lookup — keeping authentication stateless and fast.
- **Complete Data Isolation**: Each user's documents and vectors are stored in a separate Qdrant collection. A query from one user can never return another user's document chunks.

---

### 2. **Document Ingestion Pipeline**
Robust file processing from upload to vector store:
- **Supported Formats**: PDF (parsed page by page), plain text (`.txt`), and Markdown (`.md`).
- **Intelligent Text Splitting**: A recursive splitter that respects natural boundaries — paragraph breaks → line breaks → sentence endings → character-level as a last resort. This produces semantically cleaner chunks compared to naive fixed-size splitting.
- **Duplicate Detection**: Before ingesting any file, the system computes a SHA-256 hash of the file contents and checks it against the user's existing document records in Supabase. If the file was already uploaded, the ingestion is skipped entirely — no redundant embeddings, no duplicate chunks in the vector store.
- **Batched Embedding**: The Gemini embedding model supports up to 100 texts per API call. All chunks from a document are batched together in a single call, making ingestion significantly faster than one-chunk-at-a-time approaches.
- **Path Traversal Protection**: File names submitted by users are sanitized before any disk operations. Malicious filenames like `../../etc/passwd` cannot escape the intended upload directory.

---

### 3. **Retrieval & Generation (RAG Pipeline)**
The core AI flow that drives every answer:
- **Vector Search**: At query time, the user's question is converted to a 3072-dimensional vector using `gemini-embedding-001`. The system searches the user's Qdrant collection for the chunks with the highest cosine similarity to the question vector.
- **Context Assembly**: The top matching chunks are assembled into a structured prompt alongside the user's question and the last 10 messages of conversation history.
- **Hybrid Answering**: The system prompt instructs Gemini to use the retrieved document chunks as its primary reference but to supplement with its own training knowledge when needed. The model behaves like a tutor who has read your materials and can also teach beyond them — it will not refuse to explain a concept simply because the exact wording is not in the uploaded document.
- **Generation Model**: `gemini-2.5-flash` handles all response generation.

**Use case**: Upload your university syllabus or a research paper and ask detailed questions about it. The model will cite your document and also explain underlying concepts in full.

---

### 4. **Persistent Chat Memory**
Conversations that survive page refreshes and re-logins:
- Every user message and assistant reply is saved to Supabase PostgreSQL immediately after it is produced.
- When a user logs in, their full conversation history is loaded and displayed in the Streamlit chat interface.
- The last 10 messages are included in every new prompt, giving Gemini context of the ongoing session so it can answer follow-up questions coherently without the user repeating themselves.

---

### 5. **Frontend (Streamlit)**
A clean, interactive chat UI built entirely in Python:
- **Login & Registration screens** with form validation.
- **Document management sidebar**: upload files, view uploaded documents, delete documents.
- **Chat interface**: message history display, input box, streaming-style responses.
- No HTML, CSS, or JavaScript required — the entire frontend is Python.

---

### 6. **Testing Suite**
Five independent CLI test scripts, each verifiable without running the full app:

| Script | What it tests | Requires API? |
|--------|--------------|--------------|
| Chunking test | Document loading and text splitting logic | No |
| Retrieval test | Full embedding + Qdrant vector store pipeline | Yes |
| Pipeline test | End-to-end RAG flow with real questions | Yes |
| Database test | All Supabase operations (CRUD) | Yes |
| Auth test | bcrypt hashing, JWT tokens, register/login endpoints | Yes |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (see `.python-version`)
- A Google Gemini API key
- A Qdrant Cloud cluster (free tier sufficient)
- A Supabase project with three tables: `users`, `documents`, `chat_history`

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Kayab10/rag.git
   cd rag
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Fill in your API keys and URLs in .env
   ```

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key |
| `JWT_SECRET` | Secret string for signing JWT tokens |
| `API_BASE` | Backend URL (set to `http://localhost:8000` locally) |

### Running Locally

Start the FastAPI backend:
```bash
uvicorn app.main:app --reload
```

In a separate terminal, start the Streamlit frontend:
```bash
streamlit run frontend/streamlit_app.py
```

- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:8501`
- **Interactive API docs**: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
rag/
├── app/
│   ├── main.py                  # FastAPI app entry point, route registration
│   ├── api/                     # Route handlers (thin layer — validate, call service, return)
│   │   ├── auth.py              # /register, /login endpoints
│   │   ├── documents.py         # /upload, /list, /delete endpoints
│   │   └── chat.py              # /chat endpoint
│   ├── core/                    # Pure RAG logic (no HTTP, no auth, no DB)
│   │   ├── loader.py            # Document loading (PDF, TXT, MD)
│   │   ├── splitter.py          # Recursive text chunking
│   │   ├── embedder.py          # Gemini embedding, batched
│   │   ├── vectorstore.py       # Qdrant collection management, upsert, search
│   │   ├── retriever.py         # Query embedding + similarity search
│   │   ├── prompt.py            # Prompt assembly (context + history + question)
│   │   └── pipeline.py          # Orchestration: retriever → prompt → Gemini
│   ├── auth/
│   │   ├── hashing.py           # bcrypt password hash/verify
│   │   ├── jwt.py               # JWT creation and verification
│   │   └── dependencies.py      # FastAPI dependency: extract current user from header
│   ├── db/
│   │   ├── users.py             # Create user, fetch user by username
│   │   ├── documents.py         # Save document record, check hash, list, delete
│   │   └── chat.py              # Save message, load history
│   ├── services/
│   │   ├── ingest.py            # Dedup check → load → split → embed → store
│   │   └── chat.py              # Load history → run pipeline → save messages
│   └── models/
│       ├── user.py              # RegisterRequest, LoginResponse Pydantic models
│       ├── document.py          # UploadResponse, DocumentRecord models
│       └── chat.py              # ChatRequest, ChatResponse models
├── frontend/
│   └── streamlit_app.py         # Complete Streamlit UI (login, upload, chat)
├── tests/
│   ├── test_chunking.py         # Chunking unit tests (no API)
│   ├── test_retrieval.py        # Embedding + vector store integration tests
│   ├── test_pipeline.py         # End-to-end RAG pipeline tests
│   ├── test_db.py               # Supabase CRUD tests
│   └── test_auth.py             # Auth flow tests (hash, JWT, endpoints)
├── .streamlit/
│   └── secrets.toml             # Streamlit Cloud secrets config
├── .env.example                 # Environment variable template
├── .python-version              # Python version pin (3.11)
├── render.yaml                  # Render deployment config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

### File Descriptions

| File / Directory | Purpose |
|-----------------|---------|
| `app/core/` | Self-contained RAG logic. No knowledge of users, HTTP, or databases. Can be tested in isolation. |
| `app/auth/` | Password hashing, JWT creation/verification, and the FastAPI dependency that extracts the current user from a request. |
| `app/db/` | All Supabase operations: users table, documents table, chat_history table. |
| `app/services/` | Business logic layer sitting between routes and core/db. Handles dedup, history loading, and message saving. |
| `app/api/` | Thin FastAPI route handlers. Validate request → call service → return response. No business logic here. |
| `app/models/` | Pydantic models for request/response validation and automatic API documentation. |
| `frontend/streamlit_app.py` | The complete Streamlit UI in a single file: auth screens, sidebar document manager, chat interface. |
| `render.yaml` | Declarative Render deployment config — tells Render the build command, start command, and runtime. |
| `.python-version` | Pins the Python version for reproducibility across local and deployed environments. |

---




### Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Backend API** | FastAPI 0.111 | Async support, automatic docs, Pydantic integration |
| **Frontend** | Streamlit 1.35 | Full interactive UI in pure Python, no frontend stack needed |
| **Embeddings** | `gemini-embedding-001` | 3072-dim vectors, batched up to 100 texts per call |
| **Generation** | `gemini-2.5-flash` | Fast, capable, same provider as embeddings |
| **Vector DB** | Qdrant Cloud 1.18 | Managed cloud, cosine similarity, per-user collections |
| **Relational DB** | Supabase (PostgreSQL) | Managed cloud, stores users, docs, chat history |
| **Password Hashing** | bcrypt 4.1 | Industry standard, salted, deliberately slow against brute force |
| **Authentication** | PyJWT 2.8 | Stateless signed tokens, no server-side session storage |
| **PDF Parsing** | pypdf 4.2 | Page-by-page text extraction |
| **ASGI Server** | uvicorn 0.29 | High-performance async server for FastAPI |
| **Deployment** | Render + Streamlit Cloud | Backend and frontend deployed independently |

### Security Design

| Concern | Implementation |
|---------|---------------|
| Password storage | bcrypt hash with unique salt per user; plain text never stored |
| Session management | Stateless JWT with expiry; no server-side session table |
| Data isolation | Separate Qdrant collection per user; queries cannot cross user boundaries |
| File path safety | User-supplied filenames sanitized before disk operations; path traversal blocked |
| Secret management | All keys in `.env` locally; Render dashboard / Streamlit secrets in production |

---

## 🔌 API Reference

### Authentication

#### `POST /register`
Register a new user.
```json
Request:  { "username": "string", "password": "string" }
Response: { "message": "User registered successfully" }
```

#### `POST /login`
Login and receive a JWT token.
```json
Request:  { "username": "string", "password": "string" }
Response: { "access_token": "string", "token_type": "bearer" }
```

---

### Documents

#### `POST /documents/upload`
Upload and ingest a document. Requires `Authorization: Bearer <token>` header.
```
Request:  multipart/form-data with file field
Response: { "filename": "string", "chunks": int, "status": "ingested" | "duplicate" }
```

#### `GET /documents/`
List all documents uploaded by the authenticated user.
```json
Response: [ { "filename": "string", "uploaded_at": "datetime", "chunk_count": int } ]
```

#### `DELETE /documents/{filename}`
Delete a document and remove its vectors from Qdrant.
```json
Response: { "message": "Document deleted" }
```

---

### Chat

#### `POST /chat`
Send a message and receive a RAG-powered answer.
```json
Request:  { "message": "string" }
Response: { "answer": "string", "sources": [ "chunk text snippets" ] }
```

---


## 🌐 Deployment

### Backend (Render)
The `render.yaml` at the project root provides a declarative deployment config. After connecting the GitHub repository to Render:
1. Render reads `render.yaml` and knows the build command, start command, and runtime.
2. Add all secret environment variables through the Render dashboard (never commit these to the repo).
3. Render deploys on every push to `main`.

All data lives in Qdrant Cloud and Supabase — fully external to Render. The backend can restart, redeploy, or scale without any data loss.

### Frontend (Streamlit Cloud)
1. Connect the GitHub repository to Streamlit Cloud.
2. Set `APP_API_BASE` as a secret pointing to the live Render backend URL.
3. Streamlit Cloud reads this secret at runtime and the frontend connects to production automatically.

### Ephemeral Filesystem Warning
Render's local filesystem resets on every deploy. The choice of Qdrant Cloud and Supabase (rather than local ChromaDB or SQLite) was deliberate — all state persists in cloud services, making the backend fully stateless and safely restartable.




---

### Key Technologies:
- **FastAPI**: Async Python web framework with automatic OpenAPI documentation
- **Streamlit**: Interactive Python-native frontend framework
- **Google Gemini**: Unified provider for both vector embeddings and text generation
- **Qdrant**: Cloud-native vector database with cosine similarity search
- **Supabase**: Managed PostgreSQL for users, documents, and chat history
- **bcrypt + JWT**: Industry-standard authentication primitives

---
