# test_db.py - CLI test for the Supabase database layer.
#
# Tests:
#   1. Connection to Supabase
#   2. Create a test user
#   3. Fetch user by username
#   4. Save a document record
#   5. Duplicate hash check
#   6. List documents for user
#   7. Save chat messages
#   8. Fetch chat history
#   9. Cleanup — delete test data
#
# ⚠  Requires SUPABASE_URL and SUPABASE_KEY in .env
#
# Run with:
#   python tests/test_db.py

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_client
from app.db.users import create_user, get_user_by_username
from app.db.documents import save_document, get_document_by_hash, list_documents
from app.db.chat_history import save_message, get_history

# ── Test data ─────────────────────────────────────────────────────────────────
TEST_USERNAME  = "test_user_phase3"
TEST_PASSWORD  = "hashed_password_placeholder"   # real hashing done in Phase 4
TEST_FILE_NAME = "test_notes.pdf"
TEST_FILE_HASH = "abc123def456"                  # fake hash for testing


def divider(title: str = ""):
    print("\n" + "=" * 55)
    if title:
        print(f"  {title}")
        print("=" * 55)


def main():
    divider("SUPABASE DB LAYER TEST")
    print("  ⚠  Requires SUPABASE_URL and SUPABASE_KEY in .env")

    user_id = None

    # ── 1. Connection ─────────────────────────────────────────────────────────
    divider("1 — Connection")
    try:
        client = get_client()
        print("  ✓ Supabase client created successfully")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        sys.exit(1)

    # ── 2. Create user ────────────────────────────────────────────────────────
    divider("2 — Create User")
    try:
        # Clean up any leftover test user from a previous run
        existing = get_user_by_username(TEST_USERNAME)
        if existing:
            client.table("users").delete().eq("username", TEST_USERNAME).execute()
            print(f"  Cleaned up existing test user")

        user = create_user(TEST_USERNAME, TEST_PASSWORD)
        user_id = user["id"]
        print(f"  ✓ User created")
        print(f"    id       : {user_id}")
        print(f"    username : {user['username']}")
        print(f"    created  : {user['created_at']}")
    except Exception as e:
        print(f"  ✗ Create user failed: {e}")
        sys.exit(1)

    # ── 3. Fetch user by username ─────────────────────────────────────────────
    divider("3 — Get User by Username")
    try:
        fetched = get_user_by_username(TEST_USERNAME)
        assert fetched is not None, "User not found"
        assert fetched["id"] == user_id, "ID mismatch"
        print(f"  ✓ User fetched correctly")
        print(f"    username : {fetched['username']}")

        missing = get_user_by_username("nonexistent_user_xyz")
        assert missing is None, "Should return None for unknown user"
        print(f"  ✓ Returns None for unknown username")
    except Exception as e:
        print(f"  ✗ Get user failed: {e}")

    # ── 4. Save document ──────────────────────────────────────────────────────
    divider("4 — Save Document")
    try:
        doc = save_document(
            user_id=user_id,
            file_name=TEST_FILE_NAME,
            file_hash=TEST_FILE_HASH,
            chunks_stored=42,
        )
        print(f"  ✓ Document saved")
        print(f"    id            : {doc['id']}")
        print(f"    file_name     : {doc['file_name']}")
        print(f"    chunks_stored : {doc['chunks_stored']}")
    except Exception as e:
        print(f"  ✗ Save document failed: {e}")

    # ── 5. Duplicate hash check ───────────────────────────────────────────────
    divider("5 — Duplicate Hash Check")
    try:
        duplicate = get_document_by_hash(user_id, TEST_FILE_HASH)
        assert duplicate is not None, "Should find the document by hash"
        print(f"  ✓ Duplicate detected correctly")
        print(f"    file_name : {duplicate['file_name']}")

        no_match = get_document_by_hash(user_id, "nonexistent_hash_xyz")
        assert no_match is None, "Should return None for unknown hash"
        print(f"  ✓ Returns None for unknown hash")
    except Exception as e:
        print(f"  ✗ Hash check failed: {e}")

    # ── 6. List documents ─────────────────────────────────────────────────────
    divider("6 — List Documents")
    try:
        docs = list_documents(user_id)
        assert len(docs) >= 1, "Should have at least one document"
        print(f"  ✓ Listed {len(docs)} document(s)")
        for d in docs:
            print(f"    • {d['file_name']} | {d['chunks_stored']} chunks")
    except Exception as e:
        print(f"  ✗ List documents failed: {e}")

    # ── 7. Save chat messages ─────────────────────────────────────────────────
    divider("7 — Save Chat Messages")
    try:
        m1 = save_message(user_id, "user",      "What is RAG?")
        m2 = save_message(user_id, "assistant", "RAG stands for Retrieval-Augmented Generation.")
        m3 = save_message(user_id, "user",      "How does it work?")
        print(f"  ✓ Saved 3 messages")
    except Exception as e:
        print(f"  ✗ Save message failed: {e}")

    # ── 8. Fetch chat history ─────────────────────────────────────────────────
    divider("8 — Fetch Chat History")
    try:
        history = get_history(user_id, limit=10)
        assert len(history) == 3, f"Expected 3 messages, got {len(history)}"
        print(f"  ✓ Fetched {len(history)} messages (chronological order)")
        for msg in history:
            print(f"    [{msg['role']:9}] {msg['message']}")
    except Exception as e:
        print(f"  ✗ Get history failed: {e}")

    # ── 9. Cleanup ────────────────────────────────────────────────────────────
    divider("9 — Cleanup")
    try:
        # Deleting the user cascades to documents and chat_history
        client.table("users").delete().eq("id", user_id).execute()
        print(f"  ✓ Test user and all related data deleted")
    except Exception as e:
        print(f"  ✗ Cleanup failed: {e}")
        print(f"    Manually delete user '{TEST_USERNAME}' from Supabase if needed")

    divider("RESULT")
    print("  ✓ DB layer test complete.")
    


if __name__ == "__main__":
    main()
