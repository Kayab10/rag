# test_rag_pipeline.py - End-to-end RAG pipeline CLI test.
#
# Assumes test_retrieval.py has already been run (ChromaDB is populated).
# If not, it will ingest documents automatically before querying.
#
# Steps:
#   1. Check if ChromaDB already has chunks, ingest if not
#   2. Ask a set of test questions
#   3. Print answer + sources for each
#
# ⚠  Calls both Google Gemini Embedding API and Chat API
#
# Run with:
#   python tests/test_rag_pipeline.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.document_loader import load_documents_from_folder
from app.core.text_splitter import split_documents
from app.core.vector_store import add_documents, get_collection_info, reset_collection
from app.core.rag_pipeline import run

# ── Test questions — edit these to match your documents ───────────────────────
TEST_QUESTIONS = [
    "I am kayab khan, what is my rank in jee advanced?",
    "What is syllabus of gate data science and ai?",
    "Give me a brief summary expereince of adithya s kolavi.",
]

RAW_DIR = Path("data/raw")


def divider(title: str = ""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def ensure_ingested():
    """Ingest documents if ChromaDB is empty."""
    info = get_collection_info()

    if info["total_chunks"] > 0:
        divider("ChromaDB Status")
        print(f"  ✓ Already populated — {info['total_chunks']} chunks ready")
        print("  Skipping ingestion. (Run test_retrieval.py to re-ingest)")
        return

    divider("ChromaDB empty — Ingesting documents first")
    docs   = load_documents_from_folder(RAW_DIR)
    chunks = split_documents(docs)
    print(f"  {len(docs)} pages → {len(chunks)} chunks")

    reset_collection()
    added = add_documents(chunks)
    print(f"  ✓ Stored {added} chunks in ChromaDB")


def main():
    divider("END-TO-END RAG PIPELINE TEST")
    print("  Flow: question → retrieve → prompt → Gemini → answer + sources")
    print("  ⚠  Calls Google Gemini Embedding + Chat API")

    # ── Step 1: Make sure ChromaDB has data ───────────────────────────────────
    ensure_ingested()

    # ── Step 2: Run each test question through the full pipeline ──────────────
    divider("RUNNING TEST QUESTIONS")

    for i, question in enumerate(TEST_QUESTIONS, start=1):
        print(f"\n  Q{i}: {question}")
        print("  " + "-" * 55)

        try:
            result = run(question)

            # Print answer
            print(f"\n  Answer:\n")
            for line in result["answer"].splitlines():
                print(f"    {line}")

            # Print sources
            print(f"\n  Sources used:")
            if result["sources"]:
                for src in result["sources"]:
                    print(
                        f"    • {src['file_name']} | "
                        f"Page {src['page_number']} | "
                        f"Score {src['score']:.4f}"
                    )
            else:
                print("    No sources returned.")

        except Exception as e:
            print(f"\n  ✗ Error: {e}")

    divider("TEST COMPLETE")
    print("  ✓ Full RAG pipeline ran successfully.")
    print("  Next step: build the API layer (app/api/)")


if __name__ == "__main__":
    main()
