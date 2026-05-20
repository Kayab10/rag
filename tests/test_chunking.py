# test_chunking.py - CLI test for document_loader and text_splitter.
#
# Tests:
#   1. Load each PDF from data/raw/
#   2. Print extracted text preview per page
#   3. Split into chunks
#   4. Print chunk stats and previews
#
# Run with:
#   python tests/test_chunking.py

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.document_loader import load_document, SUPPORTED_EXTENSIONS
from app.core.text_splitter import split_documents

# ── Config ────────────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
PREVIEW_CHARS = 200   # how many characters to preview per chunk/page


def divider(title: str = ""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def test_file(file_path: Path):
    divider(f"FILE: {file_path.name}")

    # ── Step 1: Load ──────────────────────────────────────────────────────────
    print("\n[1] Loading document...")
    docs = load_document(file_path)
    print(f"    Pages/sections loaded : {len(docs)}")

    for i, doc in enumerate(docs):
        preview = doc["text"][:PREVIEW_CHARS].replace("\n", " ")
        print(f"\n    Page {doc['metadata']['page_number']} preview:")
        print(f"    {preview}...")

    # ── Step 2: Chunk ─────────────────────────────────────────────────────────
    print("\n[2] Splitting into chunks...")
    chunks = split_documents(docs)
    print(f"    Total chunks produced : {len(chunks)}")

    # Print first 3 chunks as sample
    for chunk in chunks[:3]:
        meta    = chunk["metadata"]
        preview = chunk["text"][:PREVIEW_CHARS].replace("\n", " ")
        print(
            f"\n    Chunk {meta['chunk_index'] + 1}/{meta['total_chunks']} "
            f"| Page {meta['page_number']} | {meta['file_name']}"
        )
        print(f"    {preview}...")

    print(f"\n    ✓ {file_path.name} — {len(docs)} pages → {len(chunks)} chunks")
    return len(docs), len(chunks)


def main():
    divider("CHUNKING TEST")
    print(f"  Scanning: {RAW_DIR.resolve()}")
    print(f"  Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")

    pdf_files = [
        f for f in sorted(RAW_DIR.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not pdf_files:
        print("\n  No supported files found in data/raw/")
        print("  Add some .pdf or .txt files and try again.")
        sys.exit(1)

    print(f"\n  Found {len(pdf_files)} file(s): {[f.name for f in pdf_files]}")

    total_pages  = 0
    total_chunks = 0

    for file_path in pdf_files:
        try:
            pages, chunks = test_file(file_path)
            total_pages  += pages
            total_chunks += chunks
        except Exception as e:
            print(f"\n  ✗ Failed to process {file_path.name}: {e}")

    divider("SUMMARY")
    print(f"  Files processed : {len(pdf_files)}")
    print(f"  Total pages     : {total_pages}")
    print(f"  Total chunks    : {total_chunks}")
    print("\n  ✓ Chunking test complete. No API calls were made.")


if __name__ == "__main__":
    main()
