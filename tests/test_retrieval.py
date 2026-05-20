# test_retrieval.py - CLI test for embeddings, vector store, and retriever.
#
# Steps:
#   1. Load + chunk all PDFs from data/raw/
#   2. Embed chunks and store in ChromaDB
#   3. Run test queries and show retrieved results + scores
#
# ⚠ This test calls the Google Gemini Embedding API — make sure GOOGLE_API_KEY is set in .env
#
# Run with:
#   python tests/test_retrieval.py

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.document_loader import load_documents_from_folder, SUPPORTED_EXTENSIONS
from app.core.text_splitter import split_documents
from app.core.vector_store import add_documents, search, get_collection_info, reset_collection
from app.core.retriever import retrieve

# ── Config ────────────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
PREVIEW_CHARS = 250

# Test queries — edit these to match your uploaded documents
TEST_QUERIES = [
    "What is this document about?",
    "Summarize the main topics covered.",
    "What are the key concepts mentioned?",
]


def divider(title: str = ""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def main():
    divider("RETRIEVAL TEST")
    print("  This test will:")
    print("  1. Ingest all files from data/raw/ into ChromaDB")
    print("  2. Run test queries and show top results")
    print(f"\n  ⚠  Calls Google Gemini Embedding API")

    # ── Step 1: Load documents ────────────────────────────────────────────────
    divider("STEP 1 — Load Documents")
    docs = load_documents_from_folder(RAW_DIR)
    print(f"  Loaded {len(docs)} pages from {RAW_DIR}")

    if not docs:
        print("  No supported files found. Add PDFs to data/raw/ and retry.")
        sys.exit(1)

    # ── Step 2: Chunk ─────────────────────────────────────────────────────────
    divider("STEP 2 — Split into Chunks")
    chunks = split_documents(docs)
    print(f"  {len(docs)} pages → {len(chunks)} chunks")

    # ── Step 3: Reset + ingest into ChromaDB ──────────────────────────────────
    divider("STEP 3 — Embed + Store in ChromaDB")
    print("  Resetting collection (fresh start)...")
    reset_collection()

    print(f"  Embedding and storing {len(chunks)} chunks...")
    print("  (this may take a moment — one API call per chunk)\n")

    added = add_documents(chunks)
    info  = get_collection_info()

    print(f"  ✓ Stored {added} chunks")
    print(f"  Collection: '{info['collection_name']}' | Total: {info['total_chunks']}")

    # ── Step 4: Run test queries ───────────────────────────────────────────────
    divider("STEP 4 — Test Queries")

    for query in TEST_QUERIES:
        print(f"\n  Query: \"{query}\"")
        print("  " + "-" * 50)

        results = retrieve(query)

        if not results:
            print("  No results found.")
            continue

        for i, result in enumerate(results, start=1):
            meta    = result["metadata"]
            score   = result["score"]
            preview = result["text"][:PREVIEW_CHARS].replace("\n", " ")

            print(f"\n  [{i}] Score: {score:.4f} | {meta.get('file_name','?')} | Page {meta.get('page_number','?')}")
            print(f"      {preview}...")

    divider("SUMMARY")
    print(f"  ✓ Ingested  : {len(chunks)} chunks from {RAW_DIR}")
    print(f"  ✓ Queries   : {len(TEST_QUERIES)} test queries ran")
    print(f"  ✓ ChromaDB  : {info['total_chunks']} chunks stored and ready")
    print("\n  Retrieval test complete. Ready for full RAG pipeline test.")


if __name__ == "__main__":
    main()
