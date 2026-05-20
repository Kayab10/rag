# password.py - bcrypt password hashing and verification.


import bcrypt


def hash_password(plain: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Parameters
    ----------
    plain : str  The user's plain-text password.

    Returns
    -------
    str  The bcrypt hash string (safe to store in DB).
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Parameters
    ----------
    plain  : str  The password the user typed at login.
    hashed : str  The hash stored in the database.

    Returns
    -------
    bool  True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
