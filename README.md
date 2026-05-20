# RAG Chatbot

A production-ready conversational AI application that lets users upload their own documents and have intelligent, context-aware conversations about them. The system is built around the Retrieval-Augmented Generation (RAG) pattern, combining the reasoning power of Google Gemini with a persistent vector database to deliver accurate, grounded answers.

---

## What is this project?

Most AI chatbots either hallucinate facts or have no knowledge of your private documents. This application solves both problems. Users upload their own files — research papers, textbooks, syllabi, notes — and the system learns from them. When a user asks a question, the app finds the most relevant parts of their documents and gives them to Gemini as context, so the model can answer accurately without making things up.

The key insight is that the model does not need to memorize your documents. Instead, it retrieves the relevant pieces at query time and reasons over them. This is what RAG means — Retrieval-Augmented Generation.

---

## How it works

When a user uploads a document, the system reads the text, breaks it into smaller overlapping pieces called chunks, and converts each chunk into a vector — a list of numbers that captures the meaning of that text. These vectors are stored in a cloud vector database called Qdrant, organized per user so that no one can access another user's documents.

When a user asks a question, the system converts the question into a vector using the same embedding model, then searches the vector database for the chunks whose meaning is closest to the question. The top matching chunks are assembled into a prompt alongside the user's question and the recent conversation history, and sent to Gemini. Gemini reads the context and generates a detailed, conversational answer.

The model is instructed to behave like a knowledgeable tutor — it uses the documents as its primary reference but draws on its own training knowledge to fill gaps, explain concepts in depth, and maintain a natural conversation. This means if you upload a syllabus that mentions linear algebra, the model can both tell you what your syllabus says about it and explain the subject in full detail.

---

## Features

**User authentication and isolation.** Every user registers with a username and password. Passwords are hashed with bcrypt and never stored in plain text. Authentication uses JWT tokens, which are short-lived signed credentials that prove identity without storing session state on the server. Each user's documents are stored in a completely separate Qdrant collection, so queries never return results from another user's files.

**Document ingestion.** The system supports PDF, plain text, and Markdown files. PDFs are parsed page by page. Text is split using a recursive splitter that respects natural boundaries — it tries to break at paragraph breaks first, then line breaks, then sentence endings, and only falls back to character-level splitting as a last resort. This produces cleaner chunks that preserve meaning better than naive character-based splitting.

**Duplicate detection.** Before ingesting a file, the system computes a SHA-256 hash of the file contents and checks whether that hash already exists in the user's document records. If it does, the upload is skipped immediately without re-embedding or re-storing anything. This prevents the vector database from accumulating duplicate chunks when the same file is uploaded multiple times.

**Batched embedding.** Embedding is the process of converting text into vectors. The Gemini embedding model supports processing up to 100 texts in a single API call. The system takes advantage of this by batching all chunks from a document together, which is significantly faster than making one API call per chunk.

**Persistent chat memory.** Every message in a conversation — both user questions and assistant answers — is saved to a Supabase PostgreSQL database. When a user logs in, their full conversation history is loaded and displayed. When they ask a new question, the last ten messages are included in the prompt so Gemini has context of the ongoing conversation. This means the model remembers what was discussed earlier in the session and can answer follow-up questions coherently.

**Hybrid answering.** The prompt instructs Gemini to use the retrieved document chunks as its primary source but to supplement with its own knowledge when needed. This means the model will not refuse to explain a concept just because the exact explanation is not in the uploaded document. It behaves like a tutor who has read your materials and can also teach beyond them.

**Path traversal protection.** File names submitted by users are sanitized before being used to save or delete files on disk. This prevents a malicious filename like `../../etc/passwd` from escaping the intended upload directory.

---

## Technology choices and why

**FastAPI** was chosen for the backend because it is fast, has automatic API documentation, and integrates cleanly with Pydantic for request validation. It also supports async endpoints natively, which matters for file upload handling.

