# dependencies.py - Shared FastAPI dependencies.
#
# Import get_current_user from here in all protected routes
# so there's one central place to manage auth dependencies.

from app.auth.auth_bearer import get_current_user

__all__ = ["get_current_user"]
