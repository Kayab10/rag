# ingest_documents.py - Bulk ingest all files from data/raw/ into the vector store.
#
# Current (v0.1): ingests into the shared ChromaDB collection.
# Phase 5 update: will require a user_id for per-user Qdrant collections.
#
# Run with:
#   python scripts/ingest_documents.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.document_loader import load_documents_from_folder
from app.core.text_splitter import split_documents
from app.core.vector_store import add_documents, get_collection_info, reset_collection

RAW_DIR = Path("data/raw")


def main():
    print("=" * 50)
    print("  BULK DOCUMENT INGESTION")
    print("=" * 50)

    print(f"\nLoading documents from {RAW_DIR}...")
    docs = load_documents_from_folder(RAW_DIR)
    print(f"Loaded {len(docs)} pages")

    if not docs:
        print("No supported files found in data/raw/. Exiting.")
        sys.exit(1)

    chunks = split_documents(docs)
    print(f"Split into {len(chunks)} chunks")

    print("\nResetting collection and re-ingesting...")
    reset_collection()
    added = add_documents(chunks)

    info = get_collection_info()
    print(f"\n✓ Done — {added} chunks stored in '{info['collection_name']}'")


if __name__ == "__main__":
    main()
