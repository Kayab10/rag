# users.py - User CRUD operations against Supabase users table.
# Phase 3.2
#
# Table schema:
#   id            UUID  PRIMARY KEY DEFAULT gen_random_uuid()
#   username      TEXT  UNIQUE NOT NULL
#   password_hash TEXT  NOT NULL
#   created_at    TIMESTAMPTZ DEFAULT now()

from app.db.database import get_client


def create_user(username: str, password_hash: str) -> dict:
    """
    Insert a new user into the users table.

    Parameters
    ----------
    username      : str  Must be unique.
    password_hash : str  bcrypt hash — never store plain text.

    Returns
    -------
    dict  The created user row: {id, username, password_hash, created_at}

    Raises
    ------
    ValueError  If the username is already taken.
    """
    client = get_client()

    response = (
        client.table("users")
        .insert({"username": username, "password_hash": password_hash})
        .execute()
    )

    if not response.data:
        raise ValueError(f"Username '{username}' is already taken.")

    return response.data[0]


def get_user_by_username(username: str) -> dict | None:
    """
    Fetch a user row by username.

    Parameters
    ----------
    username : str

    Returns
    -------
    dict | None
        The user row if found, None if no user with that username exists.
    """
    client = get_client()

    response = (
        client.table("users")
        .select("*")
        .eq("username", username)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]
