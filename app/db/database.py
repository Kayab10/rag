# database.py - Supabase client connection.
# Phase 3.1
#
# Single get_client() used by all db modules.
# Reads SUPABASE_URL and SUPABASE_KEY from config.

from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


@lru_cache
def get_client() -> Client:
    """
    Return a cached Supabase client instance.
    Created once on first call, reused for all subsequent calls.
    """
    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env before using the database."
        )

    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
