# auth_handler.py - JWT token creation and verification.


from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

_settings = get_settings()


def create_token(user_id: str) -> str:
    """
    Create a signed JWT token containing the user_id.

    Parameters
    ----------
    user_id : str  UUID of the authenticated user.

    Returns
    -------
    str  Signed JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,           # subject — who this token belongs to
        "exp": expire,            # expiry timestamp
        "iat": datetime.now(timezone.utc),  # issued at
    }

    return jwt.encode(payload, _settings.JWT_SECRET, algorithm=_settings.JWT_ALGORITHM)


def decode_token(token: str) -> str:
    """
    Decode and verify a JWT token.

    Parameters
    ----------
    token : str  The JWT string from the Authorization header.

    Returns
    -------
    str  The user_id (sub claim) from the token.

    Raises
    ------
    ValueError  If the token is expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            _settings.JWT_SECRET,
            algorithms=[_settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing subject claim.")
        return user_id

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired. Please log in again.")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
