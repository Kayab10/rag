import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.vector_store import _get_client


def main():
    client = _get_client()
    collections = client.get_collections().collections

    if not collections:
        print("No collections found.")
        return

    print(f"Found {len(collections)} collection(s):")
    for c in collections:
        print(f"  - {c.name}")

    confirm = input("\nDelete ALL collections? Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        sys.exit(0)

    for c in collections:
        client.delete_collection(c.name)
        print(f"  ✓ Deleted {c.name}")

    print("Done.")


if __name__ == "__main__":
    main()