**Streamlit** was chosen for the frontend because it lets you build a functional, interactive UI entirely in Python without writing any HTML, CSS, or JavaScript. For a project focused on backend and AI logic, this keeps the frontend simple and maintainable.

**Google Gemini** is used for both embeddings and chat generation. Using a single provider for both simplifies the setup and ensures the embedding space and generation model are well-matched. The `gemini-embedding-001` model produces 3072-dimensional vectors, and `gemini-2.5-flash` handles generation.

**Qdrant Cloud** is a purpose-built vector database that supports cosine similarity search efficiently. It was chosen over local alternatives like ChromaDB because it is a managed cloud service — data persists across server restarts, which is essential for deployment on platforms like Render where the local filesystem is ephemeral.

**Supabase** provides a managed PostgreSQL database with a clean Python client. It stores user accounts, document metadata, and chat history. Like Qdrant, it is a cloud service that survives server restarts, making it suitable for production deployment.

**bcrypt** is the industry standard for password hashing. It is deliberately slow, which makes brute-force attacks computationally expensive. Each password is hashed with a unique random salt, so identical passwords produce different hashes.

**JWT (JSON Web Tokens)** are used for authentication. After login, the server issues a signed token containing the user's ID and an expiry time. The client sends this token with every request. The server verifies the signature without needing to look up a session in the database, which keeps authentication stateless and fast.

---

## Project structure

The codebase is organized into layers, each with a single responsibility.

The `core` layer contains pure RAG logic — document loading, text splitting, embedding, vector store operations, retrieval, prompt building, and pipeline orchestration. This layer knows nothing about users, HTTP, or authentication.

The `auth` layer handles password hashing, JWT creation and verification, and the FastAPI dependency that extracts the current user from a request header.

The `db` layer contains all database operations against Supabase — creating and fetching users, saving document records, and reading and writing chat history.

The `services` layer sits between the API routes and the core/db layers. It contains the business logic — for example, checking for duplicate files before ingesting, loading chat history before running the pipeline, and saving messages after getting an answer.

The `api` layer contains the FastAPI route handlers. Each route is thin — it validates the request, calls a service function, and returns the result. All the real logic lives in the service layer.

The `models` layer contains Pydantic models that define the shape of API requests and responses. FastAPI uses these for automatic validation and documentation.

The `frontend` directory contains the entire Streamlit application — login, registration, document management sidebar, and the chat interface.

---

## Local setup

You will need a Google Gemini API key, a Supabase project with the three tables created (users, documents, chat_history), and a Qdrant Cloud cluster. All three have free tiers sufficient for development and light production use.

Copy `.env.example` to `.env` and fill in your API keys and URLs. The application reads all configuration from this file at startup — nothing is hardcoded.

Start the FastAPI backend with `uvicorn app.main:app --reload` and the Streamlit frontend with `streamlit run frontend/streamlit_app.py` in separate terminals. The backend runs on port 8000 and the frontend on port 8501.

The interactive API documentation is available at `http://localhost:8000/docs` while the backend is running. You can test every endpoint directly from the browser without needing a separate API client.

---

## Deployment

The backend is designed to deploy on Render. A `render.yaml` file at the project root tells Render how to build and start the service. The only manual step is adding the secret environment variables (API keys) through the Render dashboard, since those should never be committed to the repository.

The frontend deploys on Streamlit Cloud. After connecting the GitHub repository, you set the `API_BASE` secret to point at your Render backend URL. Streamlit Cloud reads this at runtime and the frontend automatically connects to the production backend instead of localhost.

Both Qdrant and Supabase are external cloud services, so all data persists independently of the backend server. Render can restart or redeploy the backend without any data loss.

---

## Testing

The project includes five CLI test scripts that can be run independently to verify each layer of the system. The chunking test requires no API calls and verifies that documents load and split correctly. The retrieval test verifies the full embedding and vector store pipeline. The pipeline test runs end-to-end questions through the complete RAG flow. The database test verifies all Supabase operations. The auth test verifies password hashing, JWT tokens, and the register and login endpoints.
