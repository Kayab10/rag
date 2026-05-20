# chat_history.py - Chat history CRUD against Supabase chat_history table.
# Phase 3.4
#
# Table schema:
#   id         UUID  PRIMARY KEY DEFAULT gen_random_uuid()
#   user_id    UUID  REFERENCES users(id) ON DELETE CASCADE
#   role       TEXT  NOT NULL  — 'user' or 'assistant'
#   message    TEXT  NOT NULL
#   created_at TIMESTAMPTZ DEFAULT now()

from app.config import get_settings
from app.db.database import get_client


def save_message(user_id: str, role: str, message: str) -> dict:
    """
    Insert a single chat message into the history table.

    Parameters
    ----------
    user_id : str   UUID of the user.
    role    : str   'user' or 'assistant'
    message : str   The message content.

    Returns
    -------
    dict  The created row.
    """
    if role not in ("user", "assistant"):
        raise ValueError(f"role must be 'user' or 'assistant', got '{role}'")

    client = get_client()

    response = (
        client.table("chat_history")
        .insert({
            "user_id": user_id,
            "role":    role,
            "message": message,
        })
        .execute()
    )

    return response.data[0]


def get_history(user_id: str, limit: int | None = None) -> list[dict]:
    """
    Return the last N messages for a user, ordered oldest → newest.
    This order is important — the LLM needs chronological context.

    Parameters
    ----------
    user_id : str
    limit   : int  Number of messages to return. Defaults to config CHAT_HISTORY_LIMIT.

    Returns
    -------
    list[dict]
        [{"role": "user", "message": "..."}, {"role": "assistant", "message": "..."}, ...]
    """
    settings = get_settings()
    limit = limit or settings.CHAT_HISTORY_LIMIT

    client = get_client()

    # Fetch last N messages (newest first), then reverse for chronological order
    response = (
        client.table("chat_history")
        .select("role, message, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    # Reverse so oldest message is first (chronological for LLM context)
    messages = list(reversed(response.data or []))

    return messages
